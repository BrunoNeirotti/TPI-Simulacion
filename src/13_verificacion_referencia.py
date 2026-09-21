# -*- coding: utf-8 -*-
"""Paso 13: verificacion del modelo base con el simulador de referencia.

El simulador de referencia (`anylogic/biblioteca/referencia/`) corre en Java
plano la misma logica que `anylogic/modelo/GUIA_CONSTRUCCION.md`, con la misma
biblioteca. Este script lee sus salidas y las contrasta:

1. **Consistencia interna**: conservacion de pasajeros, pools, formaciones.
2. **Contra la asignacion estatica del paso 6** (`carga_predicha` de
   `sbase_contraste_carga.csv`): con la misma matriz y las mismas rutas, la
   carga dinamica por tramo tiene que parecerse a la estatica. Si no, hay un
   error de logica.
3. **Contra SBASE**: carga por tramo en hora pico manana (calibracion, D9) y
   tarde (validacion), y ascensos por viaje.

Antes de correrlo hay que generar las salidas del simulador:

    cd anylogic/biblioteca && ./referencia/correr.sh

Salida: reports/13_verificacion_referencia.md
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

POOL_DISENO = 25_000
PERIODOS = {"HPM": 8, "HPT": 17}
TASA_SBASE = {"HPM": 1.371, "HPT": 1.426}      # reports/09_sbase_od_carga.md, seccion 7
TASA_ESTATICA = {"HPM": 1.410, "HPT": 1.437}
CORREDOR = {"A", "C", "D", "H"}                 # D3


def num(x: float, dec: int = 1) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def mil(x: float) -> str:
    return num(x, 0)


def pc(x: float, dec: int = 1) -> str:
    return num(x * 100, dec) + " %"


def ic95(s: pd.Series) -> tuple[float, float]:
    """Media e intervalo de confianza del 95 % (t de Student) entre replicaciones."""
    n = len(s)
    m = s.mean()
    h = stats.t.ppf(0.975, n - 1) * s.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")
    return m, h


def metricas(obs: pd.Series, pre: pd.Series) -> dict:
    return {
        "correlacion": float(np.corrcoef(obs, pre)[0, 1]),
        "wape": float((pre - obs).abs().sum() / obs.sum()),
        "sesgo": float((pre - obs).sum() / obs.sum()),
    }


def sensibilidad_d(w, res: pd.DataFrame, carga: pd.DataFrame, con: pd.DataFrame,
                   ruta_resumen: Path) -> None:
    """Base contra la variante con la oferta de la D de septiembre de 2024 (D4)."""
    res_v = pd.read_csv(ruta_resumen)
    carga_v = pd.read_csv(PROCESADO / "referencia_d2024_carga.csv")
    w("## 5. Sensibilidad de D4: la Línea D con la oferta de septiembre de 2024\n")
    w("D4 ajusta la oferta con julio a diciembre de 2025, pero la demanda y los perfiles "
      "de carga de SBASE son de septiembre de 2024, cuando la D despachaba bastante más "
      "espaciado (282 s en hora pico contra 218 s; `reports/12_ajuste_intervalos.md`, "
      "sección 7). Se corre el mismo modelo, con las mismas semillas, cambiando solo la "
      "oferta de la D.\n")
    w("| Indicador (toda la red) | Base | D de sept. 2024 |")
    w("|---|---:|---:|")
    for etiqueta, col, dec in (("Tiempo de viaje medio (s)", "viaje_medio_s", 1),
                               ("Espera media por viaje (s)", "espera_media_s", 1),
                               ("Pasajeros-vez que no entran en una formación", "quedaron_abajo", 0),
                               ("Pasajeros vivos a la vez, máximo", "max_vivos", 0)):
        mb, hb = ic95(res[col])
        mv, hv = ic95(res_v[col])
        w(f"| {etiqueta} | {num(mb, dec)} ± {num(hb, dec)} | {num(mv, dec)} ± {num(hv, dec)} |")
    w("")
    w("**Línea D, contra SBASE** (tramos comparables de la D):\n")
    w("| Período | Oferta | Correlación | Error absoluto ponderado | Sesgo | Ocupación media en el tramo más cargado |")
    w("|---|---|---:|---:|---:|---:|")
    cd = con[con.linea == "D"]
    for per, h in PERIODOS.items():
        for etiqueta, c in (("base (2025 jul.–dic.)", carga), ("sept. 2024", carga_v)):
            g = cd[cd.periodo == per].merge(c[c.hora == h], on=["linea", "direction_id", "nodo", "hora"])
            mt = metricas(g.carga_saliente, g.pasajeros_hora_media)
            cc = c[(c.linea == "D") & (c.hora == h)]
            ocup = (cc.pasajeros_hora_media / (cc.formaciones_hora_media * cc.capacidad)).max()
            w(f"| {per} | {etiqueta} | {num(mt['correlacion'], 3)} | {pc(mt['wape'])} | "
              f"{pc(mt['sesgo'])} | {pc(ocup, 0)} |")
    w("")
    w("El flujo por tramo en pasajeros por hora casi no depende de la frecuencia mientras "
      "no haya saturación, así que el contraste de carga contra SBASE cambia poco. Lo que "
      "sí cambia es la ocupación por formación y la espera: es el efecto que el desfase "
      "entre la oferta de 2025 y la demanda de 2024 introduce en el escenario base, y hay "
      "que declararlo al comparar contra la Línea F.\n")


def main() -> None:
    res = pd.read_csv(PROCESADO / "referencia_resumen.csv")
    carga = pd.read_csv(PROCESADO / "referencia_carga.csv")
    hora = pd.read_csv(PROCESADO / "referencia_hora.csv")
    con = pd.read_csv(PROCESADO / "sbase_contraste_carga.csv")
    nombre = pd.read_csv(PROCESADO / "grafo_nodos.csv").set_index("nodo_id").nombre

    con = con[con.comparable].copy()
    con["linea"] = con.linea.str.replace("Linea", "")
    con["direction_id"] = con.direction_id.astype(int)
    con["hora"] = con.periodo.map(PERIODOS)
    j = con.merge(carga, on=["linea", "direction_id", "nodo", "hora"], how="left")
    faltan = int(j.pasajeros_hora_media.isna().sum())

    L: list[str] = []
    w = L.append
    reps = len(res)
    w("# Paso 13, Verificación del modelo base con el simulador de referencia\n")
    w("Generado por `src/13_verificacion_referencia.py` sobre las salidas de "
      "`anylogic/biblioteca/referencia/SimuladorReferencia.java` "
      "(`data/processed/referencia_*.csv`).\n")
    w("**Qué es el simulador de referencia.** Un simulador de eventos discretos en "
      "Java plano que corre **la misma lógica** que el modelo de AnyLogic "
      "(`anylogic/modelo/GUIA_CONSTRUCCION.md`) con la misma biblioteca: los "
      "mismos eventos, el mismo orden dentro de la detención (bajan al llegar, "
      "suben al partir) y las mismas reglas (D12 a D19). **No reemplaza al modelo "
      "de AnyLogic**, que es el entregable. Sirve para verificar la lógica antes de "
      "armarla y, después, para la verificación cruzada: con los mismos insumos, "
      "AnyLogic tiene que dar lo mismo dentro del error de muestreo.\n")
    w(f"Corrida: **{reps} replicaciones** del día hábil completo (5 a 24 h), "
      f"semillas {res.semilla.min()} a {res.semilla.max()}. Cada una tarda alrededor de "
      f"{num(res.segundos_de_computo.mean())} s. Detención fija de 24 s (D13, "
      "primera etapa), sin separación mínima por tramo (entra con la detención "
      "endógena, D15).\n")

    w("## 1. Consistencia interna\n")
    w("| Control | Resultado |")
    w("|---|---|")
    w(f"| Conservación (ingresados = arribados + en el sistema) | "
      f"{'OK en las ' + str(reps) if (res.conservacion == 'OK').all() else 'FALLA'} |")
    m, h = ic95(res.ingresados)
    w(f"| Viajes generados | {mil(m)} ± {mil(h)} (esperados 827.289) |")
    w(f"| Pasajeros vivos a la vez, máximo | {mil(res.max_vivos.min())} a "
      f"{mil(res.max_vivos.max())} |")
    w(f"| Formaciones a la vez, máximo | {res.max_formaciones.min()} a "
      f"{res.max_formaciones.max()} |")
    w(f"| Quedan en el sistema a las 24 h | {mil(res.en_andenes.mean() + res.a_bordo.mean() + res.caminando.mean())} "
      "en promedio (los que entran después de la última salida de su línea) |")
    w("")
    w(f"**El pool de pasajeros del diseño no alcanza.** D10 lo fijó en {mil(POOL_DISENO)} "
      "porque la concurrencia máxima, medida sobre la asignación estática, era de "
      "20.722. Con las esperas en andén la concurrencia sube: el máximo simulado va "
      f"de {mil(res.max_vivos.min())} a {mil(res.max_vivos.max())}. **El pool tiene "
      "que ser de unos 32.000.** Sigue dentro de lo probado: la prueba D instanció "
      "una población declarada de 60.000 sin problemas. El pool de 150 formaciones "
      "sí alcanza.\n")

    w("## 2. Contra la asignación estática del paso 6\n")
    w("Con la misma matriz y las mismas rutas, la carga por tramo de la simulación "
      "tiene que parecerse a la de la asignación estática. No es igual por "
      "construcción: la estática asigna todos los viajes de la hora a la hora, y la "
      "simulación los reparte en el tiempo que tardan (un viaje que sale a las 8:50 "
      "carga tramos de las 9). Es un control de lógica, no de validez.\n")
    w("| Período | Tramos | Correlación | Error absoluto ponderado | Sesgo |")
    w("|---|---:|---:|---:|---:|")
    for per in PERIODOS:
        g = j[(j.periodo == per) & j.pasajeros_hora_media.notna()]
        mt = metricas(g.carga_predicha, g.pasajeros_hora_media)
        w(f"| {per} | {len(g)} | {num(mt['correlacion'], 3)} | {pc(mt['wape'])} | {pc(mt['sesgo'])} |")
    w("")

    w("## 3. Contra SBASE\n")
    w("La hora pico mañana es **calibración** y la tarde es **validación** (D9). "
      "Se comparan los tramos comparables del paso 9"
      + (f"; {faltan} no tienen carga simulada" if faltan else "") + ".\n")
    w("| Período | Qué es | Tramos | Modelo | Correlación | Error absoluto ponderado | Sesgo |")
    w("|---|---|---:|---|---:|---:|---:|")
    for per, rol in (("HPM", "calibración"), ("HPT", "validación")):
        g = j[(j.periodo == per) & j.pasajeros_hora_media.notna()]
        for etiqueta, col in (("estático (paso 6)", "carga_predicha"), ("simulación", "pasajeros_hora_media")):
            mt = metricas(g.carga_saliente, g[col])
            w(f"| {per} | {rol} | {len(g)} | {etiqueta} | {num(mt['correlacion'], 3)} | "
              f"{pc(mt['wape'])} | {pc(mt['sesgo'])} |")
    w("")
    w("### Por grupo de líneas (D3)\n")
    w("| Período | Líneas | Tramos | Correlación | Error absoluto ponderado |")
    w("|---|---|---:|---:|---:|")
    for per in PERIODOS:
        for etiqueta, lineas in (("corredor A, C, D, H", CORREDOR), ("B y E", {"B", "E"})):
            g = j[(j.periodo == per) & j.linea.isin(lineas) & j.pasajeros_hora_media.notna()]
            mt = metricas(g.carga_saliente, g.pasajeros_hora_media)
            w(f"| {per} | {etiqueta} | {len(g)} | {num(mt['correlacion'], 3)} | {pc(mt['wape'])} |")
    w("")
    w("### Ascensos por viaje\n")
    w("| Período | SBASE | Estático (paso 6) | Simulación |")
    w("|---|---:|---:|---:|")
    for per, col in (("HPM", "ascensos_por_viaje_hpm"), ("HPT", "ascensos_por_viaje_hpt")):
        m, h = ic95(res[col])
        w(f"| {per} | {num(TASA_SBASE[per], 3)} | {num(TASA_ESTATICA[per], 3)} | "
          f"{num(m, 3)} ± {num(h, 3)} |")
    w("")
    w("La simulación da algo más que la asignación estática porque cuenta la vuelta "
      "de las 142 rutas que cambian de sentido como un ascenso más (D19).\n")

    w("### Tramos con mayor diferencia en hora pico mañana\n")
    g = j[(j.periodo == "HPM") & j.pasajeros_hora_media.notna()].copy()
    g["dif"] = g.pasajeros_hora_media - g.carga_saliente
    g = g.reindex(g.dif.abs().sort_values(ascending=False).index).head(10)
    w("| Línea | Sale de | Sentido | SBASE | Estático | Simulación |")
    w("|---|---|---:|---:|---:|---:|")
    for _, r in g.iterrows():
        w(f"| {r.linea} | {nombre[r.nodo]} | {r.direction_id} | {mil(r.carga_saliente)} | "
          f"{mil(r.carga_predicha)} | {mil(r.pasajeros_hora_media)} |")
    w("")

    w("## 4. Indicadores del escenario base\n")
    w(f"Media e intervalo de confianza del 95 % entre las {reps} replicaciones.\n")
    w("| Indicador | Valor |")
    w("|---|---|")
    for etiqueta, col, dec in (("Tiempo de viaje medio (s)", "viaje_medio_s", 1),
                               ("Espera media por viaje, todas las etapas (s)", "espera_media_s", 1),
                               ("Ascensos por viaje, día", "ascensos_por_viaje", 3),
                               ("Pasajeros-vez que no entran en una formación", "quedaron_abajo", 0)):
        m, h = ic95(res[col])
        w(f"| {etiqueta} | {num(m, dec)} ± {num(h, dec)} |")
    w("")
    w("**Los que no entran varían mucho entre réplicas**: el intervalo de confianza es "
      "ancho porque dependen de cuándo se forma un hueco largo entre despachos en hora "
      "pico. Es justamente el indicador que la Línea F debería mover.\n")

    carga["ocupacion"] = carga.pasajeros_hora_media / (carga.formaciones_hora_media * carga.capacidad)
    pico = carga[carga.hora.isin([8, 17])].sort_values("ocupacion", ascending=False).head(8)
    w("### Tramos más cargados (ocupación media por formación)\n")
    w("| Línea | Sale de | Sentido | Hora | Pasajeros/h | Formaciones/h | Ocupación media | Máximo a bordo | Capacidad |")
    w("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in pico.iterrows():
        w(f"| {r.linea} | {nombre[r.nodo]} | {r.direction_id} | {r.hora} | {mil(r.pasajeros_hora_media)} | "
          f"{num(r.formaciones_hora_media)} | {pc(r.ocupacion, 0)} | {r.max_a_bordo} | {r.capacidad} |")
    w("")
    w("La capacidad por coche (179) es un supuesto de la especificación; la ocupación "
      "depende directamente de él.\n")

    w("### Por hora de ingreso\n")
    w("| Hora | Viajes | Viaje medio (min) | Espera media (s) | Ascensos por viaje |")
    w("|---:|---:|---:|---:|---:|")
    for _, r in hora.iterrows():
        w(f"| {int(r.hora_ingreso)} | {mil(r.viajes_por_replica)} | {num(r.viaje_medio_s / 60)} | "
          f"{num(r.espera_media_s, 0)} | {num(r.ascensos_por_viaje, 3)} |")
    w("")

    variante = PROCESADO / "referencia_d2024_resumen.csv"
    if variante.exists():
        sensibilidad_d(w, res, carga, con, variante)

    w("## 6. Lo que este paso no cubre\n")
    w("- **Detención fija** (24 s): la endógena y la separación mínima por tramo "
      "entran en la calibración (D13, D15).")
    w("- **La espera en andén no tiene contraparte observada**, igual que la "
      "aglomeración.")
    w("- **No verifica AnyLogic**: eso se hace cuando el modelo esté armado, "
      "comparando sus salidas contra estas.\n")

    (REPORTES / "13_verificacion_referencia.md").write_text("\n".join(L), encoding="utf-8")
    print("ok", reps, "replicaciones;", faltan, "tramos sin carga simulada")


if __name__ == "__main__":
    main()
