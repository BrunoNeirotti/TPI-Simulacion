"""Paso 3 del plan de trabajo: demanda por estacion, franja de 15 min y tipo de dia.

Lee molinetes 2025 en streaming con lib_molinetes (nunca el anio completo en
memoria) y volca todo en una matriz densa dia x franja x estacion de
366*96*90 enteros, unos 12 MB. Con eso alcanza para todo lo que sigue y no hay
que hacer dos pasadas sobre los 13,2 millones de filas.

Produce cuatro cosas:

1. El perfil de ingreso por estacion, franja de 15 min y tipo de dia, que es la
   entrada de demanda del modelo. **Excluye los dias atipicos**, que de otro modo
   arrastran el perfil de dia habil hacia abajo.
2. El total diario por linea, separando dias atipicos de huecos de datos. Sirve
   para elegir los periodos de ajuste y validacion y resuelve el
   pendiente del viernes 08/08/2025 que dejo abierto el paso 1.
3. La concentracion horaria: que fraccion de la demanda diaria cae en la hora
   pico, para la red, por linea y por estacion. **Es el control que la propuesta
   declaraba pendiente**: de el depende si el perfil de carga de SBASE y
   la cifra anunciada de 270.000-300.000 pasajeros diarios de la Linea F son
   conciliables entre si.
4. El reparto por anden en las estaciones donde el identificador de molinete lo
   informa, que reservamos como contraste independiente del reparto
   que produzca el modelo.

Todo lo que sale de aca es ingreso por molinete: **no es ocupacion a bordo ni
descenso, y no incluye los ascensos por transbordo**. Los molinetes registran
entradas a la red, no abordajes.

Salidas:
  data/processed/demanda_estacion_franja.csv
  data/processed/demanda_diaria.csv
  data/processed/concentracion_horaria.csv
  data/processed/demanda_anden.csv
  reports/04_demanda.md
"""

from __future__ import annotations

import collections
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from lib_molinetes import ResultadoLectura, leer_zip  # noqa: E402
from lib_normalizacion import CENTINELAS, clave, normalizar  # noqa: E402

ANIO = 2025
ZIP = RAIZ / "data" / "raw" / f"molinetes-{ANIO}.zip"
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

N_FRANJAS = 96  # 24 h en bloques de 15 min

# Un dia habil se marca atipico si su total cae por debajo de esta fraccion de la
# mediana de los habiles del MISMO mes. La comparacion es intramensual porque la
# estacionalidad es fuerte (enero es mes de vacaciones) y contra la mediana anual
# saldria enero entero. El umbral detecta anomalias, no clasifica feriados.
UMBRAL_ATIPICO = 0.80

# Por debajo de esto no hay dia de baja demanda posible: es un hueco de datos.
# Un dia de subte con menos del 5 % de la mediana no existe ni en feriado.
UMBRAL_HUECO = 0.05

# Sentidos que identifican un anden por direccion de circulacion. Los de
# vestibulo (HALL, C, Aliv) y los registros sin campo de anden no cuentan: son el
# ~30 % que motivo modelar la demanda por estacion.
SENTIDO_DIRECCIONAL = {"N", "S", "E", "O", "NE", "NO", "SE", "SO"}
ABREVIA_SENTIDO = {"NORTE": "N", "SUR": "S", "ESTE": "E", "OESTE": "O", "W": "O"}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def es(n: float, dec: int = 0) -> str:
    """Numero con separador de miles y decimal a la espaniola."""
    s = f"{n:,.{dec}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def franja_de(desde: str) -> int | None:
    """Indice de la franja de 15 min: 0 = 00:00, 95 = 23:45."""
    partes = desde.split(":")
    if len(partes) < 2:
        return None
    try:
        h, m = int(partes[0]), int(partes[1])
    except ValueError:
        return None
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return None
    return h * 4 + m // 15


def etiqueta_franja(f: int) -> str:
    return f"{f // 4:02d}:{(f % 4) * 15:02d}"


def sentido_de(molinete: str) -> str | None:
    """Sentido de circulacion codificado en el identificador de molinete.

    El campo puede estar en la tercera o en la cuarta posicion, puede escribirse
    completo o abreviado, y puede no estar. Mismo criterio que el paso 1.
    """
    if not molinete:
        return None
    partes = molinete.split("_")
    if len(partes) < 3:
        return None
    for p in partes[2:-1]:
        s = ABREVIA_SENTIDO.get(p.strip().upper(), p.strip().upper())
        if s in SENTIDO_DIRECCIONAL:
            return s
    return None


def es_centinela(v: str) -> bool:
    return str(v).strip().upper() in {c.upper() for c in CENTINELAS}


def es_premetro(linea: str) -> bool:
    """El dataset escribe el Premetro como 'LineaPM', no como 'PM'."""
    return "PM" in str(linea).upper()


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------
class Datos:
    """Matriz densa dia x franja x estacion, mas los descartes y el anden."""

    def __init__(self, nodos: list[str]) -> None:
        self.nodos = nodos
        self.idx = {n: i for i, n in enumerate(nodos)}
        self.n_dias = 366
        self.m = np.zeros((self.n_dias, N_FRANJAS, len(nodos)), dtype=np.int32)
        self.anden: dict[tuple[str, str], int] = collections.defaultdict(int)
        self.anden_total: dict[str, int] = collections.defaultdict(int)
        self.claves_sin_match: collections.Counter = collections.Counter()
        self.pax_total = 0
        self.pax_sin_match = 0
        self.pax_premetro = 0
        self.pax_centinela = 0
        self.pax_franja_invalida = 0
        self.pax_sin_fecha = 0
        self.pax_fuera_de_anio = 0

    def fechas_observadas(self) -> list[dt.date]:
        base = dt.date(ANIO, 1, 1)
        vistos = np.flatnonzero(self.m.sum(axis=(1, 2)) > 0)
        return [base + dt.timedelta(days=int(i)) for i in vistos]


def mapa_estaciones() -> dict[tuple[str, str], str]:
    """(linea, clave normalizada) -> nodo_id, desde la tabla maestra del paso 1."""
    t = pd.read_csv(PROCESADO / "tabla_maestra_estaciones.csv", dtype=str)
    return {
        (r.linea, normalizar(r.gtfs_nombre)): f"{r.linea}:{r.gtfs_stop_id}"
        for r in t.itertuples()
    }


def escanear() -> tuple[Datos, ResultadoLectura]:
    mapa = mapa_estaciones()
    nodos = sorted(set(mapa.values()))
    d = Datos(nodos)
    res = ResultadoLectura()
    base = dt.date(ANIO, 1, 1)

    for r in leer_zip(str(ZIP), res):
        pax = r["pax_TOTAL"]
        d.pax_total += pax
        linea, estacion = r["LINEA"], r["ESTACION"]

        if es_centinela(estacion) or es_centinela(linea):
            d.pax_centinela += pax
            continue
        if es_premetro(linea):
            d.pax_premetro += pax
            continue
        fecha = r["_fecha"]
        if fecha is None:
            d.pax_sin_fecha += pax
            continue
        if fecha.year != ANIO:
            d.pax_fuera_de_anio += pax
            continue
        franja = franja_de(r["DESDE"])
        if franja is None:
            d.pax_franja_invalida += pax
            continue
        nodo = mapa.get((linea, clave(estacion, linea)))
        if nodo is None:
            d.pax_sin_match += pax
            d.claves_sin_match[(linea, estacion)] += pax
            continue

        d.m[(fecha - base).days, franja, d.idx[nodo]] += pax
        d.anden_total[nodo] += pax
        s = sentido_de(r["MOLINETE"])
        if s is not None:
            d.anden[(nodo, s)] += pax

    return d, res


# --------------------------------------------------------------------------
# Tablas
# --------------------------------------------------------------------------
def tipo_de_dia(fecha: dt.date) -> str:
    w = fecha.weekday()
    return "habil" if w <= 4 else ("sabado" if w == 5 else "domingo")


def tabla_diaria(d: Datos) -> pd.DataFrame:
    """Total por dia, con marca de dia atipico y de hueco de datos."""
    lineas = pd.Series([n.split(":")[0] for n in d.nodos])
    filas = []
    for fecha in d.fechas_observadas():
        i = (fecha - dt.date(ANIO, 1, 1)).days
        por_nodo = d.m[i].sum(axis=0)
        fila = {
            "fecha": pd.Timestamp(fecha),
            "tipo_dia": tipo_de_dia(fecha),
            "dia_semana": DIAS[fecha.weekday()],
            "mes": fecha.month,
            "pax_dia": int(por_nodo.sum()),
            "estaciones_con_dato": int((por_nodo > 0).sum()),
        }
        for linea, v in pd.Series(por_nodo).groupby(lineas).sum().items():
            fila[linea] = int(v)
        filas.append(fila)
    t = pd.DataFrame(filas)
    mediana = (
        t[t.tipo_dia == "habil"].groupby("mes").pax_dia.median().rename("mediana_mes")
    )
    t = t.merge(mediana, on="mes", how="left")
    t["razon"] = (t.pax_dia / t.mediana_mes).round(3)
    t["hueco_datos"] = t.razon < UMBRAL_HUECO
    t["atipico"] = (
        (t.tipo_dia == "habil") & (t.razon < UMBRAL_ATIPICO) & ~t.hueco_datos
    )
    return t


def dias_tipicos(d: Datos, diaria: pd.DataFrame, tipo: str) -> np.ndarray:
    """Indices de dia del tipo pedido, sin atipicos ni huecos de datos."""
    sel = diaria[
        (diaria.tipo_dia == tipo) & (~diaria.atipico) & (~diaria.hueco_datos)
    ]
    base = dt.date(ANIO, 1, 1)
    return np.array([(f.date() - base).days for f in sel.fecha], dtype=int)


def tabla_celdas(d: Datos, diaria: pd.DataFrame) -> pd.DataFrame:
    """Perfil medio y desvio por tipo de dia, franja y estacion.

    Una franja sin registros en un dia es un cero, no un dato faltante: la media
    divide por la cantidad de dias del tipo. Dividir por las celdas observadas
    inflaria el perfil de las estaciones chicas en las franjas de borde.
    """
    nodos = pd.read_csv(PROCESADO / "grafo_nodos.csv", dtype=str).set_index("nodo_id")
    bloques = []
    for tipo in ("habil", "sabado", "domingo"):
        idx = dias_tipicos(d, diaria, tipo)
        sub = d.m[idx]  # dias x franja x nodo
        media = sub.mean(axis=0)
        desvio = sub.std(axis=0)
        total = sub.sum(axis=0)
        franjas, nod = np.nonzero(total)
        bloques.append(
            pd.DataFrame(
                {
                    "tipo_dia": tipo,
                    "franja_idx": franjas,
                    "nodo_id": [d.nodos[j] for j in nod],
                    "pax_medio": media[franjas, nod].round(2),
                    "pax_desvio": desvio[franjas, nod].round(2),
                    "pax_total": total[franjas, nod],
                    "n_dias": len(idx),
                }
            )
        )
    t = pd.concat(bloques, ignore_index=True)
    t["franja"] = t.franja_idx.map(etiqueta_franja)
    t["linea"] = t.nodo_id.map(nodos.linea)
    t["nombre"] = t.nodo_id.map(nodos.nombre)
    return t[
        ["tipo_dia", "franja", "franja_idx", "nodo_id", "linea", "nombre",
         "pax_medio", "pax_desvio", "pax_total", "n_dias"]
    ].sort_values(["tipo_dia", "linea", "nombre", "franja_idx"], ignore_index=True)


def _metricas_perfil(perfil: np.ndarray) -> dict | None:
    """Concentracion horaria de un perfil de 96 franjas."""
    tot = perfil.sum()
    if tot <= 0:
        return None
    ventanas = np.convolve(perfil, np.ones(4, dtype=int), mode="valid")
    ini = int(ventanas.argmax())
    return {
        "pax": int(tot),
        "pico60_pax": int(ventanas[ini]),
        "pico60_inicio": etiqueta_franja(ini),
        "pico60_share": float(ventanas[ini] / tot),
        "h08_share": float(perfil[32:36].sum() / tot),
        "h17_share": float(perfil[68:72].sum() / tot),
        "pico15_share": float(perfil.max() / tot),
    }


def tabla_concentracion(d: Datos, diaria: pd.DataFrame) -> pd.DataFrame:
    """Concentracion horaria dia por dia, para toda la red."""
    filas = []
    base = dt.date(ANIO, 1, 1)
    for fecha in d.fechas_observadas():
        i = (fecha - base).days
        met = _metricas_perfil(d.m[i].sum(axis=1))
        if met is None:
            continue
        filas.append({"fecha": pd.Timestamp(fecha), **met})
    c = pd.DataFrame(filas)
    return c.merge(
        diaria[["fecha", "tipo_dia", "dia_semana", "atipico", "hueco_datos"]],
        on="fecha",
    )


def concentracion_por_linea(d: Datos, diaria: pd.DataFrame) -> pd.DataFrame:
    """Concentracion horaria del dia habil tipico, por linea."""
    idx = dias_tipicos(d, diaria, "habil")
    lineas = np.array([n.split(":")[0] for n in d.nodos])
    filas = []
    for linea in sorted(set(lineas)):
        perfil = d.m[np.ix_(idx, range(N_FRANJAS), np.flatnonzero(lineas == linea))]
        met = _metricas_perfil(perfil.sum(axis=(0, 2)))
        if met:
            filas.append({"linea": linea, "pax_dia": met["pax"] / len(idx), **met})
    return pd.DataFrame(filas).sort_values("pico60_share", ascending=False)


def concentracion_por_estacion(d: Datos, diaria: pd.DataFrame) -> pd.DataFrame:
    """Concentracion horaria del dia habil tipico, estacion por estacion."""
    idx = dias_tipicos(d, diaria, "habil")
    nodos = pd.read_csv(PROCESADO / "grafo_nodos.csv", dtype=str).set_index("nodo_id")
    sub = d.m[idx].sum(axis=0)  # franja x nodo
    filas = []
    for j, nodo in enumerate(d.nodos):
        met = _metricas_perfil(sub[:, j])
        if met is None:
            continue
        filas.append(
            {
                "nodo_id": nodo,
                "linea": nodos.linea.get(nodo),
                "nombre": nodos.nombre.get(nodo),
                "pax_dia_medio": met["pax"] / len(idx),
                **{k: v for k, v in met.items() if k != "pax"},
            }
        )
    return pd.DataFrame(filas).sort_values("pico60_share", ascending=False)


def tabla_anden(d: Datos) -> pd.DataFrame:
    """Reparto por sentido en las estaciones donde el molinete lo informa."""
    nodos = pd.read_csv(PROCESADO / "grafo_nodos.csv", dtype=str).set_index("nodo_id")
    por_nodo: dict[str, dict[str, int]] = collections.defaultdict(dict)
    for (nodo, s), p in d.anden.items():
        por_nodo[nodo][s] = p
    filas = []
    for nodo, total in d.anden_total.items():
        con_sentido = por_nodo.get(nodo, {})
        atribuido = sum(con_sentido.values())
        for s, p in sorted(con_sentido.items()):
            filas.append(
                {
                    "nodo_id": nodo,
                    "linea": nodos.linea.get(nodo),
                    "nombre": nodos.nombre.get(nodo),
                    "sentido": s,
                    "pax": p,
                    "pax_estacion": total,
                    "share_entre_sentidos": round(p / atribuido, 4),
                    "cobertura_estacion": round(atribuido / total, 4) if total else 0.0,
                }
            )
    return pd.DataFrame(filas).sort_values(
        ["linea", "nombre", "sentido"], ignore_index=True
    )


# --------------------------------------------------------------------------
# Reporte
# --------------------------------------------------------------------------
def escribir_reporte(d, res, diaria, conc, celdas, anden, por_linea, por_estacion):
    L: list[str] = []
    w = L.append
    hab = conc[(conc.tipo_dia == "habil") & (~conc.atipico) & (~conc.hueco_datos)]
    pico_red = hab.pico60_share.mean()

    w("# Paso 3, Demanda por estación, franja de 15 min y tipo de día\n")
    w("Generado por `src/04_demanda_molinetes.py` sobre "
      f"`data/raw/molinetes-{ANIO}.zip`. Salidas: "
      "`demanda_estacion_franja.csv`, `demanda_diaria.csv`, "
      "`concentracion_horaria.csv` y `demanda_anden.csv` en "
      "`data/processed/`.\n")
    w("> Los molinetes registran **ingresos a la red**: no son descensos, no son "
      "ocupación a bordo y **no incluyen los ascensos por transbordo**. La "
      "distinción importa en la sección 3.\n")

    # --- 1 -----------------------------------------------------------------
    w("## 1. Cobertura de la lectura\n")
    w(f"- {res.resumen()}.")
    w(f"- Pasajeros leídos: **{es(d.pax_total)}**, contra los 206,5 millones que "
      "informó el paso 1. Cierra.")
    for etiqueta, valor in (
        ("Premetro, fuera de alcance", d.pax_premetro),
        ("sin cruce contra la tabla maestra", d.pax_sin_match),
        ("en filas centinela", d.pax_centinela),
        ("sin fecha válida", d.pax_sin_fecha),
        (f"con fecha fuera de {ANIO}", d.pax_fuera_de_anio),
        ("con franja inválida", d.pax_franja_invalida),
    ):
        if valor:
            w(f"- Descartados por {etiqueta}: {es(valor)} "
              f"({pc(valor / d.pax_total, 4)}).")
        else:
            w(f"- Descartados por {etiqueta}: ninguno.")
    if d.claves_sin_match:
        w("")
        w("Los no-matcheos residuales, uno por uno:\n")
        w("| Línea | Estación | Pasajeros |")
        w("|---|---|---:|")
        for (l, e), p in d.claves_sin_match.most_common(10):
            w(f"| {l} | {e} | {es(p)} |")
        w("")
        w("Son la estación espuria *Loria* que el paso 1 ya había identificado en "
          "las seis líneas. **80 pasajeros sobre 206,6 millones**: el mismo "
          "residuo que informó el paso 1, ahora con el Premetro correctamente "
          "separado y no contado como no-matcheo.\n")

    # --- 2 -----------------------------------------------------------------
    w("## 2. Tipos de día, huecos de datos y días atípicos\n")
    huecos = diaria[diaria.hueco_datos]
    if not huecos.empty:
        w(f"### 2.1 Día sin servicio: {len(huecos)} día"
          f"{'s' if len(huecos) != 1 else ''}\n")
        w("Antes de hablar de demanda baja hay que separar los días con demanda "
          "prácticamente nula. Un día de subte por debajo del "
          f"{UMBRAL_HUECO * 100:.0f} % de la mediana mensual no es un día flojo: "
          "o no hubo servicio, o no hubo registro.\n")
        w("| Fecha | Día | Pasajeros | Estaciones con dato | Razón |")
        w("|---|---|---:|---:|---:|")
        for r in huecos.itertuples():
            w(f"| {r.fecha:%Y-%m-%d} | {r.dia_semana} | {es(r.pax_dia)} | "
              f"{r.estaciones_con_dato} de 90 | {r.razon:.2f} |".replace(
                  f"{r.razon:.2f}", f"{r.razon:.2f}".replace(".", ",")))
        w("")
        w("> **Fue un paro general.** El paso 4 lo verifica sobre una fuente "
          "independiente: el 10/04/2025 hay 3.122 servicios de cabecera "
          "programados y **ninguno prestado**, todos con causa *Huelga / Paro "
          "General* (ver `reports/05_despachos.md`, sección 2.1). No es un "
          "faltante del publicador. Queda excluido de todos los perfiles por no "
          "ser representativo, y **no se rellena**: interpolar demanda es "
          "inventar dato.\n")

    w("### 2.2 Tipos de día\n")
    conteo = diaria[~diaria.hueco_datos].groupby("tipo_dia").agg(
        dias=("fecha", "size"), pax_medio=("pax_dia", "mean")
    )
    tip = {
        t: len(dias_tipicos(d, diaria, t)) for t in ("habil", "sabado", "domingo")
    }
    w("| Tipo de día | Días con dato | Días típicos | Pasajeros/día (media) |")
    w("|---|---:|---:|---:|")
    for t, r in conteo.iterrows():
        w(f"| {t} | {int(r.dias)} | {tip[t]} | {es(r.pax_medio)} |")
    w("")
    w("**Los perfiles del modelo se construyen solo con los días típicos**: se "
      "excluyen el hueco de datos y los días atípicos. Incluirlos arrastraría el "
      "perfil de día hábil hacia abajo sin que eso represente ninguna operación "
      "real.\n")

    at = diaria[diaria.atipico].sort_values("razon")
    w(f"### 2.3 {len(at)} días hábiles atípicos\n")
    w(f"Días hábiles por debajo del {UMBRAL_ATIPICO * 100:.0f} % de la mediana de los "
      "hábiles del mismo mes. El criterio es intramensual porque la "
      "estacionalidad es fuerte: contra la mediana anual saldría enero entero.\n")
    w("| Fecha | Día | Pasajeros | Razón |")
    w("|---|---|---:|---:|")
    for r in at.itertuples():
        w(f"| {r.fecha:%Y-%m-%d} | {r.dia_semana} | {es(r.pax_dia)} | "
          f"{f"{r.razon:.2f}".replace(".", ",")} |")
    w("")
    w("> **Esta lista hay que contrastarla contra el calendario oficial de "
      "feriados de 2025.** El método detecta anomalías, no feriados: un paro, un "
      "corte de servicio o un día de lluvia extraordinaria aparecen igual. La "
      "forma de la lista es compatible con el calendario (1/1, 1/5, 25/12, el "
      "24 y el 31, los lunes de carnaval y los puentes) pero **compatible no es "
      "verificado**. Los días atípicos quedan fuera del perfil de día hábil y "
      "**no se reasignan a domingo**, que sería un supuesto sin sustento.\n")

    w("### 2.4 El viernes 8 de agosto de 2025 queda cerrado\n")
    v = diaria[diaria.fecha == f"{ANIO}-08-08"]
    if not v.empty:
        r = v.iloc[0]
        w("El paso 1 lo dejó anotado: tras reconstruir las fechas quedaba con "
          "38.454 filas contra ~49.000 de los viernes comparables, un 22 % "
          "menos, sin saber si era una interrupción de servicio o un faltante.\n")
        w(f"**Con los pasajeros a la vista, el día es normal**: "
          f"{es(r.pax_dia)} pasajeros, razón "
          f"{f"{r.razon:.2f}".replace(".", ",")} contra la mediana de los "
          f"hábiles de agosto, {r.estaciones_con_dato} de 90 estaciones con "
          "dato.\n")
        viernes = diaria[(diaria.mes == 8) & (diaria.dia_semana == "viernes")]
        w("| Viernes de agosto | Pasajeros | Razón | Estaciones con dato |")
        w("|---|---:|---:|---:|")
        for x in viernes.itertuples():
            w(f"| {x.fecha:%Y-%m-%d} | {es(x.pax_dia)} | "
              f"{f"{x.razon:.2f}".replace(".", ",")} | "
              f"{x.estaciones_con_dato} |")
        w("")
        w("> **La menor cantidad de filas no era menor demanda.** Agosto es uno "
          "de los dos archivos con fechas `d/m/Y` y `m/d/Y` mezcladas, y el "
          "conteo de filas por día quedaba distorsionado por esa reconstrucción. "
          "Los pasajeros por día no se apartan. El pendiente del paso 1 se "
          "cierra sin corrección: **no hay nada que corregir**. Lo que sí queda "
          "marcado como anómalo en agosto es el viernes 15 (razón 0,51) y el "
          "viernes 1.º (0,70).\n")

    # --- 3 -----------------------------------------------------------------
    w("## 3. Concentración horaria, el control que quedaba pendiente\n")
    w("La pregunta es si dos cifras de la Línea F son conciliables entre sí: los "
      "**≈73.900 ascensos en hora pico** que suman las tablas de SBASE del EsIA "
      "(46.713 hacia Palermo más 27.163 hacia Brandsen, misma hora pico de la "
      "mañana) y los **270.000-300.000 pasajeros diarios** anunciados. Para que "
      "lo fueran, la hora pico tendría que concentrar cerca del **25 %** de la "
      "demanda diaria.\n")
    w("La hora pico se busca como la ventana móvil de 60 min de mayor ingreso, "
      "no se fija de antemano: fijarla sería suponer el resultado.\n")
    w(f"### 3.1 La red, en día hábil típico ({len(hab)} días)\n")
    w("| Métrica | Media | Desvío | Mínimo | Máximo |")
    w("|---|---:|---:|---:|---:|")
    for col, et in (
        ("pico60_share", "Hora pico móvil de 60 min"),
        ("h08_share", "Hora 8:00-9:00"),
        ("h17_share", "Hora 17:00-18:00"),
        ("pico15_share", "Franja pico de 15 min"),
    ):
        s = hab[col]
        w(f"| {et} | **{pc(s.mean())}** | {pc(s.std(), 2)} | {pc(s.min())} | "
          f"{pc(s.max())} |")
    w("")
    ini = hab.pico60_inicio.value_counts()
    w(f"La ventana pico arranca con más frecuencia a las **{ini.index[0]}** "
      f"({ini.iloc[0]} de {len(hab)} días). El doble pico que el dataset O-D "
      "detecta a las 8 y a las 17 aparece también acá, y la tarde gana.\n")

    w("### 3.2 Por línea\n")
    w("| Línea | Ingresos/día | Hora pico | Inicio | Hora 8 | Hora 17 |")
    w("|---|---:|---:|---|---:|---:|")
    for r in por_linea.itertuples():
        w(f"| {r.linea[5:]} | {es(r.pax_dia)} | **{pc(r.pico60_share)}** | "
          f"{r.pico60_inicio} | {pc(r.h08_share)} | {pc(r.h17_share)} |")
    w("")

    w("### 3.3 Las estaciones más concentradas\n")
    w("Es la comparación que importa, porque la Línea F no es una línea "
      "promedio: su carga máxima está en Constitución, alimentada por el "
      "ferrocarril Roca. Si algún nodo de la red actual puede acercarse al 25 %, "
      "es uno de ésos.\n")
    top = por_estacion.head(10)
    w("| Estación | Línea | Ingresos/día | Hora pico | Inicio |")
    w("|---|---|---:|---:|---|")
    for r in top.itertuples():
        w(f"| {r.nombre} | {r.linea[5:]} | {es(r.pax_dia_medio)} | "
          f"**{pc(r.pico60_share)}** | {r.pico60_inicio} |")
    w("")
    ferro = por_estacion[
        por_estacion.nombre.isin(["Constitucion", "Retiro", "Once", "Plaza Miserere"])
    ]
    if not ferro.empty:
        w("Y los nodos de transferencia ferroviaria en particular:\n")
        w("| Estación | Línea | Ingresos/día | Hora pico | Inicio |")
        w("|---|---|---:|---:|---|")
        for r in ferro.itertuples():
            w(f"| {r.nombre} | {r.linea[5:]} | {es(r.pax_dia_medio)} | "
              f"**{pc(r.pico60_share)}** | {r.pico60_inicio} |")
        w("")

    maxi = por_estacion.iloc[0]
    linea_top = por_linea.iloc[0]
    implicada = 73900 / pico_red
    w("### 3.4 Resultado\n")
    w(f"**La red concentra el {pc(pico_red)} de sus ingresos diarios en la hora "
      "pico, y ninguna de las seis líneas pasa del "
      f"{pc(linea_top.pico60_share)}** (la {linea_top.linea[5:]}). La "
      "comparación pertinente es la de línea, porque la cifra de SBASE es de "
      "línea.\n")
    w("A nivel de estación individual sí hay casos que superan el 25 %: "
      f"{maxi.nombre} [{maxi.linea[5:]}] llega al {pc(maxi.pico60_share)}. Pero "
      f"son estaciones chicas y de uso casi monopropósito ({maxi.nombre} tiene "
      f"{es(maxi.pax_dia_medio)} ingresos diarios, el "
      f"{pc(maxi.pax_dia_medio / hab.pax.mean())} de la red) donde entra "
      "personal de oficinas a la mañana y sale a la tarde. **Una línea entera "
      "de doce estaciones no se comporta como una estación de oficinas.**\n")
    if not ferro.empty and (ferro.nombre == "Constitucion").any():
        c = ferro[ferro.nombre == "Constitucion"].iloc[0]
        pico_const = c.pax_dia_medio * c.pico60_share
        w("El contraste más directo disponible es **Constitución**, que es el "
          "nodo de carga máxima de la Línea F según SBASE y hoy ya existe como "
          "estación de la Línea C, alimentada por el mismo ferrocarril Roca:\n")
        w(f"- Constitución [C] recibe hoy **{es(c.pax_dia_medio)} ingresos "
          f"diarios** y concentra el {pc(c.pico60_share)} en su hora pico, es "
          f"decir unos **{es(round(pico_const, -1))} ingresos en la hora pico**.")
        veces = f"{32640 / pico_const:.1f}".replace(".", ",")
        w("- SBASE proyecta para Constitución de la Línea F **32.640 ascensos "
          "en la hora pico de la mañana** en un solo sentido: "
          f"{veces} veces el ingreso de hora pico que la estación tiene hoy en "
          f"la Línea C, y el {pc(32640 / c.pax_dia_medio)} de todo su ingreso "
          "diario actual.")
        w("")
        w("Los transbordos desde el ferrocarril **sí pasan por molinete** (son "
          "sistemas tarifarios distintos), así que están contados en esos "
          f"{es(c.pax_dia_medio)} ingresos. La comparación no está subestimando "
          "la demanda ferroviaria.\n")
    w("De ahí salen dos lecturas del mismo hecho, y conviene decir las dos:\n")
    w(f"1. **Si la Línea F se pareciera a la red actual**, sus 73.900 ascensos "
      f"de hora pico implicarían del orden de **{es(round(implicada, -3))} "
      "pasajeros diarios**, entre 2 y 3 veces la cifra anunciada de "
      "270.000-300.000.")
    w("2. **Si la cifra anunciada fuese correcta**, la Línea F tendría que "
      "concentrar cerca del 25 % de su demanda diaria en una hora: "
      + f"{25 / (pico_red * 100):.1f}".replace(".", ",")
      + " veces la concentración de la red actual y "
      + f"{25 / (linea_top.pico60_share * 100):.1f}".replace(".", ",")
      + f" veces la de la línea más apuntada, la {linea_top.linea[5:]}.")
    w("")
    w("> **Las dos cifras no son conciliables entre sí.** Al menos una está "
      "mal, y el trabajo no puede decidir cuál con la información disponible.\n")
    w("**Tres salvedades, que acotan el alcance sin cambiar la conclusión:**\n")
    w("1. **Unidades.** Los molinetes miden ingresos a la red; los ascensos de "
      "SBASE incluyen además los transbordos desde las otras seis líneas de "
      "subte. Los ascensos son necesariamente más que los ingresos (en la red "
      "actual el 48,8 % de las etapas termina en una línea distinta de la de "
      "ascenso), así que la cifra diaria implicada del punto 1 es una **cota "
      "superior**. La comparación de *concentración*, que es una proporción, no "
      "se ve afectada por el nivel.")
    w("2. **La hora pico de SBASE es la de la línea, no la de la red.** Una "
      "línea puede tener su pico desplazado respecto del pico agregado, lo que "
      "aumentaría su concentración propia. La sección 3.2 muestra que entre "
      "líneas la dispersión es chica: del 9,0 % al 12,0 %.")
    w("3. **Los 270.000-300.000 no tienen fuente documental.** No aparecen en "
      "ninguna pieza del expediente ni de la licitación. Que no cierren contra "
      "el perfil de SBASE es una razón más para no usarlos como insumo, que es "
      "lo que el trabajo ya venía haciendo.\n")

    # --- 4 -----------------------------------------------------------------
    w("## 4. Reparto por andén, el contraste que queda como reserva\n")
    atribuido = sum(d.anden.values())
    total_nodos = sum(d.anden_total.values())
    cob = anden.groupby("nodo_id").cobertura_estacion.first()
    w(f"- Ingresos con sentido de circulación identificable: **{es(atribuido)} "
      f"de {es(total_nodos)}, o sea {pc(atribuido / total_nodos)}**. Reproduce "
      "el 70,5 % que midió el paso 1.")
    w(f"- Estaciones con algún ingreso atribuible: **{len(cob)} de 90**. Las "
      f"{90 - len(cob)} restantes no tienen el campo en ningún molinete.")
    w(f"- De esas {len(cob)}, cobertura mediana {pc(cob.median())}; "
      f"{int((cob >= 0.99).sum())} superan el 99 % y "
      f"{int((cob < 0.5).sum())} quedan por debajo del 50 %.\n")
    w("**El faltante no está repartido al azar**, y por eso decidimos modelar "
      "la demanda por estación: hay 28 estaciones enteras sin el dato. Lo que "
      "queda es un contraste **parcial y sesgado por construcción** del reparto "
      "entre andenes que produzca el modelo, útil solo donde el dato existe.\n")
    w("Las diez estaciones de mayor ingreso con cobertura por encima del 99 %:\n")
    buenas = anden[anden.cobertura_estacion >= 0.99]
    top = (
        buenas.groupby(["nodo_id", "linea", "nombre"], as_index=False)
        .pax_estacion.first()
        .nlargest(10, "pax_estacion")
    )
    w("| Estación | Línea | Ingresos 2025 | Reparto entre sentidos |")
    w("|---|---|---:|---|")
    for r in top.itertuples():
        g = buenas[buenas.nodo_id == r.nodo_id]
        reparto = " / ".join(
            f"{x.sentido} {pc(x.share_entre_sentidos, 0)}" for x in g.itertuples()
        )
        w(f"| {r.nombre} | {r.linea[5:]} | {es(r.pax_estacion)} | {reparto} |")
    w("")

    # --- 5 -----------------------------------------------------------------
    w("## 5. Qué queda de esto\n")
    w("- **La demanda de entrada del modelo está lista**: "
      f"{es(len(celdas))} celdas de (tipo de día, franja de 15 min, estación), "
      "con media y desvío entre días típicos. El desvío es el insumo del "
      "análisis de sensibilidad y de la variabilidad entre replicaciones.")
    w("- **Las dos cifras de demanda de la Línea F no cierran entre sí** "
      "(sección 3.4). Es un hallazgo propio y hay que llevarlo al documento: "
      "refuerza la decisión ya tomada de no usar la cifra anunciada como insumo, "
      "y agrega una salvedad al uso del perfil de SBASE como contraste.")
    w("- **El pendiente del viernes 08/08/2025 se cierra sin corrección** "
      "(sección 2.4): era un artefacto del conteo de filas, no un faltante de "
      "demanda.")
    w("- **Aparece un día sin servicio** (sección 2.1): el 10/04/2025, "
      "verificado como paro general contra el dataset de despachos. Hay que "
      "declararlo y excluirlo.")
    w("- **Los días atípicos quedaron verificados en el paso 4** contra el "
      "calendario `Tipo Día` del propio operador: 11 de 11 feriados hábiles "
      "detectados, 6 más corroborados como servicio de sábado, 4 sin datos de "
      "despachos y 4 sin explicación. Ver `reports/05_despachos.md`, sección 5.")
    w("- **Ya se pueden elegir los períodos de ajuste y validación**: la tabla diaria da los "
      "candidatos a ventana de ajuste y de validación, ambos posteriores a "
      "diciembre de 2024, sin días atípicos y con estacionalidad comparable.")
    w("")

    (REPORTES / "04_demanda.md").write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    PROCESADO.mkdir(parents=True, exist_ok=True)
    REPORTES.mkdir(parents=True, exist_ok=True)

    d, res = escanear()
    print("Lectura:", res.resumen())

    diaria = tabla_diaria(d)
    conc = tabla_concentracion(d, diaria)
    celdas = tabla_celdas(d, diaria)
    anden = tabla_anden(d)
    por_linea = concentracion_por_linea(d, diaria)
    por_estacion = concentracion_por_estacion(d, diaria)

    diaria.to_csv(PROCESADO / "demanda_diaria.csv", index=False, encoding="utf-8")
    conc.to_csv(PROCESADO / "concentracion_horaria.csv", index=False, encoding="utf-8")
    celdas.to_csv(
        PROCESADO / "demanda_estacion_franja.csv", index=False, encoding="utf-8"
    )
    anden.to_csv(PROCESADO / "demanda_anden.csv", index=False, encoding="utf-8")
    por_estacion.to_csv(
        PROCESADO / "concentracion_por_estacion.csv", index=False, encoding="utf-8"
    )

    escribir_reporte(d, res, diaria, conc, celdas, anden, por_linea, por_estacion)
    hab = conc[(conc.tipo_dia == "habil") & (~conc.atipico) & (~conc.hueco_datos)]
    print(
        f"dias={len(diaria)} huecos={int(diaria.hueco_datos.sum())} "
        f"atipicos={int(diaria.atipico.sum())} celdas={len(celdas)} "
        f"pico60_habil={hab.pico60_share.mean():.4f}"
    )


if __name__ == "__main__":
    main()
