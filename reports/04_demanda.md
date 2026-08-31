# Paso 3 — Demanda por estación, franja de 15 min y tipo de día

Generado por `src/04_demanda_molinetes.py` sobre `data/raw/molinetes-2025.zip`. Salidas: `demanda_estacion_franja.csv`, `demanda_diaria.csv`, `concentracion_horaria.csv` y `demanda_anden.csv` en `data/processed/`.

> Los molinetes registran **ingresos a la red**: no son descensos, no son ocupación a bordo y **no incluyen los ascensos por transbordo**. La distinción importa en la sección 3.

## 1. Cobertura de la lectura

- 26 archivos, 13,196,766 filas, 0 descartadas, 0 con pax no numerico, 0 con fecha invalida, 443,923 en formato m/d/Y, 3 archivos Latin-1.
- Pasajeros leídos: **206.616.377**, contra los 206,5 millones que informó el paso 1. Cierra.
- Descartados por Premetro, fuera de alcance: 157.335 (0,0761 %).
- Descartados por sin cruce contra la tabla maestra: 80 (0,0000 %).
- Descartados por en filas centinela: 10 (0,0000 %).
- Descartados por sin fecha válida: ninguno.
- Descartados por con fecha fuera de 2025: ninguno.
- Descartados por con franja inválida: ninguno.

Los no-matcheos residuales, uno por uno:

| Línea | Estación | Pasajeros |
|---|---|---:|
| LineaB | Loria | 33 |
| LineaH | Loria | 18 |
| LineaD | Loria | 14 |
| LineaE | Loria | 12 |
| LineaC | Loria | 3 |

Son la estación espuria *Loria* que el paso 1 ya había identificado en las seis líneas. **80 pasajeros sobre 206,6 millones**: el mismo residuo que informó el paso 1, ahora con el Premetro correctamente separado y no contado como no-matcheo.

## 2. Tipos de día, huecos de datos y días atípicos

### 2.1 Día sin servicio: 1 día

Antes de hablar de demanda baja hay que separar los días con demanda prácticamente nula. Un día de subte por debajo del 5 % de la mediana mensual no es un día flojo: o no hubo servicio, o no hubo registro.

| Fecha | Día | Pasajeros | Estaciones con dato | Razón |
|---|---|---:|---:|---:|
| 2025-04-10 | jueves | 66 | 31 de 90 | 0,00 |

> **Fue un paro general.** El paso 4 lo verifica sobre una fuente independiente: el 10/04/2025 hay 3.122 servicios de cabecera programados y **ninguno prestado**, todos con causa *Huelga / Paro General* (ver `reports/05_despachos.md`, sección 2.1). No es un faltante del publicador. Queda excluido de todos los perfiles por no ser representativo, y **no se rellena**: interpolar demanda es inventar dato.

### 2.2 Tipos de día

| Tipo de día | Días con dato | Días típicos | Pasajeros/día (media) |
|---|---:|---:|---:|
| domingo | 52 | 52 | 182.104 |
| habil | 260 | 235 | 689.768 |
| sabado | 52 | 52 | 339.420 |

**Los perfiles del modelo se construyen solo con los días típicos**: se excluyen el hueco de datos y los días atípicos. Incluirlos arrastraría el perfil de día hábil hacia abajo sin que eso represente ninguna operación real.

### 2.3 25 días hábiles atípicos

Días hábiles por debajo del 80 % de la mediana de los hábiles del mismo mes. El criterio es intramensual porque la estacionalidad es fuerte: contra la mediana anual saldría enero entero.

| Fecha | Día | Pasajeros | Razón |
|---|---|---:|---:|
| 2025-12-25 | jueves | 78.816 | 0,11 |
| 2025-01-01 | miercoles | 61.285 | 0,12 |
| 2025-03-03 | lunes | 138.479 | 0,20 |
| 2025-05-01 | jueves | 170.226 | 0,21 |
| 2025-03-04 | martes | 170.588 | 0,24 |
| 2025-12-31 | miercoles | 175.978 | 0,24 |
| 2025-06-16 | lunes | 201.637 | 0,25 |
| 2025-04-02 | miercoles | 217.311 | 0,27 |
| 2025-11-24 | lunes | 214.872 | 0,29 |
| 2025-04-18 | viernes | 232.255 | 0,29 |
| 2025-12-08 | lunes | 214.966 | 0,30 |
| 2025-07-09 | miercoles | 239.613 | 0,31 |
| 2025-12-24 | miercoles | 229.127 | 0,32 |
| 2025-06-20 | viernes | 285.437 | 0,35 |
| 2025-10-10 | viernes | 292.454 | 0,38 |
| 2025-03-24 | lunes | 298.621 | 0,42 |
| 2025-04-17 | jueves | 352.614 | 0,44 |
| 2025-11-21 | viernes | 369.986 | 0,49 |
| 2025-05-02 | viernes | 405.823 | 0,50 |
| 2025-08-15 | viernes | 406.536 | 0,51 |
| 2025-12-26 | viernes | 497.088 | 0,69 |
| 2025-08-01 | viernes | 551.531 | 0,70 |
| 2025-03-05 | miercoles | 503.665 | 0,72 |
| 2025-12-30 | martes | 523.682 | 0,73 |
| 2025-12-29 | lunes | 555.125 | 0,77 |

> **Esta lista hay que contrastarla contra el calendario oficial de feriados de 2025.** El método detecta anomalías, no feriados: un paro, un corte de servicio o un día de lluvia extraordinaria aparecen igual. La forma de la lista es compatible con el calendario —1/1, 1/5, 25/12, el 24 y el 31, los lunes de carnaval y los puentes— pero **compatible no es verificado**. Los días atípicos quedan fuera del perfil de día hábil y **no se reasignan a domingo**, que sería un supuesto sin sustento.

### 2.4 El viernes 8 de agosto de 2025 queda cerrado

El paso 1 lo dejó anotado: tras reconstruir las fechas quedaba con 38.454 filas contra ~49.000 de los viernes comparables, un 22 % menos, sin saber si era una interrupción de servicio o un faltante.

**Con los pasajeros a la vista, el día es normal**: 786.551 pasajeros, razón 0,99 contra la mediana de los hábiles de agosto, 90 de 90 estaciones con dato.

| Viernes de agosto | Pasajeros | Razón | Estaciones con dato |
|---|---:|---:|---:|
| 2025-08-01 | 551.531 | 0,70 | 90 |
| 2025-08-08 | 786.551 | 0,99 | 90 |
| 2025-08-15 | 406.536 | 0,51 | 89 |
| 2025-08-22 | 804.496 | 1,01 | 89 |
| 2025-08-29 | 788.772 | 0,99 | 88 |

> **La menor cantidad de filas no era menor demanda.** Agosto es uno de los dos archivos con fechas `d/m/Y` y `m/d/Y` mezcladas, y el conteo de filas por día quedaba distorsionado por esa reconstrucción. Los pasajeros por día no se apartan. El pendiente del paso 1 se cierra sin corrección: **no hay nada que corregir**. Lo que sí queda marcado como anómalo en agosto es el viernes 15 (razón 0,51) y el viernes 1.º (0,70).

## 3. Concentración horaria — el control que quedaba pendiente

La pregunta es si dos cifras de la Línea F son conciliables entre sí: los **≈73.900 ascensos en hora pico** que suman las tablas de SBASE del EsIA (46.713 hacia Palermo más 27.163 hacia Brandsen, misma hora pico de la mañana) y los **270.000–300.000 pasajeros diarios** anunciados. Para que lo fueran, la hora pico tendría que concentrar cerca del **25 %** de la demanda diaria.

La hora pico se busca como la ventana móvil de 60 min de mayor ingreso, no se fija de antemano: fijarla sería suponer el resultado.

### 3.1 La red, en día hábil típico (235 días)

| Métrica | Media | Desvío | Mínimo | Máximo |
|---|---:|---:|---:|---:|
| Hora pico móvil de 60 min | **9,9 %** | 0,43 % | 8,7 % | 12,0 % |
| Hora 8:00–9:00 | **9,2 %** | 0,53 % | 7,6 % | 10,9 % |
| Hora 17:00–18:00 | **9,9 %** | 0,44 % | 8,3 % | 12,0 % |
| Franja pico de 15 min | **2,8 %** | 0,13 % | 2,4 % | 3,4 % |

La ventana pico arranca con más frecuencia a las **17:00** (126 de 235 días). El doble pico que el dataset O-D detecta a las 8 y a las 17 aparece también acá, y la tarde gana.

### 3.2 Por línea

| Línea | Ingresos/día | Hora pico | Inicio | Hora 8 | Hora 17 |
|---|---:|---:|---|---:|---:|
| E | 76.566 | **12,0 %** | 17:15 | 8,9 % | 11,9 % |
| C | 104.035 | **11,9 %** | 08:00 | 11,9 % | 8,2 % |
| D | 155.887 | **10,6 %** | 17:00 | 7,6 % | 10,6 % |
| B | 169.338 | **10,0 %** | 17:15 | 8,6 % | 10,0 % |
| A | 142.824 | **9,8 %** | 16:45 | 9,7 % | 9,8 % |
| H | 83.061 | **9,0 %** | 17:15 | 8,8 % | 9,0 % |

### 3.3 Las estaciones más concentradas

Es la comparación que importa, porque la Línea F no es una línea promedio: su carga máxima está en Constitución, alimentada por el ferrocarril Roca. Si algún nodo de la red actual puede acercarse al 25 %, es uno de ésos.

| Estación | Línea | Ingresos/día | Hora pico | Inicio |
|---|---|---:|---:|---|
| Catalinas | E | 4.646 | **30,0 %** | 17:30 |
| Correo Central | E | 5.586 | **21,3 %** | 17:15 |
| General San Martin | C | 3.793 | **21,0 %** | 17:30 |
| Bolivar | E | 8.226 | **20,7 %** | 16:45 |
| Catedral | D | 16.552 | **20,1 %** | 17:00 |
| Plaza de Mayo | A | 12.689 | **19,9 %** | 17:00 |
| Florida | B | 9.401 | **18,7 %** | 17:15 |
| Hospitales | H | 12.086 | **18,3 %** | 07:30 |
| Peru | A | 7.188 | **18,2 %** | 17:00 |
| Plaza de los Virreyes | E | 7.736 | **17,9 %** | 07:30 |

Y los nodos de transferencia ferroviaria en particular:

| Estación | Línea | Ingresos/día | Hora pico | Inicio |
|---|---|---:|---:|---|
| Constitucion | C | 57.010 | **17,5 %** | 07:45 |
| Retiro | E | 3.761 | **15,5 %** | 17:30 |
| Plaza Miserere | A | 9.273 | **11,7 %** | 08:30 |
| Retiro | C | 19.147 | **11,4 %** | 17:15 |
| Once | H | 9.288 | **9,7 %** | 08:00 |

### 3.4 Resultado

**La red concentra el 9,9 % de sus ingresos diarios en la hora pico, y ninguna de las seis líneas pasa del 12,0 %** (la E). La comparación pertinente es la de línea, porque la cifra de SBASE es de línea.

A nivel de estación individual sí hay casos que superan el 25 %: Catalinas [E] llega al 30,0 %. Pero son estaciones chicas y de uso casi monopropósito —Catalinas tiene 4.646 ingresos diarios, el 0,6 % de la red— donde entra personal de oficinas a la mañana y sale a la tarde. **Una línea entera de doce estaciones no se comporta como una estación de oficinas.**

El contraste más directo disponible es **Constitución**, que es el nodo de carga máxima de la Línea F según SBASE y hoy ya existe como estación de la Línea C, alimentada por el mismo ferrocarril Roca:

- Constitución [C] recibe hoy **57.010 ingresos diarios** y concentra el 17,5 % en su hora pico, es decir unos **9.950 ingresos en la hora pico**.
- SBASE proyecta para Constitución de la Línea F **32.640 ascensos en la hora pico de la mañana** en un solo sentido: 3,3 veces el ingreso de hora pico que la estación tiene hoy en la Línea C, y el 57,3 % de todo su ingreso diario actual.

Los transbordos desde el ferrocarril **sí pasan por molinete** —son sistemas tarifarios distintos—, así que están contados en esos 57.010 ingresos. La comparación no está subestimando la demanda ferroviaria.

De ahí salen dos lecturas del mismo hecho, y conviene decir las dos:

1. **Si la Línea F se pareciera a la red actual**, sus 73.900 ascensos de hora pico implicarían del orden de **743.000 pasajeros diarios**, entre 2 y 3 veces la cifra anunciada de 270.000–300.000.
2. **Si la cifra anunciada fuese correcta**, la Línea F tendría que concentrar cerca del 25 % de su demanda diaria en una hora: 2,5 veces la concentración de la red actual y 2,1 veces la de la línea más apuntada, la E.

> **Las dos cifras no son conciliables entre sí.** Al menos una está mal, y el trabajo no puede decidir cuál con la información disponible.

**Tres salvedades, que acotan el alcance sin cambiar la conclusión:**

1. **Unidades.** Los molinetes miden ingresos a la red; los ascensos de SBASE incluyen además los transbordos desde las otras seis líneas de subte. Los ascensos son necesariamente más que los ingresos —en la red actual el 48,8 % de las etapas termina en una línea distinta de la de ascenso—, así que la cifra diaria implicada del punto 1 es una **cota superior**. La comparación de *concentración*, que es una proporción, no se ve afectada por el nivel.
2. **La hora pico de SBASE es la de la línea, no la de la red.** Una línea puede tener su pico desplazado respecto del pico agregado, lo que aumentaría su concentración propia. La sección 3.2 muestra que entre líneas la dispersión es chica: del 9,0 % al 12,0 %.
3. **Los 270.000–300.000 no tienen fuente documental.** No aparecen en ninguna pieza del expediente ni de la licitación. Que no cierren contra el perfil de SBASE es una razón más para no usarlos como insumo, que es lo que el trabajo ya venía haciendo.

## 4. Reparto por andén — el contraste que reserva D5

- Ingresos con sentido de circulación identificable: **145.556.349 de 206.458.952, o sea 70,5 %**. Reproduce el 70,5 % que midió el paso 1.
- Estaciones con algún ingreso atribuible: **62 de 90**. Las 28 restantes no tienen el campo en ningún molinete.
- De esas 62, cobertura mediana 98,6 %; 10 superan el 99 % y 1 quedan por debajo del 50 %.

**El faltante no está repartido al azar**, y por eso D5 decidió modelar la demanda por estación: hay 28 estaciones enteras sin el dato. Lo que queda es un contraste **parcial y sesgado por construcción** del reparto entre andenes que produzca el modelo, útil solo donde el dato existe.

Las diez estaciones de mayor ingreso con cobertura por encima del 99 %:

| Estación | Línea | Ingresos 2025 | Reparto entre sentidos |
|---|---|---:|---|
| San Pedrito | A | 6.260.126 | E 56 % / O 44 % |
| Federico Lacroze | B | 5.132.160 | E 26 % / O 70 % / S 5 % |
| Hospitales | H | 3.370.834 | N 52 % / S 48 % |
| Facultad de Medicina | D | 3.216.932 | N 37 % / S 63 % |
| Once | H | 2.755.715 | N 34 % / S 66 % |
| Scalabrini Ortiz | D | 2.309.601 | N 73 % / S 27 % |
| Venezuela | H | 1.706.080 | N 34 % / S 66 % |
| Pueyrredon | B | 1.681.932 | N 40 % / S 60 % |
| Facultad de Derecho | H | 1.478.360 | N 10 % / S 90 % |
| Lima | A | 937.875 | N 18 % / S 82 % |

## 5. Qué queda de esto

- **La demanda de entrada del modelo está lista**: 19.931 celdas de (tipo de día, franja de 15 min, estación), con media y desvío entre días típicos. El desvío es el insumo del análisis de sensibilidad y de la variabilidad entre replicaciones.
- **Las dos cifras de demanda de la Línea F no cierran entre sí** (sección 3.4). Es un hallazgo propio y hay que llevarlo al documento: refuerza la decisión ya tomada de no usar la cifra anunciada como insumo, y agrega una salvedad al uso del perfil de SBASE como contraste.
- **El pendiente del viernes 08/08/2025 se cierra sin corrección** (sección 2.4): era un artefacto del conteo de filas, no un faltante de demanda.
- **Aparece un día sin servicio** (sección 2.1): el 10/04/2025, verificado como paro general contra el dataset de despachos. Hay que declararlo y excluirlo.
- **Los días atípicos quedaron verificados en el paso 4** contra el calendario `Tipo Día` del propio operador: 11 de 11 feriados hábiles detectados, 6 más corroborados como servicio de sábado, 4 sin datos de despachos y 4 sin explicación. Ver `reports/05_despachos.md`, sección 5.
- **D4 queda en condiciones de decidirse**: la tabla diaria da los candidatos a ventana de ajuste y de validación, ambos posteriores a diciembre de 2024, sin días atípicos y con estacionalidad comparable.
