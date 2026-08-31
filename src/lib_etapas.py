"""Lectura del dataset de Viajes y Etapas del AMBA, acotada a las etapas de subte.

`etapas_BAdata_20241016.csv` pesa 1,2 GB y solo el 6,8 % de sus filas son de
subte, asi que cargarlo entero en memoria no tiene sentido. Este modulo lo lee
en streaming una sola vez y deja un intermedio chico en `data/processed/`.

El sufijo `20241016` del nombre es la fecha del dia relevado, el 16 de octubre
de 2024, no la fecha de publicacion: el dataset describe un unico dia habil
tipico, no un promedio anual.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "raw" / "etapas_BAdata_20241016.csv"
INTERMEDIO = RAIZ / "data" / "processed" / "etapas_subte.csv"

# Columnas que el paso 5 consume. El resto (id_tarjeta, genero, grupo_edad,
# departamentos) no interviene en la matriz O-D y solo agrandaria el intermedio.
COLUMNAS = [
    "id_viaje",
    "id_etapa",
    "rango_horario",
    "linea_etapa",
    "longitud_origen_etapa",
    "latitud_origen_etapa",
    "longitud_destino_etapa",
    "latitud_destino_etapa",
    "factor_expansion_etapa",
    "viaje_incompleto",
]


def extraer(forzar: bool = False) -> Path:
    """Filtra las etapas de subte del CSV crudo y las deja en el intermedio.

    Devuelve la ruta del intermedio. Si ya existe y `forzar` es falso, no
    vuelve a leer el archivo grande.
    """
    if INTERMEDIO.exists() and not forzar:
        return INTERMEDIO

    INTERMEDIO.parent.mkdir(parents=True, exist_ok=True)
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

    leidas = escritas = 0
    with open(CRUDO, encoding="utf-8", newline="") as f_in:
        lector = csv.DictReader(f_in)
        faltan = [c for c in COLUMNAS if c not in lector.fieldnames]
        if faltan:
            raise ValueError(f"faltan columnas en el crudo: {faltan}")

        with open(INTERMEDIO, "w", encoding="utf-8", newline="") as f_out:
            escritor = csv.DictWriter(f_out, fieldnames=COLUMNAS, extrasaction="ignore")
            escritor.writeheader()
            for fila in lector:
                leidas += 1
                if fila["modo_etapa"] == "SUBTE":
                    escritor.writerow(fila)
                    escritas += 1

    print(f"leidas {leidas:,} filas; escritas {escritas:,} etapas de subte")
    return INTERMEDIO


if __name__ == "__main__":
    extraer(forzar="--forzar" in sys.argv)
