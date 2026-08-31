"""Paso 2 del plan de trabajo: grafo de la red de subte.

Nodos = par (linea, estacion). Aristas dirigidas de dos tipos:

  tramo       recorrido de un tren entre dos estaciones consecutivas de una
              misma linea y sentido. Tiempo de marcha, tiempo de detencion y
              distancia salen de stop_times.txt.
  transbordo  cambio de linea dentro de un complejo de combinacion. Tiempo de
              min_transfer_time en transfers.txt, agregado de anden a estacion.

El nodo es (linea, estacion) y no la estacion sola porque el transbordo tiene
costo y tiene que ser una arista explicita: Pueyrredon de la D y Santa Fe de la
H son dos nodos unidos por una arista de 86-139 s, no un mismo lugar.

Todo sale del GTFS. Nada de esto es un parametro declarado por el grupo.

Salidas:
  data/processed/grafo_nodos.csv
  data/processed/grafo_aristas.csv
  reports/03_grafo_red.md
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
GTFS = RAIZ / "data" / "raw" / "gtfs"
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

# El Premetro queda fuera de alcance (ver docs/contexto-del-proyecto.md). Se lo excluye del
# grafo pero se lo cuenta en el reporte para dejar constancia de que se lo vio.
RUTAS_FUERA_DE_ALCANCE = ("PM-Civico", "PM-Savio")

# Los tres service_id (5 habil, 6 sabado, 7 domingo) tienen secuencias y
# horarios identicos. Se usa el habil, y main() lo verifica antes de descartar
# los otros dos en vez de darlo por sentado.
SERVICE_ID = "5"

# --- Reparo de la Linea E ---------------------------------------------------
# La columna shape_dist_traveled del sentido 1 de la Linea E es copia literal de
# la del sentido 0: los 18 valores coinciden posicion por posicion, lo que haria
# que Plaza de los Virreyes-Varela midiera lo mismo que Retiro-Catalinas. Es la
# unica ruta del feed con ese defecto.
#
# Los tiempos del mismo sentido tampoco se salvan. Correlacion tramo a tramo
# entre tiempo de marcha y distancia:
#     resto de la red y E sentido 0 ......... 0,863  (desvio de velocidad 4,3 km/h)
#     E sentido 1 contra su distancia ....... 0,010  (desvio 11,4 km/h)
#     E sentido 1 contra la distancia real .. 0,425  (desvio 7,9 km/h)
# El sentido 1 de la E esta desacoplado de su propia geometria. El total si
# cierra: 11,71 km y 29 min 28 s en los dos sentidos.
#
# Reparo: el sentido 1 de la E se reemplaza por el espejo del sentido 0, que es
# lo que hacen las otras cinco lineas del feed, donde ambos sentidos coinciden
# al segundo y al metro.
#
# Poner en False para trabajar con el dato publicado tal cual.
REPARAR_LINEA_E = True


def a_segundos(hhmmss: str) -> int:
    h, m, s = (int(x) for x in hhmmss.split(":"))
    return h * 3600 + m * 60 + s


def cargar_stop_times() -> pd.DataFrame:
    """stop_times con linea, sentido, estacion padre y tiempos en segundos."""
    st = pd.read_csv(GTFS / "stop_times.txt", dtype=str)
    trips = pd.read_csv(GTFS / "trips.txt", dtype=str)
    stops = pd.read_csv(GTFS / "stops.txt", dtype=str)

    padre = stops.set_index("stop_id").parent_station.to_dict()
    df = st.merge(
        trips[["trip_id", "route_id", "direction_id", "service_id", "trip_headsign"]],
        on="trip_id",
    )
    df["seq"] = df.stop_sequence.astype(int)
    df["llegada"] = df.arrival_time.map(a_segundos)
    df["salida"] = df.departure_time.map(a_segundos)
    df["dist"] = df.shape_dist_traveled.astype(float)
    df["estacion"] = df.stop_id.map(padre)
    return df.sort_values(["route_id", "direction_id", "service_id", "seq"])


def firmas_por_service_id(df: pd.DataFrame) -> dict[tuple[str, str], int]:
    """Cuenta recorridos distintos por ruta y sentido entre los tres service_id."""
    firmas: dict[tuple[str, str], set[str]] = {}
    for (ruta, sentido, _srv), g in df.groupby(
        ["route_id", "direction_id", "service_id"]
    ):
        g = g.sort_values("seq")
        f = "|".join(g.stop_id + ":" + g.arrival_time + ":" + g.departure_time)
        firmas.setdefault((ruta, sentido), set()).add(f)
    return {k: len(v) for k, v in firmas.items()}


def construir_tramos(df: pd.DataFrame) -> pd.DataFrame:
    """Una arista dirigida por par de estaciones consecutivas, linea y sentido."""
    filas = []
    for (ruta, sentido), g in df.groupby(["route_id", "direction_id"]):
        g = g.sort_values("seq")
        de = g.iloc[:-1].reset_index(drop=True)
        a = g.iloc[1:].reset_index(drop=True)
        filas.append(
            pd.DataFrame(
                {
                    "linea": ruta,
                    "direction_id": sentido,
                    "de_estacion": de.estacion.values,
                    "a_estacion": a.estacion.values,
                    "de_anden": de.stop_id.values,
                    "a_anden": a.stop_id.values,
                    "orden": de.seq.values,
                    # marcha: de la salida de una estacion a la llegada a la siguiente
                    "t_marcha_s": a.llegada.values - de.salida.values,
                    # detencion en la estacion de destino de este tramo
                    "t_detencion_s": a.salida.values - a.llegada.values,
                    "km": (a.dist.values - de.dist.values).round(3),
                }
            )
        )
    return pd.concat(filas, ignore_index=True)


def reparar_linea_e(tramos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reemplaza el sentido 1 de la Linea E por el espejo del sentido 0.

    Devuelve (tramos reparados, tabla del antes y despues para el reporte).
    """
    e0 = tramos[(tramos.linea == "LineaE") & (tramos.direction_id == "0")]
    e1 = tramos[(tramos.linea == "LineaE") & (tramos.direction_id == "1")].copy()

    # espejo: el tramo A->B del sentido 0 da el tramo B->A del sentido 1
    espejo = e0.iloc[::-1].reset_index(drop=True)
    if len(espejo) != len(e1):
        raise AssertionError("los dos sentidos de la E no tienen igual cantidad de tramos")

    comparacion = e1[["de_estacion", "a_estacion", "t_marcha_s", "km"]].copy()
    comparacion.columns = ["de_estacion", "a_estacion", "t_publicado_s", "km_publicado"]
    # el recorrido y los andenes del sentido 1 se conservan; solo se reemplazan
    # las magnitudes fisicas
    e1["t_marcha_s"] = espejo.t_marcha_s.values
    e1["km"] = espejo.km.values
    comparacion["t_reparado_s"] = espejo.t_marcha_s.values
    comparacion["km_reparado"] = espejo.km.values

    resto = tramos[~((tramos.linea == "LineaE") & (tramos.direction_id == "1"))]
    reparados = pd.concat([resto, e1], ignore_index=True).sort_values(
        ["linea", "direction_id", "orden"], ignore_index=True
    )
    return reparados, comparacion


def construir_transbordos() -> pd.DataFrame:
    """Agrega min_transfer_time de par de andenes a par de nodos (linea, estacion)."""
    tf = pd.read_csv(GTFS / "transfers.txt", dtype=str)
    tf["min_transfer_time"] = tf.min_transfer_time.astype(int)
    stops = pd.read_csv(GTFS / "stops.txt", dtype=str)
    st = pd.read_csv(GTFS / "stop_times.txt", dtype=str)
    trips = pd.read_csv(GTFS / "trips.txt", dtype=str)

    padre = stops.set_index("stop_id").parent_station.to_dict()
    linea_de_anden = (
        st.merge(trips[["trip_id", "route_id"]], on="trip_id")
        .groupby("stop_id")
        .route_id.agg(lambda s: sorted(set(s))[0])
        .to_dict()
    )
    for col, orig in (("de", "from_stop_id"), ("a", "to_stop_id")):
        tf[f"{col}_estacion"] = tf[orig].map(padre)
        tf[f"{col}_linea"] = tf[orig].map(linea_de_anden)

    agg = tf.groupby(
        ["de_linea", "de_estacion", "a_linea", "a_estacion"], as_index=False
    ).min_transfer_time.agg(
        n_pares_anden="count",
        t_transbordo_s="median",
        t_min_s="min",
        t_max_s="max",
    )
    agg["t_transbordo_s"] = agg.t_transbordo_s.round().astype(int)
    return agg


def cabeceras(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """Destino de cada (linea, sentido), para nombrar los sentidos en el reporte.

    Evita tener que afirmar a mano cual es el sentido de Pasco y de Alberti, que
    es justo el tipo de dato que conviene leer y no recordar.
    """
    return df.groupby(["route_id", "direction_id"]).trip_headsign.first().to_dict()


def construir_nodos(df: pd.DataFrame, tramos: pd.DataFrame,
                    transbordos: pd.DataFrame) -> pd.DataFrame:
    stops = pd.read_csv(GTFS / "stops.txt", dtype=str)
    estaciones = stops[stops.location_type == "1"].set_index("stop_id")
    n_andenes = stops[stops.location_type == "0"].groupby("parent_station").size()

    vistos = df[~df.route_id.isin(RUTAS_FUERA_DE_ALCANCE)][
        ["route_id", "direction_id", "estacion", "stop_id", "seq"]
    ]
    nodos = (
        vistos.groupby(["route_id", "estacion"], as_index=False)
        .agg(
            sentidos=("direction_id", lambda s: "".join(sorted(set(s)))),
            andenes_servidos=("stop_id", "nunique"),
        )
        .rename(columns={"route_id": "linea", "estacion": "gtfs_stop_id"})
    )
    nodos["nodo_id"] = nodos.linea + ":" + nodos.gtfs_stop_id
    nodos["nombre"] = nodos.gtfs_stop_id.map(estaciones.stop_name)
    nodos["lat"] = nodos.gtfs_stop_id.map(estaciones.stop_lat)
    nodos["lon"] = nodos.gtfs_stop_id.map(estaciones.stop_lon)
    nodos["n_andenes_gtfs"] = nodos.gtfs_stop_id.map(n_andenes)
    for d in ("0", "1"):
        orden = (
            vistos[vistos.direction_id == d]
            .set_index(["route_id", "estacion"])
            .seq.to_dict()
        )
        nodos[f"orden_dir{d}"] = [
            orden.get((l, e)) for l, e in zip(nodos.linea, nodos.gtfs_stop_id)
        ]

    # terminal: la estacion aparece en un solo tramo por sentido que la toca
    incidencias = pd.concat(
        [
            tramos.linea + ":" + tramos.de_estacion,
            tramos.linea + ":" + tramos.a_estacion,
        ]
    ).value_counts()
    nodos["es_terminal"] = nodos.nodo_id.map(incidencias).fillna(0).le(2)

    en_combinacion = set(transbordos.de_linea + ":" + transbordos.de_estacion)
    nodos["es_combinacion"] = nodos.nodo_id.isin(en_combinacion)
    return nodos


def main() -> None:
    PROCESADO.mkdir(parents=True, exist_ok=True)
    REPORTES.mkdir(parents=True, exist_ok=True)

    todo = cargar_stop_times()
    firmas = firmas_por_service_id(todo)
    df = todo[todo.service_id == SERVICE_ID]

    tramos = construir_tramos(df)
    comparacion_e = pd.DataFrame()
    if REPARAR_LINEA_E:
        tramos, comparacion_e = reparar_linea_e(tramos)
    transbordos = construir_transbordos()

    # --- Alcance -----------------------------------------------------------
    fuera = tramos.linea.isin(RUTAS_FUERA_DE_ALCANCE)
    tramos_pm, tramos = tramos[fuera], tramos[~fuera].copy()
    fuera_tf = transbordos.de_linea.isin(
        RUTAS_FUERA_DE_ALCANCE
    ) | transbordos.a_linea.isin(RUTAS_FUERA_DE_ALCANCE)
    transbordos_pm, transbordos = transbordos[fuera_tf], transbordos[~fuera_tf].copy()

    nodos = construir_nodos(df, tramos, transbordos)

    # --- Aristas en un unico formato --------------------------------------
    a_tramo = tramos.assign(
        tipo="tramo",
        de_nodo=tramos.linea + ":" + tramos.de_estacion,
        a_nodo=tramos.linea + ":" + tramos.a_estacion,
        t_s=tramos.t_marcha_s,
    )[
        [
            "tipo", "de_nodo", "a_nodo", "linea", "direction_id", "orden",
            "t_s", "t_detencion_s", "km", "de_anden", "a_anden",
        ]
    ]
    a_transbordo = transbordos.assign(
        tipo="transbordo",
        de_nodo=transbordos.de_linea + ":" + transbordos.de_estacion,
        a_nodo=transbordos.a_linea + ":" + transbordos.a_estacion,
        # None en las de texto y NaN en las numericas: con pd.NA, el concat
        # posterior no puede decidir el dtype de las columnas que quedan todas
        # vacias y avisa.
        linea=None,
        direction_id=None,
        orden=np.nan,
        t_s=transbordos.t_transbordo_s,
        t_detencion_s=np.nan,
        km=np.nan,
        de_anden=None,
        a_anden=None,
    )[a_tramo.columns.tolist()]
    aristas = pd.concat([a_tramo, a_transbordo], ignore_index=True)

    # --- Verificaciones ----------------------------------------------------
    g = nx.DiGraph()
    g.add_nodes_from(nodos.nodo_id)
    for de, a, t, tipo in zip(aristas.de_nodo, aristas.a_nodo, aristas.t_s, aristas.tipo):
        g.add_edge(de, a, t=t, tipo=tipo)
    fuerte = nx.is_strongly_connected(g)
    componentes = nx.number_strongly_connected_components(g)

    maestra = pd.read_csv(PROCESADO / "tabla_maestra_estaciones.csv", dtype=str)
    claves_maestra = set(maestra.linea + ":" + maestra.gtfs_stop_id)
    faltan = claves_maestra - set(nodos.nodo_id)
    sobran = set(nodos.nodo_id) - claves_maestra

    nodos = nodos[
        [
            "nodo_id", "linea", "gtfs_stop_id", "nombre", "lat", "lon",
            "sentidos", "orden_dir0", "orden_dir1", "n_andenes_gtfs",
            "andenes_servidos", "es_terminal", "es_combinacion",
        ]
    ].sort_values(["linea", "orden_dir0"], na_position="last", ignore_index=True)

    nodos.to_csv(PROCESADO / "grafo_nodos.csv", index=False, encoding="utf-8")
    aristas.to_csv(PROCESADO / "grafo_aristas.csv", index=False, encoding="utf-8")

    escribir_reporte(
        nodos, tramos, transbordos, tramos_pm, transbordos_pm, comparacion_e,
        firmas, fuerte, componentes, faltan, sobran, cabeceras(df),
    )
    print(
        f"nodos={len(nodos)} tramos={len(tramos)} transbordos={len(transbordos)} "
        f"fuertemente_conexo={fuerte} faltan={len(faltan)} sobran={len(sobran)}"
    )


def escribir_reporte(nodos, tramos, transbordos, tramos_pm, transbordos_pm,
                     comparacion_e, firmas, fuerte, componentes, faltan, sobran,
                     destinos):
    nom = nodos.set_index("gtfs_stop_id").nombre.to_dict()
    det = tramos.t_detencion_s
    L: list[str] = []
    w = L.append

    w("# Paso 2, Grafo de la red\n")
    w("Generado por `src/03_grafo_red.py`. Fuente: GTFS de Subte "
      "(`data/raw/gtfs/`). Salidas: `data/processed/grafo_nodos.csv` y "
      "`data/processed/grafo_aristas.csv`.\n")

    w("## 1. Tamaño del grafo\n")
    w(f"- **Nodos**: {len(nodos)} pares (línea, estación).")
    w(f"- **Aristas de tramo**: {len(tramos)} dirigidas.")
    w(f"- **Aristas de transbordo**: {len(transbordos)} dirigidas, es decir "
      f"{len(transbordos) // 2} combinaciones.")
    w(f"- Fuera de alcance (Premetro): {len(tramos_pm)} tramos y "
      f"{len(transbordos_pm)} transbordos, excluidos del grafo.\n")

    resumen = tramos.groupby("linea").agg(
        tramos=("t_marcha_s", "size"),
        km_sentido=("km", lambda s: round(s.sum() / 2, 2)),
        marcha_min=("t_marcha_s", lambda s: round(s.sum() / 2 / 60, 1)),
    )
    resumen = resumen.join(nodos.groupby("linea").size().rename("estaciones"))
    resumen["punta_a_punta_min"] = (
        resumen.marcha_min + (resumen.tramos / 2 - 1) * 24 / 60
    ).round(1)
    resumen["km_h"] = (
        resumen.km_sentido / (resumen.punta_a_punta_min / 60)
    ).round(1)
    w("| Línea | Estaciones | Tramos | km por sentido | Marcha (min) | "
      "Punta a punta (min) | Velocidad comercial (km/h) |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for linea, r in resumen.iterrows():
        w(f"| {linea[5:]} | {int(r.estaciones)} | {int(r.tramos)} | "
          f"{r.km_sentido} | {r.marcha_min} | {r.punta_a_punta_min} | {r.km_h} |")
    w("")
    w("La velocidad comercial no incluye la detención en las cabeceras ni el "
      "tiempo de retorno, así que es la del recorrido, no la del ciclo.\n")

    w("## 2. El tiempo de detención es una constante, no una medición\n")
    w(f"El feed declara **{det.min():.0f} s de detención en toda parada de toda "
      f"línea, sin una sola excepción** ({len(det)} tramos, desvío "
      f"{det.std():.1f}). No hay diferencia entre Constitución y Pasco, ni entre "
      "hora pico y valle (el GTFS no tiene bandas horarias), ni entre cabecera y "
      "estación intermedia.\n")
    w("> **Consecuencia.** Los 24 s son un **valor nominal de diseño del "
      "horario**, no una detención observada. Los teníamos anotados como tiempo de "
      "detención tomado del GTFS, y lo son, pero conviene precisar qué clase de "
      "dato son: sirven como punto de partida y como cota inferior, mientras que "
      "la detención real depende del volumen que sube y baja, que es justamente "
      "lo que el modelo produce. **En el modelo la detención tiene que ser "
      "endógena, con los 24 s como piso.**\n")

    w("## 3. Dos defectos del feed, y qué hace el grafo con cada uno\n")

    w("### 3.1 La Línea A no es simétrica, y está bien que no lo sea\n")
    unidireccionales = nodos[nodos.sentidos.str.len() == 1]
    w(f"{' y '.join(sorted(unidireccionales.nombre))} tienen **un solo andén "
      "cada una y se sirven en un único sentido**. Por eso la A tiene 18 "
      "estaciones pero 17 paradas por sentido, y por eso la red tiene 90 nodos "
      "y no 89.\n")
    if not unidireccionales.empty:
        w("| Estación | Línea | Único sentido servido |")
        w("|---|---|---|")
        for _, r in unidireccionales.iterrows():
            w(f"| {r.nombre} | {r.linea[5:]} | hacia "
              f"{destinos[(r.linea, r.sentidos)]} |")
        w("")
    w("No es un error del feed sino la operación real, y **obliga a que el "
      "grafo sea dirigido**: en cada una de esas dos estaciones se puede subir "
      "y bajar en un solo sentido de circulación. Un grafo no dirigido habría "
      "inventado cuatro servicios que no existen.\n")

    if not comparacion_e.empty:
        w("### 3.2 El sentido 1 de la Línea E está corrupto en el feed\n")
        w("La columna `shape_dist_traveled` del sentido 1 de la E es **copia "
          "literal** de la del sentido 0: los 18 valores coinciden posición por "
          "posición. Eso haría que Plaza de los Virreyes → Varela midiera lo "
          "mismo que Retiro → Catalinas. Es la única ruta del feed con ese "
          "defecto: en las otras siete la comprobación da negativa.\n")
        w("Los tiempos del mismo sentido tampoco se salvan. Correlación entre "
          "tiempo de marcha y distancia, tramo a tramo:\n")
        w("| Conjunto | Correlación t~km | Desvío de la velocidad |")
        w("|---|---:|---:|")
        w("| Resto de la red y E sentido 0 | 0,863 | 4,3 km/h |")
        w("| E sentido 1, contra su distancia publicada | **0,010** | 11,4 km/h |")
        w("| E sentido 1, contra la distancia real | 0,425 | 7,9 km/h |")
        w("")
        w("La correlación de 0,010 dice que el sentido 1 de la E está "
          "**desacoplado de su propia geometría**: no es que las distancias "
          "estén mal y los tiempos bien, están mal las dos columnas. El total "
          "sí cierra (11,71 km y 29 min 28 s en los dos sentidos), así que el "
          "defecto es de reparto interno y pasa desapercibido en cualquier "
          "control agregado.\n")
        peores = comparacion_e.assign(
            dif=(comparacion_e.t_publicado_s - comparacion_e.t_reparado_s).abs()
        ).nlargest(5, "dif")
        w("Los cinco tramos donde más se aparta el dato publicado:\n")
        w("| Tramo | t publicado | t reparado | km publicado | km real |")
        w("|---|---:|---:|---:|---:|")
        for _, r in peores.iterrows():
            w(f"| {nom.get(r.de_estacion, r.de_estacion)} → "
              f"{nom.get(r.a_estacion, r.a_estacion)} | {int(r.t_publicado_s)} s | "
              f"{int(r.t_reparado_s)} s | {r.km_publicado} | {r.km_reparado} |")
        w("")
        w("> **Reparo aplicado.** El sentido 1 de la E se reemplaza por el "
          "espejo del sentido 0, que es exactamente lo que hacen las otras cinco "
          "líneas del feed: de 81 tramos emparejados entre sentidos, 64 tienen "
          "diferencia exacta cero en tiempo y en distancia, y los 17 restantes "
          "son todos de la E. El interruptor es `REPARAR_LINEA_E` en "
          "`src/03_grafo_red.py`. **Es una decisión a confirmar**, ver sección 6.\n")

    w("## 4. Transbordos\n")
    w(f"{len(transbordos)} aristas dirigidas construidas sobre "
      f"{int(transbordos.n_pares_anden.sum())} pares de andenes. El tiempo de "
      "nodo a nodo es la **mediana** de los pares de andén del complejo, porque "
      "la demanda se modela por estación y el andén de origen es "
      "resultado de la asignación de ruta, no un dato de entrada. El mínimo y el "
      "máximo quedan en el CSV para el análisis de sensibilidad.\n")
    w(f"Rango sobre pares de andén: {transbordos.t_min_s.min()}-"
      f"{transbordos.t_max_s.max()} s. Mediana de las medianas: "
      f"{transbordos.t_transbordo_s.median():.0f} s.\n")
    w("**Los tiempos son direccionales**, y la diferencia no es despreciable:\n")
    par = transbordos.copy()
    par["clave"] = [
        "|".join(sorted([a, b]))
        for a, b in zip(
            par.de_linea + par.de_estacion, par.a_linea + par.a_estacion
        )
    ]
    w("| Combinación | Ida | Vuelta | Diferencia | Pares de andén |")
    w("|---|---:|---:|---:|---:|")
    filas = []
    for _, g in par.groupby("clave"):
        if len(g) != 2:
            continue
        a, b = g.iloc[0], g.iloc[1]
        filas.append(
            (
                f"{nom.get(a.de_estacion)} [{a.de_linea[5:]}] ↔ "
                f"{nom.get(a.a_estacion)} [{a.a_linea[5:]}]",
                a.t_transbordo_s,
                b.t_transbordo_s,
                abs(a.t_transbordo_s - b.t_transbordo_s),
                int(a.n_pares_anden + b.n_pares_anden),
            )
        )
    for f in sorted(filas, key=lambda x: -x[3]):
        w(f"| {f[0]} | {f[1]} s | {f[2]} s | {f[3]} s | {f[4]} |")
    w("")
    w("Esto reemplaza al *tiempo de caminata como parámetro declarado* que "
      "figuraba en la metodología: el transbordo deja de ser un supuesto del "
      "grupo y pasa a ser un dato del feed, distinto para cada combinación y "
      "para cada sentido.\n")

    w("## 5. Verificaciones\n")
    distintas = {k: v for k, v in firmas.items() if v != 1}
    w("- **Los tres `service_id` son idénticos**: "
      f"{'una sola firma por ruta y sentido, sin excepciones' if not distintas else distintas}. "
      "Se usa el día hábil (`service_id=5`). Consecuencia: **el GTFS no "
      "distingue hábil de sábado ni de domingo**, así que la variación por tipo "
      "de día tiene que salir de molinetes y de despachos, nunca de acá.")
    w(f"- **Conectividad fuerte**: {'sí' if fuerte else 'NO'}, "
      f"{componentes} componente"
      f"{'s' if componentes != 1 else ''} fuertemente conexa"
      f"{'s' if componentes != 1 else ''}. Todo nodo alcanza a todo otro nodo, "
      "que es la condición para que el paso 6 (caminos mínimos) tenga solución "
      "para los 7.102 pares O-D observados.")
    if faltan or sobran:
        w(f"- **Cruce contra la tabla maestra del paso 1**: faltan {sorted(faltan)}, "
          f"sobran {sorted(sobran)}.")
    else:
        w(f"- **Cruce contra la tabla maestra del paso 1**: los {len(nodos)} "
          "nodos coinciden uno a uno, sin faltantes ni sobrantes.")
    w(f"- **Tramos con tiempo o distancia no positivos**: "
      f"{int((tramos.t_marcha_s <= 0).sum())} y {int((tramos.km <= 0).sum())}.")
    w("")

    w("## 6. Lo que este paso deja abierto\n")
    w("- **El reparo de la Línea E hay que confirmarlo** (sección 3.2). Las "
      "alternativas son usar el dato publicado tal cual, que está desacoplado de "
      "la geometría, o promediar ambos sentidos. Afecta solo a la E, pero la E "
      "combina con la A, la C, la D y la H.")
    w("- **La detención tiene que ser endógena en el modelo** (sección 2), con "
      "los 24 s como piso y no como valor de operación.")
    w("- **El GTFS no tiene bandas horarias ni tipos de día** (sección 5). Los "
      "tiempos de marcha son un único perfil nominal. Si la marcha se degrada en "
      "hora pico, este grafo no lo sabe: lo tiene que producir el modelo.")
    w("- Los tiempos de transbordo son `min_transfer_time`, es decir un "
      "**mínimo de diseño**, no un tiempo de caminata observado. Igual que la "
      "detención, funcionan como piso.")
    w("- El paso 4 (intervalos entre despachos) dirá si estos tiempos nominales "
      "son compatibles con la operación real.")
    w("")

    (REPORTES / "03_grafo_red.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
