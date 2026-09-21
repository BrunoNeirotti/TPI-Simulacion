# Paso 13, Verificación del modelo base con el simulador de referencia

Generado por `src/13_verificacion_referencia.py` sobre las salidas de `anylogic/biblioteca/referencia/SimuladorReferencia.java` (`data/processed/referencia_*.csv`).

**Qué es el simulador de referencia.** Un simulador de eventos discretos en Java plano que corre **la misma lógica** que el modelo de AnyLogic (`anylogic/modelo/GUIA_CONSTRUCCION.md`) con la misma biblioteca: los mismos eventos, el mismo orden dentro de la detención (bajan al llegar, suben al partir) y las mismas reglas (D12 a D19). **No reemplaza al modelo de AnyLogic**, que es el entregable. Sirve para verificar la lógica antes de armarla y, después, para la verificación cruzada: con los mismos insumos, AnyLogic tiene que dar lo mismo dentro del error de muestreo.

Corrida: **10 replicaciones** del día hábil completo (5 a 24 h), semillas 1 a 10. Cada una tarda alrededor de 0,8 s. Detención fija de 24 s (D13, primera etapa), sin separación mínima por tramo (entra con la detención endógena, D15).

## 1. Consistencia interna

| Control | Resultado |
|---|---|
| Conservación (ingresados = arribados + en el sistema) | OK en las 10 |
| Viajes generados | 827.700 ± 439 (esperados 827.289) |
| Pasajeros vivos a la vez, máximo | 26.499 a 27.240 |
| Formaciones a la vez, máximo | 80 a 83 |
| Quedan en el sistema a las 24 h | 414 en promedio (los que entran después de la última salida de su línea) |

**El pool de pasajeros del diseño no alcanza.** D10 lo fijó en 25.000 porque la concurrencia máxima, medida sobre la asignación estática, era de 20.722. Con las esperas en andén la concurrencia sube: el máximo simulado va de 26.499 a 27.240. **El pool tiene que ser de unos 32.000.** Sigue dentro de lo probado: la prueba D instanció una población declarada de 60.000 sin problemas. El pool de 150 formaciones sí alcanza.

## 2. Contra la asignación estática del paso 6

Con la misma matriz y las mismas rutas, la carga por tramo de la simulación tiene que parecerse a la de la asignación estática. No es igual por construcción: la estática asigna todos los viajes de la hora a la hora, y la simulación los reparte en el tiempo que tardan (un viaje que sale a las 8:50 carga tramos de las 9). Es un control de lógica, no de validez.

| Período | Tramos | Correlación | Error absoluto ponderado | Sesgo |
|---|---:|---:|---:|---:|
| HPM | 166 | 0,999 | 3,2 % | 2,4 % |
| HPT | 166 | 1,000 | 2,7 % | -2,6 % |

## 3. Contra SBASE

La hora pico mañana es **calibración** y la tarde es **validación** (D9). Se comparan los tramos comparables del paso 9.

| Período | Qué es | Tramos | Modelo | Correlación | Error absoluto ponderado | Sesgo |
|---|---|---:|---|---:|---:|---:|
| HPM | calibración | 166 | estático (paso 6) | 0,994 | 6,5 % | 1,4 % |
| HPM | calibración | 166 | simulación | 0,993 | 7,6 % | 3,8 % |
| HPT | validación | 166 | estático (paso 6) | 0,985 | 8,4 % | 0,3 % |
| HPT | validación | 166 | simulación | 0,985 | 8,3 % | -2,3 % |

### Por grupo de líneas (D3)

| Período | Líneas | Tramos | Correlación | Error absoluto ponderado |
|---|---|---:|---:|---:|
| HPM | corredor A, C, D, H | 100 | 0,991 | 8,5 % |
| HPM | B y E | 66 | 0,996 | 6,1 % |
| HPT | corredor A, C, D, H | 100 | 0,981 | 7,7 % |
| HPT | B y E | 66 | 0,991 | 9,3 % |

### Ascensos por viaje

| Período | SBASE | Estático (paso 6) | Simulación |
|---|---:|---:|---:|
| HPM | 1,371 | 1,410 | 1,419 ± 0,001 |
| HPT | 1,426 | 1,437 | 1,444 ± 0,002 |

La simulación da algo más que la asignación estática porque cuenta la vuelta de las 142 rutas que cambian de sentido como un ascenso más (D19).

### Tramos con mayor diferencia en hora pico mañana

| Línea | Sale de | Sentido | SBASE | Estático | Simulación |
|---|---|---:|---:|---:|---:|
| H | Once | 1 | 6.728 | 7.692 | 8.174 |
| D | Palermo | 0 | 3.046 | 3.865 | 4.105 |
| H | Humberto 1 | 1 | 5.148 | 5.576 | 6.041 |
| A | Congreso | 0 | 2.799 | 3.539 | 3.658 |
| D | Ministro Carranza | 0 | 2.699 | 3.318 | 3.538 |
| H | Venezuela | 1 | 5.605 | 6.080 | 6.444 |
| A | Alberti | 0 | 2.592 | 3.338 | 3.415 |
| D | Plaza Italia | 0 | 3.946 | 4.540 | 4.747 |
| A | Peru | 1 | 2.071 | 2.897 | 2.834 |
| D | Juramento | 0 | 652 | 1.294 | 1.402 |

## 4. Indicadores del escenario base

Media e intervalo de confianza del 95 % entre las 10 replicaciones.

| Indicador | Valor |
|---|---|
| Tiempo de viaje medio (s) | 1.110,0 ± 0,9 |
| Espera media por viaje, todas las etapas (s) | 187,9 ± 1,0 |
| Ascensos por viaje, día | 1,443 ± 0,000 |
| Pasajeros-vez que no entran en una formación | 3.100 ± 745 |

**Los que no entran varían mucho entre réplicas**: el intervalo de confianza es ancho porque dependen de cuándo se forma un hueco largo entre despachos en hora pico. Es justamente el indicador que la Línea F debería mover.

### Tramos más cargados (ocupación media por formación)

| Línea | Sale de | Sentido | Hora | Pasajeros/h | Formaciones/h | Ocupación media | Máximo a bordo | Capacidad |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| B | Medrano | 1 | 8 | 11.974 | 14,8 | 75 % | 1074 | 1074 |
| B | Carlos Gardel | 1 | 8 | 12.047 | 14,9 | 75 % | 1074 | 1074 |
| C | San Juan | 1 | 8 | 12.386 | 18,8 | 74 % | 895 | 895 |
| B | angel Gallardo | 1 | 8 | 11.598 | 14,8 | 73 % | 1074 | 1074 |
| B | Pueyrredon | 0 | 17 | 11.167 | 14,5 | 72 % | 1074 | 1074 |
| C | Constitucion | 1 | 8 | 12.015 | 18,8 | 71 % | 895 | 895 |
| B | Pueyrredon | 1 | 8 | 11.204 | 14,7 | 71 % | 1074 | 1074 |
| B | Carlos Gardel | 0 | 17 | 10.908 | 14,5 | 70 % | 1074 | 1074 |

La capacidad por coche (179) es un supuesto de la especificación; la ocupación depende directamente de él.

### Por hora de ingreso

| Hora | Viajes | Viaje medio (min) | Espera media (s) | Ascensos por viaje |
|---:|---:|---:|---:|---:|
| 5 | 4.144 | 23,4 | 315 | 1,464 |
| 6 | 25.285 | 22,1 | 231 | 1,498 |
| 7 | 68.976 | 19,9 | 185 | 1,451 |
| 8 | 74.309 | 19,1 | 169 | 1,419 |
| 9 | 62.772 | 18,4 | 172 | 1,400 |
| 10 | 41.258 | 17,7 | 181 | 1,419 |
| 11 | 41.723 | 18,0 | 201 | 1,450 |
| 12 | 50.051 | 17,8 | 204 | 1,457 |
| 13 | 53.632 | 17,8 | 202 | 1,447 |
| 14 | 45.866 | 17,7 | 189 | 1,436 |
| 15 | 51.842 | 17,7 | 171 | 1,439 |
| 16 | 63.686 | 18,1 | 170 | 1,446 |
| 17 | 80.275 | 18,5 | 176 | 1,444 |
| 18 | 68.023 | 18,2 | 178 | 1,434 |
| 19 | 38.172 | 17,8 | 182 | 1,453 |
| 20 | 27.501 | 18,6 | 219 | 1,488 |
| 21 | 18.928 | 19,4 | 256 | 1,503 |
| 22 | 9.885 | 19,4 | 262 | 1,471 |
| 23 | 958 | 17,0 | 246 | 1,290 |

## 5. Sensibilidad de D4: la Línea D con la oferta de septiembre de 2024

D4 ajusta la oferta con julio a diciembre de 2025, pero la demanda y los perfiles de carga de SBASE son de septiembre de 2024, cuando la D despachaba bastante más espaciado (282 s en hora pico contra 218 s; `reports/12_ajuste_intervalos.md`, sección 7). Se corre el mismo modelo, con las mismas semillas, cambiando solo la oferta de la D.

| Indicador (toda la red) | Base | D de sept. 2024 |
|---|---:|---:|
| Tiempo de viaje medio (s) | 1.110,0 ± 0,9 | 1.116,3 ± 1,1 |
| Espera media por viaje (s) | 187,9 ± 1,0 | 194,4 ± 1,0 |
| Pasajeros-vez que no entran en una formación | 3.100 ± 745 | 2.780 ± 875 |
| Pasajeros vivos a la vez, máximo | 26.872 ± 179 | 26.882 ± 208 |

**Línea D, contra SBASE** (tramos comparables de la D):

| Período | Oferta | Correlación | Error absoluto ponderado | Sesgo | Ocupación media en el tramo más cargado |
|---|---|---:|---:|---:|---:|
| HPM | base (2025 jul.–dic.) | 0,978 | 9,7 % | 6,7 % | 48 % |
| HPM | sept. 2024 | 0,979 | 9,7 % | 6,8 % | 63 % |
| HPT | base (2025 jul.–dic.) | 0,967 | 6,7 % | 1,7 % | 43 % |
| HPT | sept. 2024 | 0,968 | 6,6 % | 1,0 % | 57 % |

El flujo por tramo en pasajeros por hora casi no depende de la frecuencia mientras no haya saturación, así que el contraste de carga contra SBASE cambia poco. Lo que sí cambia es la ocupación por formación y la espera: es el efecto que el desfase entre la oferta de 2025 y la demanda de 2024 introduce en el escenario base, y hay que declararlo al comparar contra la Línea F.

## 6. Lo que este paso no cubre

- **Detención fija** (24 s): la endógena y la separación mínima por tramo entran en la calibración (D13, D15).
- **La espera en andén no tiene contraparte observada**, igual que la aglomeración.
- **No verifica AnyLogic**: eso se hace cuando el modelo esté armado, comparando sus salidas contra estas.
