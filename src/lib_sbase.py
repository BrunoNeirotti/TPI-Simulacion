"""Lectura de las dos planillas que SBASE entrego por Ley 104 el 26/08/2026.

Las planillas no llegaron como adjuntos del mail sino **embebidas dentro del
PDF** `IF-2026-38553261-GCABA-SBASE.pdf` (`/Names /EmbeddedFiles`). Se
extrajeron a `data/raw/sbase-ley104/`; son XLSX pese a que el PDF las guarda
sin extension.

Contenido:

- `matrices-od-sbase-emova-2024.xlsx`: matriz origen-destino de 90x90 en tres
  hojas -- `Diaria`, `HPM` (8 a 9 h) y `HPT` (17 a 18 h)-- para un dia habil
  representativo de septiembre de 2024, del estudio de EMOVA S.A. sobre
  transacciones SUBE. La hoja `EST` trae el mapa id -> estacion.
- `perfil-carga-2024-lineas-actuales.xlsx`: ascensos, descensos y carga a bordo
  por estacion, sentido y hora pico, para las seis lineas. La hoja
  `id estacion` trae otro mapa id -> estacion.

**Los dos mapas de id NO son el mismo.** Coinciden en los ids 1 a 75 y difieren
en los 15 ultimos: la matriz O-D pone la cola de la Linea E (Correo Central,
Catalinas, Retiro E) al final, despues de la H, y el perfil de carga la pone
antes. Cruzar una planilla con el mapa de la otra corre 15 estaciones. Por eso
cada lector usa el mapa de su propio libro y nunca el del otro.

Las 90 estaciones cruzan una a una con los 90 nodos del grafo del paso 2 (par
linea-estacion). El cruce es la tabla ALIAS de abajo: explicito y
deterministico, sin comparacion difusa, igual que en `lib_normalizacion`.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "raw" / "sbase-ley104"
PROCESADO = RAIZ / "data" / "processed"

XLSX_OD = CRUDO / "matrices-od-sbase-emova-2024.xlsx"
XLSX_CARGA = CRUDO / "perfil-carga-2024-lineas-actuales.xlsx"

# Nombre abreviado de SBASE -> nombre GTFS del nodo, por linea. La clave es
# (linea, nombre SBASE) porque hay nombres que se repiten entre lineas
# (Callao, Pueyrredon, Retiro, Independencia, Congreso, Moreno).
ALIAS: dict[tuple[str, str], str] = {
    ("A", "SanPedrito"): "San Pedrito",
    ("A", "Flores"): "San Jose de Flores",
    ("A", "Carabobo"): "Carabobo",
    ("A", "Puan"): "Puan",
    ("A", "PJunta"): "Primera Junta",
    ("A", "Acoyte"): "Acoyte",
    ("A", "RJaneiro"): "Rio de Janeiro",
    ("A", "CBarros"): "Castro Barros",
    ("A", "Loria"): "Loria",
    ("A", "Miserere"): "Plaza Miserere",
    ("A", "Alberti"): "Alberti",
    ("A", "Pasco"): "Pasco",
    ("A", "Congreso"): "Congreso",
    ("A", "SnzPena"): "Saenz Pena",
    ("A", "Lima"): "Lima",
    ("A", "Piedras"): "Piedras",
    ("A", "Peru"): "Peru",
    ("A", "PMayo"): "Plaza de Mayo",
    ("B", "JMRosas"): "Juan Manuel de Rosas",
    ("B", "Echeverria"): "Echeverria",
    ("B", "LosIncas"): "De Los Incas - Parque Chas",
    ("B", "Tronador"): "Tronador - Villa Ortuzar",
    ("B", "Lacroze"): "Federico Lacroze",
    ("B", "Dorrego"): "Dorrego",
    ("B", "Malabia"): "Malabia",
    ("B", "Gallardo"): "angel Gallardo",
    ("B", "Medrano"): "Medrano",
    ("B", "Gardel"): "Carlos Gardel",
    ("B", "Pueyr"): "Pueyrredon",
    ("B", "Pasteur"): "Pasteur",
    ("B", "CallaoB"): "Callao",
    ("B", "Uruguay"): "Uruguay",
    ("B", "Pellegrini"): "Carlos Pellegrini",
    ("B", "Florida"): "Florida",
    ("B", "Alem"): "Leandro N. Alem",
    ("C", "Constitucion"): "Constitucion",
    ("C", "SanJuan"): "San Juan",
    ("C", "Indepen"): "Independencia",
    ("C", "Mariano Moreno"): "Moreno",
    ("C", "AVMayo"): "Avenida de Mayo",
    ("C", "DNorte"): "Diagonal Norte",
    ("C", "Lavalle"): "Lavalle",
    ("C", "SanMartin"): "General San Martin",
    ("C", "Retiro"): "Retiro",
    ("D", "CongresoTuc"): "Congreso de Tucuman",
    ("D", "Juramento"): "Juramento",
    ("D", "J Hernandez"): "Jose Hernandez",
    ("D", "Olleros"): "Olleros",
    ("D", "Carranza"): "Ministro Carranza",
    ("D", "Palermo"): "Palermo",
    ("D", "Pitalia"): "Plaza Italia",
    ("D", "Scal Ortiz"): "Scalabrini Ortiz",
    ("D", "Bulnes"): "Bulnes",
    ("D", "Aguero"): "Aguero",
    ("D", "Pueyrredon"): "Pueyrredon",
    ("D", "FMedicina"): "Facultad de Medicina",
    ("D", "CallaoD"): "Callao",
    ("D", "Tribuna"): "Tribunales",
    ("D", "9 de julio"): "9 de Julio",
    ("D", "Catedral"): "Catedral",
    ("E", "Virreyes"): "Plaza de los Virreyes",
    ("E", "Varela"): "Varela",
    ("E", "Medalla"): "Medalla Milagrosa",
    ("E", "EMitre"): "Emilio Mitre",
    ("E", "Moreno"): "Jose Maria Moreno",
    ("E", "LaPlata"): "La Plata",
    ("E", "Boedo"): "Boedo",
    ("E", "Urquiza"): "General Urquiza",
    ("E", "Jujuy"): "Jujuy",
    ("E", "Pichin"): "Pichincha",
    ("E", "ERios"): "Entre Rios",
    ("E", "SanJose"): "San Jose",
    ("E", "Independencia E"): "Independencia",
    ("E", "Belgrano"): "Belgrano",
    ("E", "Bolivar"): "Bolivar",
    ("E", "CCentral"): "Correo Central",
    ("E", "Catalinas"): "Catalinas",
    ("E", "RetiroE"): "Retiro",
    ("H", "Hospitales"): "Hospitales",
    ("H", "Patricios"): "Parque Patricios",
    ("H", "Caseros"): "Caseros",
    ("H", "Inclan"): "Inclan",
    ("H", "HPrimo"): "Humberto 1",
    ("H", "Venezuela"): "Venezuela",
    ("H", "Once"): "Once",
    ("H", "Corrientes"): "Corrientes",
    ("H", "Cordoba"): "Cordoba",
    ("H", "SantaFe"): "Santa Fe",
    ("H", "LasHeras"): "Las Heras",
    ("H", "FDerecho"): "Facultad de Derecho",
}


def _norm(texto: str) -> str:
    """Mayusculas sin acentos, sin puntuacion y sin espacios."""
    s = unicodedata.normalize("NFD", str(texto))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.upper()
    return re.sub(r"[^A-Z0-9]+", "", s)


def nodos() -> pd.DataFrame:
    """Los 90 nodos del grafo del paso 2, con clave normalizada de cruce."""
    g = pd.read_csv(PROCESADO / "grafo_nodos.csv")
    g["linea_corta"] = g.linea.str.replace("Linea", "", regex=False)
    g["clave"] = g.linea_corta + "|" + g.nombre.map(_norm)
    return g


def mapa_nodos(ids: dict[int, tuple[str, str]]) -> dict[int, str]:
    """id de SBASE -> nodo_id del grafo. Falla si el cruce no es 90 de 90.

    `ids` es {id: (nombre SBASE, linea)}. El cruce pasa por ALIAS y luego por
    la clave normalizada; no hay comparacion difusa en ningun paso.
    """
    por_clave = dict(zip(nodos().clave, nodos().nodo_id))
    salida: dict[int, str] = {}
    faltan = []
    for i, (nombre, linea) in ids.items():
        gtfs = ALIAS.get((linea, nombre))
        if gtfs is None:
            faltan.append((i, nombre, linea, "sin alias"))
            continue
        nodo = por_clave.get(f"{linea}|{_norm(gtfs)}")
        if nodo is None:
            faltan.append((i, nombre, linea, f"sin nodo para {gtfs!r}"))
            continue
        salida[i] = nodo
    if faltan:
        raise ValueError(f"cruce incompleto ({len(faltan)}): {faltan}")
    if len(set(salida.values())) != 90:
        raise ValueError(f"nodos repetidos: {len(set(salida.values()))} distintos")
    return salida


def ids_od() -> dict[int, tuple[str, str]]:
    """Mapa id -> (nombre, linea) de la hoja EST del libro de matrices.

    La hoja EST no trae la linea, asi que se deduce de ALIAS: el nombre de
    SBASE identifica la linea sin ambiguedad porque los que se repiten entre
    lineas llevan sufijo (CallaoB / CallaoD, RetiroE, Independencia E).
    """
    df = pd.read_excel(XLSX_OD, sheet_name="EST", header=1).dropna(subset=["id"])
    por_nombre: dict[str, list[str]] = {}
    for linea, nombre in ALIAS:
        por_nombre.setdefault(nombre, []).append(linea)
    salida = {}
    for _, r in df.iterrows():
        nombre = str(r.estacion).strip()
        lineas = por_nombre.get(nombre, [])
        if len(lineas) != 1:
            raise ValueError(f"{nombre!r} no identifica una linea unica: {lineas}")
        salida[int(r.id)] = (nombre, lineas[0])
    if len(salida) != 90:
        raise ValueError(f"la hoja EST trae {len(salida)} estaciones, no 90")
    return salida


def ids_carga() -> dict[int, tuple[str, str]]:
    """Mapa id -> (nombre, linea) de la hoja `id estacion` del perfil de carga."""
    hoja = [h for h in pd.ExcelFile(XLSX_CARGA).sheet_names if h.startswith("id")][0]
    df = pd.read_excel(XLSX_CARGA, sheet_name=hoja, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    col_id = [c for c in df.columns if c.lower().startswith("id")][0]
    col_linea = [c for c in df.columns if _norm(c) == "LINEA"][0]
    df = df.dropna(subset=[col_id])
    salida = {
        int(r[col_id]): (str(r["estacion"]).strip(), str(r[col_linea]).strip())
        for _, r in df.iterrows()
    }
    if len(salida) != 90:
        raise ValueError(f"la hoja de ids trae {len(salida)} estaciones, no 90")
    return salida


def matriz(periodo: str) -> pd.DataFrame:
    """Una de las tres matrices, en formato largo: origen, destino, viajes.

    `periodo` es 'diaria', 'hpm' o 'hpt'. Devuelve nodo_id del grafo, no ids de
    SBASE, y descarta los ceros. La diagonal es cero en las tres hojas.
    """
    hojas = {"diaria": ("Diaria", 3, 2), "hpm": ("HPM", 2, 3), "hpt": ("HPT", 2, 3)}
    hoja, fila0, col0 = hojas[periodo]
    crudo = pd.read_excel(XLSX_OD, sheet_name=hoja, header=None)
    bloque = crudo.iloc[fila0:fila0 + 90, col0:col0 + 90].to_numpy(dtype=float)
    mapa = mapa_nodos(ids_od())
    filas = []
    for i in range(90):
        for j in range(90):
            v = bloque[i][j]
            if v:
                filas.append((periodo, mapa[i + 1], mapa[j + 1], float(v)))
    return pd.DataFrame(filas, columns=["periodo", "origen", "destino", "viajes"])


def perfil_carga() -> pd.DataFrame:
    """Perfil de carga en formato largo.

    Una fila por (linea, periodo, sentido, estacion) con ascensos, descensos y
    la carga a bordo en el tramo que **sale** de esa estacion en el sentido de
    marcha. La columna P del archivo es carga saliente, no pasajeros que
    permanecen: en la Linea A hacia Plaza de Mayo, la carga en Piedras
    (5.104,7) menos los descensos de Peru (3.084,3) mas los ascensos de Peru
    (51) da 2.071,5, que es la carga en Peru y tambien lo que baja en Plaza de
    Mayo, donde la carga es cero.

    Las estaciones vienen listadas en orden inverso al sentido de marcha: la
    primera fila de cada bloque es la cabecera de llegada.
    """
    crudo = pd.read_excel(XLSX_CARGA, sheet_name="SBP-2024", header=None)
    mapa = mapa_nodos(ids_carga())
    por_nombre = {
        (linea, _norm(nombre)): mapa[i] for i, (nombre, linea) in ids_carga().items()
    }
    filas = []
    inicios = [
        i for i in range(len(crudo))
        if isinstance(crudo.iat[i, 0], str) and _norm(crudo.iat[i, 0]).startswith("LINEA")
    ]
    for ini in inicios:
        linea = str(crudo.iat[ini, 0]).split()[-1].strip()
        bloques = []  # (periodo, sentido, col_estacion, col_S)
        for col_bloque in (1, 10):
            periodo = str(crudo.iat[ini, col_bloque]).split()[0].strip().upper()
            for col in (col_bloque + 1, col_bloque + 4):
                sentido = str(crudo.iat[ini, col]).replace("Hacia", "").strip()
                bloques.append((periodo, sentido, col_bloque, col))
        i = ini + 2
        estaciones = []
        while i < len(crudo) and isinstance(crudo.iat[i, 1], str) and crudo.iat[i, 1].strip():
            estaciones.append(i)
            i += 1
        for periodo, sentido, col_est, col_s in bloques:
            for orden, fila in enumerate(estaciones, start=1):
                nombre = str(crudo.iat[fila, col_est]).strip()
                nodo = por_nombre.get((linea, _norm(nombre)))
                if nodo is None:
                    raise ValueError(f"estacion sin cruce en perfil: {linea} {nombre!r}")
                filas.append({
                    "linea": f"Linea{linea}",
                    "periodo": periodo,
                    "sentido_hacia": sentido,
                    "orden_llegada": orden,
                    "nodo": nodo,
                    "estacion_sbase": nombre,
                    "suben": float(crudo.iat[fila, col_s] or 0),
                    "bajan": float(crudo.iat[fila, col_s + 1] or 0),
                    "carga_saliente": float(crudo.iat[fila, col_s + 2] or 0),
                })
    return pd.DataFrame(filas)
