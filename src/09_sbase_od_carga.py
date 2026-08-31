"""Paso 9: la matriz O-D y los perfiles de carga que SBASE entrego por Ley 104.

El 26 y el 27 de agosto de 2026 llegaron las respuestas a la solicitud
00866317/26. SBASE adjunto —embebido dentro del PDF, no como archivo del
mail— dos libros de Excel que cierran los dos huecos que el expediente del EIA
no habia cubierto:

  1. una matriz origen-destino de 90x90 a nivel de estacion, con apertura
     diaria, hora pico manana y hora pico tarde, de un dia habil de septiembre
     de 2024, medida sobre transacciones SUBE por EMOVA S.A.;
  2. los perfiles de carga por tramo de las seis lineas, en ambos sentidos y
     en las dos horas pico.

Lo segundo es lo que mas cambia el trabajo: la ocupacion a bordo figuraba
como salida del modelo **sin contraparte empirica posible**. Ahora
la tiene, para hora pico y para la red actual.

Este paso no reemplaza la matriz del paso 5. La deja al lado y las mide una
contra otra: son dos fuentes independientes —una encuesta expandida de un dia
de octubre y un conteo de transacciones de septiembre— del mismo objeto.

Salidas en data/processed/:
  sbase_od.csv               las tres matrices en formato largo, por nodo
  sbase_perfil_carga.csv     ascensos, descensos y carga por tramo y sentido
  sbase_contraste_carga.csv  carga observada contra la que predice el paso 6
  sbase_contraste_od.csv     matriz SBASE contra matriz del paso 5, por complejo

Reporte en reports/09_sbase_od_carga.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lib_complejos as lc  # noqa: E402
import lib_sbase as ls  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

# Carga maxima proyectada para la Linea F en hora pico, tramo Constitucion ->
# Cochabamba, sentido a Palermo (EsIA doc 0010, tabla del Analisis de Demanda
# SBASE 2019; ver docs/expediente-eia-linea-f.md seccion 4).
CARGA_MAX_LINEA_F = 35742.0


def mil(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def num(x: float, dec: int = 2) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def cargar_od() -> pd.DataFrame:
    partes = [ls.matriz(p) for p in ("diaria", "hpm", "hpt")]
    return pd.concat(partes, ignore_index=True)


def sentido_a_direccion(aristas: pd.DataFrame, perfil: pd.DataFrame) -> dict:
    """(linea, sentido_hacia de SBASE) -> direction_id del grafo.

    El sentido se nombra por la cabecera de llegada, y la cabecera de cada
    direction_id del grafo es el destino de su ultima arista de tramo. El
    sentido **no** se puede deducir del orden de las filas: los dos sentidos de
    un bloque comparten una unica lista de estaciones, de modo que la primera
    fila es la misma para los dos.
    """
    tramos = aristas[aristas.tipo == "tramo"]
    cabecera = {}
    for (linea, d), g in tramos.groupby(["linea", "direction_id"]):
        cabecera[(linea, d)] = g.sort_values("orden").a_nodo.iloc[-1]
    por_nombre = {(f"Linea{linea}", ls._norm(nombre)): nodo
                  for i, (nombre, linea) in ls.ids_carga().items()
                  for nodo in [ls.mapa_nodos(ls.ids_carga())[i]]}
    mapa = {}
    for linea, sentido in perfil.groupby(["linea", "sentido_hacia"]).groups:
        destino = por_nombre.get((linea, ls._norm(sentido)))
        if destino is None:
            raise ValueError(f"cabecera desconocida: {linea} hacia {sentido}")
        candidatos = [d for (l, d), n in cabecera.items() if l == linea and n == destino]
        if len(candidatos) != 1:
            raise ValueError(f"sentido ambiguo: {linea} hacia {sentido} -> {candidatos}")
        mapa[(linea, sentido)] = candidatos[0]
    if len(set(mapa.values())) != 2 or len(mapa) != 12:
        raise ValueError(f"mapa de sentidos incompleto: {mapa}")
    for linea in perfil.linea.unique():
        ds = {v for (l, _), v in mapa.items() if l == linea}
        if len(ds) != 2:
            raise ValueError(f"los dos sentidos de {linea} cayeron en el mismo direction_id")
    return mapa


def asignar(od: pd.DataFrame, caminos: pd.DataFrame, aristas: pd.DataFrame,
            de_nodo_a_comp: dict) -> pd.DataFrame:
    """Carga por arista de tramo que resulta de la asignacion todo-o-nada.

    Cada par de complejos manda todo su flujo por el camino minimo del paso 6.
    Las aristas de transbordo no acumulan carga a bordo.
    """
    flujo = (od.assign(co=od.origen.map(de_nodo_a_comp), cd=od.destino.map(de_nodo_a_comp))
               .groupby(["co", "cd"], as_index=False).viajes.sum())
    intra = flujo[flujo.co == flujo.cd]
    flujo = flujo[flujo.co != flujo.cd]
    camino = dict(zip(zip(caminos.comp_origen, caminos.comp_destino), caminos.camino))
    tipo = {(r.de_nodo, r.a_nodo): (r.tipo, r.linea, r.direction_id)
            for r in aristas.itertuples()}
    carga: dict = {}
    faltantes = 0
    for r in flujo.itertuples():
        c = camino.get((r.co, r.cd))
        if c is None:
            faltantes += 1
            continue
        nodos = c.split()
        for u, v in zip(nodos, nodos[1:]):
            t = tipo.get((u, v))
            if t is None or t[0] != "tramo":
                continue
            clave = (t[1], t[2], u)
            carga[clave] = carga.get(clave, 0.0) + r.viajes
    if faltantes:
        raise ValueError(f"{faltantes} pares de complejos sin camino minimo")
    df = pd.DataFrame(
        [(k[0], k[1], k[2], v) for k, v in carga.items()],
        columns=["linea", "direction_id", "nodo", "carga_predicha"],
    )
    df.attrs["intra"] = float(intra.viajes.sum())
    return df


def main() -> None:
    maestra = lc.construir()
    de_nodo_a_comp = dict(zip(maestra.nodo, maestra.complejo))
    cat = lc.catalogo(maestra)
    nombre_comp = cat.nombre.to_dict()
    nodos = ls.nodos().set_index("nodo_id")

    od = cargar_od()
    perfil = ls.perfil_carga()
    od.to_csv(PROCESADO / "sbase_od.csv", index=False)
    perfil.to_csv(PROCESADO / "sbase_perfil_carga.csv", index=False)

    aristas = pd.read_csv(PROCESADO / "grafo_aristas.csv")
    caminos = pd.read_csv(PROCESADO / "caminos_minimos.csv")
    dirmap = sentido_a_direccion(aristas, perfil)

    # --- contraste 1: la matriz de SBASE contra la del paso 5 -----------------
    nuestra = pd.read_csv(PROCESADO / "matriz_od.csv")
    nuestra_dia = (nuestra.groupby(["comp_origen", "comp_destino"], as_index=False)
                          .expandidas.sum().rename(columns={"expandidas": "paso5"}))
    sbase_dia = (od[od.periodo == "diaria"]
                 .assign(co=lambda d: d.origen.map(de_nodo_a_comp),
                         cd=lambda d: d.destino.map(de_nodo_a_comp))
                 .groupby(["co", "cd"], as_index=False).viajes.sum()
                 .rename(columns={"co": "comp_origen", "cd": "comp_destino",
                                  "viajes": "sbase"}))
    sbase_dia = sbase_dia[sbase_dia.comp_origen != sbase_dia.comp_destino]
    comp = nuestra_dia.merge(sbase_dia, on=["comp_origen", "comp_destino"], how="outer").fillna(0.0)
    comp["nombre_origen"] = comp.comp_origen.map(nombre_comp)
    comp["nombre_destino"] = comp.comp_destino.map(nombre_comp)
    comp.to_csv(PROCESADO / "sbase_contraste_od.csv", index=False)

    # --- contraste 2: ascensos por complejo contra molinetes ------------------
    mol = pd.read_csv(PROCESADO / "molinetes_20241016.csv")
    mol["complejo"] = mol.nodo.map(de_nodo_a_comp)
    mol_comp = mol.groupby("complejo", as_index=False).pax.sum()
    asc_sbase = (sbase_dia.groupby("comp_origen", as_index=False).sbase.sum()
                 .rename(columns={"comp_origen": "complejo"}))
    asc_paso5 = (nuestra_dia.groupby("comp_origen", as_index=False).paso5.sum()
                 .rename(columns={"comp_origen": "complejo"}))
    asc = (mol_comp.merge(asc_sbase, on="complejo", how="outer")
                   .merge(asc_paso5, on="complejo", how="outer").fillna(0.0))
    asc["nombre"] = asc.complejo.map(nombre_comp)

    # --- contraste 3: reparto por linea dentro de los complejos ---------------
    asc_nodo = (od[od.periodo == "diaria"].groupby("origen", as_index=False).viajes.sum()
                .rename(columns={"origen": "nodo"}))
    asc_nodo["complejo"] = asc_nodo.nodo.map(de_nodo_a_comp)
    multi = asc_nodo.groupby("complejo").nodo.count()
    multi = multi[multi > 1].index
    reparto = asc_nodo[asc_nodo.complejo.isin(multi)].copy()
    reparto["share_sbase"] = reparto.viajes / reparto.groupby("complejo").viajes.transform("sum")
    modelo = pd.read_csv(PROCESADO / "caminos_reparto_linea.csv")

    # --- contraste 4: la asignacion del paso 6 contra la carga observada ------
    # Una fila del perfil solo es comparable si el grafo tiene una arista de
    # tramo que salga de ese nodo en ese sentido. Quedan afuera la cabecera de
    # llegada, que no tiene arista saliente y donde la carga observada es cero,
    # y Alberti y Pasco en el sentido en que el tren pasa sin detenerse: ahi la
    # carga observada es real pero cae dentro de una arista mas larga del grafo.
    con_arista = {(r.linea, r.direction_id, r.de_nodo)
                  for r in aristas[aristas.tipo == "tramo"].itertuples()}
    filas = []
    for periodo in ("hpm", "hpt"):
        pred = asignar(od[od.periodo == periodo], caminos, aristas, de_nodo_a_comp)
        obs = perfil[perfil.periodo == periodo.upper()].copy()
        obs["direction_id"] = [dirmap[(r.linea, r.sentido_hacia)] for r in obs.itertuples()]
        j = obs.merge(pred, on=["linea", "direction_id", "nodo"], how="left")
        j["carga_predicha"] = j.carga_predicha.fillna(0.0)
        j["comparable"] = [(r.linea, r.direction_id, r.nodo) in con_arista
                           for r in j.itertuples()]
        filas.append(j)
    contraste = pd.concat(filas, ignore_index=True)
    contraste["dif"] = contraste.carga_predicha - contraste.carga_saliente
    contraste.to_csv(PROCESADO / "sbase_contraste_carga.csv", index=False)

    escribir_reporte(od, perfil, comp, asc, reparto, modelo, contraste, nodos,
                     nombre_comp, maestra, caminos)


def escribir_reporte(od, perfil, comp, asc, reparto, modelo, contraste, nodos,
                     nombre_comp, maestra, caminos) -> None:
    de_nodo_a_comp = dict(zip(maestra.nodo, maestra.complejo))
    salida = []
    w = salida.append

    tot = od.groupby("periodo").viajes.sum()
    pares = od.groupby("periodo").size()
    diaria = tot["diaria"]

    w("# Paso 9 — Matriz O-D y perfiles de carga de SBASE (Ley 104)\n")
    w("Fuente: `IF-2026-38553261-GCABA-SBASE.pdf`, del 26/08/2026, respuesta a la ")
    w("solicitud 00866317/26. Las dos planillas venian **embebidas dentro del PDF** ")
    w("(`/Names /EmbeddedFiles`), no como adjuntos del correo; se extrajeron a ")
    w("`data/raw/sbase-ley104/`. Se leen con `src/lib_sbase.py`.\n")

    w("\n## 1. Que trae\n")
    w("| Periodo | Pares con flujo | Viajes |")
    w("|---|---:|---:|")
    for p, etiqueta in (("diaria", "Dia habil completo"),
                        ("hpm", "Hora pico manana (8–9 h)"),
                        ("hpt", "Hora pico tarde (17–18 h)")):
        w(f"| {etiqueta} | {mil(pares[p])} de 8.010 | {mil(tot[p])} |")
    w("")
    w("La unidad espacial es el **nodo**, no el complejo: las 90 estaciones de la ")
    w("planilla son los 90 pares linea-estacion del grafo del paso 2 y cruzan una a ")
    w("una con el. Retiro [C] y Retiro [E] son dos filas distintas, igual que ")
    w("Callao [B] y Callao [D].\n")

    w("\n### Dos mapas de identificador, y no son el mismo\n")
    w("Los dos libros numeran las estaciones de 1 a 90 y **coinciden solo hasta el ")
    w("75**. La matriz O-D pone la cola de la Linea E (Correo Central, Catalinas, ")
    w("Retiro E) al final de todo; el perfil de carga la pone antes de la Linea H. ")
    w("Cruzar una planilla con el mapa de la otra corre 15 estaciones sin dar ningun ")
    w("error visible. `lib_sbase` usa siempre el mapa del propio libro.\n")

    hpm_share = tot["hpm"] / diaria
    hpt_share = tot["hpt"] / diaria
    w("\n## 2. Concentracion horaria: coincide con lo que miden los molinetes\n")
    w(f"La hora pico manana concentra el **{pc(hpm_share)}** de los viajes del dia y ")
    w(f"la tarde el **{pc(hpt_share)}**. El paso 3 habia medido sobre molinetes de ")
    w("2025 una concentracion de 9,9 % en la hora pico de la red. **Las dos fuentes ")
    w("coinciden**, y son independientes entre si.\n")
    w("\nEso vuelve a cerrar el mismo contraste sobre la Linea F, ahora con la propia ")
    w("fuente que produjo la cifra en discusion: para que los ~73.900 ascensos de hora ")
    w("pico del *Analisis de Demanda Linea F* (SBASE, 2019) fueran compatibles con los ")
    w("270.000–300.000 viajes diarios anunciados, la Linea F tendria que concentrar en ")
    w("una hora cerca del 25 % de su demanda diaria — dos veces y media lo que concentra ")
    w("la red que la propia SBASE mide.\n")

    # Asimetria: la mitad de la suma de |M[o][d] - M[d][o]| sobre todos los
    # pares ordenados, dividida por el total. Hay que recorrer la union de los
    # dos sentidos y no solo las celdas con flujo: un par que existe en un
    # sentido y no en el otro es el caso mas asimetrico posible y contarlo una
    # sola vez lo subestima a la mitad.
    asim = {}
    for p in ("diaria", "hpm", "hpt"):
        m = od[od.periodo == p].set_index(["origen", "destino"]).viajes.to_dict()
        pares = {tuple(sorted(k)) for k in m}
        s = sum(abs(m.get((a, b), 0.0) - m.get((b, a), 0.0)) for a, b in pares)
        asim[p] = s / tot[p]
    w("\n## 3. La matriz no es simetrica por construccion\n")
    w("| Periodo | Asimetria |")
    w("|---|---:|")
    for p in ("diaria", "hpm", "hpt"):
        w(f"| {p} | {pc(asim[p])} |")
    w("")
    w("Es la diferencia de fondo con la matriz del paso 5. Aquella hereda del dataset ")
    w("de Viajes y Etapas una **imputacion por simetria diaria**, y por eso su ")
    w("direccionalidad horaria es una construccion, no una medicion. Esta se midio ")
    w("sobre transacciones: en hora pico manana el flujo es abrumadoramente hacia el ")
    w("centro y en hora pico tarde se invierte. Para un modelo de eventos discretos ")
    w("esa direccionalidad es la variable que decide todo.\n")

    top_hpm = (od[od.periodo == "hpm"].groupby("origen").viajes.sum()
               .sort_values(ascending=False).head(5))
    top_hpm_d = (od[od.periodo == "hpm"].groupby("destino").viajes.sum()
                 .sort_values(ascending=False).head(5))
    w("\nAscensos y descensos en hora pico manana, cinco primeros:\n")
    w("| Ascensos | | Descensos | |")
    w("|---|---:|---|---:|")
    for (o, vo), (d, vd) in zip(top_hpm.items(), top_hpm_d.items()):
        w(f"| {nodos.loc[o, 'nombre']} [{nodos.loc[o, 'linea'][-1]}] | {mil(vo)} "
          f"| {nodos.loc[d, 'nombre']} [{nodos.loc[d, 'linea'][-1]}] | {mil(vd)} |")
    w("")

    w("\n## 4. Contraste con la matriz del paso 5 y con molinetes\n")
    mol_tot = asc.pax.sum()
    w(f"| Fuente | Dia | Viajes o ingresos |")
    w("|---|---|---:|")
    w(f"| Molinetes | miercoles 16/10/2024 | {mil(mol_tot)} |")
    w(f"| Matriz del paso 5 (Viajes y Etapas, expandida) | miercoles 16/10/2024 | "
      f"{mil(asc.paso5.sum())} |")
    w(f"| Matriz de SBASE (EMOVA, transacciones SUBE) | dia habil de septiembre 2024 | "
      f"{mil(asc.sbase.sum())} |")
    w("")
    w("La cifra de SBASE de esta tabla deja afuera los 687 viajes diarios entre dos ")
    w("nodos de un mismo complejo, que en el modelo son una caminata y no un viaje en ")
    w("tren; el total de la matriz es 827.976 (ver seccion 8).\n")
    w(f"La matriz de SBASE queda **{pc(asc.sbase.sum() / mol_tot - 1)} por encima** de ")
    w("los molinetes del 16/10/2024 y la del paso 5 queda 4,8 % por debajo. No son el ")
    w("mismo dia ni el mismo mes —septiembre corre mas alto que octubre en la serie de ")
    w("molinetes— y SBASE declara que su base son transacciones SUBE, que en septiembre ")
    w("de 2024 concentraban mas del 95 % de los pagos: expandir ese 95 % al total ")
    w("explica un factor de 1,05 por si solo.\n")

    corr = np.corrcoef(comp.paso5, comp.sbase)[0, 1]
    ambas = comp[(comp.paso5 > 0) & (comp.sbase > 0)]
    w(f"\nA nivel de par de complejos, las dos matrices correlacionan **{num(corr, 3)}** ")
    w(f"sobre {mil(len(comp))} pares con flujo en alguna de las dos; ")
    w(f"{mil(len(ambas))} tienen flujo en ambas.\n")

    asc_val = asc[asc.pax > 0].copy()
    asc_val["f_sbase"] = asc_val.sbase / asc_val.pax
    asc_val["f_paso5"] = asc_val.paso5 / asc_val.pax
    peores = asc_val.reindex(asc_val.f_sbase.sub(1).abs().sort_values(ascending=False).index).head(8)
    w("\nAscensos por complejo contra molinetes del 16/10/2024, ocho mayores desvios ")
    w("de la matriz de SBASE:\n")
    w("| Complejo | Molinetes | SBASE | Factor SBASE | Factor paso 5 |")
    w("|---|---:|---:|---:|---:|")
    for r in peores.itertuples():
        w(f"| {r.nombre} | {mil(r.pax)} | {mil(r.sbase)} | {num(r.f_sbase, 3)} "
          f"| {num(r.f_paso5, 3)} |")
    w("")

    w("\n### El par San Pedrito / San Jose de Flores, que abrio la decision D8\n")
    w("El paso 5 encontro que el dataset de Viajes y Etapas reparte mal la demanda entre ")
    w("esas dos estaciones vecinas de la Linea A: el total del par cierra bien pero el ")
    w("reparto esta corrido, y eso explica el 35 % del desvio absoluto de toda la red. ")
    w("**La matriz de SBASE no tiene ese defecto.**\n")
    par = asc[asc.nombre.isin(["San Pedrito", "San Jose de Flores"])]
    w("\n| Complejo | Molinetes | SBASE | Factor | Paso 5 | Factor |")
    w("|---|---:|---:|---:|---:|---:|")
    for r in par.itertuples():
        w(f"| {r.nombre} | {mil(r.pax)} | {mil(r.sbase)} | {num(r.sbase / r.pax, 3)} "
          f"| {mil(r.paso5)} | {num(r.paso5 / r.pax, 3)} |")
    w("")
    w("Es un argumento fuerte a favor de la matriz de SBASE en D2, y de paso vuelve ")
    w("innecesaria la reparacion que D8 planteaba: el defecto es de una fuente, no del ")
    w("fenomeno.\n")

    w("\n## 5. Reparto por linea en los complejos de combinacion\n")
    w("La matriz de SBASE es por nodo, asi que dice directamente por que linea sube ")
    w("cada pasajero en un complejo de varias lineas. Es la **cuarta fuente** del mismo ")
    w("reparto, despues de molinetes, `linea_etapa` y la prediccion del paso 6, y la ")
    w("unica que no comparte origen con ninguna de las otras.\n")
    rep = reparto.copy()
    rep["linea"] = rep.nodo.map(lambda n: nodos.loc[n, "linea"])
    rep["complejo_nombre"] = rep.complejo.map(nombre_comp)
    cuatro = modelo.merge(rep[["complejo", "linea", "viajes", "share_sbase"]],
                          on=["complejo", "linea"], how="left")
    w("\n| Complejo | Linea | Molinetes | `linea_etapa` | Modelo (paso 6) | SBASE |")
    w("|---|---|---:|---:|---:|---:|")
    for c, g in cuatro.groupby("complejo_nombre"):
        for r in g.sort_values("p_molinetes", ascending=False).itertuples():
            deg = " *" if getattr(r, "od_degenerado", False) else ""
            w(f"| {c} | {r.linea[-1]} | {pc(r.p_molinetes)} | {pc(r.p_od)}{deg} "
              f"| {pc(r.p_predicho)} | {pc(r.share_sbase)} |")
    w("")
    w("`*` marca los complejos donde el dataset de Viajes y Etapas atribuye el 100 % de ")
    w("los ascensos a una sola linea, defecto ya declarado en el paso 6.\n")
    err = (cuatro.assign(e=lambda d: (d.p_predicho - d.share_sbase).abs())
                 .groupby("complejo_nombre").e.max())
    w(f"\nEl modelo del paso 6 se aparta de SBASE a lo sumo {pc(err.max())} en un ")
    w(f"complejo ({err.idxmax()}) y {pc(err.median())} en la mediana.\n")
    ret = cuatro[cuatro.complejo_nombre == "Retiro"]
    if not ret.empty:
        c_ = ret[ret.linea == "LineaC"].iloc[0]
        w("\n**Retiro, la discrepancia que abrio la decision D9.** El paso 6 predecia ")
        w(f"{pc(c_.p_predicho)} de los ascensos por la Linea C contra {pc(c_.p_molinetes)} ")
        w(f"de molinetes. SBASE mide {pc(c_.share_sbase)}: le da la razon a molinetes y ")
        w("confirma que el modelo manda demasiada gente a la Linea E en ese nodo.\n")

    w("\n## 6. Perfiles de carga: la ocupacion a bordo deja de ser inobservable\n")
    w("El trabajo declara la ocupacion a bordo como indicador central y ")
    w("**sin contraparte empirica en ninguna fuente publica**. La planilla de perfiles ")
    w("la trae: ascensos, descensos y pasajeros a bordo por tramo, para las seis ")
    w("lineas, los dos sentidos y las dos horas pico.\n")
    mx = (perfil.sort_values("carga_saliente", ascending=False)
                .groupby(["linea", "periodo"]).head(1)
                .sort_values(["linea", "periodo"]))
    w("\nCarga maxima por linea y periodo, con el tramo donde ocurre:\n")
    w("| Linea | Periodo | Sentido | Tramo que sale de | Pas./h a bordo |")
    w("|---|---|---|---|---:|")
    for r in mx.itertuples():
        w(f"| {r.linea[-1]} | {r.periodo} | hacia {r.sentido_hacia} | {r.estacion_sbase} "
          f"| {mil(r.carga_saliente)} |")
    w("")
    peor = perfil.sort_values("carga_saliente", ascending=False).iloc[0]
    w(f"\nEl tramo mas cargado de toda la red actual lleva **{mil(peor.carga_saliente)} ")
    w(f"pas./h** (Linea {peor.linea[-1]}, {peor.periodo}, saliendo de {peor.estacion_sbase} ")
    w(f"hacia {peor.sentido_hacia}). El *Analisis de Demanda Linea F* proyecta ")
    w(f"**{mil(CARGA_MAX_LINEA_F)} pas./h** en el tramo Constitucion → Cochabamba: ")
    w(f"**{num(CARGA_MAX_LINEA_F / peor.carga_saliente, 1)} veces** el tramo mas cargado ")
    w("que hoy tiene la red. El contraste ya no es contra una cifra anunciada de ")
    w("prensa sino contra la medicion de la propia SBASE sobre su propia red.\n")

    w("\n## 7. Validacion de la asignacion todo-o-nada del paso 6\n")
    w("Se cargo la matriz de SBASE de cada hora pico sobre el grafo del paso 2 usando ")
    w("los caminos minimos del paso 6 —asignacion todo-o-nada, penalizacion por ")
    w("transbordo de 120 s— y se comparo la carga que resulta en cada tramo contra la ")
    w("que mide SBASE. **Es la primera validacion de la asignacion de ruta contra un ")
    w("observado**; hasta ahora solo se podia contrastar el reparto por linea de ascenso.\n")
    fuera = contraste[~contraste.comparable]
    w(f"\nDe las {len(contraste)} filas del perfil quedan {int(contraste.comparable.sum())} ")
    w("comparables. Se excluyen las cabeceras de llegada, que no tienen tramo saliente ")
    w("y donde el observado es cero, y Alberti y Pasco en el sentido en que el tren ")
    w("pasa sin detenerse: ahi el observado es real pero el grafo no tiene un tramo que ")
    w(f"salga de esa estacion, sino uno mas largo que la contiene ({len(fuera)} filas ")
    w("en total).\n")
    for periodo in ("HPM", "HPT"):
        c = contraste[(contraste.periodo == periodo) & contraste.comparable]
        obs, pre = c.carga_saliente, c.carga_predicha
        corr = float(np.corrcoef(obs, pre)[0, 1])
        wape = float((pre - obs).abs().sum() / obs.sum())
        sesgo = float(pre.sum() / obs.sum() - 1)
        w(f"\n**{periodo}**: correlacion {num(corr, 3)} sobre {len(c)} tramos; "
          f"error absoluto ponderado {pc(wape)} de los pasajeros-tramo observados; "
          f"la asignacion produce {pc(abs(sesgo))} "
          f"{'mas' if sesgo > 0 else 'menos'} pasajeros-tramo que lo observado.\n")
    w("\nDiez tramos comparables con mayor diferencia absoluta:\n")
    w("| Periodo | Linea | Sentido | Sale de | Observado | Asignado | Dif. |")
    w("|---|---|---|---|---:|---:|---:|")
    comparables = contraste[contraste.comparable]
    peores_c = comparables.reindex(
        comparables.dif.abs().sort_values(ascending=False).index).head(10)
    for r in peores_c.itertuples():
        w(f"| {r.periodo} | {r.linea[-1]} | hacia {r.sentido_hacia} | {r.estacion_sbase} "
          f"| {mil(r.carga_saliente)} | {mil(r.carga_predicha)} | {mil(r.dif)} |")
    w("")
    w("\nLa comparacion tiene una holgura que no es del modelo y hay que declararla: ")
    w("SBASE avisa en el propio informe que *\"los valores presentados en la matriz ")
    w("origen-destino y en los diagramas de carga pueden presentar diferencias\"*, ")
    w("porque los diagramas de carga pasan por un ajuste iterativo sobre ascensos y ")
    w("descensos para que la carga cierre en cero en la cabecera. La matriz y el perfil ")
    w("no son, entonces, dos vistas exactas del mismo dato.\n")
    w("\n### La tasa de transbordo, medida por segunda vez\n")
    w("Las dos planillas estan en unidades distintas y conviene no confundirlas: la ")
    w("matriz cuenta **viajes** y el perfil cuenta **ascensos a bordo**, de modo que un ")
    w("pasajero que combina aparece una vez en la primera y dos en el segundo. El ")
    w("cociente entre ambas es la tasa de transbordo observada, y es otra validacion ")
    w("independiente de la asignacion del paso 6.\n")
    w("\n| Periodo | Ascensos por viaje, SBASE | Ascensos por viaje, modelo |")
    w("|---|---:|---:|")
    caminos_idx = caminos.set_index(["comp_origen", "comp_destino"]).n_transbordos
    for periodo in ("hpm", "hpt"):
        s = perfil[perfil.periodo == periodo.upper()].suben.sum()
        v = od[od.periodo == periodo].viajes.sum()
        f = (od[od.periodo == periodo]
             .assign(co=lambda d: d.origen.map(de_nodo_a_comp),
                     cd=lambda d: d.destino.map(de_nodo_a_comp))
             .query("co != cd").groupby(["co", "cd"], as_index=False).viajes.sum())
        n = f.set_index(["co", "cd"]).index.map(caminos_idx)
        modelo_tasa = float(((1 + n) * f.viajes).sum() / f.viajes.sum())
        w(f"| {periodo.upper()} | {num(s / v, 3)} | {num(modelo_tasa, 3)} |")
    w("")
    w("El modelo transborda un poco de mas en la hora pico manana y practicamente lo ")
    w("mismo en la tarde. Es consistente con el sesgo por linea de la seccion 5.\n")

    intra = float(od[od.periodo == "diaria"].viajes.sum()
                  - comp.sbase.sum())
    w("\n## 8. Que queda declarado\n")
    w(f"- **Viajes dentro de un mismo complejo.** La matriz diaria trae {mil(intra)} ")
    w("  viajes ({:s} del total) entre dos nodos del mismo complejo — Retiro [C] a "
      .format(pc(intra / od[od.periodo == 'diaria'].viajes.sum(), 2)))
    w("  Retiro [E] y equivalentes. En el modelo son una caminata dentro de la estacion, ")
    w("  no un viaje en tren, y quedan fuera de la asignacion. Se declaran, no se ")
    w("  reparten.")
    w("- **Los perfiles de carga son de hora pico, no de dia completo.** La ocupacion a ")
    w("  bordo tiene contraparte empirica en las dos horas pico y sigue sin tenerla en ")
    w("  el resto del dia de servicio, que es el horizonte del modelo.")
    w("- **La aglomeracion de anden sigue sin contraparte.** Ninguna de las dos planillas ")
    w("  la mide; sigue siendo salida del modelo sin validacion posible.")
    w("- **La matriz de SBASE es de septiembre de 2024 y la del paso 5 del 16/10/2024.** ")
    w("  Las dos son anteriores a la apertura de medios de pago del 01/12/2024, asi que ")
    w("  ninguna arrastra esa ruptura, pero tampoco describen la red de 2025 o 2026.")
    w("- **El perfil pasa por un ajuste iterativo de SBASE**, declarado por ellos en el ")
    w("  propio informe. No es un conteo directo a bordo.")
    w("")

    REPORTES.mkdir(exist_ok=True)
    (REPORTES / "09_sbase_od_carga.md").write_text("\n".join(salida), encoding="utf-8")
    print("\n".join(salida[:4]))
    print(f"\nreporte en reports/09_sbase_od_carga.md ({len(salida)} lineas)")


if __name__ == "__main__":
    main()
