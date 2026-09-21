# Paso 13, Verificación del modelo base con el simulador de referencia

Generado por `src/13_verificacion_referencia.py` sobre las salidas de `anylogic/biblioteca/referencia/SimuladorReferencia.java` (`data/processed/referencia_*.csv`).

**Qué es el simulador de referencia.** Un simulador de eventos discretos en Java plano que corre **la misma lógica** que el modelo de AnyLogic (`anylogic/modelo/GUIA_CONSTRUCCION.md`) con la misma biblioteca: los mismos eventos, el mismo orden dentro de la detención (bajan al llegar, suben al partir) y las mismas reglas (D12 a D19). **No reemplaza al modelo de AnyLogic**, que es el entregable. Sirve para verificar la lógica antes de armarla y, después, para la verificación cruzada: con los mismos insumos, AnyLogic tiene que dar lo mismo dentro del error de muestreo.

Corrida: **10 replicaciones** del día hábil completo (5 a 24 h), semillas 1 a 10. Cada una tarda alrededor de 0,8 s. Detención fija de 24 s (D13, primera etapa), sin separación mínima por tramo (entra con la detención endógena, D15).

## 1. Consistencia interna

| Control | Resultado |
|---|---|
| Conservación (ingresados = arribados + en el sistema) | OK en las 10 |
| Viajes generados | 827.619 ± 482 (esperados 827.289) |
| Pasajeros vivos a la vez, máximo | 26.647 a 27.796 |
| Formaciones a la vez, máximo | 76 a 82 |
| Quedan en el sistema a las 24 h | 431 en promedio (los que entran después de la última salida de su línea) |

**El pool de pasajeros del diseño no alcanza.** D10 lo fijó en 25.000 porque la concurrencia máxima, medida sobre la asignación estática, era de 20.722. Con las esperas en andén la concurrencia sube: el máximo simulado va de 26.647 a 27.796. **El pool tiene que ser de unos 32.000.** Sigue dentro de lo probado: la prueba D instanció una población declarada de 60.000 sin problemas. El pool de 150 formaciones sí alcanza.

## 2. Contra la asignación estática del paso 6

Con la misma matriz y las mismas rutas, la carga por tramo de la simulación tiene que parecerse a la de la asignación estática. No es igual por construcción: la estática asigna todos los viajes de la hora a la hora, y la simulación los reparte en el tiempo que tardan (un viaje que sale a las 8:50 carga tramos de las 9). Es un control de lógica, no de validez.

| Período | Tramos | Correlación | Error absoluto ponderado | Sesgo |
|---|---:|---:|---:|---:|
| HPM | 166 | 0,999 | 3,2 % | 2,4 % |
| HPT | 166 | 0,999 | 2,7 % | -2,6 % |

## 3. Contra SBASE

La hora pico mañana es **calibración** y la tarde es **validación** (D9). Se comparan los tramos comparables del paso 9.

| Período | Qué es | Tramos | Modelo | Correlación | Error absoluto ponderado | Sesgo |
|---|---|---:|---|---:|---:|---:|
| HPM | calibración | 166 | estático (paso 6) | 0,994 | 6,5 % | 1,4 % |
| HPM | calibración | 166 | simulación | 0,993 | 7,6 % | 3,9 % |
| HPT | validación | 166 | estático (paso 6) | 0,985 | 8,4 % | 0,3 % |
| HPT | validación | 166 | simulación | 0,983 | 8,7 % | -2,3 % |

### Por grupo de líneas (D3)

| Período | Líneas | Tramos | Correlación | Error absoluto ponderado |
|---|---|---:|---:|---:|
| HPM | corredor A, C, D, H | 100 | 0,992 | 8,4 % |
| HPM | B y E | 66 | 0,996 | 6,2 % |
| HPT | corredor A, C, D, H | 100 | 0,980 | 8,0 % |
| HPT | B y E | 66 | 0,989 | 10,1 % |

### Ascensos por viaje

| Período | SBASE | Estático (paso 6) | Simulación |
|---|---:|---:|---:|
| HPM | 1,371 | 1,410 | 1,417 ± 0,002 |
| HPT | 1,426 | 1,437 | 1,444 ± 0,001 |

La simulación da algo más que la asignación estática porque cuenta la vuelta de las 142 rutas que cambian de sentido como un ascenso más (D19).

### Tramos con mayor diferencia en hora pico mañana

| Línea | Sale de | Sentido | SBASE | Estático | Simulación |
|---|---|---:|---:|---:|---:|
| H | Once | 1 | 6.728 | 7.692 | 7.987 |
| D | Palermo | 0 | 3.046 | 3.865 | 4.189 |
| B | Callao | 1 | 8.850 | 9.437 | 9.656 |
| D | Ministro Carranza | 0 | 2.699 | 3.318 | 3.505 |
| H | Venezuela | 1 | 5.605 | 6.080 | 6.398 |
| D | Juramento | 0 | 652 | 1.294 | 1.434 |
| A | Congreso | 0 | 2.799 | 3.539 | 3.578 |
| H | Humberto 1 | 1 | 5.148 | 5.576 | 5.894 |
| D | Plaza Italia | 0 | 3.946 | 4.540 | 4.683 |
| D | Pueyrredon | 0 | 5.378 | 5.861 | 6.115 |

## 4. Indicadores del escenario base

Media e intervalo de confianza del 95 % entre las 10 replicaciones.

| Indicador | Valor |
|---|---|
| Tiempo de viaje medio (s) | 1.121,6 ± 1,7 |
| Espera media por viaje, todas las etapas (s) | 199,4 ± 1,7 |
| Ascensos por viaje, día | 1,442 ± 0,000 |
| Pasajeros-vez que no entran en una formación | 6.992 ± 2.130 |

**Los que no entran varían mucho entre réplicas**: el intervalo de confianza es ancho porque dependen de cuándo se forma un hueco largo entre despachos en hora pico. Es justamente el indicador que la Línea F debería mover.

### Tramos más cargados (ocupación media por formación)

| Línea | Sale de | Sentido | Hora | Pasajeros/h | Formaciones/h | Ocupación media | Máximo a bordo | Capacidad |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| B | Medrano | 1 | 8 | 12.016 | 14,1 | 79 % | 1074 | 1074 |
| B | Carlos Gardel | 1 | 8 | 11.898 | 14,0 | 79 % | 1074 | 1074 |
| B | angel Gallardo | 1 | 8 | 11.708 | 14,2 | 77 % | 1074 | 1074 |
| C | San Juan | 1 | 8 | 12.388 | 18,4 | 75 % | 895 | 895 |
| B | Pueyrredon | 0 | 17 | 11.378 | 14,1 | 75 % | 1074 | 1074 |
| B | Pueyrredon | 1 | 8 | 11.079 | 13,9 | 74 % | 1074 | 1074 |
| B | Carlos Gardel | 0 | 17 | 11.172 | 14,2 | 73 % | 1074 | 1074 |
| C | Constitucion | 1 | 8 | 11.903 | 18,2 | 73 % | 895 | 895 |

La capacidad por coche (179) es un supuesto de la especificación; la ocupación depende directamente de él.

### Por hora de ingreso

| Hora | Viajes | Viaje medio (min) | Espera media (s) | Ascensos por viaje |
|---:|---:|---:|---:|---:|
| 5 | 4.192 | 23,3 | 316 | 1,460 |
| 6 | 25.320 | 22,2 | 237 | 1,496 |
| 7 | 68.856 | 20,2 | 198 | 1,451 |
| 8 | 74.390 | 19,5 | 188 | 1,417 |
| 9 | 62.713 | 18,6 | 186 | 1,401 |
| 10 | 41.253 | 18,0 | 195 | 1,418 |
| 11 | 41.823 | 18,1 | 207 | 1,450 |
| 12 | 50.027 | 17,9 | 213 | 1,457 |
| 13 | 53.610 | 18,0 | 209 | 1,447 |
| 14 | 45.866 | 17,9 | 200 | 1,434 |
| 15 | 51.856 | 17,9 | 184 | 1,439 |
| 16 | 63.593 | 18,4 | 187 | 1,447 |
| 17 | 80.151 | 18,7 | 189 | 1,444 |
| 18 | 68.110 | 18,3 | 186 | 1,434 |
| 19 | 38.185 | 17,9 | 189 | 1,452 |
| 20 | 27.465 | 18,8 | 229 | 1,489 |
| 21 | 18.916 | 19,5 | 261 | 1,502 |
| 22 | 9.896 | 19,4 | 266 | 1,466 |
| 23 | 966 | 16,8 | 236 | 1,273 |

## 5. Lo que este paso no cubre

- **Detención fija** (24 s): la endógena y la separación mínima por tramo entran en la calibración (D13, D15).
- **La espera en andén no tiene contraparte observada**, igual que la aglomeración.
- **No verifica AnyLogic**: eso se hace cuando el modelo esté armado, comparando sus salidas contra estas.
