"""Paso 1 del plan de trabajo: tabla maestra de estaciones.

Cruza los nombres de estacion del dataset de molinetes contra los stop_id del
GTFS, con reporte explicito de los no matcheos. Ademas normaliza el sufijo de
anden que codifica el identificador de molinete.

Salidas:
  data/processed/tabla_maestra_estaciones.csv
  data/processed/molinetes_inventario.csv
  reports/01_tabla_maestra.md
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from lib_molinetes import ResultadoLectura, leer_zip  # noqa: E402
from lib_normalizacion import (  # noqa: E402
    CENTINELAS,
    clave,
    normalizar,
    quitar_sufijo_linea,
)

RAIZ = Path(__file__).resolve().parent.parent
ZIP_MOLINETES = RAIZ / "data" / "raw" / "molinetes-2025.zip"
GTFS = RAIZ / "data" / "raw" / "gtfs"
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

# El identificador de molinete no tiene una unica forma. Verificado sobre 2025:
#   3 campos  Linea_Estacion_Aparato              -> sin dato de anden
#   4 campos  Linea_Estacion_Sentido_Aparato      -> caso mayoritario
#   5 campos  Linea_Estacion_Zona_Sentido_Aparato -> ej. LineaA_Miserere_Q_NE_Turn01
# Ademas hay registros con MOLINETE nulo, que conservan demanda de estacion pero
# no permiten atribuirla a un anden.
SENTIDO_CANONICO = {
    "N": "N", "NORTE": "N",
    "S": "S", "SUR": "S",
    "E": "E", "ESTE": "E",
    "O": "O", "OESTE": "O", "W": "O",
    "NE": "NE", "NO": "NO", "SE": "SE", "SO": "SO",
    # No son puntos cardinales sino zonas de vestibulo: se reconocen para no
    # confundirlas con un anden, pero no identifican sentido de circulacion.
    "HALL": "HALL",
    "C": "C",        # anden central (LineaD_CongresoTuc_C_*)
    "ALIV": "ALIV",  # acceso aliviador (LineaD_Pueyrredon_Aliv_*)
}
# Sentidos que si identifican un anden por direccion de circulacion.
SENTIDO_DIRECCIONAL = {"N", "S", "E", "O", "NE", "NO", "SE", "SO"}
# Sufijos de aparato: Turn=molinete, Asc=ascensor, Discap=acceso accesible.
RE_APARATO = re.compile(r"^(Turn|Asc|Discap|Torniquete|Mol)", re.IGNORECASE)


def cargar_gtfs() -> pd.DataFrame:
    """Estaciones del GTFS (location_type=1) con su linea, derivada de los viajes."""
    stops = pd.read_csv(GTFS / "stops.txt", dtype=str)
    trips = pd.read_csv(GTFS / "trips.txt", dtype=str)
    stop_times = pd.read_csv(GTFS / "stop_times.txt", dtype=str)

    andenes = stops[stops.location_type == "0"][["stop_id", "parent_station"]]
    estaciones = stops[stops.location_type == "1"][
        ["stop_id", "stop_name", "stop_lat", "stop_lon"]
    ].rename(columns={"stop_id": "parent_station", "stop_name": "gtfs_nombre"})

    m = (
        stop_times.merge(trips[["trip_id", "route_id"]], on="trip_id")
        .merge(andenes, on="stop_id")
        .merge(estaciones, on="parent_station")
    )
    g = (
        m.groupby(["route_id", "parent_station", "gtfs_nombre", "stop_lat", "stop_lon"])
        .agg(n_andenes=("stop_id", "nunique"))
        .reset_index()
        .rename(columns={"route_id": "linea", "parent_station": "gtfs_stop_id"})
    )
    g["gtfs_clave"] = g.gtfs_nombre.map(normalizar)
    # El Premetro esta fuera del alcance del modelo (ver docs/contexto-del-proyecto.md).
    return g[~g.linea.str.upper().str.startswith("PM")].reset_index(drop=True)


def escanear_molinetes() -> tuple[pd.DataFrame, ResultadoLectura]:
    """Inventario de (linea, estacion, molinete) con registros y pasajeros."""
    res = ResultadoLectura()
    acc: dict[tuple[str, str, str], list[int]] = collections.defaultdict(
        lambda: [0, 0, None, None]
    )
    for r in leer_zip(str(ZIP_MOLINETES), res):
        k = (r["LINEA"], r["ESTACION"], r["MOLINETE"])
        a = acc[k]
        a[0] += 1
        a[1] += r["pax_TOTAL"]
        f = r["_fecha"]
        if f is not None:
            a[2] = f if a[2] is None or f < a[2] else a[2]
            a[3] = f if a[3] is None or f > a[3] else a[3]
    filas = [
        {
            "linea": l, "estacion_molinetes": e, "molinete": mo,
            "n_registros": v[0], "pax_total": v[1],
            "primera_fecha": v[2], "ultima_fecha": v[3],
        }
        for (l, e, mo), v in acc.items()
    ]
    return pd.DataFrame(filas), res


def parsear_molinete(mid) -> tuple[str | None, str | None]:
    """Extrae (sentido_canonico, sentido_crudo) del identificador de molinete.

    Devuelve (None, None) cuando el identificador no trae campo de anden. El
    anteultimo campo solo se acepta como sentido si figura en SENTIDO_CANONICO:
    de lo contrario es parte del nombre de la estacion, como en los
    identificadores de tres campos (LineaA_Alberti_Turn01).
    """
    if mid is None or not isinstance(mid, str) or es_centinela(mid):
        return None, None
    partes = mid.split("_")
    if len(partes) < 3 or not RE_APARATO.match(partes[-1]):
        return None, None
    crudo = partes[-2]
    canon = SENTIDO_CANONICO.get(crudo.upper())
    return (canon, crudo) if canon else (None, crudo)


def es_centinela(valor) -> bool:
    """Detecta valores centinela, comparando el texto crudo y el normalizado.

    Hace falta mirar el crudo porque la normalizacion quita la puntuacion y
    convierte '#N/D' en 'N D', que ya no coincide con el centinela declarado.
    """
    if valor is None or not isinstance(valor, str):
        return True
    return valor.strip().upper() in CENTINELAS or normalizar(valor) in CENTINELAS


def main() -> None:
    PROCESADO.mkdir(parents=True, exist_ok=True)
    REPORTES.mkdir(parents=True, exist_ok=True)

    gtfs = cargar_gtfs()
    inv, res = escanear_molinetes()
    print("Molinetes:", res.resumen())

    inv["es_centinela"] = (
        inv.estacion_molinetes.map(es_centinela) | inv.linea.map(es_centinela)
    )
    inv["es_premetro"] = inv.linea.str.upper().str.contains("PM")
    inv[["sentido", "sentido_crudo"]] = inv.molinete.map(
        lambda m: pd.Series(parsear_molinete(m))
    ).apply(pd.Series)

    sufijos = inv.apply(
        lambda r: quitar_sufijo_linea(str(r.estacion_molinetes), r.linea)[1], axis=1
    )
    inv["sufijo_linea"] = sufijos
    inv["sufijo_incoherente"] = [
        s is not None and l.endswith(s) is False
        for s, l in zip(inv.sufijo_linea, inv.linea)
    ]
    inv["clave"] = [
        clave(str(e), l) for e, l in zip(inv.estacion_molinetes, inv.linea)
    ]

    # --- Cruce ---
    activo = inv[~inv.es_centinela & ~inv.es_premetro].copy()
    llaves = activo.groupby(["linea", "estacion_molinetes", "clave"], as_index=False).agg(
        n_molinetes=("molinete", "nunique"),
        n_registros=("n_registros", "sum"),
        pax_total=("pax_total", "sum"),
    )
    cruce = llaves.merge(
        gtfs[["linea", "gtfs_clave", "gtfs_stop_id", "gtfs_nombre", "stop_lat", "stop_lon", "n_andenes"]],
        left_on=["linea", "clave"], right_on=["linea", "gtfs_clave"], how="left",
    )
    sin_match = cruce[cruce.gtfs_stop_id.isna()].sort_values("pax_total", ascending=False)
    con_match = cruce[cruce.gtfs_stop_id.notna()]

    # Estaciones del GTFS que ningun nombre de molinetes alcanzo
    alcanzadas = set(zip(con_match.linea, con_match.gtfs_stop_id))
    huerfanas = gtfs[[(l, s) not in alcanzadas for l, s in zip(gtfs.linea, gtfs.gtfs_stop_id)]]

    tabla = (
        con_match.groupby(
            ["linea", "gtfs_stop_id", "gtfs_nombre", "stop_lat", "stop_lon", "n_andenes"],
            as_index=False,
        )
        .agg(
            nombres_molinetes=("estacion_molinetes", lambda s: " | ".join(sorted(set(s)))),
            n_molinetes=("n_molinetes", "sum"),
            n_registros=("n_registros", "sum"),
            pax_total=("pax_total", "sum"),
        )
        .sort_values(["linea", "gtfs_nombre"])
    )
    tabla.to_csv(PROCESADO / "tabla_maestra_estaciones.csv", index=False, encoding="utf-8")
    inv.sort_values(["linea", "estacion_molinetes", "molinete"]).to_csv(
        PROCESADO / "molinetes_inventario.csv", index=False, encoding="utf-8"
    )

    escribir_reporte(inv, tabla, sin_match, huerfanas, gtfs, res)
    print(f"Estaciones matcheadas: {len(tabla)} / {len(gtfs)} del GTFS")
    print(f"Nombres sin match: {len(sin_match)} | Estaciones GTFS huerfanas: {len(huerfanas)}")


def escribir_reporte(inv, tabla, sin_match, huerfanas, gtfs, res) -> None:
    pax_activo = inv[~inv.es_centinela & ~inv.es_premetro].pax_total.sum()
    L = []
    A = L.append
    A("# Paso 1, Tabla maestra de estaciones\n")
    A("Generado por `src/01_tabla_maestra_estaciones.py`. "
      "Fuente de demanda: `molinetes-2025.zip`. Fuente de topologia: GTFS.\n")
    A("## Control de lectura\n")
    A(f"- {res.resumen()}\n")
    A(f"- Total de pasajeros leidos: **{inv.pax_total.sum():,}**\n")
    A(f"- Pasajeros en registros utilizables (sin Premetro ni centinelas): "
      f"**{pax_activo:,}**\n")
    A("\n## Resultado del cruce\n")
    A(f"- Estaciones del GTFS (subte, sin Premetro): **{len(gtfs)}**\n")
    A(f"- Estaciones con demanda asignada: **{len(tabla)}**\n")
    A(f"- Nombres de molinetes sin correspondencia: **{len(sin_match)}**\n")
    A(f"- Estaciones del GTFS sin ningun molinete: **{len(huerfanas)}**\n")

    if len(sin_match):
        A("\n### Nombres de molinetes sin correspondencia en el GTFS\n")
        A("| Linea | Nombre en molinetes | Clave normalizada | Molinetes | Pasajeros |")
        A("|---|---|---|---:|---:|")
        for _, r in sin_match.iterrows():
            A(f"| {r.linea} | `{r.estacion_molinetes}` | `{r.clave}` | "
              f"{r.n_molinetes} | {r.pax_total:,} |")
    if len(huerfanas):
        A("\n### Estaciones del GTFS sin demanda asignada\n")
        A("| Linea | Estacion GTFS | stop_id |")
        A("|---|---|---|")
        for _, r in huerfanas.iterrows():
            A(f"| {r.linea} | {r.gtfs_nombre} | `{r.gtfs_stop_id}` |")

    cent = inv[inv.es_centinela]
    A("\n## Registros centinela descartados\n")
    if len(cent):
        A("| Linea | Estacion | Molinete | Registros | Pasajeros |")
        A("|---|---|---|---:|---:|")
        for _, r in cent.sort_values("pax_total", ascending=False).iterrows():
            A(f"| {r.linea} | `{r.estacion_molinetes}` | `{r.molinete}` | "
              f"{r.n_registros:,} | {r.pax_total:,} |")
    else:
        A("Ninguno.\n")

    inc = inv[inv.sufijo_incoherente & ~inv.es_centinela]
    A("\n## Sufijo de linea incoherente con el campo LINEA\n")
    if len(inc):
        A("| Linea | Estacion | Sufijo | Molinetes | Pasajeros |")
        A("|---|---|---|---:|---:|")
        for (l, e, s), g in inc.groupby(["linea", "estacion_molinetes", "sufijo_linea"]):
            A(f"| {l} | `{e}` | `.{s}` | {g.molinete.nunique()} | {g.pax_total.sum():,} |")
    else:
        A("Ninguno.\n")

    act = inv[~inv.es_centinela & ~inv.es_premetro]
    tot = act.pax_total.sum()
    sin_id = act[act.molinete.map(es_centinela)]
    direccional = act[act.sentido.isin(SENTIDO_DIRECCIONAL)]
    A("\n## Atribucion de la demanda a un anden\n")
    A("El identificador de molinete codifica el anden, lo que en principio "
      "permitiria demanda por anden y no solo por estacion. La cobertura real "
      "es parcial:\n")
    A("| Situacion | Molinetes | Pasajeros | % del total |")
    A("|---|---:|---:|---:|")
    A(f"| Sentido de circulacion identificable | {len(direccional)} | "
      f"{direccional.pax_total.sum():,} | {100*direccional.pax_total.sum()/tot:.1f}\\% |")
    no_dir = act[act.sentido.notna() & ~act.sentido.isin(SENTIDO_DIRECCIONAL)]
    A(f"| Zona de vestibulo, sin sentido (HALL, C, Aliv) | {len(no_dir)} | "
      f"{no_dir.pax_total.sum():,} | {100*no_dir.pax_total.sum()/tot:.1f}\\% |")
    sin_campo = act[act.sentido.isna() & ~act.molinete.map(es_centinela)]
    A(f"| Identificador sin campo de anden | {len(sin_campo)} | "
      f"{sin_campo.pax_total.sum():,} | {100*sin_campo.pax_total.sum()/tot:.1f}\\% |")
    A(f"| Sin identificador de molinete | {len(sin_id)} | "
      f"{sin_id.pax_total.sum():,} | {100*sin_id.pax_total.sum()/tot:.1f}\\% |")
    A(f"\n**Solo el {100*direccional.pax_total.sum()/tot:.1f}\\% de la demanda es "
      "atribuible a un anden por sentido de circulacion.**\n")
    vc = act.groupby(act.sentido.fillna("(sin dato)")).agg(
        molinetes=("molinete", "nunique"), pax=("pax_total", "sum")
    ).sort_values("pax", ascending=False)
    A("\n| Sentido | Molinetes | Pasajeros |")
    A("|---|---:|---:|")
    for k, r in vc.iterrows():
        A(f"| {k} | {r.molinetes} | {r.pax:,} |")

    (REPORTES / "01_tabla_maestra.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
