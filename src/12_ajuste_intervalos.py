# -*- coding: utf-8 -*-
"""Paso 12: oferta del modelo. Intervalos entre despachos y apertura del servicio.

Es el insumo de oferta de AnyLogic (ver docs/diseno-modelo-base.md, D14:
despachos independientes por cabecera). Resuelve tres cosas:

1. **Que cabecera es cada lado.** El dataset de despachos llama A y D a los dos
   extremos de cada linea sin decir cual es cual, y `cabeceras-estaciones.csv`
   esta desactualizado (la E termina en Bolivar, la H en Las Heras). Se deduce de
   los datos: las formaciones que arrancan en la apertura desde una estacion
   intermedia recorren una distancia (`Km`) que solo coincide con la distancia
   de esa estacion a la cabecera de destino bajo una de las dos asignaciones.

2. **La apertura del servicio.** A las 5:30 salen a la vez varias formaciones
   desde distintos puntos de la linea, no desde la cabecera. Se mide desde que
   estaciones arrancan (configuracion tipica) para que el modelo las ubique ahi.
   Decidido con el grupo el 21/09/2026 (ver decisiones.md, D16).

3. **La distribucion de los intervalos entre despachos** por linea, cabecera y
   hora. Se hace el procedimiento de la materia (histograma, maxima
   verosimilitud para cinco familias, seleccion por AIC, chi-cuadrado y
   Kolmogorov-Smirnov), pero **el modelo usa la distribucion empirica** de cada
   celda: 39 de 215 celdas, 30 de ellas de la Linea H, no ajustan a ninguna
   teorica, y el grupo eligio la empirica en todas (21/09/2026, D17). La
   empirica es la continua lineal por tramos de Law (cap. 6): se muestrea por
   transformada inversa sobre una tabla de cuantiles.

Base: dia habil tipico de 2025, con los mismos filtros del paso 4 (sin dias
parciales, sin despachos con causa). Solo cuentan como despacho desde cabecera
los viajes de **recorrido completo**; los de recorrido parcial son formaciones
que entran desde un punto intermedio (36 % de los viajes de la hora 5, menos del
1 % en el resto del dia). Los intervalos del grupo de apertura (despachos a
menos de 120 s de la primera salida del dia) no cuentan como intervalos.

**Se excluyen los cortes de servicio**: intervalos de mas de `FACTOR_CORTE`
veces la mediana de su celda (hasta 7 h dentro de dias tipicos, sin causa
registrada, a veces en los dos sentidos a la vez). El modelo representa la
operacion normal, como al excluir los despachos con causa. Decidido con el grupo
el 21/09/2026 (D18); se conserva el resto del dia.

**Periodo**: todo 2025, como el paso 4. Depende de D4, que sigue abierta: si D4
reserva parte de 2025 para validar, se cambia `FILTRO_FECHAS`.

Salidas:
  data/processed/cabeceras_despacho.csv
  data/processed/apertura_formaciones.csv
  data/processed/intervalos_empiricos.csv       (lo que consume el modelo)
  data/processed/distribuciones_despacho.csv    (ajuste teorico, referencia)
  docs/figuras/ajuste-intervalos-c-pico.png
  docs/figuras/ajuste-intervalos-h-pico.png
  reports/12_ajuste_intervalos.md
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
PROCESADO = RAIZ / "data" / "processed"
REPORTES = RAIZ / "reports"
FIGURAS = RAIZ / "docs" / "figuras"

from lib_despachos import ResultadoLectura, leer  # noqa: E402

# El paso 4 empieza con digito y no se puede importar con `import`.
_spec = importlib.util.spec_from_file_location("paso4", Path(__file__).parent / "05_despachos.py")
paso4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(paso4)

LINEAS = paso4.LINEAS
HORAS = range(5, 24)          # horizonte del modelo (D11)
N_MINIMO = 50                 # menos que esto: toma la hora vecina
VENTANA_APERTURA_S = 120      # despachos del grupo de apertura
TOLERANCIA_COMPLETO_KM = 0.05
FACTOR_CORTE = 5              # intervalo > 5 x mediana de la celda: corte
N_CUANTILES = 501             # tabla de la empirica: paso de 0,2 %
FILTRO_FECHAS = None          # p. ej. ("2025-04-01", "2025-09-30"), segun D4
ALFA = 0.05
SEMILLA = 20260921

FAMILIAS = {
    "exponencial": (stats.expon, {"floc": 0}),
    "gamma": (stats.gamma, {"floc": 0}),
    "lognormal": (stats.lognorm, {"floc": 0}),
    "weibull": (stats.weibull_min, {"floc": 0}),
    "normal": (stats.norm, {}),
}


def mil(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def num(x: float, dec: int = 2) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def pc(x: float, dec: int = 1) -> str:
    return f"{x * 100:.{dec}f}".replace(".", ",") + " %"


def hhmm(s: float) -> str:
    s = int(round(s))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}"


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------

def despachos() -> tuple[pd.DataFrame, ResultadoLectura]:
    """Una fila por viaje prestado desde un lado, en dia habil tipico."""
    res = ResultadoLectura()
    crudo = leer(paso4.ANIO, res)
    crudo = crudo[crudo.linea.isin(LINEAS)]
    trozos = []
    for lado in ("A", "D"):
        g = crudo[crudo[f"viajo_{lado}"] & crudo[f"salida_{lado}"].notna()]
        trozos.append(pd.DataFrame({
            "fecha": g.fecha, "linea": g.linea, "tipo_dia": g.tipo_dia,
            "cabecera": lado, "salida_s": g[f"salida_{lado}"].astype(int),
            "km": g[f"km_{lado}"], "causa": g[f"causa_{lado}"],
        }))
    d = pd.concat(trozos, ignore_index=True)
    # dias parciales: mismo criterio que el paso 4, sobre todos los viajes
    por_dia = paso4.marcar_dias_parciales(d)
    parciales = set(zip(por_dia[por_dia.parcial].linea, por_dia[por_dia.parcial].fecha))
    d["parcial"] = [(l, f) in parciales for l, f in zip(d.linea, d.fecha)]
    d = d[(d.tipo_dia == "Habil") & ~d.parcial].copy()
    if FILTRO_FECHAS is not None:
        d = d[(d.fecha >= FILTRO_FECHAS[0]) & (d.fecha <= FILTRO_FECHAS[1])]

    largo = d.groupby("linea").km.agg(lambda s: s.round(2).mode()[0]).rename("km_linea")
    d = d.merge(largo, left_on="linea", right_index=True)
    d["completo"] = d.km >= d.km_linea - TOLERANCIA_COMPLETO_KM
    d["apertura_s"] = d.groupby(["linea", "cabecera", "fecha"]).salida_s.transform("min")
    d["de_apertura"] = d.salida_s <= d.apertura_s + VENTANA_APERTURA_S
    return d.sort_values(["linea", "cabecera", "fecha", "salida_s"]), res


def recorridos() -> dict:
    """Por linea y sentido del GTFS: nodos en orden y km acumulados."""
    a = pd.read_csv(PROCESADO / "grafo_aristas.csv")
    a = a[a.tipo == "tramo"]
    salida = {}
    for (linea, sentido), g in a.groupby(["linea", "direction_id"]):
        g = g.sort_values("orden")
        nodos = [g.de_nodo.iloc[0]] + g.a_nodo.tolist()
        km = np.concatenate([[0.0], g.km.cumsum().to_numpy()])
        salida[(linea.replace("Linea", ""), int(sentido))] = (nodos, km)
    return salida


# --------------------------------------------------------------------------
# 1. Que cabecera es cada lado
# --------------------------------------------------------------------------

def estacion_de_inicio(km_viaje: np.ndarray, km_acum: np.ndarray, km_linea: float) -> tuple[np.ndarray, np.ndarray]:
    """Indice de la estacion desde la que arranca cada viaje y el error en km.

    Un viaje que arranca en la estacion i recorre hasta la cabecera de destino
    `L - km_acum[i]`. El largo del GTFS y el del dataset difieren levemente, asi
    que se reescala al del dataset.
    """
    L = km_acum[-1]
    restante = (L - km_acum) * km_linea / L
    dif = np.abs(km_viaje[:, None] - restante[None, :])
    return dif.argmin(axis=1), dif.min(axis=1)


def inferir_sentidos(d: pd.DataFrame, rec: dict) -> pd.DataFrame:
    filas = []
    for (linea, lado), g in d.groupby(["linea", "cabecera"]):
        op = g[g.de_apertura & ~g.completo & g.km.notna()]
        km_linea = g.km_linea.iloc[0]
        errores = {}
        for sentido in (0, 1):
            _, km_acum = rec[(linea, sentido)]
            _, err = estacion_de_inicio(op.km.to_numpy(), km_acum, km_linea)
            errores[sentido] = err.mean()
        elegido = min(errores, key=errores.get)
        otro = 1 - elegido
        nodos, _ = rec[(linea, elegido)]
        filas.append({
            "linea": linea, "cabecera": lado, "direction_id": elegido,
            "nodo_cabecera": nodos[0], "nodo_destino": nodos[-1],
            "km_linea": km_linea, "viajes_apertura": len(op),
            "error_km_elegido": errores[elegido], "error_km_otro": errores[otro],
        })
    s = pd.DataFrame(filas)
    # cada linea tiene que quedar con un lado por sentido
    chequeo = s.groupby("linea").direction_id.nunique()
    if (chequeo != 2).any():
        raise ValueError(f"asignacion de sentidos ambigua: {chequeo[chequeo != 2]}")
    return s


# --------------------------------------------------------------------------
# 2. Apertura
# --------------------------------------------------------------------------

def apertura(d: pd.DataFrame, sentidos: pd.DataFrame, rec: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Configuracion tipica de arranque y resumen por linea y lado."""
    nombre = pd.read_csv(PROCESADO / "grafo_nodos.csv").set_index("nodo_id").nombre
    config, resumen = [], []
    for _, s in sentidos.iterrows():
        g = d[(d.linea == s.linea) & (d.cabecera == s.cabecera) & d.de_apertura & d.km.notna()]
        nodos, km_acum = rec[(s.linea, s.direction_id)]
        idx, _ = estacion_de_inicio(g.km.to_numpy(), km_acum, s.km_linea)
        g = g.assign(i=idx)
        dias = g.fecha.nunique()
        tam = int(g.groupby("fecha").size().median())
        frec = (g.groupby("i").fecha.nunique() / dias).sort_values(ascending=False)
        elegidas = sorted(frec.index[:tam])
        hora = g.groupby("fecha").apertura_s.first()
        hora_moda = int(hora.mode()[0])
        resumen.append({
            "linea": s.linea, "cabecera": s.cabecera, "dias": dias,
            "hora_apertura": hhmm(hora_moda), "frac_dias_hora_moda": (hora == hora_moda).mean(),
            "formaciones": tam, "tam_p10": g.groupby("fecha").size().quantile(.1),
            "tam_p90": g.groupby("fecha").size().quantile(.9),
            "cobertura": frec.loc[elegidas].mean(),
        })
        for i in elegidas:
            config.append({
                "linea": s.linea, "cabecera": s.cabecera, "direction_id": s.direction_id,
                "hora_s": hora_moda, "orden_en_recorrido": int(i),
                "nodo_inicio": nodos[i], "estacion": nombre[nodos[i]],
                "km_desde_cabecera": round(float(km_acum[i]), 3),
                "frac_dias": round(float(frec.loc[i]), 3),
            })
    return pd.DataFrame(config), pd.DataFrame(resumen)


# --------------------------------------------------------------------------
# 3. Intervalos
# --------------------------------------------------------------------------

def intervalos(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Intervalos entre despachos de recorrido completo, fuera de la apertura."""
    c = d[d.completo & ~d.de_apertura].copy()
    # el primer despacho regular se mide contra el ultimo de la apertura
    ultimo = (d[d.de_apertura].groupby(["linea", "cabecera", "fecha"]).salida_s.max()
              .rename("fin_apertura"))
    c = c.merge(ultimo, left_on=["linea", "cabecera", "fecha"], right_index=True, how="left")
    c["previa"] = c.groupby(["linea", "cabecera", "fecha"]).salida_s.shift(1)
    c["previa"] = c.previa.fillna(c.fin_apertura)
    c["intervalo_s"] = c.salida_s - c.previa
    c = c[c.intervalo_s.notna()]
    conteo = {"con_causa": int((c.causa != "").sum()), "ceros": int((c.intervalo_s <= 0).sum())}
    c = c[(c.causa == "") & (c.intervalo_s > 0)].copy()
    c["hora"] = (c.salida_s // 3600).astype(int)
    mediana = c.groupby(["linea", "cabecera", "hora"]).intervalo_s.transform("median")
    corte = c.intervalo_s > FACTOR_CORTE * mediana
    conteo["cortes"] = int(corte.sum())
    conteo["cortes_1h"] = int((c.intervalo_s > 3600).sum())
    conteo["cortes_por_linea"] = c[corte].groupby("linea").size().to_dict()
    c = c[~corte].copy()
    conteo["parciales_fuera_apertura"] = int((~d.completo & ~d.de_apertura).sum())
    conteo["viajes"] = len(d)
    return c[["fecha", "linea", "cabecera", "hora", "intervalo_s"]], conteo


def celda(t: pd.DataFrame, linea: str, cab: str, h: int) -> np.ndarray:
    return t[(t.linea == linea) & (t.cabecera == cab) & (t.hora == h)].intervalo_s.to_numpy(float)


def hora_de_datos(t: pd.DataFrame, linea: str, cab: str, h: int) -> int:
    """La hora con datos suficientes mas cercana (la misma si alcanza)."""
    n = t[(t.linea == linea) & (t.cabecera == cab)].groupby("hora").size()
    validas = [x for x in HORAS if n.get(x, 0) >= N_MINIMO]
    return min(validas, key=lambda v: (abs(v - h), -v))


# ---- ajuste teorico (referencia) -----------------------------------------

def chi_cuadrado(x: np.ndarray, congelada, k_params: int) -> tuple[float, int, float]:
    """Clases equiprobables, k = ceil(2 n^(2/5)) (Law), al menos 5 esperados."""
    n = len(x)
    k = max(3, min(int(np.ceil(2 * n ** 0.4)), n // 5))
    bordes = congelada.ppf(np.linspace(0, 1, k + 1))
    bordes[0], bordes[-1] = -np.inf, np.inf
    obs, _ = np.histogram(x, bins=bordes)
    esp = n / k
    chi2 = float(np.sum((obs - esp) ** 2 / esp))
    gl = k - 1 - k_params
    return chi2, gl, float(stats.chi2.sf(chi2, gl))


def ajuste_teorico(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    elegidas, detalle = [], []
    for linea in LINEAS:
        for cab in ("A", "D"):
            for h in HORAS:
                x = celda(t, linea, cab, h)
                if len(x) < N_MINIMO:
                    continue
                filas = []
                for fam, (dist, fijos) in FAMILIAS.items():
                    params = dist.fit(x, **fijos)
                    cong = dist(*params)
                    k = 1 if fam == "exponencial" else 2
                    aic = 2 * k - 2 * float(np.sum(cong.logpdf(x)))
                    ks = stats.kstest(x, cong.cdf)
                    chi2, gl, p = chi_cuadrado(x, cong, k)
                    filas.append({"linea": linea, "cabecera": cab, "hora": h, "n": len(x),
                                  "familia": fam, "aic": aic, "ks_d": ks.statistic,
                                  "ks_p": ks.pvalue, "chi2": chi2, "chi2_gl": gl,
                                  "chi2_p": p, "media_ajustada": cong.mean()})
                detalle.extend(filas)
                mejor = min(filas, key=lambda f: f["aic"])
                elegidas.append({**mejor, "media_obs": x.mean(),
                                 "cv_obs": x.std(ddof=1) / x.mean()})
    return pd.DataFrame(elegidas), pd.DataFrame(detalle)


# ---- empirica (lo que usa el modelo) --------------------------------------

def tabla_empirica(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cuantiles por celda y verificacion por muestreo."""
    p = np.linspace(0, 1, N_CUANTILES)
    rng = np.random.default_rng(SEMILLA)
    filas, control = [], []
    for linea in LINEAS:
        for cab in ("A", "D"):
            for h in HORAS:
                fuente = hora_de_datos(t, linea, cab, h)
                x = celda(t, linea, cab, fuente)
                q = np.quantile(x, p)
                for pi, qi in zip(p, q):
                    filas.append((linea, cab, h, round(float(pi), 4), float(qi)))
                muestra = np.interp(rng.random(100_000), p, q)
                control.append({
                    "linea": linea, "cabecera": cab, "hora": h,
                    "n": len(celda(t, linea, cab, h)), "hora_fuente": fuente,
                    "media_obs": x.mean(), "media_muestra": muestra.mean(),
                    "mediana_obs": np.median(x), "cv_obs": x.std(ddof=1) / x.mean(),
                    "ks_d_muestra": stats.ks_2samp(x, muestra).statistic,
                })
    tabla = pd.DataFrame(filas, columns=["linea", "cabecera", "hora", "p", "intervalo_s"])
    return tabla, pd.DataFrame(control)


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------

def figura(t: pd.DataFrame, linea: str, destino: Path) -> None:
    """Histograma, empirica y densidades teoricas en las dos horas pico."""
    fig, ejes = plt.subplots(2, 2, figsize=(11, 7.5))
    colores = {"exponencial": "#9aa0a6", "gamma": "#1a73e8", "lognormal": "#d93025",
               "weibull": "#188038", "normal": "#f29900"}
    for i, h in enumerate((8, 17)):
        for j, cab in enumerate(("A", "D")):
            ax = ejes[i, j]
            x = celda(t, linea, cab, h)
            tope = np.quantile(x, 0.995)
            ax.hist(x[x <= tope], bins=60, density=True, color="#e8eaed",
                    edgecolor="#bdc1c6", label="observado")
            xs = np.linspace(1, tope, 400)
            for fam, (dist, fijos) in FAMILIAS.items():
                if fam == "exponencial":
                    continue
                params = dist.fit(x, **fijos)
                ax.plot(xs, dist(*params).pdf(xs), color=colores[fam], lw=1.4, label=fam)
            ax.set_title(f"Línea {linea}, cabecera {cab}, {h} h (n = {mil(len(x))})", fontsize=10)
            ax.set_xlabel("Intervalo entre despachos (s)")
            ax.set_ylabel("Densidad")
    ejes[0, 0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------
# Reporte
# --------------------------------------------------------------------------

def escribir_reporte(res, conteo, sentidos, ap_config, ap_res, t, teo, det, control) -> None:
    L: list[str] = []
    w = L.append
    nombre = pd.read_csv(PROCESADO / "grafo_nodos.csv").set_index("nodo_id").nombre
    fuera = teo[teo.hora > 5]

    w("# Paso 12, Oferta del modelo: intervalos entre despachos y apertura\n")
    w("Generado por `src/12_ajuste_intervalos.py`. Salidas en `data/processed/`: "
      "`cabeceras_despacho.csv`, `apertura_formaciones.csv`, "
      "`intervalos_empiricos.csv` (lo que consume el modelo) y "
      "`distribuciones_despacho.csv` (ajuste teórico, de referencia). Figuras en "
      "`docs/figuras/ajuste-intervalos-*.png`.\n")

    w("## 1. Base\n")
    w(f"- {res.resumen()}.")
    w(f"- **{mil(conteo['viajes'])} viajes prestados** en días hábiles típicos de "
      "2025 (sin días parciales). Período: "
      f"{'todo 2025' if FILTRO_FECHAS is None else ' a '.join(FILTRO_FECHAS)}; "
      "**depende de D4**, que sigue abierta.")
    w("- Un despacho desde cabecera es un viaje de **recorrido completo**. La "
      "columna `Km` da la distancia de cada viaje y la moda por línea es el "
      "recorrido completo. Los de recorrido parcial son formaciones que entran "
      "desde un punto intermedio: casi todos en la apertura. Fuera de ella son "
      f"{mil(conteo['parciales_fuera_apertura'])} viajes, menos del 1 % en cada hora "
      "entre las 6 y las 23 h, y se excluyen.")
    w("- **`Km` mezcla tres escrituras** (metros con punto de miles, metros sin "
      "separador y, en 2026, kilómetros con coma o redondeados). Se corrigió la "
      "lectura en `src/lib_despachos.py` (punto 7 de su encabezado); ningún paso "
      "anterior usaba la columna.\n")

    w("## 2. Qué cabecera es cada lado\n")
    w("El dataset llama **A** y **D** a los dos extremos de cada línea sin decir "
      "cuál es cuál, y `cabeceras-estaciones.csv` está desactualizado (la E "
      "todavía termina en Bolívar y la H en Las Heras). Se dedujo de los datos: "
      "una formación que arranca en la estación *i* recorre la distancia de *i* "
      "a la cabecera de destino, y eso solo coincide bajo una de las dos "
      "asignaciones.\n")
    w("| Línea | Lado | Sale de | Va a | Viajes de apertura | Error medio (km) | Con la otra asignación |")
    w("|---|---|---|---|---:|---:|---:|")
    for _, s in sentidos.iterrows():
        w(f"| {s.linea} | {s.cabecera} | {nombre[s.nodo_cabecera]} | "
          f"{nombre[s.nodo_destino]} | {mil(s.viajes_apertura)} | "
          f"{num(s.error_km_elegido, 3)} | {num(s.error_km_otro, 3)} |")
    w("")
    el_min, el_max = sentidos.error_km_elegido.min() * 1000, sentidos.error_km_elegido.max() * 1000
    ot_min, ot_max = sentidos.error_km_otro.min() * 1000, sentidos.error_km_otro.max() * 1000
    w("En cinco líneas el lado A es la cabecera 1 de `cabeceras-estaciones.csv`. "
      "**En la E es al revés**: el lado A sale de Retiro. Por eso la "
      "correspondencia sale de los datos y no se supone. El error con la "
      f"asignación elegida va de {el_min:.0f} a {el_max:.0f} m, contra {ot_min:.0f} a "
      f"{ot_max:.0f} m con la otra. El caso menos marcado es el lado A de la C, "
      "pero el lado D de la misma línea, que tiene que ir en el otro sentido, es "
      "claro.\n")

    w("## 3. Apertura del servicio\n")
    w("La apertura es a las **5:30** en todas las líneas. Salen a la vez varias "
      "formaciones desde estaciones intermedias y cada una va hasta la cabecera "
      "de destino. **Decidido con el grupo el 21/09/2026 (D16): el modelo las "
      "ubica donde arrancan.** La configuración típica toma las *k* estaciones "
      "más frecuentes, con *k* el tamaño mediano del grupo de apertura.\n")
    w("| Línea | Lado | Hora | Días en esa hora | Formaciones (p10–p90) | Arrancan desde |")
    w("|---|---|---|---:|---|---|")
    for _, r in ap_res.iterrows():
        est = ap_config[(ap_config.linea == r.linea) & (ap_config.cabecera == r.cabecera)]
        lista = ", ".join(f"{e.estacion} ({pc(e.frac_dias, 0)})" for _, e in est.iterrows())
        w(f"| {r.linea} | {r.cabecera} | {r.hora_apertura} | {pc(r.frac_dias_hora_moda, 0)} | "
          f"{r.formaciones} ({num(r.tam_p10, 0)}–{num(r.tam_p90, 0)}) | {lista} |")
    w("")
    w("El porcentaje junto a cada estación es la fracción de días en que "
      "arranca una formación desde ahí. Las que quedan por debajo del 100 % "
      "muestran que la configuración cambia entre días (en la B hay dos que "
      "se alternan); se toma la típica y **se declara como supuesto**.\n")

    w("## 4. Intervalos entre despachos\n")
    w(f"**{mil(len(t))} intervalos** entre despachos de recorrido completo, fuera "
      "de la apertura, sin despachos con causa registrada. El primer despacho "
      "regular se mide contra el último de la apertura.\n")
    w("### Cortes de servicio\n")
    lineas_corte = ", ".join(f"{k} {v}" for k, v in sorted(conteo["cortes_por_linea"].items()))
    w(f"Dentro de días hábiles típicos, sin causa registrada, hay intervalos de "
      f"hasta 7 h: **{mil(conteo['cortes_1h'])} de más de una hora**, a veces en los dos "
      "sentidos de la línea al mismo tiempo (la A el 18/12/2025, la D el "
      "16/10/2025). Son cortes de servicio, no intervalos de operación. "
      f"**Decidido con el grupo el 21/09/2026 (D18): se excluye el intervalo** si "
      f"supera {FACTOR_CORTE} veces la mediana de su celda, y se conserva el resto del "
      f"día. Son **{mil(conteo['cortes'])} intervalos** ({lineas_corte}). El modelo "
      "representa la operación normal, igual que al excluir los despachos con "
      "causa; los cortes se declaran y pueden ir como escenario aparte.\n")
    n_ajust = len(teo)
    w(f"### 4.1 Ajuste teórico (procedimiento de la materia)\n")
    w(f"Se ajustaron {n_ajust} celdas (línea × lado × hora, de 5 a 23 h) con cinco "
      "familias por máxima verosimilitud, eligiendo por AIC.\n")
    cuenta = teo.familia.value_counts()
    w("| Familia | Celdas donde gana |")
    w("|---|---:|")
    for fam in FAMILIAS:
        w(f"| {fam} | {int(cuenta.get(fam, 0))} |")
    w("")
    w(f"El coeficiente de variación tiene mediana **{num(teo.cv_obs.median())}**. "
      "La exponencial queda descartada de entrada: exige 1, y un servicio "
      "programado es mucho más regular que un proceso de Poisson.\n")
    w(f"Bondad de ajuste de la familia elegida, al {pc(ALFA, 0)}: chi-cuadrado rechaza "
      f"en **{pc((teo.chi2_p < ALFA).mean())}** de las celdas y Kolmogorov-Smirnov "
      f"en **{pc((teo.ks_p < ALFA).mean())}**. Con del orden de "
      f"{mil(teo.n.median())} intervalos por celda las dos pruebas rechazan "
      "cualquier distribución teórica frente a datos reales (Law, cap. 6), así que "
      "se mira además el **estadístico D de Kolmogorov-Smirnov**, que no depende "
      "de n: la máxima distancia entre la acumulada observada y la ajustada.\n")
    d = fuera.ks_d
    w(f"Sin la hora 5: D mediano **{num(d.median(), 3)}**, y **{int((d > 0.10).sum())} "
      f"de {len(fuera)} celdas con D > 0,10**, de las cuales "
      f"{int(((d > 0.10) & (fuera.linea == 'H')).sum())} son de la Línea H.\n")
    w("La H despacha con un horario muy rígido: en hora pico, la mitad de los "
      "intervalos cae en una franja de unos 15 s alrededor de 205 s. Además tiene "
      "**un segundo pico cerca de 290 s**. Esa forma bimodal no la reproduce "
      "ninguna familia unimodal; tampoco las versiones desplazadas de tres "
      "parámetros, que se probaron (en la H, cabecera D, 8 h, D baja de 0,233 a "
      "0,208). Ver "
      "`docs/figuras/ajuste-intervalos-h-pico.png` contra "
      "`ajuste-intervalos-c-pico.png`.\n")
    w("#### Comparación de familias en hora pico, Líneas C y H\n")
    w("| Línea | Lado | Hora | Familia | AIC − mínimo | D de K-S |")
    w("|---|---|---:|---|---:|---:|")
    for linea in ("C", "H"):
        for cab in ("A", "D"):
            for h in (8, 17):
                g = det[(det.linea == linea) & (det.cabecera == cab) & (det.hora == h)].sort_values("aic")
                for _, r in g.head(3).iterrows():
                    w(f"| {linea} | {cab} | {h} | {r.familia} | {num(r.aic - g.aic.min(), 1)} | "
                      f"{num(r.ks_d, 3)} |")
    w("")

    w("### 4.2 Lo que usa el modelo: la distribución empírica\n")
    w("**Decidido con el grupo el 21/09/2026 (D17): distribución empírica en "
      "todas las celdas.** Es la continua lineal por tramos de Law (cap. 6): una "
      f"tabla de {N_CUANTILES} cuantiles por celda (paso de 0,2 %), que el modelo "
      "muestrea por transformada inversa: `u = uniform()`, se interpola el "
      "cuantil. Reproduce la forma observada sin elegir familia; el costo es que "
      "no extrapola más allá del mínimo y el máximo observados en cada celda, "
      "que con miles de datos por celda no es una restricción práctica.\n")
    fb = control[control.hora_fuente != control.hora]
    w(f"- Celdas con menos de {N_MINIMO} intervalos, que toman la hora vecina: "
      + (", ".join(f"{r.linea}-{r.cabecera} {r.hora} h (n = {r.n}, usa {r.hora_fuente} h)"
                   for _, r in fb.iterrows()) or "ninguna") + ".")
    w(f"- **Verificación**: 100.000 valores muestreados de cada tabla contra los "
      f"datos de su celda. D de Kolmogorov-Smirnov máximo **{num(control.ks_d_muestra.max(), 3)}**; "
      f"diferencia de medias máxima {num((control.media_muestra / control.media_obs - 1).abs().max() * 100, 2)} %.\n")
    w("| Línea | Lado | Hora | n | Media (s) | Mediana (s) | Coef. de variación |")
    w("|---|---|---:|---:|---:|---:|---:|")
    for _, r in control[control.hora.isin([8, 17])].iterrows():
        w(f"| {r.linea} | {r.cabecera} | {r.hora} | {mil(r.n)} | {num(r.media_obs, 1)} | "
          f"{num(r.mediana_obs, 0)} | {num(r.cv_obs)} |")
    w("")

    w("## 5. Lo que este paso no resuelve\n")
    w("- **Los intervalos consecutivos no son independientes**: un despacho "
      "atrasado acorta el siguiente. Muestrear intervalos independientes pierde "
      "esa correlación. Se ve en la verificación del modelo.")
    w("- **La configuración de apertura es la típica**, no la de cada día.")
    w("- **El período depende de D4.**")
    w("- **Las formaciones que se retiran al final del servicio** (horas 0 y 1, "
      "con recorrido parcial) quedan fuera: el modelo corta a las 24 h.\n")

    (REPORTES / "12_ajuste_intervalos.md").write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    d, res = despachos()
    rec = recorridos()
    sentidos = inferir_sentidos(d, rec)
    ap_config, ap_res = apertura(d, sentidos, rec)
    t, conteo = intervalos(d)
    teo, det = ajuste_teorico(t)
    tabla, control = tabla_empirica(t)

    sentidos.to_csv(PROCESADO / "cabeceras_despacho.csv", index=False, float_format="%.4g")
    ap_config.to_csv(PROCESADO / "apertura_formaciones.csv", index=False)
    tabla.to_csv(PROCESADO / "intervalos_empiricos.csv", index=False, float_format="%.6g")
    teo.to_csv(PROCESADO / "distribuciones_despacho.csv", index=False, float_format="%.6g")
    FIGURAS.mkdir(parents=True, exist_ok=True)
    figura(t, "C", FIGURAS / "ajuste-intervalos-c-pico.png")
    figura(t, "H", FIGURAS / "ajuste-intervalos-h-pico.png")
    escribir_reporte(res, conteo, sentidos, ap_config, ap_res, t, teo, det, control)
    print(f"viajes={conteo['viajes']:,} intervalos={len(t):,} celdas={len(control)} "
          f"ks_max_empirica={control.ks_d_muestra.max():.4f}")
    print(sentidos[["linea", "cabecera", "direction_id", "error_km_elegido", "error_km_otro"]].to_string())
    print(ap_res.to_string())


if __name__ == "__main__":
    main()
