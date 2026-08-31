"""Lectura de los CSV anuales de formaciones despachadas.

El dataset "Subte: Trenes despachados" se publica en un recurso por anio. El
recurso "Formaciones despachadas - Total", que es el que veniamos
usando, **esta congelado**: su metadato dice
last_modified=2019-06-04 y su contenido termina el 22/10/2021, ademas de no tener
2016, 2017 ni 2018. Para el periodo que el trabajo necesita hay que usar los
recursos por anio.

El esquema cambio entre uno y otro. El archivo Total trae nombres tipo
`fr1_salc1` y causas codificadas en una o dos letras; los anuales de 2025 y 2026
traen nombres legibles, causas en texto y (sobre todo) una columna **`Tipo Dia`
con el valor `Feriado`**, que es el calendario operativo del propio operador.

Particularidades del formato, verificadas sobre los archivos de 2025 y 2026 el
18/08/2026:

1. Separador `;`. La columna de coches del lado D se llama `Cantidad  coches D`,
   con dos espacios. Se normalizan los nombres colapsando espacios.
2. La codificacion cambia por anio y cada archivo es internamente consistente:
   2025 es Latin-1 sin BOM y 2026 es UTF-8 con BOM. Se prueba UTF-8 estricto y se
   cae a Latin-1.
3. **Tres formatos de fecha conviven en el archivo de 2025**: `d/m/aaaa`,
   `dd/mm/aa` y vacio. El componente de dia llega a 31 en los dos formatos con
   datos, asi que ninguno es ambiguo: los dos son dia primero. El corte entre
   formatos es cercano al 03/04/2025 pero **no es igual para todas las lineas**,
   y hay dos pares (fecha, linea) presentes en los dos formatos que resultaron
   ser partes distintas del mismo dia, no duplicados: se verifico que los numeros
   de orden no se solapan.
4. Las filas de fecha vacia estan **completamente vacias** en las veinte
   columnas. Son relleno: se descartan.
5. Un despacho puede salir de una cabecera, de la otra o de las dos. `Tipo Viaje
   A` y `Tipo Viaje D` valen S cuando el viaje se hizo. Todo `S` tiene hora de
   salida; hay ademas registros con `N` y hora cargada, que son servicios
   programados que no se prestaron.
6. Las causas vienen en texto con espacios de relleno: "Falta de custodia
   policial" aparece como dos valores distintos si no se recortan.

Este modulo no corrige nada en silencio: devuelve los datos normalizados y deja
los contadores de lo descartado en `ResultadoLectura`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / "data" / "raw"

# Las dos cabeceras de cada linea, del recurso cabeceras-estaciones.csv. Se usan
# solo para rotular: el dataset identifica los extremos como A y D.
CABECERAS = CRUDO / "cabeceras-estaciones.csv"

RE_HORA = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$")


@dataclass
class ResultadoLectura:
    """Contadores de control de una pasada sobre un CSV anual."""

    archivo: str = ""
    codificacion: str = ""
    filas_crudas: int = 0
    filas_vacias: int = 0
    filas: int = 0
    fecha_invalida: int = 0
    formatos_fecha: dict = field(default_factory=dict)

    def resumen(self) -> str:
        f = ", ".join(f"{k}: {v:,}" for k, v in sorted(self.formatos_fecha.items()))
        return (
            f"{self.archivo} en {self.codificacion}, {self.filas_crudas:,} filas "
            f"crudas, {self.filas_vacias:,} vacias descartadas, {self.filas:,} "
            f"utiles, {self.fecha_invalida:,} con fecha invalida. "
            f"Formatos de fecha -> {f}"
        )


def _leer_texto(ruta: Path) -> tuple[str, str]:
    """Devuelve (texto, codificacion). Prueba UTF-8 estricto y cae a Latin-1."""
    crudo = ruta.read_bytes()
    try:
        return crudo.decode("utf-8-sig"), "UTF-8"
    except UnicodeDecodeError:
        return crudo.decode("latin-1"), "Latin-1"


def a_segundos(hora: str) -> int | None:
    """Hora del dia a segundos desde medianoche. Devuelve None si no es hora."""
    if hora is None or (isinstance(hora, float) and pd.isna(hora)):
        return None
    m = RE_HORA.match(str(hora))
    if not m:
        return None
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if h > 23 or mi > 59 or s > 59:
        return None
    return h * 3600 + mi * 60 + s


def _parsear_fechas(serie: pd.Series, res: ResultadoLectura) -> pd.Series:
    """Parsea las tres variantes de fecha, contando cada una."""
    partes = serie.str.split("/")
    largo_anio = partes.str[2].str.len()
    res.formatos_fecha = {
        ("d/m/aaaa" if n == 4 else "dd/mm/aa" if n == 2 else f"anio de {n}"): int(c)
        for n, c in largo_anio.value_counts().items()
    }
    fuera = pd.to_datetime(serie, format="mixed", dayfirst=True, errors="coerce")
    res.fecha_invalida = int(fuera.isna().sum())
    return fuera


def leer(anio: int, res: ResultadoLectura | None = None) -> pd.DataFrame:
    """Lee un CSV anual de formaciones despachadas, ya normalizado.

    Devuelve una fila por despacho con columnas:
      fecha, linea, tipo_dia, registro, orden, tren,
      formacion_A/D, modelo_A/D, causa_A/D, coches_A/D, km_A/D,
      viajo_A/D (bool), salida_A/D (segundos desde medianoche)
    """
    r = res if res is not None else ResultadoLectura()
    ruta = CRUDO / f"formaciones-despachadas-{anio}.csv"
    texto, cod = _leer_texto(ruta)
    r.archivo, r.codificacion = ruta.name, cod

    from io import StringIO

    d = pd.read_csv(StringIO(texto), sep=";", dtype=str)
    d.columns = [re.sub(r"\s+", " ", c).strip() for c in d.columns]
    r.filas_crudas = len(d)

    vacias = d.isna().all(axis=1) | d.Fecha.isna()
    r.filas_vacias = int(vacias.sum())
    d = d[~vacias].copy()

    d["fecha"] = _parsear_fechas(d.Fecha, r)
    d = d[d.fecha.notna()].copy()
    r.filas = len(d)

    ren = {
        "Linea": "linea", "Tipo Dia": "tipo_dia", "Tipo Día": "tipo_dia",
        "Registro": "registro", "Orden": "orden", "Tren": "tren",
    }
    d = d.rename(columns={k: v for k, v in ren.items() if k in d.columns})
    for lado in ("A", "D"):
        d[f"formacion_{lado}"] = d.get(f"Formación {lado}", d.get(f"Formacion {lado}"))
        d[f"modelo_{lado}"] = d[f"Modelo {lado}"]
        # las causas traen relleno de espacios: sin recortar, el mismo texto
        # aparece como dos categorias distintas
        d[f"causa_{lado}"] = (
            d[f"Causa {lado}"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
        )
        d[f"coches_{lado}"] = pd.to_numeric(
            d[f"Cantidad coches {lado}"], errors="coerce"
        )
        d[f"km_{lado}"] = pd.to_numeric(d[f"Km {lado}"], errors="coerce")
        d[f"viajo_{lado}"] = d[f"Tipo Viaje {lado}"].fillna("").str.strip().eq("S")
        d[f"salida_{lado}"] = d[f"Hora sale {lado}"].map(a_segundos)

    columnas = ["fecha", "linea", "tipo_dia", "registro", "orden", "tren"] + [
        f"{c}_{l}"
        for c in ("formacion", "modelo", "causa", "coches", "km", "viajo", "salida")
        for l in ("A", "D")
    ]
    d = d[[c for c in columnas if c in d.columns]]
    d["linea"] = d.linea.str.strip()
    d["tipo_dia"] = d.tipo_dia.str.strip()
    if res is None:
        print(r.resumen())
    return d.reset_index(drop=True)


def cabeceras() -> pd.DataFrame:
    """Las dos cabeceras declaradas de cada linea."""
    c = pd.read_csv(CABECERAS, sep=";", dtype=str, encoding="latin-1")
    c.columns = [re.sub(r"\s+", "_", x.strip().lower()) for x in c.columns]
    return c
