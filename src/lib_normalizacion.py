"""Normalizacion de nombres de estacion e identificadores de molinete.

El criterio es que todo cruce sea deterministico y auditable. La normalizacion
solo hace transformaciones tipograficas (acentos, mayusculas, puntuacion,
espacios). Las equivalencias que no se resuelven asi van en ALIAS, una tabla
explicita: cada entrada es una decision tomada, no una coincidencia difusa.
"""

from __future__ import annotations

import re
import unicodedata

# Sufijos de linea que el dataset de molinetes agrega al nombre para desambiguar
# los complejos de combinacion (Callao.B / Callao.D, Pueyrredon.B / Pueyrredon.D).
_SUFIJO_LINEA = re.compile(r"[ .]([ABCDEH])$")

# Valores centinela que el dataset usa en lugar de dejar el campo vacio.
CENTINELAS = {"", "NULL", "#N/D", "#N/A", "NA", "S/D", "PRUEBA"}


def normalizar(texto: str) -> str:
    """Mayusculas sin acentos, sin puntuacion y con espacios colapsados."""
    if texto is None:
        return ""
    s = unicodedata.normalize("NFD", str(texto))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.upper()
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def quitar_sufijo_linea(nombre: str, linea: str) -> tuple[str, str | None]:
    """Separa el sufijo de linea del nombre de estacion.

    Devuelve (nombre_sin_sufijo, sufijo). El sufijo se devuelve tal cual para
    poder reportar los casos en que no coincide con la linea del registro, que
    son errores de carga del publicador y no equivalencias.
    """
    m = _SUFIJO_LINEA.search(nombre.rstrip())
    if not m:
        return nombre.strip(), None
    return nombre.rstrip()[: m.start()].strip(), m.group(1)


def clave(nombre: str, linea: str) -> str:
    """Clave de cruce: nombre normalizado, sin sufijo de linea y sin alias."""
    base, _ = quitar_sufijo_linea(nombre, linea)
    n = normalizar(base)
    return ALIAS.get((linea, n), ALIAS.get(("*", n), n))


# ---------------------------------------------------------------------------
# Tabla de equivalencias. Clave: (linea o '*', nombre normalizado en molinetes).
# Valor: nombre normalizado tal como aparece en stops.txt del GTFS.
#
# Cada entrada se justifica por evidencia, no por parecido tipografico. Las que
# llevan comentario son las que no son una simple abreviatura.
# ---------------------------------------------------------------------------
ALIAS: dict[tuple[str, str], str] = {
    # --- Molinetes usa la forma corta; el GTFS, la denominacion completa ---
    ("LineaA", "FLORES"): "SAN JOSE DE FLORES",
    ("LineaB", "ROSAS"): "JUAN MANUEL DE ROSAS",
    ("LineaB", "LOS INCAS"): "DE LOS INCAS PARQUE CHAS",
    ("LineaB", "TRONADOR"): "TRONADOR VILLA ORTUZAR",
    ("LineaE", "PZA DE LOS VIRREYES"): "PLAZA DE LOS VIRREYES",
    ("LineaH", "PATRICIOS"): "PARQUE PATRICIOS",

    # --- Al reves: molinetes usa la forma larga y el GTFS la corta ---
    ("LineaC", "MARIANO MORENO"): "MORENO",
    ("LineaE", "GENERAL BELGRANO"): "BELGRANO",
    ("LineaE", "AVENIDA LA PLATA"): "LA PLATA",

    # --- Discrepancias de denominacion entre ambas fuentes ---
    ("LineaE", "URQUIZA"): "GENERAL URQUIZA",
    # El GTFS escribe el ordinal con digito ("Humberto 1") y molinetes con
    # numeral romano ("Humberto I"); la normalizacion no puede unificarlos.
    ("LineaH", "HUMBERTO I"): "HUMBERTO 1",

    # --- Error de carga del publicador, no equivalencia ---
    # "Independencia.H" aparece bajo LineaE con los molinetes LineaE_Indepen_*.
    # La Linea H no tiene estacion Independencia: el sufijo esta equivocado y
    # son los molinetes de la Linea E. Ver reports/01_tabla_maestra.md.
    ("LineaE", "INDEPENDENCIA H"): "INDEPENDENCIA",
}
