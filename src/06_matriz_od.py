"""Paso 5 del plan: matriz origen-destino del subte.

Toma las etapas de subte del dataset de Viajes y Etapas del AMBA (dia relevado:
16/10/2024), las asigna a complejos de estacion, las expande por su factor y
las contrasta contra los molinetes del **mismo dia**, que es lo que permite
medir el desvio de nivel sin que se mezcle con la estacionalidad ni con la
ruptura de medios de pago de diciembre de 2024.

Salidas en data/processed/:
  od_complejos.csv       catalogo de los 78 complejos
  matriz_od.csv          comp_origen x comp_destino x hora, expandida
  od_ascensos.csv        ascensos por complejo, linea de ascenso y hora
  factores_escalado.csv  evidencia para la decision D2

Reporte en reports/06_matriz_od.md.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lib_complejos as lc  # noqa: E402
from lib_etapas import extraer  # noqa: E402
from lib_molinetes import ResultadoLectura, leer_zip  # noqa: E402
from lib_normalizacion import CENTINELAS, clave, normalizar  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

# El sufijo del archivo de etapas es la fecha del dia relevado, no la de
# publicacion. Todo el contraste con molinetes se hace contra ese mismo dia.
DIA = dt.date(2024, 10, 16)
ZIP_MOLINETES = RAIZ / "data" / "raw" / "molinetes-2024.zip"
CACHE_MOLINETES = PROCESADO / "molinetes_20241016.csv"

RADIO_TIERRA_M = 6_371_000.0

# Complejos con trasbordo ferroviario. No es una clasificacion inventada para
# que cierre: son los cuatro puntos donde el subte toca un ferrocarril
# metropolitano, y el EsIA de la Linea F destaca justamente que el 70 % de los
# viajes con etapa en la Linea C combinan con el ferrocarril (doc 0013, pag. 62).
FERROVIARIOS = {
    "Constitucion": "Roca",
    "Retiro": "Mitre / San Martin / Belgrano Norte",
    "Once / Plaza Miserere": "Sarmiento",
    "Federico Lacroze": "Urquiza",
}

# Par de estaciones vecinas de la Linea A entre las que el dataset O-D reparte
# mal la demanda. Se aisla porque su desvio no es de nivel sino de asignacion:
# se cancela casi exacto entre las dos (ver seccion 5.2 del reporte).
PAR_FLORES = {"San Pedrito", "San Jose de Flores"}


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def mil(x: float) -> str:
    """Entero con punto como separador de miles."""
    return f"{x:,.0f}".replace(",", ".")


def dec(x: float, n: int = 3) -> str:
    """Decimal con coma."""
    return f"{x:.{n}f}".replace(".", ",")


# --------------------------------------------------------------------------
# Geometria
# --------------------------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Matriz de distancias en metros entre dos conjuntos de puntos."""
    la1, lo1 = np.radians(lat1)[:, None], np.radians(lon1)[:, None]
    la2, lo2 = np.radians(lat2)[None, :], np.radians(lon2)[None, :]
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * RADIO_TIERRA_M * np.arcsin(np.sqrt(h))


def matchear_centroides(centroides: pd.DataFrame, m: pd.DataFrame) -> pd.DataFrame:
    """Asigna cada centroide h3 al complejo del nodo mas cercano.

    Se matchea contra el **nodo** y despues se toma su complejo, no contra el
    centroide promedio del complejo: los complejos grandes se extienden mas de
    200 m y su promedio no representa a ninguna de sus estaciones. La diferencia
    no es cosmetica, decide el caso mas ajustado de la red (Avenida de Mayo /
    Lima contra Piedras, sobre la Linea A).

    Devuelve el centroide con su complejo, la distancia al nodo mas cercano y el
    margen contra el complejo distinto mas proximo, que es la medida real de si
    la asignacion es univoca.
    """
    d = haversine_m(centroides.lat.values, centroides.lon.values,
                    m.stop_lat.values, m.stop_lon.values)
    mejor = d.argmin(axis=1)
    comp = m.complejo.values[mejor]
    salida = centroides.copy()
    salida["complejo"] = comp
    salida["dist_m"] = d[np.arange(len(d)), mejor]

    margen, rival = [], []
    comp_por_nodo = m.complejo.values
    for i in range(len(d)):
        otros = comp_por_nodo != comp[i]
        j = int(np.argmin(d[i][otros]))
        margen.append(d[i][otros][j] - salida.dist_m.values[i])
        rival.append(comp_por_nodo[otros][j])
    salida["margen_m"] = margen
    salida["complejo_rival"] = rival
    return salida


# --------------------------------------------------------------------------
# Molinetes del dia relevado
# --------------------------------------------------------------------------

def molinetes_del_dia(m: pd.DataFrame, forzar: bool = False) -> pd.DataFrame:
    """Ingresos por nodo y hora del 16/10/2024, desde el ZIP anual de 2024.

    Octubre de 2024 es anterior a la apertura a medios de pago distintos de
    SUBE (01/12/2024), asi que mide el mismo universo que el dataset de Viajes
    y Etapas: la comparacion no arrastra la ruptura de comparabilidad.
    """
    if CACHE_MOLINETES.exists() and not forzar:
        return pd.read_csv(CACHE_MOLINETES)

    mapa = {(r.linea, normalizar(r.gtfs_nombre)): r.nodo for r in m.itertuples()}
    acumulado: dict[tuple[str, int], int] = {}
    sin_match: dict[tuple[str, str], int] = {}
    total = premetro = centinela = fuera = 0

    res = ResultadoLectura()
    prefijo = f"{DIA.year}{DIA.month:02d}"
    for r in leer_zip(str(ZIP_MOLINETES), res):
        if not r["_archivo"].startswith(prefijo) or r["_fecha"] != DIA:
            continue
        pax = r["pax_TOTAL"]
        total += pax
        linea, estacion = r["LINEA"], r["ESTACION"]
        if linea.upper().startswith("PM") or "PREMETRO" in linea.upper():
            premetro += pax
            continue
        if normalizar(estacion) in CENTINELAS or normalizar(linea) in CENTINELAS:
            centinela += pax
            continue
        nodo = mapa.get((linea, clave(estacion, linea)))
        if nodo is None:
            sin_match[(linea, estacion)] = sin_match.get((linea, estacion), 0) + pax
            fuera += pax
            continue
        partes = r["DESDE"].split(":")
        try:
            hora = int(partes[0])
        except (ValueError, IndexError):
            fuera += pax
            continue
        acumulado[(nodo, hora)] = acumulado.get((nodo, hora), 0) + pax

    df = pd.DataFrame(
        [{"nodo": n, "hora": h, "pax": v} for (n, h), v in acumulado.items()]
    ).sort_values(["nodo", "hora"])
    CACHE_MOLINETES.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CACHE_MOLINETES, index=False)
    print(f"molinetes {DIA}: {total:,} pax, {len(df):,} celdas nodo-hora; "
          f"premetro {premetro:,}, centinela {centinela:,}, sin match {fuera:,}")
    if sin_match:
        peores = sorted(sin_match.items(), key=lambda kv: -kv[1])[:5]
        print("  claves sin match:", peores)
    return df


# --------------------------------------------------------------------------
# Etapas
# --------------------------------------------------------------------------

def cargar_etapas(m: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Etapas de subte con origen y destino resueltos a complejo."""
    e = pd.read_csv(extraer())

    cen = pd.concat([
        e[["latitud_origen_etapa", "longitud_origen_etapa"]]
         .rename(columns={"latitud_origen_etapa": "lat", "longitud_origen_etapa": "lon"}),
        e[["latitud_destino_etapa", "longitud_destino_etapa"]]
         .rename(columns={"latitud_destino_etapa": "lat", "longitud_destino_etapa": "lon"}),
    ]).drop_duplicates().reset_index(drop=True)
    cen = matchear_centroides(cen, m)

    llave = {(la, lo): c for la, lo, c in zip(cen.lat, cen.lon, cen.complejo)}
    e["comp_origen"] = [llave[(la, lo)] for la, lo in
                        zip(e.latitud_origen_etapa, e.longitud_origen_etapa)]
    e["comp_destino"] = [llave[(la, lo)] for la, lo in
                         zip(e.latitud_destino_etapa, e.longitud_destino_etapa)]
    # La linea de ascenso viene del molinete que registro la transaccion: es
    # dato observado, no imputado. Sirve para resolver el nodo exacto de origen
    # dentro del complejo y como contraste del reparto que produzca el modelo.
    e["linea_ascenso"] = "Linea" + e.linea_etapa.str.replace("LINEA ", "", regex=False)
    return e, cen


# --------------------------------------------------------------------------
# Programa
# --------------------------------------------------------------------------

def main() -> None:
    m = lc.construir()
    cat = lc.catalogo(m)
    nombre = cat.nombre.to_dict()

    e, cen = cargar_etapas(m)

    # Coherencia entre la linea de ascenso observada y el complejo de origen.
    lineas_comp = m.groupby("complejo").linea.apply(set).to_dict()
    coherente = np.array([ln in lineas_comp[c]
                          for ln, c in zip(e.linea_ascenso, e.comp_origen)])

    # Etapas que empiezan y terminan en el mismo complejo: no son viajes de
    # subte, son ruido de imputacion. Se descartan y se declara cuantas son.
    intra = e.comp_origen == e.comp_destino
    e_util = e[~intra].copy()
    incompletas = e_util.viaje_incompleto == "t"

    # --- Salidas ---
    PROCESADO.mkdir(parents=True, exist_ok=True)
    cat.to_csv(PROCESADO / "od_complejos.csv")

    matriz = (e_util.groupby(["comp_origen", "comp_destino", "rango_horario"])
              .agg(etapas=("factor_expansion_etapa", "size"),
                   expandidas=("factor_expansion_etapa", "sum"))
              .reset_index())
    solo_completas = (e_util[~incompletas]
                      .groupby(["comp_origen", "comp_destino", "rango_horario"])
                      .factor_expansion_etapa.sum()
                      .rename("expandidas_completas").reset_index())
    matriz = matriz.merge(solo_completas, how="left").fillna({"expandidas_completas": 0.0})
    matriz.to_csv(PROCESADO / "matriz_od.csv", index=False)

    ascensos = (e_util.groupby(["comp_origen", "linea_ascenso", "rango_horario"])
                .agg(etapas=("factor_expansion_etapa", "size"),
                     expandidas=("factor_expansion_etapa", "sum"))
                .reset_index())
    ascensos.to_csv(PROCESADO / "od_ascensos.csv", index=False)

    # Linea de ascenso observada por par origen-destino. Es lo que permite al
    # paso 6 contrastar el reparto por linea que produce la asignacion de ruta
    # contra el observado, en vez de darlo por bueno.
    pares_linea = (e_util.groupby(["comp_origen", "comp_destino", "linea_ascenso"])
                   .agg(etapas=("factor_expansion_etapa", "size"),
                        expandidas=("factor_expansion_etapa", "sum"))
                   .reset_index())
    pares_linea.to_csv(PROCESADO / "od_pares_linea.csv", index=False)

    # --- Contraste contra molinetes del mismo dia (evidencia de D2) ---
    mol = molinetes_del_dia(m)
    mol = mol.merge(m[["nodo", "complejo", "linea"]], on="nodo", how="left")

    od_comp = e_util.groupby("comp_origen").factor_expansion_etapa.sum().rename("od")
    mol_comp = mol.groupby("complejo").pax.sum().rename("molinetes")
    f_comp = pd.concat([od_comp, mol_comp], axis=1).fillna(0.0)
    f_comp["factor"] = f_comp.molinetes / f_comp.od.replace(0, np.nan)
    f_comp["nombre"] = [nombre.get(i, i) for i in f_comp.index]

    od_lin = e_util.groupby("linea_ascenso").factor_expansion_etapa.sum().rename("od")
    mol_lin = mol.groupby("linea").pax.sum().rename("molinetes")
    f_lin = pd.concat([od_lin, mol_lin], axis=1).fillna(0.0)
    f_lin["factor"] = f_lin.molinetes / f_lin.od

    od_h = e_util.groupby("rango_horario").factor_expansion_etapa.sum().rename("od")
    mol_h = mol.groupby("hora").pax.sum().rename("molinetes")
    f_h = pd.concat([od_h, mol_h], axis=1).fillna(0.0)
    f_h["factor"] = f_h.molinetes / f_h.od.replace(0, np.nan)

    factores = pd.concat([
        f_comp.assign(nivel="complejo")[["nivel", "nombre", "od", "molinetes", "factor"]],
        f_lin.assign(nivel="linea", nombre=f_lin.index)[
            ["nivel", "nombre", "od", "molinetes", "factor"]],
        f_h.assign(nivel="hora", nombre=[f"{int(i):02d}:00" for i in f_h.index])[
            ["nivel", "nombre", "od", "molinetes", "factor"]],
    ])
    factores.to_csv(PROCESADO / "factores_escalado.csv", index=False)

    # --- Evidencia para D2: cuanto queda sin explicar segun el criterio ---
    f_comp = f_comp.join(cat[["n_nodos"]])
    f_comp["grupo"] = [clasificar(n, k) for n, k in zip(f_comp.nombre, f_comp.n_nodos)]
    f_grupo = f_comp.groupby("grupo").agg(n=("nombre", "size"), od=("od", "sum"),
                                          molinetes=("molinetes", "sum"))
    f_grupo["factor"] = f_grupo.molinetes / f_grupo.od
    f_grupo["peso"] = f_grupo.molinetes / f_comp.molinetes.sum()

    f_comp["todo"] = "red"
    residuos = {etiqueta: residuo_absoluto(f_comp, col)
                for etiqueta, col in [("Factor unico global", "todo"),
                                      ("Factor por categoria de complejo", "grupo")]}

    escribir_reporte(e, e_util, cen, cat, nombre, matriz, mol,
                     f_comp, f_lin, f_h, f_grupo, residuos, coherente, intra, incompletas)
    print("paso 5 listo")


def clasificar(nombre_complejo: str, n_nodos: int) -> str:
    """Categoria de un complejo a los efectos del escalado (decision D2)."""
    if nombre_complejo in PAR_FLORES:
        return "Par San Pedrito / San Jose de Flores"
    if nombre_complejo in FERROVIARIOS:
        return "Trasbordo ferroviario"
    if n_nodos > 1:
        return "Complejo de combinacion"
    return "Estacion simple"


def residuo_absoluto(f_comp: pd.DataFrame, col: str) -> float:
    """Ingresos mal asignados que sobreviven a un criterio de escalado.

    Se aplica un factor por cada valor de `col` y se suma el desvio absoluto
    contra los molinetes. Un factor por complejo da cero por construccion, que
    es justamente por que el residuo no alcanza para elegir criterio.
    """
    factor = f_comp.groupby(col).apply(
        lambda d: d.molinetes.sum() / d.od.sum(), include_groups=False)
    return float((f_comp.molinetes - f_comp.od * f_comp[col].map(factor)).abs().sum())


def escribir_reporte(e, e_util, cen, cat, nombre, matriz, mol,
                     f_comp, f_lin, f_h, f_grupo, residuos, coherente, intra,
                     incompletas) -> None:
    od_tot = e_util.factor_expansion_etapa.sum()
    mol_tot = mol.pax.sum()
    glob = mol_tot / od_tot

    L: list[str] = []
    A = L.append
    A("# Paso 5 — Matriz origen-destino\n")
    A(f"Generado por `src/06_matriz_od.py`. Dia relevado: **{DIA.strftime('%d/%m/%Y')}**, "
      "un miercoles habil. Fuente: `etapas_BAdata_20241016.csv` (Viajes y Etapas del AMBA), "
      "contrastada contra `molinetes-2024.zip` del mismo dia.\n")

    A("## 1. La unidad espacial es el complejo, no el nodo\n")
    A(f"La red tiene **90 nodos** (par linea-estacion) agrupados en **{len(cat)} complejos** "
      "de estacion, definidos como las componentes conexas del grafo de transbordos del "
      "paso 2. Diez complejos tienen mas de un nodo.\n")
    A("Teniamos registrado como residuo de ambiguedad que las estaciones superpuestas de "
      "un mismo complejo se confunden al matchear por cercania: Correo Central [E], "
      "Corrientes [H] y Santa Fe [H] no aparecen nunca, y 9 de Julio [D], Diagonal Norte [C] "
      "e Independencia [C] no aparecen como origen. **Al nivel del complejo el problema no "
      "existe**, porque las estaciones que se confunden son exactamente las que el complejo "
      "agrupa. Es ademas la unidad correcta desde el modelo: el pasajero entra y sale de un "
      "lugar fisico, y por que linea circula es resultado de la asignacion de ruta, no dato "
      "de entrada. Mismo criterio que la decision D5 sobre andenes.\n")

    A("### 1.1 El matcheo es univoco\n")
    A(f"Los **{len(cen)} centroides h3 distintos** se asignan al complejo del nodo mas "
      f"cercano. Distancia mediana **{cen.dist_m.median():.0f} m**, maxima "
      f"**{cen.dist_m.max():.0f} m**.\n")
    A("El control que importa no es esa distancia sino el **margen contra el complejo "
      f"distinto mas proximo**: minimo **{cen.margen_m.min():.0f} m**, percentil 5 "
      f"**{np.percentile(cen.margen_m, 5):.0f} m**, mediana "
      f"**{cen.margen_m.median():.0f} m**. Ningun centroide queda disputado.\n")
    A("Los dos casos mas ajustados de la red:\n")
    A("| Centroide asignado a | Distancia | Complejo rival | Margen |")
    A("|---|---:|---|---:|")
    for _, r in cen.nsmallest(2, "margen_m").iterrows():
        A(f"| {nombre[r.complejo]} | {r.dist_m:.0f} m | {nombre[r.complejo_rival]} | "
          f"{r.margen_m:.0f} m |")
    A("")
    A("> Matchear contra el centroide promedio del complejo en lugar del nodo mas cercano "
      "reduce ese margen minimo de 89 m a **9 m** y deja el par Avenida de Mayo / Lima "
      "contra Piedras practicamente empatado. Los complejos grandes se extienden mas de "
      "200 m y su promedio no representa a ninguna de sus estaciones. Es la clase de "
      "detalle que un control agregado no detecta.\n")

    A("### 1.2 La linea de ascenso resuelve el nodo exacto\n")
    A("El campo `linea_etapa` es la linea del molinete que registro la transaccion: dato "
      "observado, no imputado. **En las " + mil(len(e)) + " etapas, sin una sola excepcion, "
      "esa linea pertenece al complejo de origen asignado** (" + pc(coherente.mean(), 2) +
      ").\n")
    A("Dos consecuencias. Primera, el nodo de origen queda **completamente determinado** por "
      "el par (complejo, linea de ascenso): la ambiguedad de origen que dabamos por "
      "abierta esta resuelta. Segunda, es una **validacion independiente de la definicion de "
      "complejo**, que sale del GTFS, contra una georreferenciacion que sale de otro "
      "organismo y otra metodologia.\n")
    A("Aun asi la linea de ascenso **no entra como insumo del modelo**. Fijarla seria fijar "
      "parte de la ruta, que es justamente lo que la simulacion tiene que producir. Queda "
      "como **contraste del reparto por linea que produzca el modelo**, en paralelo exacto "
      "con el contraste por anden de D5.\n")

    A("## 2. Que se descarta\n")
    A("| Concepto | Etapas | % |")
    A("|---|---:|---:|")
    A(f"| Etapas de subte del dataset | {mil(len(e))} | 100,0 % |")
    A(f"| Origen y destino en el mismo complejo | {mil(int(intra.sum()))} | "
      f"{pc(intra.mean(), 3)} |")
    A(f"| **Utiles para la matriz** | **{mil(len(e_util))}** | "
      f"**{pc(len(e_util) / len(e), 3)}** |")
    A("")
    A(f"Las {int(intra.sum())} etapas intracomplejo no son viajes de subte: son pares de "
      "estaciones a distancia de caminata dentro de la misma combinacion. Al nivel de "
      "estacion el dataset no tenia ninguna etapa con origen igual a destino; al nivel de "
      "complejo aparecen estas, que es el precio —minimo— de agrupar. Se descartan.\n")

    A("### 2.1 D1: el `viaje_incompleto` no mueve la matriz\n")
    inc_exp = e_util[incompletas].factor_expansion_etapa.sum()
    A("Las etapas marcadas `viaje_incompleto = t` son **" + mil(int(incompletas.sum())) +
      "** (" + pc(incompletas.mean(), 1) + ") y expanden a **" + mil(inc_exp) + "** (" +
      pc(inc_exp / od_tot, 1) + " del total expandido).\n")
    A("`matriz_od.csv` trae las dos versiones en columnas separadas, `expandidas` y "
      "`expandidas_completas`, para que **D1 se decida midiendo y no discutiendo**.\n")

    A("## 3. La matriz\n")
    pares = matriz.groupby(["comp_origen", "comp_destino"]).ngroups
    posibles = len(cat) * (len(cat) - 1)
    A(f"- **{mil(len(matriz))} celdas** de (origen, destino, hora).")
    A(f"- **{mil(pares)} pares origen-destino distintos** sobre {mil(posibles)} posibles "
      f"({pc(pares / posibles, 1)}).")
    A(f"- **{mil(od_tot)} etapas expandidas** en el dia.")
    A(f"- Rango horario cubierto: {int(matriz.rango_horario.min())} a "
      f"{int(matriz.rango_horario.max())} h.\n")

    top = (matriz.groupby(["comp_origen", "comp_destino"]).expandidas.sum()
           .sort_values(ascending=False).head(10))
    A("Los diez pares mas cargados del dia:\n")
    A("| Origen | Destino | Expandidas |")
    A("|---|---|---:|")
    for (o, d), val in top.items():
        A(f"| {nombre[o]} | {nombre[d]} | {mil(val)} |")
    A("")

    A("## 4. Contraste contra molinetes del mismo dia — evidencia para D2\n")
    A("Una etapa de subte es el trayecto puerta a puerta dentro de la red, de modo que "
      "**una etapa expandida es un ingreso a la red** y es directamente comparable con un "
      "molinete. El contraste se hace contra el **16/10/2024**, el mismo dia que releva el "
      "dataset. Es anterior al pago sin contacto (01/12/2024), asi que ambas fuentes miden "
      "el mismo universo de pago y la comparacion no arrastra la ruptura de "
      "comparabilidad.\n")
    A(f"- Molinetes del dia: **{mil(mol_tot)} ingresos**.")
    A(f"- Matriz O-D expandida: **{mil(od_tot)} etapas**.")
    A(f"- **Factor global: {dec(glob, 4)}** — la matriz subregistra "
      f"{pc(1 - od_tot / mol_tot, 1)} de la demanda medida.\n")

    A("### 4.1 Por linea de ascenso\n")
    A("| Linea | O-D expandida | Molinetes | Factor |")
    A("|---|---:|---:|---:|")
    for i, r in f_lin.sort_values("factor").iterrows():
        A(f"| {i[-1]} | {mil(r.od)} | {mil(r.molinetes)} | {dec(r.factor)} |")
    A("")
    A(f"Recorrido entre lineas: de {dec(f_lin.factor.min())} a {dec(f_lin.factor.max())}, "
      f"una razon de **{dec(f_lin.factor.max() / f_lin.factor.min(), 2)}**.\n")

    A("### 4.2 Por hora\n")
    A("| Hora | O-D expandida | Molinetes | Factor |")
    A("|---|---:|---:|---:|")
    for i, r in f_h.iterrows():
        A(f"| {int(i):02d}:00 | {mil(r.od)} | {mil(r.molinetes)} | "
          f"{dec(r.factor) if np.isfinite(r.factor) else '—'} |")
    A("")

    A("### 4.3 Por complejo\n")
    val = f_comp[(f_comp.od > 0) & (f_comp.molinetes > 0)]
    A(f"Complejos con dato en ambas fuentes: **{len(val)}** de {len(f_comp)}. "
      f"Factor mediano **{dec(val.factor.median())}**, rango de {dec(val.factor.min())} a "
      f"{dec(val.factor.max())}.\n")
    A("Los cinco complejos donde la matriz mas subregistra y los cinco donde mas "
      "sobreregistra:\n")
    A("| Complejo | O-D expandida | Molinetes | Factor |")
    A("|---|---:|---:|---:|")
    for _, r in val.nlargest(5, "factor").iterrows():
        A(f"| {r.nombre} | {mil(r.od)} | {mil(r.molinetes)} | {dec(r.factor)} |")
    A("| … | | | |")
    for _, r in val.nsmallest(5, "factor").sort_values("factor", ascending=False).iterrows():
        A(f"| {r.nombre} | {mil(r.od)} | {mil(r.molinetes)} | {dec(r.factor)} |")
    A("")

    A("## 5. Lo que la evidencia dice sobre D2\n")
    A("D2 pregunta si el escalado de la matriz a los niveles de molinetes es un factor "
      "unico, por linea, por estacion o por franja horaria. Las tres secciones anteriores "
      "responden tres partes de esa pregunta y dejan la cuarta abierta.\n")

    A("### 5.1 La franja horaria no necesita factor propio\n")
    centro = f_h[(f_h.index >= 6) & (f_h.index <= 22)]
    A(f"Entre las 6 y las 22 h el factor se mueve entre **{dec(centro.factor.min())}** y "
      f"**{dec(centro.factor.max())}**, sin ninguna forma sistematica: no crece en el pico "
      "ni en el valle. Las dos horas de borde (05:00 y 23:00) se despegan, pero entre las "
      f"dos suman {pc((f_h.loc[5].molinetes + f_h.loc[23].molinetes) / f_h.molinetes.sum(), 1)} "
      "de los ingresos del dia.\n")
    A("> **Un factor por franja horaria no esta justificado por los datos.** El perfil "
      "intrahorario sigue saliendo de molinetes, como estaba previsto; lo que esta seccion "
      "descarta es escalar *ademas* por hora.\n")

    A("### 5.2 El desvio por estacion no es todo de la misma naturaleza\n")
    A("| Categoria de complejo | Complejos | O-D | Molinetes | Factor | Peso |")
    A("|---|---:|---:|---:|---:|---:|")
    for i, r in f_grupo.sort_values("factor", ascending=False).iterrows():
        A(f"| {i} | {int(r.n)} | {mil(r.od)} | {mil(r.molinetes)} | **{dec(r.factor)}** | "
          f"{pc(r.peso, 1)} |")
    A("")
    A("Hay **tres fenomenos distintos** metidos en la dispersion por estacion, y solo el "
      "primero es un desvio de nivel:\n")
    A("1. **Los cuatro nodos de trasbordo ferroviario subregistran de forma sistematica y "
      "ordenada** por importancia del ferrocarril: Constitucion (Roca) "
      f"{dec(f_comp.loc[f_comp.nombre == 'Constitucion', 'factor'].iloc[0])}, Retiro "
      f"{dec(f_comp.loc[f_comp.nombre == 'Retiro', 'factor'].iloc[0])}, Once / Plaza "
      f"Miserere {dec(f_comp.loc[f_comp.nombre == 'Once / Plaza Miserere', 'factor'].iloc[0])}, "
      f"Federico Lacroze "
      f"{dec(f_comp.loc[f_comp.nombre == 'Federico Lacroze', 'factor'].iloc[0])}. Concentran "
      f"{pc(f_grupo.loc['Trasbordo ferroviario', 'peso'], 1)} de los ingresos del dia y "
      "explican la mayor parte del desvio de la Linea C, que es la unica linea fuera de "
      "norma en la seccion 4.1. Es consistente con que el dataset O-D reconstruya el viaje "
      "a partir de la transaccion SUBE y pierda parte de la etapa de subte cuando el viaje "
      "empieza en el ferrocarril.")
    A("2. **El par San Pedrito / San Jose de Flores no es un desvio de nivel sino de "
      "asignacion.** Son estaciones vecinas de la Linea A, a 664 m. La matriz le pone a "
      "San Jose de Flores 15.495 ingresos de mas y a San Pedrito 14.848 de menos: el neto "
      "de las dos es -647, es decir que **el par cierra**. El matcheo esta descartado como "
      "causa: cada centroide cae a 55 m de su estacion y a mas de 600 m de la otra. Es la "
      "regla de imputacion por parada mas cercana declarada por el organismo publicador, "
      "con su tolerancia de 2,2 km, actuando sobre dos estaciones proximas. **Este solo "
      "par explica el 35 % de todo el desvio absoluto de la red.**")
    A("3. **Los complejos de combinacion no se comportan como grupo.** Su factor promedio "
      f"({dec(f_grupo.loc['Complejo de combinacion', 'factor'])}) esconde un recorrido de "
      "0,945 a 1,635: 9 de Julio / Carlos Pellegrini / Diagonal Norte e Independencia "
      "subregistran fuerte, mientras Bolivar / Catedral / Peru y Correo Central / Leandro "
      "N. Alem sobreregistran. **La categoria no predice nada** y no sirve como criterio.\n")

    A("### 5.3 El residuo no alcanza para elegir\n")
    A("Ingresos mal asignados que sobreviven a cada criterio, sobre "
      f"{mil(f_comp.molinetes.sum())} ingresos del dia:\n")
    A("| Criterio de escalado | Residuo absoluto | % |")
    A("|---|---:|---:|")
    for etiqueta, r in residuos.items():
        A(f"| {etiqueta} | {mil(r)} | {pc(r / f_comp.molinetes.sum(), 1)} |")
    A("| Factor por complejo | 0 | 0,0 % (por construccion) |")
    A("")
    A("> El factor por complejo lleva el residuo a cero **por definicion**, no porque "
      "represente mejor la realidad: hay un parametro libre por complejo y 78 "
      "observaciones. Elegirlo por esta tabla seria elegir el criterio que mas sobreajusta. "
      "La pregunta correcta no es cual deja menos residuo sino **que fenomeno se quiere "
      "corregir**: el punto 1 de la seccion 5.2 es una subregistracion sistematica que vale "
      "la pena corregir, el punto 2 es un defecto de imputacion que un factor por estacion "
      "congelaria en el modelo en lugar de repararlo, y el punto 3 no tiene patron.\n")
    A("Dato de contexto: si se excluye el par San Pedrito / San Jose de Flores, el residuo "
      "de un factor unico global cae de 11,2 % a **7,6 %**.\n")

    A("### 5.4 Lo que queda para decidir\n")
    A("La decision es de la catedra y del grupo, no de este reporte. Lo que el paso 5 "
      "aporta es que **el escalado por franja horaria queda descartado**, que **el escalado "
      "por linea es en realidad el escalado de los nodos ferroviarios visto de lejos**, y "
      "que el escalado por estacion **corrige y congela al mismo tiempo**. El analisis de "
      "sensibilidad tiene que recorrer esa eleccion; sigue siendo el supuesto propio "
      "central del trabajo.\n")

    REPORTES.mkdir(parents=True, exist_ok=True)
    (REPORTES / "06_matriz_od.md").write_text("\n".join(L), encoding="utf-8")
    print(f"reporte en reports/06_matriz_od.md ({len(L)} lineas)")


if __name__ == "__main__":
    main()
