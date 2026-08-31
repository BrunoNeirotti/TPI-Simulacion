"""Lectura de los ZIP anuales de molinetes.

El dataset "Subte: Viajes Molinetes" se publica en ZIP anuales de varios millones
de filas, por lo que todo el modulo trabaja en streaming: nunca se carga un anio
completo en memoria.

Particularidades del formato, verificadas sobre molinetes-2025.zip el 05/08/2026:

1. Cada registro viene envuelto en comillas dobles con ';' como separador interno.
2. Conviven DOS variantes en el mismo ZIP. Unos archivos agregan nueve campos
   vacios de cola ('...;2";;;;;;;;;') y otros no ('...;2"'). Un parser que
   contemple solo la primera variante descarta en silencio el pax_TOTAL de la
   segunda, porque el ultimo campo queda como '2"' y falla la conversion a int.
3. El separador decimal no aparece: los cuatro campos de pasajeros son enteros.
4. La codificacion no es uniforme. Algunos archivos son UTF-8 y otros Latin-1;
   decodificar todo como UTF-8 con errors='replace' corrompe las enies y parte
   estaciones como "Saenz Pena" en dos nombres distintos. Se prueba UTF-8 y se
   cae a Latin-1.
5. FECHA mezcla dos convenciones. Todos los archivos son d/m/Y salvo los DOS de
   agosto de 2025, donde conviven d/m/Y y m/d/Y dentro del mismo archivo y para
   los mismos dias. Es recuperable sin perdida porque el mes lo fija el nombre
   del archivo: se verifico que ningun registro de esos archivos cae fuera de
   agosto. La regla es tomar como dia el componente que no coincide con el mes.
"""

from __future__ import annotations

import datetime as dt
import re
import zipfile
from dataclasses import dataclass

COLUMNAS = [
    "FECHA", "DESDE", "HASTA", "LINEA", "MOLINETE", "ESTACION",
    "pax_pagos", "pax_pases_pagos", "pax_franq", "pax_TOTAL",
]
N_COLUMNAS = len(COLUMNAS)


@dataclass
class ResultadoLectura:
    """Contadores de control de una pasada sobre un ZIP anual."""

    archivos: int = 0
    filas: int = 0
    filas_descartadas: int = 0
    pax_no_numerico: int = 0
    fecha_invalida: int = 0
    archivos_latin1: int = 0
    fecha_mdY: int = 0

    def resumen(self) -> str:
        return (
            f"{self.archivos} archivos, {self.filas:,} filas, "
            f"{self.filas_descartadas:,} descartadas, "
            f"{self.pax_no_numerico:,} con pax no numerico, "
            f"{self.fecha_invalida:,} con fecha invalida, "
            f"{self.fecha_mdY:,} en formato m/d/Y, "
            f"{self.archivos_latin1} archivos Latin-1"
        )


def _desenvolver(linea: str) -> str:
    """Devuelve el registro sin las comillas envolventes ni los campos de cola."""
    s = linea.rstrip("\r\n").rstrip(";")
    if s.startswith('"'):
        s = s[1:]
    if s.endswith('"'):
        s = s[:-1]
    return s


def _decodificar(bruto: bytes) -> tuple[str, bool]:
    """Decodifica una linea probando UTF-8 y cayendo a Latin-1."""
    try:
        return bruto.decode("utf-8-sig"), False
    except UnicodeDecodeError:
        return bruto.decode("latin-1"), True


def _mes_del_archivo(nombre: str) -> tuple[int, int] | None:
    """Extrae (anio, mes) del prefijo AAAAMM del nombre de archivo."""
    m = re.match(r"(\d{4})(\d{2})", nombre)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def parsear_fecha(texto: str, anio_mes: tuple[int, int] | None) -> dt.date | None:
    """Convierte FECHA a date resolviendo la ambiguedad d/m vs m/d.

    Si se conoce el mes del archivo, el dia es el componente que no coincide con
    ese mes; asi los dos formatos que conviven en agosto de 2025 colapsan al
    mismo dia. Sin esa referencia se asume d/m/Y, que es el formato del resto.
    """
    partes = texto.split("/")
    if len(partes) != 3:
        return None
    try:
        a, b, anio = int(partes[0]), int(partes[1]), int(partes[2])
    except ValueError:
        return None
    if anio_mes is not None:
        _, mes = anio_mes
        if b == mes:
            dia = a
        elif a == mes:
            dia = b
        else:
            return None
    else:
        dia, mes = a, b
    try:
        return dt.date(anio, mes, dia)
    except ValueError:
        return None


def leer_zip(ruta_zip: str, resultado: ResultadoLectura | None = None):
    """Itera los registros de un ZIP anual como dict, sin cargarlo en memoria.

    Se saltea la fila de encabezado de cada archivo y se descartan las filas que
    no tengan exactamente diez campos. Los contadores quedan en `resultado`.
    """
    res = resultado if resultado is not None else ResultadoLectura()
    with zipfile.ZipFile(ruta_zip) as z:
        for nombre in sorted(n for n in z.namelist() if n.lower().endswith(".csv")):
            res.archivos += 1
            corto = nombre.rsplit("/", 1)[-1]
            anio_mes = _mes_del_archivo(corto)
            latin1_en_archivo = False
            with z.open(nombre) as f:
                for i, cruda in enumerate(f):
                    texto, fue_latin1 = _decodificar(cruda)
                    latin1_en_archivo = latin1_en_archivo or fue_latin1
                    s = _desenvolver(texto)
                    if i == 0 or not s.strip(";"):
                        continue
                    partes = s.split(";")
                    if len(partes) != N_COLUMNAS:
                        res.filas_descartadas += 1
                        continue
                    res.filas += 1
                    reg = dict(zip(COLUMNAS, partes))
                    reg["_archivo"] = corto
                    for c in COLUMNAS[6:]:
                        try:
                            reg[c] = int(reg[c])
                        except ValueError:
                            reg[c] = 0
                            if c == "pax_TOTAL":
                                res.pax_no_numerico += 1
                    reg["_fecha"] = parsear_fecha(reg["FECHA"], anio_mes)
                    if reg["_fecha"] is None:
                        res.fecha_invalida += 1
                    elif anio_mes is not None:
                        primero = reg["FECHA"].split("/")[0]
                        if primero.isdigit() and int(primero) == anio_mes[1] and reg["_fecha"].day != anio_mes[1]:
                            res.fecha_mdY += 1
                    yield reg
            if latin1_en_archivo:
                res.archivos_latin1 += 1
    if resultado is None:
        print(res.resumen())
