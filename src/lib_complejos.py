"""Complejos de estacion: la unidad espacial de la matriz origen-destino.

Un complejo es el conjunto de nodos (par linea-estacion) que comparten
ubicacion fisica y estan unidos por una arista de transbordo en el grafo del
paso 2. Constitucion [C] es un complejo de un solo nodo; 9 de Julio [D],
Carlos Pellegrini [B] y Diagonal Norte [C] son un unico complejo de tres.

Por que importa: el dataset de Viajes y Etapas georreferencia origen y destino
con el centroide de un hexagono h3 de ~150 m, que no distingue entre estaciones
superpuestas de un mismo complejo. Al nivel del nodo esa confusion es real y
La teniamos registrada como residuo de ambiguedad. **Al nivel del complejo
desaparece**, porque las estaciones que se confunden son justamente las que el
complejo agrupa. El complejo es ademas la unidad correcta desde el modelo: el
pasajero entra y sale de un lugar fisico, y por que linea circula es resultado
de la asignacion de ruta, no dato de entrada. Es el mismo criterio de la
decision D5 sobre andenes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"


def _raiz(padre: dict[str, str], x: str) -> str:
    while padre[x] != x:
        padre[x] = padre[padre[x]]
        x = padre[x]
    return x


def construir() -> pd.DataFrame:
    """Tabla maestra del paso 1 con una columna `complejo` agregada.

    Los complejos son las componentes conexas del grafo de transbordos del
    paso 2. El identificador de cada uno es el nodo representante que elige el
    union-find; no tiene significado propio, solo sirve de clave.
    """
    m = pd.read_csv(PROCESADO / "tabla_maestra_estaciones.csv")
    m["nodo"] = m.linea + ":" + m.gtfs_stop_id.astype(str)

    aristas = pd.read_csv(PROCESADO / "grafo_aristas.csv")
    transbordos = aristas[aristas.tipo == "transbordo"]

    padre = {n: n for n in m.nodo}
    for de, a in zip(transbordos.de_nodo, transbordos.a_nodo):
        ra, rb = _raiz(padre, de), _raiz(padre, a)
        if ra != rb:
            padre[ra] = rb

    m["complejo"] = [_raiz(padre, n) for n in m.nodo]
    return m


def catalogo(m: pd.DataFrame) -> pd.DataFrame:
    """Un renglon por complejo: nombre legible, lineas, nodos y ubicacion.

    El nombre lleva sufijo de linea cuando no alcanza para identificar al
    complejo. **Callao [B] y Callao [D] son dos complejos distintos con el mismo
    nombre**: son estaciones separadas, sin arista de transbordo entre ellas, y
    el dataset de molinetes ya las desambigua con el sufijo `Callao.B` /
    `Callao.D`. Cruzar por nombre en lugar de por identificador de complejo
    duplica esas dos filas y contamina cualquier agregado; el sufijo lo evita.
    """
    g = m.groupby("complejo")
    cat = pd.DataFrame({
        "nombre": g.gtfs_nombre.apply(lambda s: " / ".join(sorted(set(s)))),
        "lineas": g.linea.apply(lambda s: "+".join(sorted(x[-1] for x in set(s)))),
        "n_nodos": g.size(),
        "nodos": g.nodo.apply(lambda s: " ".join(sorted(s))),
        "lat": g.stop_lat.mean(),
        "lon": g.stop_lon.mean(),
    })
    repetidos = cat.nombre.duplicated(keep=False)
    cat.loc[repetidos, "nombre"] = (
        cat.loc[repetidos, "nombre"] + " [" + cat.loc[repetidos, "lineas"] + "]"
    )
    if cat.nombre.duplicated().any():
        raise ValueError("quedan nombres de complejo ambiguos")
    return cat.sort_values("nombre")
