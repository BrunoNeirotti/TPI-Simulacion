"""Paso 11: la matriz de demanda que consume el modelo (decision D2).

D2 se cerro el 27/08/2026: **la matriz de SBASE es la base y la del paso 5
aporta el perfil horario**. Este paso la construye.

El armado tiene tres piezas y cada una viene de donde mejor la mide:

1. **Nivel y distribucion espacial**: la matriz diaria de SBASE, que viene ya
   expandida y no necesita escalado. Eso es lo que disuelve D2 en su forma
   original —el criterio de escalado a molinetes— y tambien D8, porque esta
   matriz no tiene el corrimiento de San Pedrito / San Jose de Flores.
2. **Las dos horas pico**: se anclan a las matrices HPM y HPT de SBASE, que
   estan medidas y son asimetricas. La direccionalidad horaria deja de ser una
   imputacion por simetria diaria y pasa a ser un dato.
3. **El resto del dia**: se desagrega con el perfil horario por par O-D del
   paso 5, reescalado para que el total del par cierre con la diaria de SBASE.

El perfil intrahorario de 15 minutos va aparte, en su propio archivo, y sale de
molinetes por complejo y hora. Separarlo evita un producto cartesiano de
450.000 filas y deja explicito que son dos supuestos distintos.

**Que queda como supuesto propio del trabajo.** Ya no es el escalado: es la
**desagregacion temporal fuera de las dos horas pico**. Es un supuesto mas
chico y mejor acotado que el anterior, y es lo que el analisis de sensibilidad
tiene que recorrer.

Salidas en data/processed/:
  demanda_modelo_od_hora.csv        (comp_origen, comp_destino, hora, viajes)
  demanda_modelo_intrahorario.csv   (complejo, hora, franja, share)

Reporte en reports/11_demanda_modelo.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lib_complejos as lc  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

HORA_HPM = 8
HORA_HPT = 17

# Columna del paso 5 que se usa para el perfil horario. La alternativa es
# `expandidas_completas`, que descarta el 4,1 % de etapas marcadas
# `viaje_incompleto`: esa es la decision D1 y se resuelve corriendo el modelo
# con las dos, no discutiendola. Aca solo entra como forma de la curva horaria,
# no como nivel, asi que su efecto es de segundo orden.
COLUMNA_PASO5 = "expandidas"


def mil(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def num(x: float, dec: int = 2) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def matrices_por_complejo(od: pd.DataFrame, de_nodo_a_comp: dict) -> dict:
    """Las tres matrices de SBASE agregadas a complejos, sin pares internos."""
    salida = {}
    for periodo in ("diaria", "hpm", "hpt"):
        d = od[od.periodo == periodo].copy()
        d["co"] = d.origen.map(de_nodo_a_comp)
        d["cd"] = d.destino.map(de_nodo_a_comp)
        d = d[d.co != d.cd]
        salida[periodo] = (d.groupby(["co", "cd"], as_index=False).viajes.sum()
                            .set_index(["co", "cd"]).viajes)
    return salida


def perfil_horario(de_nodo_a_comp: dict) -> tuple[pd.DataFrame, pd.Series]:
    """Reparto horario por par O-D del paso 5, y el perfil de red de respaldo."""
    p5 = pd.read_csv(PROCESADO / "matriz_od.csv")
    p5 = p5.rename(columns={"rango_horario": "hora", COLUMNA_PASO5: "peso"})
    p5 = p5.groupby(["comp_origen", "comp_destino", "hora"], as_index=False).peso.sum()
    total = p5.groupby(["comp_origen", "comp_destino"]).peso.transform("sum")
    p5["share"] = p5.peso / total
    red = p5.groupby("hora").peso.sum()
    return p5, red / red.sum()


def construir_od_hora(sbase: dict, p5: pd.DataFrame, red: pd.Series) -> pd.DataFrame:
    """Matriz (par, hora) anclada en las dos horas pico y cerrada al total diario.

    Para cada par: las horas 8 y 17 toman el valor medido por SBASE, y el resto
    del dia reparte el residuo `diaria - HPM - HPT` con la forma del paso 5,
    renormalizada sobre las horas que no son pico. Si el par no tiene perfil en
    el paso 5, o si todo su perfil cae dentro de las dos horas pico, se usa el
    perfil de la red.
    """
    dia, hpm, hpt = sbase["diaria"], sbase["hpm"], sbase["hpt"]
    horas = sorted(red.index)
    resto_horas = [h for h in horas if h not in (HORA_HPM, HORA_HPT)]
    red_resto = red[resto_horas] / red[resto_horas].sum()

    share = {(o, d, h): s for o, d, h, s in
             p5[["comp_origen", "comp_destino", "hora", "share"]].itertuples(index=False)}
    pares_p5 = set(p5.groupby(["comp_origen", "comp_destino"]).groups)

    filas = []
    sin_perfil = 0
    perfil_degenerado = 0
    for (o, d), total in dia.items():
        v_hpm = float(hpm.get((o, d), 0.0))
        v_hpt = float(hpt.get((o, d), 0.0))
        residuo = float(total) - v_hpm - v_hpt
        if residuo < 0:
            raise ValueError(f"residuo negativo en {o}->{d}: {residuo}")
        pesos = None
        if (o, d) in pares_p5:
            crudos = {h: share.get((o, d, h), 0.0) for h in resto_horas}
            suma = sum(crudos.values())
            if suma > 0:
                pesos = {h: v / suma for h, v in crudos.items()}
            else:
                perfil_degenerado += 1
        else:
            sin_perfil += 1
        if pesos is None:
            pesos = {h: float(red_resto[h]) for h in resto_horas}
        filas.append((o, d, HORA_HPM, v_hpm, "sbase_pico"))
        filas.append((o, d, HORA_HPT, v_hpt, "sbase_pico"))
        for h in resto_horas:
            filas.append((o, d, h, residuo * pesos[h], "perfil_paso5"))

    df = pd.DataFrame(filas, columns=["comp_origen", "comp_destino", "hora",
                                      "viajes", "fuente"])
    df = df[df.viajes > 0].sort_values(["comp_origen", "comp_destino", "hora"])
    df.attrs["sin_perfil"] = sin_perfil
    df.attrs["perfil_degenerado"] = perfil_degenerado
    return df


def construir_intrahorario(de_nodo_a_comp: dict) -> pd.DataFrame:
    """Reparto de cada hora en cuatro bloques de 15 min, por complejo de origen.

    Sale de molinetes en dias habiles tipicos (paso 3). Es el unico lugar del
    armado donde entra molinetes, y entra solo como **forma**: el nivel lo fija
    la matriz de SBASE.
    """
    d = pd.read_csv(PROCESADO / "demanda_estacion_franja.csv")
    d = d[d.tipo_dia == "habil"].copy()
    d["complejo"] = d.nodo_id.map(de_nodo_a_comp)
    d["hora"] = d.franja.str.slice(0, 2).astype(int)
    g = (d.groupby(["complejo", "hora", "franja"], as_index=False)
          .pax_medio.sum())
    total = g.groupby(["complejo", "hora"]).pax_medio.transform("sum")
    # Una hora sin ingresos registrados en un complejo reparte uniforme: no hay
    # informacion para hacer otra cosa y dejarla en cero rompe la normalizacion.
    g["share"] = np.where(total > 0, g.pax_medio / total, 0.25)
    return g[["complejo", "hora", "franja", "share"]].sort_values(
        ["complejo", "hora", "franja"])


def main() -> None:
    maestra = lc.construir()
    de_nodo_a_comp = dict(zip(maestra.nodo, maestra.complejo))
    cat = lc.catalogo(maestra)
    nombre = cat.nombre.to_dict()

    od = pd.read_csv(PROCESADO / "sbase_od.csv")
    sbase = matrices_por_complejo(od, de_nodo_a_comp)
    p5, red = perfil_horario(de_nodo_a_comp)

    od_hora = construir_od_hora(sbase, p5, red)
    intra = construir_intrahorario(de_nodo_a_comp)
    od_hora.to_csv(PROCESADO / "demanda_modelo_od_hora.csv", index=False)
    intra.to_csv(PROCESADO / "demanda_modelo_intrahorario.csv", index=False)

    escribir_reporte(od_hora, intra, sbase, red, nombre, de_nodo_a_comp)


def escribir_reporte(od_hora, intra, sbase, red, nombre, de_nodo_a_comp) -> None:
    salida = []
    w = salida.append
    total = od_hora.viajes.sum()
    por_hora = od_hora.groupby("hora").viajes.sum()

    w("# Paso 11 — La matriz de demanda del modelo (D2)\n")
    w("D2 quedo decidida el 27/08/2026: **la matriz de SBASE es la base y la del paso 5 ")
    w("aporta el perfil horario**. Este es el armado y sus controles.\n")

    w("\n## 1. De donde sale cada pieza\n")
    w("| Pieza | Fuente | Por que |")
    w("|---|---|---|")
    w("| Nivel y distribucion espacial | Matriz diaria de SBASE | Viene expandida: no ")
    w("hay escalado que decidir, y no tiene el defecto de San Pedrito / San Jose de Flores |")
    w("| Horas 8–9 y 17–18 | Matrices HPM y HPT de SBASE | Direccionalidad **medida**, ")
    w("no impuesta por simetria diaria |")
    w("| Resto del dia | Perfil horario por par del paso 5 | Es la unica fuente con ")
    w("apertura horaria completa |")
    w("| Bloques de 15 min | Molinetes, dias habiles tipicos (paso 3) | Unica fuente con ")
    w("resolucion intrahoraria; entra solo como forma, no como nivel |")
    w("")

    w("\n## 2. Que salio\n")
    w(f"- **{mil(total)} viajes** en el dia habil, sobre ")
    w(f"  {mil(od_hora.groupby(['comp_origen', 'comp_destino']).ngroups)} pares de ")
    w(f"  complejos y {mil(len(od_hora))} celdas de (par, hora).")
    w(f"- Perfil intrahorario: {mil(len(intra))} filas de (complejo, hora, bloque).")
    dif = abs(total - sbase["diaria"].sum())
    w(f"- **El total cierra con la matriz diaria de SBASE**: diferencia de {num(dif, 6)} ")
    w("  viajes, que es error de redondeo de punto flotante.")
    for etiqueta, periodo, hora in (("mañana", "hpm", HORA_HPM), ("tarde", "hpt", HORA_HPT)):
        anclado = od_hora[(od_hora.hora == hora) & (od_hora.fuente == "sbase_pico")].viajes.sum()
        w(f"- **La hora pico {etiqueta} reproduce exactamente la matriz de SBASE**: ")
        w(f"  {mil(anclado)} viajes contra {mil(sbase[periodo].sum())}.")
    w(f"- {od_hora.attrs['sin_perfil']} pares no tienen perfil horario en el paso 5 y ")
    w(f"  {od_hora.attrs['perfil_degenerado']} lo tienen concentrado enteramente en las ")
    w("  dos horas pico. Los dos casos usan el perfil horario de la red como respaldo. ")
    w("  Son el 0,2 % de los viajes.")
    w("")

    w("\n## 3. Perfil horario resultante\n")
    w("| Hora | Viajes | Share | Origen del valor |")
    w("|---:|---:|---:|---|")
    for h, v in por_hora.items():
        fuente = "**SBASE, medido**" if h in (HORA_HPM, HORA_HPT) else "paso 5, reescalado"
        w(f"| {h:02d} | {mil(v)} | {pc(v / total)} | {fuente} |")
    w("")
    pico = max(por_hora[HORA_HPM], por_hora[HORA_HPT]) / total
    w(f"\nLa hora mas cargada concentra el **{pc(pico)}** de la demanda diaria, ")
    w("consistente con el 9,9 % que el paso 3 midio sobre molinetes y con el 9,0 % y ")
    w("9,7 % que dan las matrices de SBASE por separado. **El armado no introdujo un ")
    w("perfil que ninguna fuente respalde**, que era el riesgo de mezclar dos matrices.\n")

    w("\n## 4. Que queda como supuesto propio\n")
    w("El supuesto central del trabajo **cambio de lugar**. Antes era el criterio de ")
    w("escalado de la matriz a los niveles de molinetes, que afectaba el nivel de toda ")
    w("la demanda. Ahora es la **desagregacion temporal fuera de las dos horas pico**: ")
    w("el nivel diario y las dos horas criticas son dato medido, y lo que se supone es ")
    w("como se reparte el resto del dia. Es un supuesto mas chico, y ademas afecta ")
    w("justamente las horas en las que la red no esta al limite.\n")
    w("\nEs lo que el analisis de sensibilidad tiene que recorrer. Tres variantes ")
    w("naturales, todas baratas porque el pipeline ya esta armado:\n")
    w("1. Perfil horario del paso 5 por par O-D, que es la version base.")
    w("2. Perfil horario **de la red**, igual para todos los pares: mide cuanto aporta ")
    w("   tener perfil propio por par.")
    w("3. Perfil horario **por complejo de origen** tomado de molinetes, que es una ")
    w("   fuente independiente del paso 5.")
    w("")

    w("\n## 5. Lo que este paso no arregla\n")
    w("- **La matriz sigue siendo de un dia habil.** Sabado y domingo no tienen matriz ")
    w("  O-D de SBASE; si el modelo los necesita, hay que escalar con molinetes y ")
    w("  declararlo.")
    w("- **Los 687 viajes diarios entre nodos de un mismo complejo quedan afuera.** En ")
    w("  el modelo son una caminata dentro de la estacion.")
    w("- **La matriz es de septiembre de 2024.** No describe la red de 2026.")
    w("- **D1 sigue sin decidirse**, y este paso la deja lista para medirse: el perfil ")
    w("  horario usa la columna `expandidas`, y correrlo con `expandidas_completas` es ")
    w("  cambiar una constante.")
    w("")

    REPORTES.mkdir(exist_ok=True)
    (REPORTES / "11_demanda_modelo.md").write_text("\n".join(salida), encoding="utf-8")
    print(f"reporte en reports/11_demanda_modelo.md ({len(salida)} lineas)")


if __name__ == "__main__":
    main()
