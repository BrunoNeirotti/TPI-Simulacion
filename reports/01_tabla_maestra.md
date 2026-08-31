# Paso 1 — Tabla maestra de estaciones

Generado por `src/01_tabla_maestra_estaciones.py`. Fuente de demanda: `molinetes-2025.zip`. Fuente de topologia: GTFS.

## Control de lectura

- 26 archivos, 13,196,766 filas, 0 descartadas, 0 con pax no numerico, 0 con fecha invalida, 443,923 en formato m/d/Y, 3 archivos Latin-1

- Total de pasajeros leidos: **206,616,377**

- Pasajeros en registros utilizables (sin Premetro ni centinelas): **206,459,032**


## Resultado del cruce

- Estaciones del GTFS (subte, sin Premetro): **90**

- Estaciones con demanda asignada: **90**

- Nombres de molinetes sin correspondencia: **5**

- Estaciones del GTFS sin ningun molinete: **0**


### Nombres de molinetes sin correspondencia en el GTFS

| Linea | Nombre en molinetes | Clave normalizada | Molinetes | Pasajeros |
|---|---|---|---:|---:|
| LineaB | `Loria` | `LORIA` | 1 | 33 |
| LineaH | `Loria` | `LORIA` | 1 | 18 |
| LineaD | `Loria` | `LORIA` | 1 | 14 |
| LineaE | `Loria` | `LORIA` | 1 | 12 |
| LineaC | `Loria` | `LORIA` | 1 | 3 |

## Registros centinela descartados

| Linea | Estacion | Molinete | Registros | Pasajeros |
|---|---|---|---:|---:|
| LineaH | `#N/D` | `LineaH_Validador_Central_Turn01` | 6 | 8 |
| Prueba | `Prueba` | `Prueba` | 1 | 1 |
| LineaH | `NULL` | `LineaH_Validador_Central_Turn01` | 1 | 1 |

## Sufijo de linea incoherente con el campo LINEA

| Linea | Estacion | Sufijo | Molinetes | Pasajeros |
|---|---|---|---:|---:|
| LineaE | `Independencia.H` | `.H` | 5 | 1,522,600 |

## Atribucion de la demanda a un anden

El identificador de molinete codifica el anden, lo que en principio permitiria demanda por anden y no solo por estacion. La cobertura real es parcial:

| Situacion | Molinetes | Pasajeros | % del total |
|---|---:|---:|---:|
| Sentido de circulacion identificable | 494 | 145,556,349 | 70.5\% |
| Zona de vestibulo, sin sentido (HALL, C, Aliv) | 11 | 2,598,815 | 1.3\% |
| Identificador sin campo de anden | 158 | 55,713,076 | 27.0\% |
| Sin identificador de molinete | 93 | 2,590,792 | 1.3\% |

**Solo el 70.5\% de la demanda es atribuible a un anden por sentido de circulacion.**


| Sentido | Molinetes | Pasajeros |
|---|---:|---:|
| (sin dato) | 137 | 58,303,868 |
| S | 150 | 46,323,993 |
| N | 159 | 41,194,284 |
| O | 83 | 30,470,372 |
| E | 71 | 26,589,830 |
| HALL | 6 | 1,551,606 |
| SO | 2 | 613,058 |
| ALIV | 3 | 528,918 |
| C | 2 | 518,291 |
| NE | 4 | 364,812 |
