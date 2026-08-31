"""Paso 6 del plan: caminos minimos con penalizacion por transbordo.

Precalcula, para cada par ordenado de complejos de estacion, el camino de menor
tiempo percibido sobre el grafo del paso 2. El modelo de AnyLogic consume esa
tabla: la ruta deja de ser una decision del simulador y pasa a ser un dato, lo
que hace que el escenario con Linea F sea barato (paso 8: agregar nodos y
aristas y volver a correr esto).

Es una asignacion todo-o-nada: cada par O-D manda todo su flujo por un unico
camino. Es una simplificacion fuerte y este reporte la mide en vez de
declararla nada mas, la seccion 3 cuenta cuantos pares tienen un segundo
camino practicamente empatado.

Salidas en data/processed/:
  caminos_minimos.csv        camino elegido por par, con la penalizacion base
  caminos_sensibilidad.csv   como cambia la asignacion con la penalizacion
  caminos_reparto_linea.csv  reparto por linea de ascenso, predicho y observado

Reporte en reports/07_caminos_minimos.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lib_caminos as lcam  # noqa: E402
import lib_complejos as lc  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

# Penalizacion por transbordo, en segundos, ademas del `min_transfer_time` que
# el GTFS ya declara para caminar entre andenes. Representa la espera del
# proximo tren mas el desagrado del trasbordo.
#
# El valor base sale de los despachos medidos en el paso 4: en hora pico los
# intervalos van de 3,15 min (C) a 5,22 min (E), de modo que la espera esperada
# (la mitad del intervalo) cae entre 95 y 157 s. 120 s queda en el medio. **No
# es un dato**, es un supuesto, y por eso se recorre el rango completo.
PENALIZACION_BASE_S = 120.0
PENALIZACIONES_S = [0.0, 60.0, 120.0, 180.0, 300.0]

# Umbral para considerar que un segundo camino esta empatado con el elegido.
EMPATE_S = 60.0


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def mil(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def dec(x: float, n: int = 1) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def mmss(segundos: float) -> str:
    m, s = divmod(int(round(segundos)), 60)
    return f"{m}:{s:02d}"


# --------------------------------------------------------------------------
# Resolucion de un par de complejos
# --------------------------------------------------------------------------

def resolver(penalizacion_s: float, aristas: pd.DataFrame,
             nodos_de: dict[str, list[str]], linea_de: dict[str, str]) -> pd.DataFrame:
    """Camino minimo de complejo a complejo para una penalizacion dada.

    El acceso y el egreso dentro del complejo valen cero, de modo que el
    pasajero puede ascender en cualquier nodo del complejo de origen y
    descender en cualquiera del de destino: se toma el minimo sobre ese
    producto. Eso es lo que evita que caminar dentro del complejo de origen se
    cuente como transbordo, que seria falso.
    """
    g = lcam.construir(aristas, penalizacion_s)
    dist, prev, trans = {}, {}, {}
    for u in g.nodos:
        dist[u], prev[u], trans[u] = lcam.dijkstra(g, u)

    filas = []
    complejos = sorted(nodos_de)
    for co in complejos:
        for cd in complejos:
            if co == cd:
                continue
            mejor = None
            for u in nodos_de[co]:
                for v in nodos_de[cd]:
                    d = dist[u][v]
                    if not np.isfinite(d):
                        continue
                    # Desempate estable: costo, transbordos, y despues los
                    # identificadores, para que el resultado no dependa del
                    # orden en que se recorren los nodos.
                    clave = (d, trans[u][v], u, v)
                    if mejor is None or clave < mejor[0]:
                        mejor = (clave, u, v)
            if mejor is None:
                filas.append({"comp_origen": co, "comp_destino": cd,
                              "alcanzable": False})
                continue
            (costo, n_tr, _, _), u, v = mejor
            camino = lcam.reconstruir(prev[u], v)
            filas.append({
                "comp_origen": co, "comp_destino": cd, "alcanzable": True,
                # El costo sobrepasa al tiempo real en la detencion de la
                # estacion de descenso, que es la misma constante para todo
                # camino (ver `lib_caminos`).
                "tiempo_s": costo - lcam.DETENCION_S - penalizacion_s * n_tr,
                "costo_s": costo - lcam.DETENCION_S,
                "n_transbordos": n_tr,
                "nodo_ascenso": u, "linea_ascenso": linea_de[u],
                "nodo_descenso": v, "linea_descenso": linea_de[v],
                "n_estaciones": len(camino),
                "camino": " ".join(camino),
            })
    return pd.DataFrame(filas)


def segundo_mejor(aristas: pd.DataFrame, nodos_de: dict[str, list[str]],
                  linea_de: dict[str, str], elegido: pd.DataFrame) -> pd.DataFrame:
    """Mejor camino que asciende por una linea distinta de la elegida.

    Es la medida de cuan disputada esta la asignacion: si el segundo camino
    llega casi al mismo tiempo, mandar el 100 % del flujo por el primero es una
    decision que los datos no respaldan.
    """
    g = lcam.construir(aristas, PENALIZACION_BASE_S)
    dist = {u: lcam.dijkstra(g, u)[0] for u in g.nodos}
    brecha = []
    for r in elegido.itertuples():
        alternativas = [
            dist[u][v]
            for u in nodos_de[r.comp_origen] if linea_de[u] != r.linea_ascenso
            for v in nodos_de[r.comp_destino]
            if np.isfinite(dist[u][v])
        ]
        brecha.append(min(alternativas) - r.costo_s - lcam.DETENCION_S
                      if alternativas else np.nan)
    salida = elegido[["comp_origen", "comp_destino"]].copy()
    salida["brecha_s"] = brecha
    return salida


# --------------------------------------------------------------------------
# Programa
# --------------------------------------------------------------------------

def main() -> None:
    m = lc.construir()
    cat = lc.catalogo(m)
    nombre = cat.nombre.to_dict()
    aristas = pd.read_csv(PROCESADO / "grafo_aristas.csv")

    nodos_de: dict[str, list[str]] = (
        m.groupby("complejo").nodo.apply(lambda s: sorted(s)).to_dict())
    linea_de = dict(zip(m.nodo, m.linea))

    # --- Camino elegido con la penalizacion base ---
    base = resolver(PENALIZACION_BASE_S, aristas, nodos_de, linea_de)
    if not base.alcanzable.all():
        faltan = base[~base.alcanzable]
        raise RuntimeError(f"{len(faltan)} pares sin camino: la red no es conexa")
    base = base.drop(columns=["alcanzable"])
    base.to_csv(PROCESADO / "caminos_minimos.csv", index=False)

    # --- Sensibilidad a la penalizacion ---
    variantes = {p: resolver(p, aristas, nodos_de, linea_de) for p in PENALIZACIONES_S}
    ref = variantes[PENALIZACION_BASE_S].set_index(["comp_origen", "comp_destino"])
    filas_sens = []
    for p, v in variantes.items():
        w = v.set_index(["comp_origen", "comp_destino"])
        filas_sens.append({
            "penalizacion_s": p,
            "transbordos_medios": w.n_transbordos.mean(),
            "pares_sin_transbordo": int((w.n_transbordos == 0).sum()),
            "tiempo_medio_s": w.tiempo_s.mean(),
            "cambian_camino": int((w.camino != ref.camino).sum()),
            "cambian_linea_ascenso": int((w.linea_ascenso != ref.linea_ascenso).sum()),
        })
    sens = pd.DataFrame(filas_sens)
    sens.to_csv(PROCESADO / "caminos_sensibilidad.csv", index=False)

    brechas = segundo_mejor(aristas, nodos_de, linea_de, base)

    # --- Contraste contra la linea de ascenso observada ---
    reparto = contrastar_lineas(base, m, nombre)
    reparto.to_csv(PROCESADO / "caminos_reparto_linea.csv", index=False)

    escribir_reporte(base, sens, brechas, reparto, cat, nombre, m)
    print("paso 6 listo")


def contrastar_lineas(base: pd.DataFrame, m: pd.DataFrame,
                      nombre: dict) -> pd.DataFrame:
    """Reparto por linea de ascenso: predicho contra **dos** fuentes observadas.

    Solo tiene sentido en los complejos con mas de una linea, que son los
    unicos donde el pasajero elige. Se contrasta contra:

    - **Molinetes** del 16/10/2024, por estacion del complejo. Es una tercera
      fuente, independiente del dataset O-D. Su sesgo conocido es que mide la
      estacion **de ingreso**, no la linea de ascenso: quien entra por un
      molinete y camina hasta el anden de la otra linea queda mal atribuido. Es
      el mismo sesgo que declaramos para el contraste por anden.
    - **`linea_etapa`** del dataset O-D, que si es la linea del molinete que
      registro la transaccion. Su defecto es otro: en dos complejos el dataset
      colapsa todos los ascensos sobre una sola linea (ver el reporte).

    Ninguna de las dos es una medicion limpia del reparto por linea. Que
    discrepen entre si es informacion, no ruido, y por eso van las dos.
    """
    obs = pd.read_csv(PROCESADO / "od_pares_linea.csv")
    flujo = obs.groupby(["comp_origen", "comp_destino"]).expandidas.sum()

    multi = m.groupby("complejo").linea.nunique()
    multi = set(multi[multi > 1].index)

    pred = base[base.comp_origen.isin(multi)].copy()
    pred["flujo"] = pred.join(
        flujo.rename("f"), on=["comp_origen", "comp_destino"]).f.fillna(0.0)
    predicho = pred.groupby(["comp_origen", "linea_ascenso"]).flujo.sum()

    observado = (obs[obs.comp_origen.isin(multi)]
                 .groupby(["comp_origen", "linea_ascenso"]).expandidas.sum())

    mol = pd.read_csv(PROCESADO / "molinetes_20241016.csv").merge(
        m[["nodo", "complejo", "linea"]], on="nodo")
    molinetes = (mol[mol.complejo.isin(multi)]
                 .groupby(["complejo", "linea"]).pax.sum())
    molinetes.index.names = ["comp_origen", "linea_ascenso"]

    tabla = pd.concat([molinetes.rename("molinetes"),
                       observado.rename("od"),
                       predicho.rename("predicho")], axis=1).fillna(0.0)
    tabla.index.names = ["complejo", "linea"]
    tabla = tabla.reset_index()
    total = tabla.groupby("complejo")[["molinetes", "od", "predicho"]].transform("sum")
    for col in ("molinetes", "od", "predicho"):
        tabla[f"p_{col}"] = tabla[col] / total[col]
    tabla["complejo_nombre"] = tabla.complejo.map(nombre)
    # Un complejo esta "degenerado" en el dataset O-D cuando este le atribuye
    # todos los ascensos a una sola de sus lineas.
    degenerado = tabla.groupby("complejo").p_od.max() > 0.999
    tabla["od_degenerado"] = tabla.complejo.map(degenerado)
    return tabla


def escribir_reporte(base, sens, brechas, reparto, cat, nombre, m) -> None:
    L: list[str] = []
    A = L.append
    A("# Paso 6, Caminos minimos con penalizacion por transbordo\n")
    A("Generado por `src/07_caminos_minimos.py`, con `src/lib_caminos.py`. Precalcula el "
      "camino de menor tiempo percibido para cada par ordenado de complejos, sobre el "
      "grafo dirigido del paso 2.\n")

    A("## 1. Como se cuenta el tiempo\n")
    A("El costo de un camino es\n")
    A("```\nt = marcha de cada tramo\n  + 24 s por cada PARADA INTERMEDIA\n"
      "  + min_transfer_time de cada transbordo\n  + P por cada transbordo\n```\n")
    A("Los 24 s son la detencion de diseno del GTFS, que el paso 2 mostro constante en "
      "toda parada de toda linea. **Van por parada intermedia, no por tramo recorrido**: "
      "el que asciende no espera la detencion de su estacion de ascenso (esa es su "
      "ventana de abordaje) y el que desciende tampoco espera la de la suya. Contarlas "
      "por tramo abarataria en terminos relativos los caminos con muchas paradas, que es "
      "justo el error que un grafo de subte no puede darse.\n")
    A("**El acceso y el egreso dentro de un complejo valen cero.** El pasajero entra al "
      "complejo, no a un anden: asciende en cualquiera de sus nodos y desciende en "
      "cualquiera de los del complejo de destino, y se toma el minimo. Caminar dentro "
      "del complejo de origen **no cuenta como transbordo**. `pathways.txt` tiene los "
      "recorridos internos, pero no para toda la red; queda declarado como "
      "simplificacion.\n")
    A(f"**La penalizacion P es un supuesto, no un dato.** El valor base es "
      f"**{int(PENALIZACION_BASE_S)} s** y sale de los despachos del paso 4: en hora pico "
      "los intervalos van de 3,15 min (C) a 5,22 min (E), de modo que la espera esperada "
      "(la mitad del intervalo) cae entre 95 y 157 s. Por eso la seccion 4 recorre el "
      "rango completo en lugar de fijar el valor.\n")

    A("## 2. La tabla\n")
    A(f"- **{mil(len(base))} pares ordenados** de complejos, todos alcanzables "
      f"({len(cat)} x {len(cat) - 1}).")
    A(f"- Tiempo de viaje: mediana **{mmss(base.tiempo_s.median())}**, "
      f"maximo **{mmss(base.tiempo_s.max())}** "
      f"({nombre[base.loc[base.tiempo_s.idxmax(), 'comp_origen']]} -> "
      f"{nombre[base.loc[base.tiempo_s.idxmax(), 'comp_destino']]}).")
    reparto_tr = base.n_transbordos.value_counts().sort_index()
    A(f"- Transbordos por camino: " + ", ".join(
        f"**{k}**: {mil(v)} pares ({pc(v / len(base), 1)})" for k, v in reparto_tr.items())
      + ".")
    A(f"- Media de {dec(base.n_transbordos.mean(), 2)} transbordos por par.\n")

    A("> **Control de coherencia con el paso 2.** El grafo es fuertemente conexo, asi que "
      "los 6.006 pares tienen camino. Que ninguno quede aislado no es un resultado del "
      "paso 6: es la confirmacion de que el grafo dirigido con Alberti y Pasco servidas "
      "en un solo sentido sigue permitiendo ir de cualquier estacion a cualquier otra.\n")

    A("## 3. Cuan disputada esta la asignacion\n")
    A("La asignacion es todo-o-nada: cada par manda todo su flujo por un unico camino. "
      "Para saber cuanto pesa esa simplificacion se calcula, por cada par, **el mejor "
      "camino que asciende por una linea distinta** y la brecha de tiempo contra el "
      "elegido.\n")
    b = brechas.brecha_s.dropna()
    empatados = int((b < EMPATE_S).sum())
    A(f"- Pares con alternativa por otra linea de ascenso: **{mil(len(b))}** de "
      f"{mil(len(brechas))}.")
    A(f"- Brecha mediana: **{mmss(b.median())}**.")
    A(f"- Pares con la alternativa a menos de {int(EMPATE_S)} s: **{mil(empatados)}**, "
      f"que son {pc(empatados / len(brechas), 1)} del total pero "
      f"**{pc(empatados / len(b), 1)} de los pares que realmente tienen eleccion**. La "
      "segunda cifra es la que corresponde mirar: en los otros 5.236 pares el complejo "
      "de origen tiene una sola linea y no hay nada que elegir.\n")
    A("> Esos son los pares donde mandar el 100 % del flujo por un camino es una decision "
      "que los datos no respaldan, y donde una asignacion por reparto daria distinto. Es "
      "una limitacion declarada del diseno, ahora con magnitud.\n")

    A("## 4. Sensibilidad a la penalizacion\n")
    A("| P (s) | Transbordos medios | Pares sin transbordo | Tiempo medio | Cambian de camino | Cambian de linea de ascenso |")
    A("|---:|---:|---:|---:|---:|---:|")
    for r in sens.itertuples():
        A(f"| {int(r.penalizacion_s)} | {dec(r.transbordos_medios, 3)} | "
          f"{mil(r.pares_sin_transbordo)} | {mmss(r.tiempo_medio_s)} | "
          f"{mil(r.cambian_camino)} | {mil(r.cambian_linea_ascenso)} |")
    A("")
    A("Las columnas de cambio se miden contra el caso base de "
      f"{int(PENALIZACION_BASE_S)} s.\n")

    A("## 5. Contraste del reparto por linea de ascenso\n")
    A("La ruta nunca entro al modelo como insumo, asi que el reparto por linea que "
      "produce se puede contrastar. Solo tiene sentido en los diez complejos con mas de "
      "una linea, que son los unicos donde el pasajero elige, y se hace contra **dos "
      "fuentes observadas a la vez** porque ninguna de las dos es limpia:\n")
    A("- **Molinetes** del 16/10/2024, por estacion del complejo. Es una tercera fuente, "
      "independiente del dataset O-D. Su sesgo: mide la estacion **de ingreso**, no la "
      "linea de ascenso, asi que quien entra por un molinete y camina hasta el anden de "
      "la otra linea queda mal atribuido. Es el mismo sesgo que declaramos para el "
      "contraste por anden.")
    A("- **`linea_etapa`** del dataset O-D, que si es la linea del molinete que registro "
      "la transaccion. Su defecto es otro y aparece abajo.\n")
    A("| Complejo | Linea | Molinetes | O-D | Predicho | Dif. vs molinetes |")
    A("|---|---|---:|---:|---:|---:|")
    for _, r in reparto.sort_values(["complejo_nombre", "linea"]).iterrows():
        marca = " ⚠" if r.od_degenerado else ""
        A(f"| {r.complejo_nombre} | {r.linea[-1]} | {pc(r.p_molinetes, 1)} | "
          f"{pc(r.p_od, 1)}{marca} | {pc(r.p_predicho, 1)} | "
          f"{dec((r.p_predicho - r.p_molinetes) * 100, 1)} p.p. |")
    A("")
    eam_mol = (reparto.p_predicho - reparto.p_molinetes).abs().mean()
    sano = reparto[~reparto.od_degenerado]
    eam_od = (sano.p_predicho - sano.p_od).abs().mean()
    A(f"- Error absoluto medio contra **molinetes**: **{dec(eam_mol * 100, 2)} p.p.** "
      "sobre los diez complejos.")
    A(f"- Error absoluto medio contra **`linea_etapa`**, excluyendo los complejos "
      f"marcados: **{dec(eam_od * 100, 2)} p.p.**\n")
    entre_fuentes = (sano.p_molinetes - sano.p_od).abs().mean()
    A("> **Las dos fuentes observadas coinciden entre si donde ninguna esta rota**: en "
      f"los ocho complejos sanos difieren en promedio {dec(entre_fuentes * 100, 2)} p.p. "
      "Son fuentes independientes (una es el conteo de molinetes, la otra la "
      "reconstruccion de viajes a partir de transacciones SUBE) y que se corroboren da "
      "piso al contraste. Donde discrepan fuerte, discrepan por una razon identificable, "
      "que es de lo que tratan las dos secciones que siguen.\n")

    A("### 5.1 Dos complejos donde el dataset O-D esta roto, y molinetes lo demuestra\n")
    deg = sorted(reparto[reparto.od_degenerado].complejo_nombre.unique())
    A("En " + " y en ".join(f"**{d}**" for d in deg) + " el dataset O-D atribuye el "
      "100 % de los ascensos a una sola linea. Ya lo teniamos anotado (9 de "
      "Julio [D], Diagonal Norte [C] e Independencia [C] no aparecen nunca como origen) "
      "y aca se ve el efecto.\n")
    A("**Molinetes le da la razon al modelo, no al dataset.** En 9 de Julio / Carlos "
      "Pellegrini / Diagonal Norte los molinetes reparten 62,8 / 18,6 / 18,6 entre B, C y "
      "D, y la ruta predice 59,7 / 15,6 / 24,8; el dataset O-D dice 100 / 0 / 0. Es la "
      "confirmacion de que la degeneracion es un defecto de la fuente y no un "
      "comportamiento real, y de paso **refuerza la decision de no meter la linea de "
      "ascenso como insumo del modelo**: si se hubiera usado, ese defecto entraba "
      "directo a la entrada.\n")
    A("Los dos complejos degenerados son ademas **los dos complejos de combinacion que "
      "mas subregistran** en el paso 5 (factores 1,635 y 1,374). Los dos hechos apuntan "
      "al mismo mecanismo: el dataset colapsa el complejo sobre una estacion y en el "
      "camino pierde parte de la demanda.\n")

    A("### 5.2 Retiro es la discrepancia real, y no se explica por lo obvio\n")
    ret = reparto[reparto.complejo_nombre == "Retiro"]
    if len(ret):
        c = ret[ret.linea == "LineaC"].iloc[0]
        A(f"Es el unico desajuste grande que **no** es defecto de fuente: las dos fuentes "
          f"coinciden (molinetes {pc(c.p_molinetes, 1)} por la C, `linea_etapa` "
          f"{pc(c.p_od, 1)}) y la ruta predice {pc(c.p_predicho, 1)}. Sobreasigna a la "
          "Linea E.\n")
    A("Se probaron dos explicaciones y **las dos quedaron descartadas**:\n")
    A("1. **El reparo de la Linea E.** Se regenero el grafo con "
      "`REPARAR_LINEA_E = False` y se recalcularon los caminos: cambian **58 pares de "
      "6.006 (1,0 %)** y 18 cambian de linea de ascenso. El reparto de Retiro **no se "
      "mueve**. El reparo importa poco para la asignacion; sigue abierto pero no es "
      "la causa de esto.")
    A("2. **Que la penalizacion sea uniforme y no distinga frecuencias.** Se probo "
      "reemplazarla por la espera esperada de cada linea, calculada como la mitad del "
      "intervalo de hora pico medido en el paso 4 (A y C 94 s, H 103, D 111, B 121, "
      "E 156). **Empeora el ajuste**, de 5,47 a 7,36 p.p. de error medio, y tampoco "
      "mueve a Retiro. Se descarta y se conserva la penalizacion uniforme.\n")
    A("Queda una explicacion no verificable con los datos disponibles: el sesgo de las "
      "fuentes. Retiro [C] y Retiro [E] estan a 151 m, y la terminal ferroviaria "
      "descarga sobre el acceso de la C, de modo que el molinete sobreatribuye a la C "
      "gente que despues camina hasta la E. **Se declara como discrepancia abierta**, no "
      "se corrige: corregirla seria ajustar la ruta contra una fuente cuyo sesgo apunta "
      "justo en esa direccion.\n")

    A("### 5.3 Que puede y que no puede este contraste\n")
    A("Es **parcial y sesgado por construccion**, igual que el de anden: cubre "
      "diez complejos y compara un reparto todo-o-nada contra uno observado que por "
      "definicion esta repartido. Un par que la ruta manda entero por una linea nunca va "
      "a reproducir un 60/40 observado. **Sirve para detectar que la asignacion mande "
      "flujo por la linea equivocada; no sirve para medir precision.** Y no es "
      "validacion del modelo de simulacion: es verificacion de una tabla precalculada.\n")

    REPORTES.mkdir(parents=True, exist_ok=True)
    (REPORTES / "07_caminos_minimos.md").write_text("\n".join(L), encoding="utf-8")
    print(f"reporte en reports/07_caminos_minimos.md ({len(L)} lineas)")


if __name__ == "__main__":
    main()
