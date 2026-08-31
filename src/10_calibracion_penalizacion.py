"""Paso 10: calibracion de la penalizacion por transbordo (decision D9).

Hasta que llegaron los perfiles de carga de SBASE, la penalizacion por
transbordo era un supuesto sin nada contra que medirse: el valor base de 120 s
salia de que la espera esperada en hora pico cae entre 95 y 157 s, y ahi
terminaba el argumento. Ahora hay un observado por tramo, asi que el valor se
puede elegir midiendo.

**Criterio, fijado antes de correr nada para que no sea a medida del
resultado:**

- Se recorre la penalizacion de 0 a 300 s de a 10 s.
- Para cada valor se recalculan los caminos minimos de complejo a complejo, se
  carga sobre el grafo la matriz de **hora pico manana** de SBASE con asignacion
  todo-o-nada y se mide el error absoluto ponderado (WAPE) de la carga por tramo
  contra el perfil observado.
- **Se calibra con la manana y se valida con la tarde.** La hora pico tarde no
  participa de la eleccion: es la muestra de reserva. Sin esa particion el
  contraste del paso 9 dejaria de ser validacion y pasaria a ser verificacion
  circular, que es exactamente lo que ya paso con los intervalos de despacho en
  el paso 4.
- El reparto por linea de ascenso y la tasa de transbordo se informan como
  control, no entran en el criterio.

El resultado esta en `reports/10_calibracion_penalizacion.md`, y es que **el
observado no identifica el parametro** por encima de 30 s. Ver la constante
PENALIZACION_ELEGIDA_S.

Salidas en data/processed/:
  calibracion_penalizacion.csv   una fila por penalizacion, con todas las metricas

Reporte en reports/10_calibracion_penalizacion.md.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lib_complejos as lc  # noqa: E402

p07 = importlib.import_module("07_caminos_minimos")
p09 = importlib.import_module("09_sbase_od_carga")

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

PENALIZACIONES_S = list(range(0, 301, 10))

# Valor que se conserva despues de correr el barrido, y por que no es el minimo
# de la curva. El criterio pre-registrado —minimizar el WAPE de la hora pico
# manana— apunta a 30 s, pero por 0,26 pp sobre una curva que entre 30 y 300 s
# es plana, mientras que la muestra de reserva apunta a 270 s y el control de
# reparto por linea empeora casi dos puntos en 30 s. Cuando dos muestras del
# mismo fenomeno apuntan a extremos opuestos de un rango plano, lo que el dato
# dice es que **no identifica el parametro**, no que el optimo sea el argmin de
# una de las dos. Lo que si identifica es una **cota inferior dura**: por debajo
# de 30 s el modelo se rompe. Dentro de la zona plana decide el argumento
# fisico del paso 6 —la espera esperada es la mitad del intervalo, entre 95 y
# 157 s en hora pico— y 120 s cae ahi.
PENALIZACION_ELEGIDA_S = 120.0

# Nodo Retiro de la Linea C, que es la discrepancia declarada del paso 6.
NODO_RETIRO_C = "LineaC:1102"


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def num(x: float, dec: int = 2) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def wape(obs: pd.Series, pre: pd.Series) -> float:
    return float((pre - obs).abs().sum() / obs.sum())


def main() -> None:
    maestra = lc.construir()
    de_nodo_a_comp = dict(zip(maestra.nodo, maestra.complejo))

    aristas = pd.read_csv(PROCESADO / "grafo_aristas.csv")
    nodos = pd.read_csv(PROCESADO / "grafo_nodos.csv")
    linea_de = dict(zip(nodos.nodo_id, nodos.linea))
    nodos_de: dict[str, list[str]] = {}
    for nodo, comp in de_nodo_a_comp.items():
        nodos_de.setdefault(comp, []).append(nodo)
    nodos_de = {c: sorted(v) for c, v in nodos_de.items()}

    od = pd.read_csv(PROCESADO / "sbase_od.csv")
    perfil = pd.read_csv(PROCESADO / "sbase_perfil_carga.csv")
    dirmap = p09.sentido_a_direccion(aristas, perfil)
    con_arista = {(r.linea, r.direction_id, r.de_nodo)
                  for r in aristas[aristas.tipo == "tramo"].itertuples()}

    obs = {}
    for periodo in ("hpm", "hpt"):
        o = perfil[perfil.periodo == periodo.upper()].copy()
        o["direction_id"] = [dirmap[(r.linea, r.sentido_hacia)] for r in o.itertuples()]
        o = o[[(r.linea, r.direction_id, r.nodo) in con_arista for r in o.itertuples()]]
        obs[periodo] = o

    # Reparto por linea observado, para el control: ascensos de SBASE por nodo
    # dentro de cada complejo de mas de un nodo.
    asc = (od[od.periodo == "diaria"].groupby("origen", as_index=False).viajes.sum()
           .rename(columns={"origen": "nodo"}))
    asc["complejo"] = asc.nodo.map(de_nodo_a_comp)
    multi = asc.groupby("complejo").nodo.count()
    asc = asc[asc.complejo.isin(multi[multi > 1].index)].copy()
    asc["share_sbase"] = asc.viajes / asc.groupby("complejo").viajes.transform("sum")
    share_obs = dict(zip(asc.nodo, asc.share_sbase))

    dia = (od[od.periodo == "diaria"]
           .assign(co=lambda d: d.origen.map(de_nodo_a_comp),
                   cd=lambda d: d.destino.map(de_nodo_a_comp))
           .query("co != cd").groupby(["co", "cd"], as_index=False).viajes.sum())
    tot_origen = dia.groupby("co").viajes.sum()

    filas = []
    for p in PENALIZACIONES_S:
        cam = p07.resolver(float(p), aristas, nodos_de, linea_de)
        cam = cam[cam.alcanzable]
        fila: dict = {"penalizacion_s": p}
        for periodo in ("hpm", "hpt"):
            pred = p09.asignar(od[od.periodo == periodo], cam, aristas, de_nodo_a_comp)
            j = obs[periodo].merge(pred, on=["linea", "direction_id", "nodo"], how="left")
            j["carga_predicha"] = j.carga_predicha.fillna(0.0)
            fila[f"wape_{periodo}"] = wape(j.carga_saliente, j.carga_predicha)
            fila[f"corr_{periodo}"] = float(np.corrcoef(j.carga_saliente,
                                                        j.carga_predicha)[0, 1])
            fila[f"sesgo_{periodo}"] = float(j.carga_predicha.sum()
                                             / j.carga_saliente.sum() - 1)
        j = dia.merge(cam[["comp_origen", "comp_destino", "nodo_ascenso",
                           "n_transbordos"]],
                      left_on=["co", "cd"], right_on=["comp_origen", "comp_destino"])
        rep = j.groupby(["co", "nodo_ascenso"], as_index=False).viajes.sum()
        rep = rep[rep.nodo_ascenso.isin(share_obs)].copy()
        rep["share"] = rep.viajes / rep.co.map(tot_origen)
        rep["obs"] = rep.nodo_ascenso.map(share_obs)
        fila["err_reparto_medio"] = float((rep.share - rep.obs).abs().mean())
        fila["err_reparto_max"] = float((rep.share - rep.obs).abs().max())
        ret = rep[rep.nodo_ascenso == NODO_RETIRO_C]
        fila["retiro_c"] = float(ret.share.iloc[0]) if len(ret) else float("nan")
        fila["transbordos_medios"] = float((j.n_transbordos * j.viajes).sum()
                                           / j.viajes.sum())
        filas.append(fila)
        print(f"P={p:>3} s  WAPE HPM {fila['wape_hpm']:.4f}  "
              f"HPT {fila['wape_hpt']:.4f}  Retiro C {fila['retiro_c']:.3f}")

    barrido = pd.DataFrame(filas)
    barrido.to_csv(PROCESADO / "calibracion_penalizacion.csv", index=False)

    argmin_hpm = int(barrido.loc[barrido.wape_hpm.idxmin(), "penalizacion_s"])
    argmin_hpt = int(barrido.loc[barrido.wape_hpt.idxmin(), "penalizacion_s"])
    escribir_reporte(barrido, int(PENALIZACION_ELEGIDA_S), argmin_hpm, argmin_hpt)


def escribir_reporte(barrido: pd.DataFrame, elegida: int, argmin_hpm: int,
                     argmin_hpt: int) -> None:
    salida = []
    w = salida.append
    f_e = barrido[barrido.penalizacion_s == elegida].iloc[0]
    f_hpm = barrido[barrido.penalizacion_s == argmin_hpm].iloc[0]
    f_hpt = barrido[barrido.penalizacion_s == argmin_hpt].iloc[0]
    f_0 = barrido[barrido.penalizacion_s == 0].iloc[0]
    meseta = barrido[barrido.penalizacion_s >= 30]

    w("# Paso 10 — Calibracion de la penalizacion por transbordo (D9)\n")
    w("El paso 6 fijo la penalizacion en **120 s** por un argumento indirecto: en hora ")
    w("pico los intervalos entre despachos van de 3,15 a 5,22 min, asi que la espera ")
    w("esperada —la mitad del intervalo— cae entre 95 y 157 s. Era un supuesto sin nada ")
    w("contra que medirse. Los perfiles de carga que entrego SBASE (paso 9) dan por ")
    w("primera vez un observado por tramo, y con eso el valor se puede elegir midiendo.\n")

    w("\n## 1. Criterio, fijado antes de correr\n")
    w("- Penalizacion recorrida de 0 a 300 s de a 10 s.")
    w("- Metrica: error absoluto ponderado (WAPE) de la carga por tramo, con la matriz ")
    w("  de **hora pico manana** de SBASE cargada sobre el grafo por asignacion ")
    w("  todo-o-nada.")
    w("- **Se calibra con la manana y se valida con la tarde.** La hora pico tarde no ")
    w("  participa de la eleccion: es la muestra de reserva. Sin esa particion el ")
    w("  contraste del paso 9 dejaria de ser validacion y pasaria a ser verificacion ")
    w("  circular, que es el mismo problema que ya obligo a reclasificar el contraste de ")
    w("  intervalos en el paso 4.")
    w("- El reparto por linea de ascenso y la tasa de transbordo se informan como ")
    w("  control y **no entran en el criterio**.")
    w("")

    w("\n## 2. La curva\n")
    w("| Penalizacion | WAPE HPM (calibracion) | WAPE HPT (reserva) | Error medio de reparto | Transbordos medios | Retiro por la C |")
    w("|---:|---:|---:|---:|---:|---:|")
    for r in barrido.itertuples():
        marcas = []
        if int(r.penalizacion_s) == elegida:
            marcas.append("**elegida**")
        if int(r.penalizacion_s) == argmin_hpm:
            marcas.append("min HPM")
        if int(r.penalizacion_s) == argmin_hpt:
            marcas.append("min HPT")
        m = (" " + ", ".join(marcas)) if marcas else ""
        w(f"| {int(r.penalizacion_s)} s{m} | {pc(r.wape_hpm, 2)} | {pc(r.wape_hpt, 2)} "
          f"| {pc(r.err_reparto_medio, 2)} | {num(r.transbordos_medios, 3)} "
          f"| {pc(r.retiro_c)} |")
    w("")

    w("\n## 3. El dato no identifica el parametro\n")
    w(f"El criterio pre-registrado apunta a **{argmin_hpm} s**, con un WAPE de ")
    w(f"{pc(f_hpm.wape_hpm, 2)} en la hora pico manana. Hay tres razones para no tomarlo, ")
    w("y las tres salen de la misma tabla:\n")
    w("1. **La curva es plana.** Entre 30 y 300 s el WAPE de calibracion se mueve entre ")
    w(f"   {pc(meseta.wape_hpm.min(), 2)} y {pc(meseta.wape_hpm.max(), 2)}: una amplitud ")
    w(f"   de {num((meseta.wape_hpm.max() - meseta.wape_hpm.min()) * 100, 2)} puntos ")
    w("   porcentuales sobre un error del orden del 6,5 %. Todo ese rango es ")
    w("   indistinguible.")
    w(f"2. **Las dos muestras apuntan a extremos opuestos.** La calibracion elige ")
    w(f"   {argmin_hpm} s y la reserva elige {argmin_hpt} s ({pc(f_hpt.wape_hpt, 2)}). ")
    w("   Cuando dos muestras del mismo fenomeno se van a los dos extremos de un rango ")
    w("   plano, lo que dicen es que **no identifican el parametro**, no que el optimo ")
    w("   sea el minimo de una de las dos.")
    w(f"3. **El control independiente empeora en el minimo.** En {argmin_hpm} s el error ")
    w(f"   medio de reparto por linea es {pc(f_hpm.err_reparto_medio, 2)} contra ")
    w(f"   {pc(f_e.err_reparto_medio, 2)} en {elegida} s. Tomar el argmin mejoraria ")
    w("   0,26 pp la muestra de calibracion empeorando casi dos puntos un control que no ")
    w("   participa del ajuste. Eso es sobreajuste, no calibracion.")
    w("")

    w("\n### Lo que el dato si dice: una cota inferior dura\n")
    w("Por debajo de 30 s el modelo se rompe. Con penalizacion cero el WAPE salta a ")
    w(f"{pc(f_0.wape_hpm, 2)} y el reparto del complejo Retiro por la Linea C cae a ")
    w(f"{pc(f_0.retiro_c)} contra el 86,0 % observado: sin costo de transbordo la ")
    w("asignacion manda gente a combinar por caminos que nadie usa. **El salto entre 20 ")
    w("y 30 s es el unico rasgo nitido de toda la curva.**\n")

    w("\n## 4. Decision\n")
    w(f"**Se conserva la penalizacion de {elegida} s**, ahora con fundamento en vez de ")
    w("por defecto:\n")
    w("- cae dentro de la zona plana, donde el observado no discrimina;")
    w("- esta muy por encima de la cota inferior de 30 s, que es lo unico que el dato fija;")
    w("- coincide con el argumento fisico del paso 6, que es la mitad del intervalo ")
    w("  medido en hora pico (95–157 s), y ese argumento es el que corresponde usar ")
    w("  cuando el ajuste no discrimina.")
    w("")
    w(f"Rinde {pc(f_e.wape_hpm, 2)} de WAPE en calibracion y {pc(f_e.wape_hpt, 2)} fuera ")
    w("de muestra. **No se reescribe `caminos_minimos.csv`**: la tabla del paso 6 ya ")
    w("estaba calculada con este valor y queda vigente tal cual.\n")
    w("\n**Lo que cambia no es el numero sino su estatus.** Deja de ser un supuesto ")
    w("declarado y pasa a ser un parametro cuyo rango admisible se midio, con la ")
    w("salvedad —que hay que escribir en el informe— de que **el indicador central es ")
    w("poco sensible a el**. Eso es un resultado, no una limitacion: significa que la ")
    w("carga por tramo que produzca el modelo no depende de la parte mas discutible de ")
    w("la asignacion.\n")

    w("\n## 5. Retiro no se arregla con esto\n")
    w("El reparto de ascensos del complejo Retiro por la Linea C va de ")
    w(f"{pc(barrido.retiro_c.min())} a {pc(barrido.retiro_c.max())} en todo el rango ")
    w("recorrido, contra **86,0 % que mide SBASE**, 85,5 % de molinetes y 83,9 % de ")
    w("`linea_etapa`. **Ninguna penalizacion llega al valor observado**, asi que la ")
    w("discrepancia no es del valor del parametro.\n")
    w("\n(El 65,7 % de esta tabla no contradice el 69,8 % del paso 6: aquel reparto se ")
    w("pondera con la matriz del paso 5 y este con la de SBASE. La conclusion es la ")
    w("misma con las dos.)\n")
    w("\nQueda declarada como **error residual del modelo**, no como discrepancia entre ")
    w("fuentes ni como consecuencia de un supuesto mal elegido. La explicacion mas ")
    w("probable sigue siendo geometrica: Retiro [C] y Retiro [E] estan a 151 m y el ")
    w("grafo trata ese transbordo como cualquier otro. **No se corrige a mano**: ajustar ")
    w("el costo de ese transbordo hasta reproducir el 86 % seria calibrar un parametro ")
    w("contra el mismo dato que despues se usa para validar.\n")

    w("\n## 6. Que queda declarado\n")
    w("- La penalizacion **ya no es un supuesto ciego**: se midio su rango admisible con ")
    w("  criterio fijado de antemano y con muestra de reserva.")
    w("- **El dato no la identifica** por encima de 30 s. Se informa el rango, no un ")
    w("  valor finamente determinado.")
    w("- **El contraste de carga en hora pico manana pasa a ser calibracion**, no ")
    w("  validacion. La validacion es la hora pico tarde.")
    w("- **Retiro sigue mal** y queda como limitacion del modelo.")
    w("")

    REPORTES.mkdir(exist_ok=True)
    (REPORTES / "10_calibracion_penalizacion.md").write_text("\n".join(salida),
                                                             encoding="utf-8")
    print(f"\nreporte en reports/10_calibracion_penalizacion.md ({len(salida)} lineas)")


if __name__ == "__main__":
    main()
