"""Paso 4 del plan de trabajo: intervalos reales entre despachos.

Trabaja sobre los recursos anuales de "Subte: Trenes despachados", leidos con
lib_despachos. **No usa el recurso "Formaciones despachadas - Total"** que
teniamos anotado usar: ese archivo esta congelado en 2019, su
contenido termina el 22/10/2021 y le faltan 2016, 2017 y 2018 enteros.

Produce:

1. La distribucion de intervalos entre despachos por linea, cabecera y hora, en
   dia habil tipico. Es la oferta observada, contra la que se contrasta el
   servicio nominal del GTFS.
2. El contraste contra el headway de diseno de la Linea F, que el EsIA fija en
   1,5 min (40 trenes por sentido y hora).
3. Los despachos con causa registrada, que se separan del resto porque son
   servicio no prestado y no ruido de la operacion normal.
4. La cobertura del dataset, incluido el mes entero que le falta.
5. El cruce del calendario `Tipo Dia` del operador contra los dias atipicos que
   detecto el paso 3, que es la verificacion externa que ese paso dejo abierta.

Los despachos se miden **en cabecera**. El intervalo en una estacion intermedia
puede diferir por acumulacion, y eso es justamente una salida del modelo.

Salidas:
  data/processed/intervalos_despacho.csv
  data/processed/despachos_diario.csv
  reports/05_despachos.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from lib_despachos import ResultadoLectura, cabeceras, leer  # noqa: E402

PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"

ANIO = 2025
LINEAS = ("A", "B", "C", "D", "E", "H")  # P es Premetro, fuera de alcance

# Un dia se considera parcial si su cantidad de despachos cae por debajo de esta
# fraccion de la mediana de los dias del mismo tipo y linea. No es lo mismo que
# un dia de servicio reducido: es un dia con datos incompletos.
UMBRAL_PARCIAL = 0.60

# Headway de diseno de la Linea F, del EsIA (doc 0010): 40 trenes por sentido y
# hora, 1,5 min entre trenes.
HEADWAY_F_S = 90
TRENES_F_HORA = 40


def es(n: float, dec: int = 0) -> str:
    return f"{n:,.{dec}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def num(x: float, dec: int = 1) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def servicios_largos(d: pd.DataFrame) -> pd.DataFrame:
    """Pasa de una fila por formacion a una fila por servicio de cabecera.

    Cada registro puede tener servicio por la cabecera A, por la D o por las dos.
    Se conservan los **no prestados**: son el objeto de la seccion de causas.
    Descartar los `viajo=False` de entrada haria invisible justamente lo que un
    paro produce, que es servicio programado y no prestado.
    """
    trozos = []
    for lado in ("A", "D"):
        g = d[d[f"salida_{lado}"].notna() | (d[f"causa_{lado}"] != "")].copy()
        trozos.append(
            pd.DataFrame(
                {
                    "fecha": g.fecha,
                    "linea": g.linea,
                    "tipo_dia": g.tipo_dia,
                    "cabecera": lado,
                    "prestado": g[f"viajo_{lado}"],
                    "salida_s": g[f"salida_{lado}"],
                    "coches": g[f"coches_{lado}"],
                    "causa": g[f"causa_{lado}"],
                    "tren": g.tren,
                }
            )
        )
    return pd.concat(trozos, ignore_index=True)


def marcar_dias_parciales(desp: pd.DataFrame) -> pd.DataFrame:
    """Marca los (linea, fecha) con muchos menos despachos de los esperables."""
    por_dia = desp.groupby(["linea", "tipo_dia", "fecha"], as_index=False).size()
    mediana = por_dia.groupby(["linea", "tipo_dia"], as_index=False)["size"].median()
    mediana = mediana.rename(columns={"size": "mediana"})
    por_dia = por_dia.merge(mediana, on=["linea", "tipo_dia"])
    por_dia["razon"] = por_dia["size"] / por_dia.mediana
    por_dia["parcial"] = por_dia.razon < UMBRAL_PARCIAL
    return por_dia


def intervalos(desp: pd.DataFrame) -> pd.DataFrame:
    """Intervalo entre despachos consecutivos de una misma linea y cabecera."""
    d = desp.sort_values(["linea", "cabecera", "fecha", "salida_s"]).copy()
    clave = ["linea", "cabecera", "fecha"]
    d["intervalo_s"] = d.groupby(clave).salida_s.diff()
    d = d[d.intervalo_s.notna()].copy()
    d["hora"] = (d.salida_s // 3600).astype(int)
    return d


def main() -> None:
    PROCESADO.mkdir(parents=True, exist_ok=True)
    REPORTES.mkdir(parents=True, exist_ok=True)

    res = ResultadoLectura()
    crudo = leer(ANIO, res)
    print(res.resumen())

    crudo = crudo[crudo.linea.isin(LINEAS)].copy()
    servicios = servicios_largos(crudo)
    desp = servicios[servicios.prestado & servicios.salida_s.notna()].copy()
    desp["salida_s"] = desp.salida_s.astype(int)
    por_dia = marcar_dias_parciales(desp)
    parciales = set(
        zip(por_dia[por_dia.parcial].linea, por_dia[por_dia.parcial].fecha)
    )
    desp["parcial"] = [
        (l, f) in parciales for l, f in zip(desp.linea, desp.fecha)
    ]

    inter = intervalos(desp)
    tipicos = inter[
        (inter.tipo_dia == "Habil") & (~inter.parcial) & (inter.causa == "")
    ]

    por_dia.to_csv(PROCESADO / "despachos_diario.csv", index=False, encoding="utf-8")
    resumen = (
        tipicos.groupby(["linea", "cabecera", "hora"])
        .intervalo_s.agg(
            n="size", mediana="median", media="mean",
            p10=lambda s: s.quantile(0.10), p90=lambda s: s.quantile(0.90),
            minimo="min", maximo="max", desvio="std",
        )
        .round(1)
        .reset_index()
    )
    resumen.to_csv(PROCESADO / "intervalos_despacho.csv", index=False, encoding="utf-8")

    escribir_reporte(res, crudo, servicios, desp, por_dia, inter, tipicos, resumen)
    print(
        f"despachos={len(desp):,} intervalos={len(inter):,} "
        f"tipicos={len(tipicos):,} dias={desp.fecha.nunique()}"
    )


def escribir_reporte(res, crudo, servicios, desp, por_dia, inter, tipicos,
                     resumen) -> None:
    L: list[str] = []
    w = L.append
    cab = cabeceras().set_index("linea")

    w("# Paso 4 — Intervalos entre despachos\n")
    w("Generado por `src/05_despachos.py` sobre "
      f"`data/raw/formaciones-despachadas-{ANIO}.csv`, leído con "
      "`src/lib_despachos.py`. Salidas: `intervalos_despacho.csv` y "
      "`despachos_diario.csv` en `data/processed/`.\n")

    w("## 1. El recurso agregado del portal no sirve\n")
    w("Teníamos anotado usar el recurso **«Formaciones "
      "despachadas - Total» (CSV, 2015 a la actualidad, archivo único)** y "
      "que *«su historia desde 2015 es homogénea»*. **Las dos cosas son "
      "falsas.** Verificado sobre la copia local y contra la API del portal el "
      "18/08/2026:\n")
    w("| Afirmación | Qué se verificó |")
    w("|---|---|")
    w("| «2015 a la actualidad» | El contenido **termina el 22/10/2021**. El "
      "metadato del recurso dice `last_modified = 2019-06-04`. |")
    w("| «archivo único» | El dataset publica además **un recurso por año**, "
      "incluidos 2025 y 2026. |")
    w("| «historia homogénea desde 2015» | Faltan **2016, 2017 y 2018 enteros**, "
      "y de 2015 hay 6 días. |")
    w("")
    w("Es el mismo patrón que `viajes_anual.csv`: un recurso agregado que quedó "
      "congelado mientras el dataset siguió publicando por año. **Este paso usa "
      "los recursos anuales**, descargados el 18/08/2026 de "
      "`cdn.buenosaires.gob.ar/datosabiertos/datasets/sbase/subte-trenes-despachados/`.\n")
    w("El esquema anual además es mejor: nombres legibles, causas en texto y una "
      "columna **`Tipo Día` con el valor `Feriado`**, que es el calendario "
      "operativo del propio operador. Ver la sección 5.\n")
    w(f"Lectura: {res.resumen()}.\n")

    w("## 2. Cobertura, y el mes que falta\n")
    dias = sorted(servicios.fecha.dt.date.unique())
    todos = pd.date_range(f"{ANIO}-01-01", f"{ANIO}-12-31").date
    faltan = sorted(set(todos) - set(dias))
    sin_servicio = sorted(set(dias) - set(desp.fecha.dt.date))
    w(f"- Días con registros: **{len(dias)} de {len(todos)}**.")
    w(f"- Servicios de cabecera programados: **{es(len(servicios))}**, de los "
      f"cuales **{es(len(desp))} prestados** y "
      f"{es(len(servicios) - len(desp))} no prestados. Seis líneas; el Premetro "
      "queda fuera de alcance.")
    if faltan:
        meses = pd.Series(faltan).map(lambda x: x.month).value_counts().sort_index()
        det = ", ".join(f"{n} día{'s' if n != 1 else ''} de {m:02d}" for m, n in meses.items())
        w(f"- **Faltan {len(faltan)} días**: {det}.")
        w("")
        w("> **Marzo de 2025 no está.** Faltan 30 de sus 31 días; solo "
          "sobrevive el 08/03. **Es un faltante del publicador, no un mes sin "
          "servicio**: los molinetes registran demanda normal en todo marzo, "
          "así que los trenes circularon y lo que falta es el registro de "
          "oferta. **Marzo queda fuera de cualquier ventana de ajuste o "
          "validación** (decisión D4), y deja sin verificar los cuatro días "
          "atípicos que el paso 3 detectó en ese mes.\n")
    n_parc = int(por_dia.parcial.sum())
    w(f"- Pares (línea, día) con datos parciales, por debajo del "
      f"{UMBRAL_PARCIAL * 100:.0f} % de la mediana de su tipo de día: **{n_parc}**. "
      "Quedan excluidos de los intervalos.\n")

    if sin_servicio:
        w("### 2.1 Un día con registros y cero servicios prestados\n")
        for f in sin_servicio:
            g = servicios[servicios.fecha.dt.date == f]
            causa = g[g.causa != ""].causa.value_counts()
            w(f"**{f}**: {es(len(g))} servicios programados, **ninguno "
              f"prestado**, en las seis líneas. Causa registrada: "
              f"*{causa.index[0]}* en {es(int(causa.iloc[0]))} de ellos.\n")
        w("> **Esto corrige al paso 3.** Ese paso encontró el 10/04/2025 en "
          "molinetes con 66 pasajeros y 31 de 90 estaciones con dato, y lo "
          "clasificó como **hueco de datos del publicador**. No lo es: fue un "
          "**paro general, un día sin servicio**. Las dos fuentes son "
          "independientes y coinciden. El tratamiento no cambia —el día se "
          "excluye de todos los perfiles por no ser representativo— pero la "
          "caracterización sí, y ahora está verificada en lugar de supuesta. "
          "Ver `reports/04_demanda.md`, sección 2.1.\n")

    w("## 3. Intervalos entre despachos en día hábil típico\n")
    w("Se miden **en cabecera**: es el intervalo con que la línea despacha, no "
      "el que ve un pasajero en una estación intermedia, que puede degradarse "
      "por acumulación. Esa degradación es una salida del modelo, no una "
      "entrada.\n")
    w(f"Base: {es(len(tipicos))} intervalos de días hábiles completos, "
      "excluyendo los despachos con causa registrada (sección 4).\n")

    pico = tipicos[tipicos.hora.isin([7, 8, 17, 18])]
    valle = tipicos[tipicos.hora.isin([11, 12, 13, 14])]
    w("### 3.1 Por línea\n")
    w("| Línea | Cabeceras | Pico (7–9 y 17–19) | Valle (11–15) | Trenes/h en pico |")
    w("|---|---|---:|---:|---:|")
    for l in LINEAS:
        p = pico[pico.linea == l].intervalo_s
        v = valle[valle.linea == l].intervalo_s
        if p.empty:
            continue
        c1 = cab.cabecera_1.get(l, "").title()
        c2 = cab.cabecera_2.get(l, "").title()
        w(f"| {l} | {c1} ↔ {c2} | {num(p.median() / 60, 2)} min | "
          f"{num(v.median() / 60, 2)} min | {num(3600 / p.median())} |")
    w("")
    w("La cifra de trenes por hora es por cabecera, es decir **por sentido**.\n")

    w("### 3.2 Perfil horario\n")
    perfil = (
        tipicos.groupby(["linea", "hora"]).intervalo_s.median().unstack(0) / 60
    )
    horas = [h for h in range(5, 24) if h in perfil.index]
    w("Mediana del intervalo, en minutos:\n")
    w("| Hora | " + " | ".join(LINEAS) + " |")
    w("|---|" + "---:|" * len(LINEAS))
    for h in horas:
        celdas = []
        for l in LINEAS:
            v = perfil.loc[h, l] if l in perfil.columns else np.nan
            celdas.append(num(v, 2) if pd.notna(v) else "—")
        w(f"| {h:02d} | " + " | ".join(celdas) + " |")
    w("")

    w("### 3.3 Contraste con el diseño de la Línea F\n")
    mejor = None
    for l in LINEAS:
        p = pico[pico.linea == l].intervalo_s
        if p.empty:
            continue
        if mejor is None or p.median() < mejor[1]:
            mejor = (l, p.median())
    w(f"El EsIA fija para la Línea F un headway de **1,5 min, {TRENES_F_HORA} "
      "trenes por sentido y hora**. La línea más frecuente de la red actual en "
      f"hora pico es la **{mejor[0]}**, con una mediana de "
      f"{num(mejor[1] / 60, 2)} min, es decir {num(3600 / mejor[1])} trenes por "
      "hora y sentido.\n")
    w(f"> El diseño de la Línea F supone despachar **{num(mejor[1] / HEADWAY_F_S, 1)} "
      "veces más seguido que lo que hoy logra la mejor línea de la red**. No es "
      "imposible —es una línea nueva, con señalamiento nuevo— pero **es un "
      "supuesto fuerte del escenario futuro y hay que tratarlo como variable de "
      "escenario, no como dato**. El documento ya declara 1,5 min como cota "
      "superior de frecuencia; este contraste le da la magnitud.\n")

    w("## 4. Servicio no prestado y sus causas\n")
    no_prest = servicios[~servicios.prestado]
    w(f"De {es(len(servicios))} servicios de cabecera programados, "
      f"**{es(len(no_prest))} no se prestaron ({pc(len(no_prest) / len(servicios), 2)})**. "
      f"El {pc((no_prest.causa != '').mean(), 1)} de ellos tiene causa "
      "registrada, así que la trazabilidad es prácticamente total.\n")
    w("> La distinción importa y es fácil de perder: si se filtran de entrada "
      "los servicios no prestados, **las causas que se ven son las de los "
      "servicios que sí se hicieron**, y un paro —que por definición cancela— "
      "desaparece del análisis. Acá se cuentan los no prestados.\n")
    w("| Causa | Servicios no prestados |")
    w("|---|---:|")
    for c, n in no_prest[no_prest.causa != ""].causa.value_counts().head(12).items():
        w(f"| {c} | {es(n)} |")
    w("")
    gremial = no_prest[
        no_prest.causa.str.contains("Huelga|Gremial|Paro", case=False, na=False)
    ]
    if not gremial.empty:
        dias_g = gremial.groupby(gremial.fecha.dt.date).size().sort_values(
            ascending=False
        )
        w(f"Las causas gremiales concentran **{es(len(gremial))} servicios "
          f"cancelados en {len(dias_g)} días**, es decir "
          f"{pc(len(gremial) / len(no_prest))} de todo el servicio no prestado "
          "del año. Los seis días de mayor incidencia:\n")
        w("| Fecha | Servicios cancelados | Tipo de día |")
        w("|---|---:|---|")
        tipos = servicios.groupby(servicios.fecha.dt.date).tipo_dia.first()
        for f, n in dias_g.head(6).items():
            w(f"| {f} | {es(n)} | {tipos.get(f, '')} |")
        w("")
        w("**Estos días no pueden entrar en las ventanas de ajuste ni de "
          "validación** (decisión D4): la oferta está afectada y la demanda "
          "medida en molinetes también, por razones que el modelo no representa.\n")
    con_causa = inter[inter.causa != ""]
    w(f"Aparte, {es(len(con_causa))} de los {es(len(inter))} intervalos entre "
      f"despachos **sí prestados** ({pc(len(con_causa) / len(inter))}) tienen "
      "una causa cargada —demoras y anomalías que no impidieron el viaje—. "
      "También se excluyen del cálculo de intervalos típicos.\n")

    w("## 5. El calendario del operador valida el paso 3\n")
    w("La columna `Tipo Día` de este dataset es el **calendario operativo de "
      "SBASE**, y permite hacer la verificación externa que el paso 3 dejó "
      "abierta sobre sus 25 días hábiles atípicos.\n")
    cal = crudo.groupby(crudo.fecha.dt.date).tipo_dia.agg(
        lambda s: s.mode().iloc[0]
    )
    feriados = sorted(cal[cal == "Feriado"].index)
    fer_habiles = [f for f in feriados if f.weekday() <= 4]
    diaria = pd.read_csv(PROCESADO / "demanda_diaria.csv", parse_dates=["fecha"])
    atipicos = set(diaria[diaria.atipico].fecha.dt.date)
    aciertos = [f for f in fer_habiles if f in atipicos]
    w(f"- SBASE declara **{len(feriados)} feriados** en {ANIO}, de los cuales "
      f"**{len(fer_habiles)} caen en día hábil**.")
    w(f"- El método del paso 3 detectó **{len(aciertos)} de esos {len(fer_habiles)}**"
      f"{' —todos—' if len(aciertos) == len(fer_habiles) else ''}, sin conocer "
      "el calendario.\n")
    resto = sorted(atipicos - set(feriados))
    sin_dato = [f for f in resto if f not in cal.index]
    sabado = [f for f in resto if cal.get(f) == "Sabado"]
    habil = [f for f in resto if cal.get(f) == "Habil"]
    w(f"De los {len(resto)} días atípicos que **no** son feriado:\n")
    w(f"- **{len(sabado)} están declarados por SBASE como servicio de sábado** "
      f"pese a caer en día hábil: {', '.join(str(f) for f in sabado)}. "
      "Es decir que el operador ya reconoce que no son días normales, y explica "
      "la menor demanda por menor oferta.")
    w(f"- **{len(sin_dato)} caen en marzo**, que no tiene datos de despachos "
      f"({', '.join(str(f) for f in sin_dato)}), así que **no se pueden "
      "verificar con esta fuente**.")
    w(f"- **{len(habil)} quedan sin explicación**: SBASE los declara hábiles con "
      f"servicio normal ({', '.join(str(f) for f in habil)}). Son días de menor "
      "demanda con oferta normal.\n")
    w("> **El criterio del paso 3 queda validado**: recall de "
      f"{pc(len(aciertos) / len(fer_habiles), 0)} sobre los feriados hábiles, y "
      f"{len(sabado)} detecciones más que el propio operador corrobora como días "
      "de servicio reducido. Sigue sin ser un clasificador de feriados —no lo "
      "pretende— pero como detector de días no representativos funciona.\n")

    w("## 6. Coches por formación\n")
    coches = (
        desp[desp.coches > 0].groupby("linea").coches.agg(
            mediana="median", media="mean", minimo="min", maximo="max"
        )
    )
    w("Insumo directo de la capacidad de formación del modelo:\n")
    w("| Línea | Mediana | Media | Mínimo | Máximo |")
    w("|---|---:|---:|---:|---:|")
    for l, r in coches.iterrows():
        w(f"| {l} | {num(r.mediana, 0)} | {num(r.media, 2)} | {num(r.minimo, 0)} | "
          f"{num(r.maximo, 0)} |")
    w("")
    w("La capacidad por formación no sale de acá —depende del modelo de coche— "
      "pero la cantidad de coches sí, y varía dentro de una misma línea.\n")

    w("## 7. Qué queda de esto\n")
    w("- **Corregido en `docs/contexto-del-proyecto.md`, sección 4**: el recurso «Total» "
      "está congelado y la historia no es homogénea desde 2015 (sección 1).")
    w("- **Marzo de 2025 no existe en este dataset** (sección 2). Condiciona "
      "D4: ninguna ventana de ajuste o validación puede tocar marzo.")
    w("- **El headway de 1,5 min de la Línea F es un supuesto fuerte** "
      "(sección 3.3), no un dato: exige despachar bastante más seguido que la "
      "mejor línea actual. Va como variable de escenario.")
    w("- **El pendiente de verificación del paso 3 se cierra** (sección 5).")
    w("- **Sigue faltando el contraste GTFS contra operación real**: los tiempos "
      "de marcha del GTFS son un perfil nominal único y este paso mide "
      "despachos, no tiempos de recorrido. El contraste completo necesita el "
      "modelo.")
    w("")

    (REPORTES / "05_despachos.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
