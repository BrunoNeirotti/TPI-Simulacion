"""
Figuras del documento de propuesta (docs/definitivo-main.tex).

Genera en docs/figuras/:

  1. red-y-linea-f.png        Esquemático de la red y de la Línea F   [EN USO]
  2. perfil-carga-linea-f.png Carga por tramo de la Línea F, hora pico mañana
  3. perfil-horario-red.png   Perfil horario de la demanda de la red actual

Solo la primera se incluye hoy en el documento. Las otras dos se conservan porque el
informe final las va a necesitar; para el documento de propuesta se descartaron por no
aportar lo suficiente a esa altura del trabajo.

Procedencia de los datos, por figura:

  Figura 1. DIAGRAMA TOPOLÓGICO, no un mapa: no está a escala. Trazado de las seis
    líneas en operación, extraído del Mapa de red oficial de SBASE; orden y espaciado
    de las estaciones, del feed GTFS; Línea F, de las progresivas de la Tabla 4 del
    EsIA (doc 0010, págs. 20-21) y de las estaciones con las que combina. Detalle del
    procedimiento en src/lib_esquematico.py. La vista está acercada al corredor: a
    escala de red completa los doce nombres no entran, que es por lo que el mapa
    oficial del proyecto también está acercado. Se descartó una representación
    geográfica, ilegible al ancho del documento.

  Figura 2. Tablas 2 y 3 del EsIA, doc 0010, págs. 15-16 (Análisis de Demanda Línea F,
    SBASE 2019), transcriptas en docs/expediente-eia-linea-f.md, sección 4.2. Capacidad
    de diseño de 43.000 pas./sentido/hora: doc 0010, pág. 15.

  Figura 3. `etapas_BAdata_20241016.csv` (dataset de viajes y etapas del AMBA, edición
    2024, día relevado 16/10/2024), filtrando modo_etapa == SUBTE y expandiendo por
    factor_expansion_etapa.

Uso:  python src/02_figuras_propuesta.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_esquematico as esq        # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "data" / "raw"
FIGURAS = RAIZ / "docs" / "figuras"

# Colores oficiales de las lineas en operacion.
COLOR_LINEA = {
    "A": "#12A0DB",
    "B": "#E4322B",
    "C": "#2A5CAA",
    "D": "#00895F",
    "E": "#642F81",
    "H": "#F2C300",
}
# Naranja con que el GCBA representa a la Linea F en el mapa oficial del proyecto,
# muestreado de esa imagen. La linea va con trazo lleno, como las demas, pero mas
# gruesa: es el objeto del trabajo. Que se trata de un proyecto lo dice la referencia.
COLOR_F = "#D27314"

TINTA = "#1A1A1A"
GRIS = "#6E6E6E"
GRIS_SUAVE = "#D8D8D8"


def estilo() -> None:
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8.5,
        "axes.edgecolor": GRIS,
        "axes.labelcolor": TINTA,
        "axes.linewidth": 0.6,
        "text.color": TINTA,
        "xtick.color": GRIS,
        "ytick.color": GRIS,
        "xtick.labelcolor": TINTA,
        "ytick.labelcolor": TINTA,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        # Se exporta a PNG: a 400 ppp los rotulos de 6,5 pt siguen limpios en papel.
        "savefig.dpi": 400,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


# ---------------------------------------------------------------------------
# Figura 1 -- esquemático de la red y de la Línea F
# ---------------------------------------------------------------------------
# La geometría vive en src/lib_esquematico.py, con la procedencia de cada dato.
# Acá está solamente el dibujo.

# Cabecera: (línea, estación, rótulo, ha, va, desplazamiento). Sin rótulo cuando lo
# aporta otra cabecera del mismo complejo o la referencia de la Línea F.
# La vista se acerca al corredor de la Línea F: a escala de red completa no hay lugar
# para los doce nombres, que es exactamente por lo que el mapa oficial del proyecto
# también está acercado. Las radiales quedan cortadas al borde.
VISTA = (18.2, 41.8, -31.4, -0.5)

# Cabeceras que caen dentro de la vista: (línea, estación, rótulo, ha, va, despl.).
CABECERAS = [
    ("A", "Plaza de Mayo",       "Plaza de Mayo",        "left",   "center", ( .55,  .00)),
    ("B", "Leandro N. Alem",     "L. N. Alem",           "left",   "center", ( .55,  .00)),
    ("C", "Retiro",              "Retiro",               "center", "bottom", ( .00,  .55)),
    ("D", "Catedral",            "Catedral",             "left",   "top",    ( .30, -.35)),
    ("E", "Retiro",              "",                     "left",   "center", ( .55,  .00)),
    ("H", "Facultad de Derecho", "Facultad\nde Derecho", "center", "bottom", ( .00,  .50)),
    ("H", "Hospitales",          "Hospitales",           "center", "top",    ( .00, -.50)),
]

# Radiales que salen de la vista: hacia dónde siguen. (línea, estación de referencia,
# hacia qué cabecera, desplazamiento del rótulo).
CONTINUAN = [
    ("A", "San Pedrito",           "a San Pedrito",           ( .00, -.85), "center"),
    ("B", "Juan Manuel de Rosas",  "a J. M. de Rosas",        ( .00, -.85), "center"),
    ("D", "Congreso de Tucumán",   "a Congreso\nde Tucumán",  ( .00, -1.95), "center"),
    ("E", "Plaza de los Virreyes", "a Pza. de\nlos Virreyes", ( .00, -1.05), "center"),
]

# La prolongación natural del trazo, para el distintivo de línea, chocaría con la
# Línea F al sur de Constitución: ahí se la manda hacia el otro lado.
DIR_CABECERA = {("C", "Constitución"): (-1.0, -0.45)}

# Rótulo de cada estación de la Línea F: (dx, dy, ha) y, en las combinaciones, hacia
# dónde se corre el distintivo de la línea que empalma.
ROTULO_F = {
    1: ( -.60, -.15, "right",  ( .00,  .00)),
    2: (  .70,  .50, "left",   ( .70, -.55)),
    3: (  .85,  .00, "left",   (-.70,  .00)),
    4: (  .85,  .00, "left",   ( .00,  .00)),
    5: (  .85,  .00, "left",   (-.70,  .00)),
    6: (  .85,  .00, "left",   (-.70,  .00)),
    7: (  .85,  .00, "left",   (-.70,  .00)),
    8: (  .30,  .72, "left",   ( .00,  .00)),
    9: (  .10,  .78, "center", ( .00,  .00)),
    10: (-.10,  .78, "center", ( .00,  .00)),
    11: ( .00,  .82, "center", ( .00, -.80)),
    12: ( -.70, -.80, "right", ( .30, -.88)),
}


def figura_esquematico() -> None:
    g = esq.construir()
    trazas, pos = g["trazas"], g["pos"]

    fig, ax = plt.subplots(figsize=(6.6, 5.2))
    halo = [pe.withStroke(linewidth=2.0, foreground="white")]

    # --- trazado de las seis líneas en operación -----------------------------
    for k, P in trazas.items():
        ax.plot(P[:, 0], P[:, 1], color=COLOR_LINEA[k], lw=3.4,
                solid_capstyle="round", solid_joinstyle="round", zorder=2)

    # --- estaciones: una marca blanca sobre el trazo, como el esquemático oficial
    combis = {(ln, nm) for ln, nm in esq.COMBINACIONES_ACTUALES}
    for k, (nombres, _f) in esq.ESTACIONES.items():
        for nombre in nombres:
            x, y = pos[k][nombre]
            if (k, nombre) in combis:
                ax.plot(x, y, "o", ms=4.6, mfc="white", mec="#3C3C3C", mew=0.9,
                        zorder=4)
            else:
                ax.plot(x, y, "o", ms=2.6, mfc="white", mec="none", zorder=3)

    # Retiro: la C y la E son dos estaciones de un mismo complejo de combinación.
    (xc, yc), (xe, ye) = pos["C"]["Retiro"], pos["E"]["Retiro"]
    ax.plot([xc, xe], [yc, ye], color="#3C3C3C", lw=0.9, ls=(0, (1.6, 1.6)),
            zorder=3)

    # --- Línea F -------------------------------------------------------------
    F = g["traza_f"]
    ax.plot(F[:, 0], F[:, 1], color="white", lw=6.6, solid_capstyle="round",
            solid_joinstyle="round", zorder=5)
    ax.plot(F[:, 0], F[:, 1], color=COLOR_F, lw=4.2, solid_capstyle="round",
            solid_joinstyle="round", zorder=6)

    for n, nombre, (x, y), comb, declarada in g["estaciones_f"]:
        dx, dy, ha, (bx, by) = ROTULO_F[n]
        ax.plot(x, y, "o", ms=6.0, mfc="white", mec=COLOR_F, mew=1.6, zorder=8)
        ax.annotate(nombre, (x + dx, y + dy), ha=ha, va="center", fontsize=7.0,
                    color=TINTA, zorder=9, path_effects=halo)
        if comb:
            # Distintivo de la línea con la que empalma, como en el mapa oficial del
            # proyecto. El anillo blanco marca las dos combinaciones que ese mapa
            # muestra pero que el EsIA no declara estación por estación.
            ln = comb[0]
            ax.plot(x + bx, y + by, "o", ms=9.4, mfc=COLOR_LINEA[ln],
                    mec="white" if declarada else COLOR_F, mew=1.3, zorder=9)
            ax.annotate(ln, (x + bx, y + by), ha="center", va="center", fontsize=6.4,
                        color="white", fontweight="bold", zorder=10)

    # Distintivo de línea sobre la prolongación del trazo, al sur de Brandsen.
    p0, p1 = F[0], F[1]
    d = (p0 - p1) / np.hypot(*(p0 - p1))
    xb, yb = p0 + d * 0.85
    ax.plot([p0[0], xb], [p0[1], yb], color=COLOR_F, lw=3.4, zorder=6)
    ax.plot(xb, yb, "o", ms=8.4, mfc=COLOR_F, mec="white", mew=1.1, zorder=8)
    ax.annotate("F", (xb, yb), ha="center", va="center", fontsize=6.0,
                color="white", fontweight="bold", zorder=9)

    # --- ferrocarriles que la Línea F alcanza --------------------------------
    for ln, nm, texto, ha, dx, dy in [
            ("C", "Constitución", "FF.CC. Roca", "left", 1.05, -0.60),
            ("D", "Palermo", "FF.CC. San Martín", "left", 0.30, 1.55)]:
        x, y = pos[ln][nm]
        ax.annotate(texto, (x + dx, y + dy), ha=ha, va="center", fontsize=6.4,
                    color=GRIS, style="italic", zorder=9, path_effects=halo)

    # --- cabeceras -----------------------------------------------------------
    # El esquemático oficial pone el distintivo de línea PASADA la última estación,
    # sobre una prolongación del trazo. Así no pisa el marcador de la estación.
    for k, nombre, texto, ha, va, (dx, dy) in CABECERAS:
        nombres = esq.ESTACIONES[k][0]
        i = nombres.index(nombre)
        p = np.array(pos[k][nombre])
        if (k, nombre) in DIR_CABECERA:      # la prolongación natural chocaría
            u = np.array(DIR_CABECERA[(k, nombre)], float)
            u /= np.hypot(*u)
        else:
            vecino = np.array(pos[k][nombres[1 if i == 0 else -2]])
            u = (p - vecino) / np.hypot(*(p - vecino))
        q = p + u * 0.80
        ax.plot([p[0], q[0]], [p[1], q[1]], color=COLOR_LINEA[k], lw=3.4,
                solid_capstyle="butt", zorder=2)
        ax.plot(*q, "o", ms=8.6, mfc=COLOR_LINEA[k], mec="white", mew=1.1, zorder=8)
        ax.annotate(k, q, ha="center", va="center", fontsize=6.0, color="white",
                    fontweight="bold", zorder=9)
        if texto:
            ax.annotate(texto, (q[0] + dx, q[1] + dy), ha=ha, va=va, fontsize=6.5,
                        color=TINTA, zorder=9, linespacing=1.2,
                        path_effects=halo)

    # --- radiales que salen de la vista --------------------------------------
    x0v, x1v, y0v, y1v = VISTA
    for k, cabecera, texto, (dx, dy), ha in CONTINUAN:
        P = trazas[k]
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        ss = np.linspace(0, s[-1], 4000)
        xs, ys = np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])
        dentro = (xs >= x0v) & (xs <= x1v) & (ys >= y0v) & (ys <= y1v)
        # Se recorre desde la cabecera, que queda fuera de la vista, hasta el primer
        # punto que entra: ahí está el corte. El distintivo va un poco hacia adentro,
        # nunca hacia afuera, o el recorte se lo come.
        desde_el_final = cabecera == esq.ESTACIONES[k][0][-1]
        idx = np.flatnonzero(dentro)
        j = int(idx[-1] if desde_el_final else idx[0])
        adentro = -1 if desde_el_final else +1
        q = np.array([xs[j], ys[j]])
        v = np.array([xs[j + 8 * adentro] - xs[j], ys[j + 8 * adentro] - ys[j]])
        p = q + v / np.hypot(*v) * 0.62
        ax.plot(*p, "o", ms=9.4, mfc=COLOR_LINEA[k], mec="white", mew=1.3, zorder=8)
        ax.annotate(k, p, ha="center", va="center", fontsize=6.4, color="white",
                    fontweight="bold", zorder=9)
        ax.annotate(texto, (p[0] + dx, p[1] + dy), ha=ha, va="center", fontsize=6.4,
                    color=GRIS, zorder=9, linespacing=1.2, path_effects=halo)

    # La referencia de los dos tipos de marcador va en el epígrafe, no sobre el mapa:
    # el único claro de la vista es angosto y el texto no entra sin pisar las líneas.

    ax.set_aspect("equal")
    ax.set_xlim(x0v, x1v)
    ax.set_ylim(y0v, y1v)
    ax.set_axis_off()

    salida = FIGURAS / "red-y-linea-f.png"
    fig.savefig(salida)
    plt.close(fig)
    n_est = sum(len(v[0]) for v in esq.ESTACIONES.values())
    print(f"  {n_est} estaciones en operación + 12 de la Línea F")
    print(f"  -> {salida.relative_to(RAIZ)}")


# ---------------------------------------------------------------------------
# Figura 2 -- perfil de carga por tramo de la Linea F
# ---------------------------------------------------------------------------

# Pasajeros que permanecen a bordo al salir de cada estacion, hora pico manana.
# Columna P de las Tablas 2 y 3 del EsIA (doc 0010, pags. 15-16).
P_A_PALERMO = [5450, 35742, 34080, 34542, 30534, 20829, 11912, 10743, 10503, 8739,
               3132, 0]
P_A_BRANDSEN = [0, 4368, 11014, 13081, 13652, 16378, 17918, 15587, 11906, 10633,
                8248, 4544]

CAPACIDAD = 43_000     # pas./sentido/hora: 40 formaciones x 1.075 pasajeros


def figura_perfil_carga() -> None:
    nombres = [n for _i, n, _p, _c, _d in esq.LINEA_F]

    # Carga del tramo (i, i+1). El servicio a Palermo lleva P(i); el servicio a Brandsen
    # recorre el tramo en sentido inverso y lleva P(i+1) de su propia tabla.
    tramos = list(range(len(nombres) - 1))
    carga_norte = [P_A_PALERMO[i] for i in tramos]
    carga_sur = [P_A_BRANDSEN[i + 1] for i in tramos]

    pico = max(carga_norte)
    i_pico = carga_norte.index(pico)

    fig, ax = plt.subplots(figsize=(6.6, 2.9))

    bordes = list(range(len(nombres)))
    ax.stairs(carga_norte, bordes, baseline=0, fill=True,
              facecolor="#12A0DB", alpha=0.22, edgecolor="#0E7FAE", lw=1.5,
              label="Sentido a Palermo", zorder=2)
    ax.stairs(carga_sur, bordes, baseline=0, fill=False,
              edgecolor="#B03A2E", lw=1.5, ls=(0, (4, 2)),
              label="Sentido a Brandsen", zorder=3)

    ax.axhline(CAPACIDAD, color=TINTA, lw=0.9, ls=(0, (1.5, 1.5)), zorder=4)
    ax.annotate(f"Capacidad de diseño: {CAPACIDAD:,.0f} pas./h".replace(",", "."),
                (0.12, CAPACIDAD), ha="left", va="bottom",
                fontsize=7, color=TINTA)

    ax.annotate(f"{pico:,.0f}".replace(",", ".") + f"  ({pico / CAPACIDAD:.0%})",
                (i_pico + 0.5, pico), (i_pico + 1.35, pico + 3200),
                fontsize=7.2, color="#0E7FAE", ha="left",
                arrowprops=dict(arrowstyle="-", color="#0E7FAE", lw=0.7,
                                shrinkA=0, shrinkB=2))

    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels([f"{i + 1}" for i in range(len(nombres))], fontsize=7)
    ax.set_xlim(0, len(nombres) - 1)
    ax.set_ylim(0, CAPACIDAD * 1.16)
    ax.set_yticks(range(0, 45_000, 10_000))
    ax.set_yticklabels([f"{v // 1000}" for v in range(0, 45_000, 10_000)])
    ax.set_ylabel("Miles de pasajeros por hora")
    ax.set_xlabel("Estación (orden sobre la traza, 1 = Brandsen … 12 = Palermo)")

    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color=GRIS_SUAVE, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=7.2, bbox_to_anchor=(1.0, 0.82))

    salida = FIGURAS / "perfil-carga-linea-f.png"
    fig.savefig(salida)
    plt.close(fig)
    print(f"  pico {pico:,} pas./h en el tramo {i_pico + 1}-{i_pico + 2} "
          f"({nombres[i_pico]}-{nombres[i_pico + 1]}), "
          f"{pico / CAPACIDAD:.1%} de la capacidad")
    print(f"  -> {salida.relative_to(RAIZ)}")


# ---------------------------------------------------------------------------
# Figura 3 -- perfil horario de la demanda de la red actual
# ---------------------------------------------------------------------------

def figura_perfil_horario() -> None:
    cols = ["rango_horario", "modo_etapa", "linea_etapa", "factor_expansion_etapa"]
    df = pd.read_csv(RAW / "etapas_BAdata_20241016.csv", usecols=cols)
    subte = df[df["modo_etapa"] == "SUBTE"]

    por_hora = (subte.groupby("rango_horario")["factor_expansion_etapa"]
                .sum().reindex(range(24), fill_value=0.0))
    total = por_hora.sum()
    print(f"  etapas de subte: {len(subte):,} filas, {total:,.0f} expandidas")

    fig, ax = plt.subplots(figsize=(6.6, 2.6))

    ax.fill_between(por_hora.index, por_hora.values, color="#2A5CAA", alpha=0.16,
                    zorder=2)
    ax.plot(por_hora.index, por_hora.values, color="#2A5CAA", lw=1.6, zorder=3)

    picos = por_hora.nlargest(2).sort_index()
    for hora, valor in picos.items():
        ax.plot(hora, valor, "o", ms=4.5, mfc="white", mec="#2A5CAA", mew=1.3, zorder=4)
        ax.annotate(f"{hora}:00 h\n{valor / 1000:,.1f} mil".replace(".", ","),
                    (hora, valor), (hora, valor + total * 0.014),
                    ha="center", va="bottom", fontsize=7, color="#1B3F7A")

    cuota = picos.max() / total
    # La franja inferior izquierda esta vacia hasta las 5 de la manana: la nota entra
    # ahi sin pisar la curva ni las etiquetas de los dos picos.
    ax.annotate(
        "La hora de máxima\ndemanda concentra\n"
        + f"el {cuota:.1%} del total diario".replace(".", ","),
        (0.5, por_hora.max() * 0.90), ha="left", va="top", fontsize=7,
        color=GRIS, style="italic", linespacing=1.5)

    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h}" for h in range(0, 24, 2)])
    ax.set_xlim(0, 23)
    ax.set_ylim(0, por_hora.max() * 1.28)
    ax.set_yticks(range(0, 80_001, 20_000))
    ax.set_yticklabels([f"{v // 1000}" for v in range(0, 80_001, 20_000)])
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Miles de etapas")

    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color=GRIS_SUAVE, lw=0.5, zorder=0)
    ax.set_axisbelow(True)

    salida = FIGURAS / "perfil-horario-red.png"
    fig.savefig(salida)
    plt.close(fig)
    print("  picos: " + ", ".join(f"{h}:00 h = {v:,.0f}" for h, v in picos.items())
          + f" | concentracion de la hora pico: {cuota:.1%}")
    print(f"  -> {salida.relative_to(RAIZ)}")


def main() -> None:
    estilo()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    print("Figura 1 - esquemático de la red y de la Línea F  [en el documento]")
    figura_esquematico()
    print("Figura 2 - perfil de carga por tramo de la Línea F (HPM)")
    figura_perfil_carga()
    print("Figura 3 - perfil horario de la demanda de la red actual")
    figura_perfil_horario()


if __name__ == "__main__":
    main()
