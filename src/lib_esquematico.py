"""Geometría del esquemático de la red de Subte, y ubicación de la Línea F sobre él.

De dónde sale cada cosa:

* **Trazado de las seis líneas en operación.** Extraído del *Mapa de red* oficial de
  SBASE (`docs/Esquemático 2025_148x112,6cm_web.png`, 17.481 x 13.300 px) por
  clasificación de color, cierre morfológico, trazado del camino de diámetro sobre el
  grafo de la máscara y simplificación Ramer--Douglas--Peucker. El procedimiento está
  en el historial del proyecto; acá quedan las polilíneas ya resueltas, en píxeles de
  la imagen a un cuarto de escala, para que la figura no dependa del PNG.

* **Orden y espaciado de las estaciones.** Del feed GTFS oficial: secuencia de paradas
  y `shape_dist_traveled` de `stop_times.txt`. Cada estación se ubica sobre la
  polilínea en la fracción de recorrido que le corresponde, de modo que el espaciado
  refleja las distancias reales entre estaciones y no un reparto uniforme.

* **Línea F.** El orden de las doce estaciones y sus progresivas salen de la Tabla 4
  del EsIA (doc 0010, págs. 20--21). Las seis combinaciones declaradas fijan seis
  puntos de la traza sobre la red existente; las otras seis estaciones se interpolan
  por progresiva. El tramo Pizzurno--Palermo corre en paralelo a la Línea D, que es la
  relación real entre ambos corredores.

**Es un diagrama topológico.** No está a escala y las orientaciones son esquemáticas.
"""

from __future__ import annotations

import numpy as np

# --- trazado de cada línea, en píxeles de la imagen oficial (y hacia abajo) --------
# El primer vértice es la cabecera que el GTFS enumera primero.
TRAZAS_PX = {
    "A": [(3874, 1524), (3292, 1554), (1956, 1554), (1913, 1569), (1064, 2420),
          (943, 2481)],
    "B": [(3889, 1235), (2412, 1215), (2044, 952), (676, 924)],
    "C": [(3896, 743), (3769, 836), (3650, 1002), (3590, 1321), (3522, 1386),
          (3478, 1506), (3499, 2634)],
    "D": [(3768, 1496), (3484, 1260), (3480, 1213), (3261, 1050), (2812, 876),
          (2436, 595), (887, 567)],
    "E": [(3897, 821), (3812, 884), (3804, 1260), (3706, 1476), (3707, 1558),
          (3526, 1796), (3475, 1797), (3411, 1948), (3372, 2164), (3340, 2196),
          (2180, 2220), (1880, 2248), (1577, 2481), (1401, 2657), (1384, 2732),
          (1425, 2832)],
    "H": [(3400, 255), (2962, 754), (2902, 872), (2902, 2732), (2876, 2765),
          (2743, 2799), (2638, 2782)],
}

# --- estaciones por línea: nombre y fracción de recorrido, del GTFS ---------------
ESTACIONES = {
    "A": (["Plaza de Mayo", "Perú", "Piedras", "Lima", "Sáenz Peña", "Congreso",
           "Alberti", "Plaza Miserere", "Loria", "Castro Barros", "Río de Janeiro",
           "Acoyte", "Primera Junta", "Puan", "Carabobo", "San José de Flores",
           "San Pedrito"],
          [0.0, .0291, .0675, .1059, .1454, .2035, .2804, .3385, .4206, .4849,
           .567, .6376, .6978, .7767, .8536, .9315, 1.0]),
    "B": (["Leandro N. Alem", "Florida", "Carlos Pellegrini", "Uruguay", "Callao",
           "Pasteur", "Pueyrredón", "Carlos Gardel", "Medrano", "Ángel Gallardo",
           "Malabia", "Dorrego", "Federico Lacroze", "Tronador", "De los Incas",
           "Echeverría", "Juan Manuel de Rosas"],
          [0.0, .034, .0875, .1325, .1776, .2285, .2744, .3254, .401, .4766,
           .5523, .6449, .7094, .8054, .8658, .9397, 1.0]),
    "C": (["Retiro", "General San Martín", "Lavalle", "Diagonal Norte",
           "Avenida de Mayo", "Moreno", "Independencia", "San Juan", "Constitución"],
          [0.0, .0965, .2847, .3812, .5129, .6024, .7506, .8706, 1.0]),
    "D": (["Catedral", "9 de Julio", "Tribunales", "Callao", "Facultad de Medicina",
           "Pueyrredón", "Agüero", "Bulnes", "Scalabrini Ortiz", "Plaza Italia",
           "Palermo", "Ministro Carranza", "Olleros", "José Hernández", "Juramento",
           "Congreso de Tucumán"],
          [0.0, .0651, .1118, .1905, .2362, .3168, .3673, .4198, .4723, .5316,
           .5879, .6744, .7755, .8562, .9135, 1.0]),
    "E": (["Retiro", "Catalinas", "Correo Central", "Bolívar", "Belgrano",
           "Independencia", "San José", "Entre Ríos", "Pichincha", "Jujuy",
           "General Urquiza", "Boedo", "La Plata", "José María Moreno",
           "Emilio Mitre", "Medalla Milagrosa", "Varela", "Plaza de los Virreyes"],
          [0.0, .0418, .1119, .1896, .2664, .3356, .4065, .462, .5158, .5611,
           .6055, .6533, .7148, .766, .8147, .8839, .9471, 1.0]),
    "H": (["Facultad de Derecho", "Las Heras", "Santa Fe", "Córdoba", "Corrientes",
           "Once", "Venezuela", "Humberto 1", "Inclán", "Caseros", "Parque Patricios",
           "Hospitales"],
          [0.0, .0857, .2008, .257, .3325, .4079, .4949, .6113, .7008, .7877,
           .899, 1.0]),
}

# Combinaciones entre líneas en operación, para marcar dónde se resuelven hoy los
# transbordos. Se nombran por (línea, estación) de una de las dos partes.
COMBINACIONES_ACTUALES = [
    ("H", "Santa Fe"), ("H", "Corrientes"), ("H", "Once"), ("H", "Humberto 1"),
    ("C", "Diagonal Norte"), ("C", "Avenida de Mayo"), ("C", "Independencia"),
    ("C", "Retiro"), ("D", "9 de Julio"), ("A", "Lima"), ("B", "Pueyrredón"),
    ("D", "Pueyrredón"), ("E", "Bolívar"), ("B", "Carlos Pellegrini"),
    ("A", "Perú"), ("E", "Independencia"), ("E", "Retiro"),
]

# --- Línea F ----------------------------------------------------------------------
# Progresiva del centro de andén, en metros sobre la traza (EsIA doc 0010, Tabla 4).
#
# La combinación indica con qué estación de la red actual empalma. El último campo
# distingue la procedencia: True si el EsIA la declara estación por estación (son
# seis), False si solo aparece en el mapa oficial del proyecto que publicó el GCBA
# (son dos más: la Línea H en Pueyrredón y la Línea D en Plaza Italia). De ahí sale
# la cifra de ocho estaciones de combinación que citan los anuncios y que el
# expediente ambiental no respalda.
LINEA_F = [
    ( 1, "Brandsen",      393, None,                    False),
    ( 2, "Constitución", 1521, ("C", "Constitución"),   True),
    ( 3, "Cochabamba",   3107, ("E", "Entre Ríos"),     True),
    ( 4, "Chile",        3714, None,                    False),
    ( 5, "Congreso",     4501, ("A", "Congreso"),       True),
    ( 6, "Corrientes",   5306, ("B", "Callao"),         True),
    ( 7, "Pizzurno",     5950, ("D", "Callao"),         True),
    ( 8, "Junín",        6850, None,                    False),
    ( 9, "Pueyrredón",   7508, None,                    False),
    (10, "P. Las Heras", 8425, None,                    False),
    (11, "Plaza Italia", 9535, ("D", "Plaza Italia"),   False),
    (12, "Palermo",     10400, ("D", "Palermo"),        True),
]

# Las cuatro radiales que la F cruza se atraviesan sobre una misma vertical: la traza
# real corre por una sola avenida (Entre Ríos, que al norte de Rivadavia es Callao).
# El esquemático oficial no las alinea porque reparte las estaciones para acomodar los
# rótulos, así que se corrige fijando esas cuatro estaciones sobre la vertical de la F
# y redistribuyendo el resto de cada línea de forma monótona.
X_F_PX = 3242.0


def _arco(P: np.ndarray) -> np.ndarray:
    return np.r_[0.0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]


def _punto(P: np.ndarray, f: float) -> tuple[float, float]:
    d = _arco(P)
    s = f * d[-1]
    return float(np.interp(s, d, P[:, 0])), float(np.interp(s, d, P[:, 1]))


def _fraccion_en_x(P: np.ndarray, x: float) -> float:
    """Fracción de recorrido donde la polilínea cruza la vertical x."""
    d = _arco(P)
    for i in range(len(P) - 1):
        x0, x1 = P[i, 0], P[i + 1, 0]
        if (x0 - x) * (x1 - x) <= 0 and x0 != x1:
            t = (x - x0) / (x1 - x0)
            return float((d[i] + t * (d[i + 1] - d[i])) / d[-1])
    raise ValueError("la traza no cruza esa vertical")


def _desplazar(P: np.ndarray, d: float) -> np.ndarray:
    """Paralela a la polilínea, desplazada d hacia el lado de x creciente."""
    seg = np.diff(P, axis=0)
    t = seg / np.hypot(seg[:, 0], seg[:, 1])[:, None]
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    v = np.zeros_like(P)
    v[0], v[-1] = nrm[0], nrm[-1]
    v[1:-1] = nrm[:-1] + nrm[1:]
    v /= np.hypot(v[:, 0], v[:, 1])[:, None]
    if v[:, 0].mean() < 0:          # el lado correcto es el de x creciente
        v = -v
    return P + d * v


def construir(escala: float = 100.0) -> dict:
    """Devuelve trazas, estaciones y Línea F en coordenadas de figura (y hacia arriba)."""
    def T(P):
        A = np.asarray(P, float)
        return np.stack([A[:, 0] / escala, -A[:, 1] / escala], 1)

    trazas = {k: T(v) for k, v in TRAZAS_PX.items()}
    x_f = X_F_PX / escala

    # Las cuatro radiales que la F atraviesa de lado a lado se fijan sobre su vertical.
    # Las que empalma en el extremo del corredor (C en Constitución, H en Pueyrredón,
    # D en Plaza Italia y en Palermo) no se tocan: ahí la F llega hasta la estación.
    fijar = {"E": "Entre Ríos", "A": "Congreso", "B": "Callao", "D": "Callao"}

    pos, fracs = {}, {}
    for k, (nombres, f) in ESTACIONES.items():
        f = np.array(f, float)
        if k in fijar:
            i = nombres.index(fijar[k])
            objetivo = _fraccion_en_x(trazas[k], x_f)
            f = np.where(f <= f[i], f * (objetivo / f[i]),
                         objetivo + (f - f[i]) * (1 - objetivo) / (1 - f[i]))
        fracs[k] = f
        pos[k] = {n: _punto(trazas[k], t) for n, t in zip(nombres, f)}

    # --- traza de la Línea F ------------------------------------------------------
    p_const = np.array(pos["C"]["Constitución"])
    p_cocha = np.array(pos["E"]["Entre Ríos"])
    p_pizz = np.array(pos["D"]["Callao"])
    p_paler = np.array(pos["D"]["Palermo"])

    # Sur: Constitución baja hacia Barracas a 45°, a la distancia que dan las
    # progresivas (1.128 m entre Brandsen y Constitución sobre 1.586 m entre
    # Constitución y Cochabamba, que en el diagrama mide |p_cocha - p_const|).
    largo_2_3 = float(np.hypot(*(p_cocha - p_const)))
    paso = largo_2_3 * (1521 - 393) / (3107 - 1521) / np.sqrt(2)
    p_brand = p_const + np.array([paso, -paso])

    # Codo entre Constitución y la vertical de la F, a 45°.
    dx = p_const[0] - x_f
    p_codo = np.array([x_f, p_const[1] + dx])

    # Norte: la F deja la vertical en Pizzurno y va empalmando, una tras otra, las
    # estaciones con las que combina: la H en Pueyrredón, y la D en Plaza Italia y en
    # Palermo. Ese encadenamiento define por sí solo la forma del corredor.
    # Ojo: NO se ancla en la Est. Las Heras de la H. El esquemático oficial empuja el
    # extremo norte de esa línea hacia el nordeste para acomodar su cabecera, y anclar
    # ahí manda al corredor a dar un rodeo que no existe. La proximidad entre ambas
    # queda como cruce, sin marcar.
    arm = np.array([[x_f, p_pizz[1]], pos["D"]["Plaza Italia"], p_paler], float)

    traza_f = np.vstack([p_brand, p_const, p_codo, arm])

    # --- las doce estaciones sobre esa traza --------------------------------------
    anclas = {2: p_const, 3: p_cocha, 5: np.array(pos["A"]["Congreso"]),
              6: np.array(pos["B"]["Callao"]), 7: p_pizz,
              11: np.array(pos["D"]["Plaza Italia"]), 12: p_paler}
    # Los tramos rectos no tienen vertices intermedios, asi que hay que densificar
    # antes de proyectar: si no, cada ancla cae sobre un extremo del tramo.
    df0 = _arco(traza_f)
    ss = np.arange(0.0, df0[-1], 0.02)
    denso = np.stack([np.interp(ss, df0, traza_f[:, 0]),
                      np.interp(ss, df0, traza_f[:, 1])], 1)
    df = _arco(traza_f)
    s_ancla = {}
    for n, p in anclas.items():
        j = int(np.argmin(np.hypot(*(denso - p).T)))
        s_ancla[n] = float(ss[j])
    s_ancla[1] = 0.0

    estaciones_f = []
    prog = {n: p for n, _nm, p, _c, _d in LINEA_F}
    for n, nombre, p, comb, declarada in LINEA_F:
        if n in s_ancla:
            s = s_ancla[n]
        else:                                    # interpolar por progresiva
            antes = max(k for k in s_ancla if k < n)
            desp = min(k for k in s_ancla if k > n)
            u = (p - prog[antes]) / (prog[desp] - prog[antes])
            s = s_ancla[antes] + u * (s_ancla[desp] - s_ancla[antes])
        x = float(np.interp(s, df, traza_f[:, 0]))
        y = float(np.interp(s, df, traza_f[:, 1]))
        estaciones_f.append((n, nombre, (x, y), comb, declarada))

    return {"trazas": trazas, "pos": pos, "traza_f": traza_f,
            "estaciones_f": estaciones_f}
