"""Caminos minimos sobre el grafo de la red, con penalizacion por transbordo.

El costo de un camino es tiempo de viaje percibido:

    t = suma(marcha de cada tramo)
      + 24 s por cada **parada intermedia**
      + suma(min_transfer_time de cada transbordo)
      + P por cada transbordo

Los 24 s son la detencion de diseno del GTFS (paso 2). Van por parada intermedia
y no por tramo recorrido: el pasajero que asciende no espera la detencion de su
estacion de ascenso —esa es su ventana de abordaje— y el que desciende tampoco
espera la de su estacion de descenso. Contarlas por tramo abarataria en terminos
relativos los caminos con muchas paradas, que es justo el error que un grafo de
subte no puede darse.

**Como se implementa sin romper Dijkstra.** Se le carga la detencion a la arista
de tramo y se le descuenta a la de transbordo:

    costo(tramo u->v)      = marcha + 24
    costo(transbordo v->w) = min_transfer_time - 24 + P

Para un camino con k tramos y m transbordos eso da exactamente el tiempo real
mas 24 s, siempre: el sobrante es la detencion de la estacion de descenso final,
que es **la misma constante para todo camino** y por lo tanto no altera el
ordenamiento. El tiempo que se informa es el costo menos esos 24 s.

Los pesos quedan todos positivos: el `min_transfer_time` mas chico de la red es
de 58 s, asi que 58 - 24 = 34 s > 0.

**El acceso y el egreso dentro de un complejo valen cero.** El pasajero entra al
complejo, no a un anden: puede ascender en cualquiera de sus nodos y descender
en cualquiera de los del complejo de destino. Caminar del molinete al anden no
se modela —`pathways.txt` lo tiene, pero no para toda la red— y queda declarado
como simplificacion. La consecuencia buscada es que **caminar dentro del
complejo de origen no cuenta como transbordo**, que seria falso.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

import pandas as pd

DETENCION_S = 24


@dataclass
class Grafo:
    """Grafo dirigido de la red, listo para Dijkstra."""

    nodos: list[str]
    ady: dict[str, list[tuple[str, float, bool]]] = field(default_factory=dict)

    def vecinos(self, u: str) -> list[tuple[str, float, bool]]:
        return self.ady.get(u, [])


def construir(aristas: pd.DataFrame, penalizacion_s: float) -> Grafo:
    """Grafo con el costo ya cargado para una penalizacion por transbordo dada."""
    nodos = sorted(set(aristas.de_nodo) | set(aristas.a_nodo))
    g = Grafo(nodos=nodos, ady={n: [] for n in nodos})
    for r in aristas.itertuples():
        if r.tipo == "tramo":
            costo = float(r.t_s) + DETENCION_S
            es_transbordo = False
        elif r.tipo == "transbordo":
            costo = float(r.t_s) - DETENCION_S + penalizacion_s
            es_transbordo = True
        else:
            raise ValueError(f"tipo de arista desconocido: {r.tipo}")
        if costo < 0:
            raise ValueError(f"costo negativo en {r.de_nodo}->{r.a_nodo}: {costo}")
        g.ady[r.de_nodo].append((r.a_nodo, costo, es_transbordo))
    return g


def dijkstra(g: Grafo, origen: str) -> tuple[dict[str, float], dict[str, str | None],
                                             dict[str, int]]:
    """Costos, predecesores y cantidad de transbordos desde `origen`.

    El desempate entre caminos de igual costo es por menor cantidad de
    transbordos: sin eso el resultado dependeria del orden de las aristas, que
    es un detalle de archivo y no una decision de modelado.
    """
    dist = {n: float("inf") for n in g.nodos}
    prev: dict[str, str | None] = {n: None for n in g.nodos}
    trans = {n: 0 for n in g.nodos}
    dist[origen] = 0.0
    cola: list[tuple[float, int, str]] = [(0.0, 0, origen)]
    visto: set[str] = set()

    while cola:
        d, t, u = heapq.heappop(cola)
        if u in visto:
            continue
        visto.add(u)
        for v, w, es_tr in g.vecinos(u):
            nd, nt = d + w, t + (1 if es_tr else 0)
            if nd < dist[v] - 1e-9 or (abs(nd - dist[v]) <= 1e-9 and nt < trans[v]):
                dist[v], prev[v], trans[v] = nd, u, nt
                heapq.heappush(cola, (nd, nt, v))
    return dist, prev, trans


def reconstruir(prev: dict[str, str | None], destino: str) -> list[str]:
    camino = [destino]
    while prev[camino[-1]] is not None:
        camino.append(prev[camino[-1]])  # type: ignore[arg-type]
    return list(reversed(camino))
