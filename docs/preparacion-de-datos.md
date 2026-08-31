# Preparación de datos: bitácora

Bitácora del pipeline de datos. Acá va el detalle técnico y los problemas de
calidad de datos que fuimos encontrando; de acá se toma después lo que
corresponda para el informe.

Cada paso corresponde al plan de trabajo de la sección 8 de `contexto-del-proyecto.md`.

| Paso | Estado | Script | Reporte |
|---|---|---|---|
| 1. Tabla maestra de estaciones | **Hecho** | `src/01_tabla_maestra_estaciones.py` | `reports/01_tabla_maestra.md` |
| 2. Grafo de la red | **Hecho** | `src/03_grafo_red.py` | `reports/03_grafo_red.md` |
| 3. Demanda por estación y 15 min | **Hecho** | `src/04_demanda_molinetes.py` | `reports/04_demanda.md` |
| 4. Intervalos entre despachos | **Hecho** | `src/05_despachos.py` | `reports/05_despachos.md` |
| 5. Matriz O-D | **Hecho** | `src/06_matriz_od.py` | `reports/06_matriz_od.md` |
| 6. Caminos mínimos | **Hecho** | `src/07_caminos_minimos.py` | `reports/07_caminos_minimos.md` |

---

## 0. Estructura del repositorio

Se aplicó la convención declarada en la sección 10 de `contexto-del-proyecto.md`:

```
data/raw/        22 archivos, 2,18 GB, tal como se descargaron. Nunca se modifican.
data/raw/gtfs/   los 14 .txt del feed, ya desanidados
data/processed/  todo lo derivado
src/             código
reports/         reportes de control generados por los scripts
docs/            documento LaTeX y notas
```

`data/` y el expediente del EIA quedan fuera de control de versiones
(`.gitignore`). Los reportes de `reports/` en formato Markdown sí se versionan,
porque son el registro de qué se decidió y por qué.

**El GTFS venía doble-anidado**, como estaba anotado: `subte-gtfs-zip.zip`
contiene un único archivo sin extensión llamado `subte_gtfs` que a su vez es el
ZIP con los 14 `.txt`. Ya está desanidado en `data/raw/gtfs/`.

---

## 1. Tabla maestra de estaciones

**Objetivo.** Mapear los nombres de estación del dataset de molinetes contra los
`stop_id` del GTFS, con reporte explícito de los no-matcheos.

**Resultado: 90 de 90 estaciones de subte cruzadas, ninguna huérfana.** Los
no-matcheos residuales suman 80 pasajeros sobre 206 millones.

### 1.1 Lo que costó: el formato de molinetes está bastante roto

Cinco problemas, ninguno documentado por el publicador. Los cinco están
resueltos en `src/lib_molinetes.py` y valen para cualquier año, no solo 2025.

**a) Dos formatos de fila en el mismo ZIP.** Cada registro viene envuelto en
comillas dobles con `;` interno. Algunos archivos agregan nueve campos vacíos de
cola (`...;2";;;;;;;;;`) y otros no (`...;2"`). Un parser que contemple solo el
primero deja el último campo como `2"`, falla la conversión a entero y
**descarta en silencio el `pax_TOTAL` de la mitad de los archivos**. El síntoma
fue un total anual de 15,5 millones de pasajeros donde correspondían 206,6. Es
el tipo de error que no rompe nada y contamina todo aguas abajo.

**b) Codificación mixta.** Tres archivos son Latin-1 y el resto UTF-8.
Decodificar todo como UTF-8 corrompe las eñes y parte `Saenz Peña` en dos
estaciones distintas, una de ellas con la mitad de la demanda.

**c) La fecha mezcla `d/m/Y` y `m/d/Y`.** Los dos archivos de **agosto de 2025**
(y solo esos) traen ambas convenciones conviviendo, para los mismos días:
881.538 filas en `d/m` y 443.923 en `m/d`. Es recuperable sin pérdida porque el
mes lo fija el nombre del archivo: se verificó que **ningún registro de esos
archivos cae fuera de agosto**, así que el día es el componente que no es 8. La
prueba de que la reconstrucción es correcta es que el perfil semanal aparece
limpio recién después de aplicarla: domingos ~30.000 filas, sábados ~41.000,
hábiles ~49.000.

**d) Valores centinela.** Hay una línea `Prueba`, una estación `#N/D`, otra
`NULL` y un molinete `LineaH_Validador_Central_Turn01`. Suman 10 pasajeros. Se
descartan y quedan listados en el reporte. Ojo: la normalización tipográfica
convierte `#N/D` en `N D`, así que la detección de centinelas mira el texto
crudo además del normalizado.

**e) La estación `Loria` aparece en las seis líneas.** Loria existe solo en la
Línea A. Bajo B, C, D, E y H suma 80 pasajeros en todo 2025 contra 126.838 en la
A. Es ruido de carga. Se descarta y queda reportado.

> **Corrección a lo que teníamos anotado.** Estaba anotado que `202507_PAX15min-DEH-… (1).csv`
> era "un artefacto de descarga duplicada, verificar que no se procese dos
> veces". **No hay duplicación**: ese archivo es el único de julio para el grupo
> DEH y el `(1)` quedó solo en el nombre. No existe una versión sin sufijo. Los
> 26 archivos del ZIP son 26 combinaciones distintas de mes y grupo de líneas.

### 1.2 Criterio de cruce

El cruce es determinístico y auditable. No se usa comparación difusa en ningún
punto: si dos nombres no coinciden después de normalizar, la equivalencia se
declara a mano en `src/lib_normalizacion.py`, con su justificación.

1. **Normalización tipográfica**: mayúsculas, sin acentos, sin puntuación,
   espacios colapsados.
2. **Sufijo de línea**: molinetes desambigua los complejos de combinación
   agregando la línea al nombre (`Callao.B` contra `Callao.D`, `Pueyrredon.B`
   contra `Pueyrredon.D`). Como el cruce ya se hace dentro de cada línea, el
   sufijo se quita, y se reporta cuando no coincide con la línea del registro.
3. **Tabla de alias**: 12 equivalencias explícitas.

Las 12 equivalencias se dividen en tres clases:

| Clase | Ejemplos |
|---|---|
| Molinetes abrevia, el GTFS no | `Flores` → `San Jose de Flores`, `Rosas` → `Juan Manuel de Rosas`, `Los Incas` → `De Los Incas - Parque Chas`, `Tronador` → `Tronador - Villa Ortuzar`, `Patricios` → `Parque Patricios` |
| Molinetes alarga, el GTFS abrevia | `Mariano Moreno` → `Moreno`, `General Belgrano` → `Belgrano`, `Avenida La Plata` → `La Plata` |
| Denominación distinta | `Urquiza` → `General Urquiza`, `Humberto I` → `Humberto 1` (romano contra dígito) |

**Un caso no es una equivalencia sino un error del publicador.** Bajo `LineaE`
figura una estación `Independencia.H` con 1.522.600 pasajeros y molinetes
`LineaE_Indepen_Turn01..04`. La Línea H no tiene estación Independencia: el
sufijo está mal y son los molinetes de la Línea E. Se corrige y se deja
declarado, porque no es una abreviatura sino un dato equivocado.

Además, **siete estaciones aparecen con dos nombres distintos dentro del mismo
año**, y no por partición temporal: los dos nombres conviven en el mismo mes y
con los mismos molinetes. Son `Pueyrredon`/`Pueyrredon.B`,
`Independencia`/`Independencia.C`, `Retiro`/`Retiro.C`, `9 de Julio`/`9 de
julio`, `Callao`/`Callao.D`, `Independencia.E`/`Independencia.H` y `Retiro
E`/`Retiro.E`. Si no se consolidan, la demanda de cada una queda partida en dos.

### 1.3 Salidas

- `data/processed/tabla_maestra_estaciones.csv`: 90 filas: línea, `stop_id`,
  nombre GTFS, coordenadas, cantidad de andenes, nombres en molinetes,
  molinetes, registros y pasajeros 2025.
- `data/processed/molinetes_inventario.csv`: 794 filas, un molinete por fila,
  con su sentido normalizado y sus banderas de control.
- `reports/01_tabla_maestra.md`: el reporte de control completo.

### 1.4 Hallazgo que afecta una decisión de modelado

Estaba anotado que el identificador de molinete codifica el andén y que eso
"permitiría demanda por andén y no solo por estación, alineado con la estructura
del GTFS". **La cobertura real no alcanza para eso:**

| Situación | Molinetes | Pasajeros | % |
|---|---:|---:|---:|
| Sentido de circulación identificable | 494 | 145.556.349 | **70,5 %** |
| Zona de vestíbulo, sin sentido (`HALL`, `C`, `Aliv`) | 11 | 2.598.815 | 1,3 % |
| Identificador sin campo de andén | 158 | 55.713.076 | **27,0 %** |
| Sin identificador de molinete | 93 | 2.590.792 | 1,3 % |

El identificador no tiene una forma única: conviven `Linea_Estacion_Aparato`
(sin andén, ej. `LineaA_Alberti_Turn01`), `Linea_Estacion_Sentido_Aparato` (el
caso mayoritario) y `Linea_Estacion_Zona_Sentido_Aparato` (ej.
`LineaA_Miserere_Q_NE_Turn01`).

**Consecuencia: casi el 30 % de la demanda no es atribuible a un andén.** El
faltante no está repartido al azar: estaciones enteras (Alberti, Pasco, Los
Incas) no tienen el campo. Modelar la demanda por andén exigiría inventar un
criterio de reparto para ese 30 %, que es exactamente el tipo de supuesto que el
trabajo viene evitando.

> **Decisión tomada el 05/08/2026** (ver `contexto-del-proyecto.md`, sección 7). La demanda se
> modela **a nivel de estación** y el reparto entre andenes queda como resultado
> de la asignación de ruta. El 70,5 % con andén identificable se reserva como
> **contraste independiente de ese reparto**, en las estaciones donde el dato
> existe. Es un contraste parcial y sesgado por construcción, y así se declara.
> El paso 3 debe producir, además de la demanda por estación, el agregado por
> andén restringido a esas estaciones.

### 1.5 Dos contrastes de consistencia que salieron bien

**Reparto por línea contra el dataset O-D.** Son dos fuentes independientes
(molinetes 2025 registra ingresos, el dataset de viajes y etapas del AMBA
imputa etapas de un día de octubre de 2024) y coinciden en el ordenamiento y
muy de cerca en los pesos:

| Línea | Molinetes 2025 | Etapas O-D 2024 |
|---|---:|---:|
| B | 23,5 % | 24,2 % |
| D | 21,2 % | 21,8 % |
| A | 19,4 % | 19,9 % |
| C | 14,3 % | 12,8 % |
| H | 11,4 % | 10,8 % |
| E | 10,1 % | 10,5 % |

La diferencia mayor está en la Línea C (+1,5 puntos en molinetes). Es la línea
de Constitución y Retiro, es decir la más expuesta a la transferencia
ferroviaria, así que la diferencia es plausible y merece revisarse en el paso 5.

**Constitución domina.** 16,49 millones de pasajeros en 2025, 2,6 veces la
segunda estación (San Pedrito, 6,26 millones). Es coherente con lo que sostiene
el EsIA de la Línea F sobre el peso del nodo.

### 1.6 Lo que este paso dejó abierto, y cómo se cerró

- ~~Redescargar `viajes_anual.csv`.~~ **Cerrado el 05/08/2026: el recurso está
  discontinuado.** Se redescargó del dataset Subte: Estaciones y trae exactamente
  lo mismo que la copia vieja: 48 filas, 2013-2020. La API del portal lo confirma:
  `last_modified = 2020-09-07`. El "Desde junio 2013" del título del recurso y la
  fecha de actualización que muestra la página web corresponden al **dataset**, no
  al archivo. **No volver a intentarlo.**

  **Consecuencia:** no hay control agregado oficial de pasajeros por línea y año
  para el período posterior a diciembre de 2024, que es el único que el trabajo
  puede usar. Lo reemplaza el contraste de reparto entre líneas contra el dataset
  de viajes y etapas (sección 1.5), que es independiente y ya cierra bien. El
  contraste contra 2019 (341,3 millones frente a 206,6 en 2025) queda solo como
  referencia de orden de magnitud, y ni siquiera es limpio: median cosas distintas
  y en el medio está la pandemia y el cambio de medios de pago.
- **El viernes 8 de agosto de 2025.** Tras reconstruir las fechas, ese día
  quedaba con 38.454 filas contra unas 49.000 de los viernes comparables, un
  22 % menos, y no sabíamos si era una interrupción real de servicio o un
  faltante de datos. El paso 3 lo resolvió: el día es normal y no hay que
  corregir nada.

---

## 2. Grafo de la red

`src/03_grafo_red.py` · reporte en `reports/03_grafo_red.md` · salidas
`data/processed/grafo_nodos.csv` y `data/processed/grafo_aristas.csv`.

Paso 2 del plan. **90 nodos** (par linea-estacion, cruzan uno a uno con la tabla
maestra del paso 1), **166 aristas de tramo** dirigidas y **28 de transbordo**
(14 combinaciones). El grafo es **fuertemente conexo**, que es la condicion para
que el paso 6 tenga solucion para los 7.102 pares O-D observados. El Premetro
queda excluido: 56 tramos y 2 transbordos.

El nodo es (linea, estacion) y no la estacion sola porque el transbordo tiene
costo y tiene que ser arista explicita. Pueyrredon de la D y Santa Fe de la H son
dos nodos unidos por una arista de 90/112 s, no un mismo lugar.

### 2.1 Los 24 s de detencion no son una medicion

El feed declara **exactamente 24 s de detencion en toda parada de toda linea**,
sin una sola excepcion sobre 166 tramos, desvio 0,0. No distingue Constitucion de
Pasco, ni cabecera de estacion intermedia, ni hora pico de valle, porque el GTFS
no tiene bandas horarias.

Los teniamos anotados como "tiempo de detencion (~24 s)" salido de
`stop_times.txt`, y lo son, pero conviene precisar de que clase de dato se trata:
es un **valor nominal de diseño del horario**. La detencion real depende del
volumen que sube y baja, que es justo lo que el modelo produce. **En el modelo la
detencion tiene que ser endogena, con los 24 s como piso.** Lo mismo vale para
`min_transfer_time`, que es un minimo de diseño y no una caminata observada.

### 2.2 El GTFS no distingue tipos de dia

Los tres `service_id` (5 habil, 6 sabado, 7 domingo) tienen **secuencias y
horarios identicos**: una sola firma por ruta y sentido. La variacion por tipo de
dia tiene que salir de molinetes y de despachos, nunca del GTFS.

### 2.3 Alberti y Pasco fuerzan un grafo dirigido

Tienen **un solo anden cada una y se sirven en un unico sentido**: Alberti solo
hacia San Pedrito, Pasco solo hacia Plaza de Mayo (derivado del `trip_headsign`,
no afirmado a mano). Por eso la Linea A tiene 18 estaciones pero 17 paradas por
sentido, y por eso la red tiene 90 nodos y no 89. Un grafo no dirigido habria
inventado cuatro servicios que no existen.

### 2.4 El sentido 1 de la Linea E esta corrupto en el feed

**Defecto nuevo, no documentado por el publicador.** La columna
`shape_dist_traveled` del sentido 1 de la Linea E es **copia literal** de la del
sentido 0: los 18 valores coinciden posicion por posicion. Eso haria que Plaza de
los Virreyes-Varela midiera lo mismo que Retiro-Catalinas. Es la unica ruta del
feed con el defecto; en las otras siete la comprobacion da negativa.

Los tiempos del mismo sentido tampoco se salvan. Correlacion entre tiempo de
marcha y distancia, tramo a tramo:

| Conjunto | Correlacion t~km | Desvio de la velocidad |
|---|---:|---:|
| Resto de la red y E sentido 0 | 0,863 | 4,3 km/h |
| E sentido 1, contra su distancia publicada | **0,010** | 11,4 km/h |
| E sentido 1, contra la distancia real | 0,425 | 7,9 km/h |

La correlacion de 0,010 dice que el sentido 1 de la E esta **desacoplado de su
propia geometria**: estan mal las dos columnas, no una sola. El total si cierra
(11,71 km y 29 min 28 s en ambos sentidos), asi que el defecto es de reparto
interno y **pasa desapercibido en cualquier control agregado**. En los peores
tramos la diferencia llega a 61 s sobre 121 (San Jose-Independencia).

> **Reparo aplicado, a confirmar.** El sentido 1 de la E se
> reemplaza por el espejo del sentido 0, que es lo que hacen las otras cinco
> lineas: de 81 tramos emparejados entre sentidos, 64 tienen diferencia exacta
> cero y los 17 restantes son todos de la E. Interruptor `REPARAR_LINEA_E` en
> `src/03_grafo_red.py`.

### 2.5 Los transbordos dejan de ser un parametro declarado

28 aristas dirigidas sobre 104 pares de anden. El tiempo de nodo a nodo es la
**mediana** de los pares de anden del complejo, coherente con modelar la demanda por estacion: el anden de
origen es resultado de la asignacion de ruta, no dato de entrada. Minimo y maximo
quedan en el CSV para sensibilidad.

Rango 42-258 s. **Son direccionales**: Pueyrredon [D] a Santa Fe [H] son 90 s y
la vuelta 112 s. Las combinaciones mas caras son Carlos Pellegrini [B] con
Diagonal Norte [C] (243 s) y Catedral [D] con Bolivar [E] (220 s); la mas barata,
Leandro N. Alem [B] con Correo Central [E] (58 s).

### 2.6 Lo que este paso dejó abierto

- **Confirmar el reparo de la Linea E.** Sigue abierto. El paso 6 lo acotó:
  apagarlo cambia 58 pares de 6.006, o sea el 1,0 %, asi que para la eleccion de
  ruta pesa poco. Afecta si los tiempos de viaje sobre la E.
- **La detencion endogena** en el modelo, con 24 s de piso.
- El GTFS tiene **un unico perfil de marcha nominal**. Si la marcha se degrada en
  hora pico, el grafo no lo sabe: lo tiene que producir el modelo. El paso 4
  (intervalos entre despachos) es el primer contraste disponible.

---

## 3. Demanda por estación, franja de 15 min y tipo de día

`src/04_demanda_molinetes.py` · reporte en `reports/04_demanda.md` · salidas
`demanda_estacion_franja.csv`, `demanda_diaria.csv`, `concentracion_horaria.csv`,
`concentracion_por_estacion.csv` y `demanda_anden.csv` en `data/processed/`.

Paso 3 del plan, sobre molinetes 2025. **13.196.766 filas, 206.616.377
pasajeros**, que cierra contra los 206,5 millones del paso 1. La lectura sigue
siendo en streaming, pero todo se vuelca en una **matriz densa día × franja ×
estación** de 366×96×90 enteros (unos 12 MB), así que alcanza con una sola pasada
y quedan disponibles los totales por día, por línea y por estación sin
reprocesar.

Salida principal: **19.931 celdas** de (tipo de día, franja de 15 min, estación)
con media y desvío entre días. El desvío es el insumo del análisis de
sensibilidad y de la variabilidad entre replicaciones.

### 3.1 Los perfiles se construyen solo con días típicos

| Tipo de día | Días con dato | Días típicos | Pasajeros/día |
|---|---:|---:|---:|
| hábil | 260 | 235 | 689.768 |
| sábado | 52 | 52 | 339.420 |
| domingo | 52 | 52 | 182.104 |

Se excluyen 25 días hábiles atípicos y 1 hueco de datos. **Incluirlos arrastraba
el perfil de día hábil hacia abajo** sin representar ninguna operación real: la
primera versión del paso los promediaba y daba 687.125 pas./día en lugar de
689.768.

### 3.2 Un hueco de datos nuevo: el jueves 10/04/2025

**66 pasajeros en todo el día y 31 de 90 estaciones con algún registro.** No es
un día sin servicio: es un faltante del publicador. Queda excluido de todos los
perfiles y **no se rellena** (interpolar demanda es inventar dato), pero hay que
declararlo.

Es un defecto más de los no documentados del dataset, y se suma a los cinco que
ya resuelve `lib_molinetes.py`.

### 3.3 El viernes 08/08/2025 se cierra sin corrección

El paso 1 lo dejó anotado con 38.454 filas contra ~49.000 de los viernes
comparables, un 22 % menos, sin saber si era interrupción de servicio o faltante.
**Con los pasajeros a la vista el día es normal**: 786.551 pasajeros, razón 0,99
contra la mediana de los hábiles de agosto, 90 de 90 estaciones con dato.

La menor cantidad de filas no era menor demanda: agosto es uno de los dos
archivos con fechas `d/m/Y` y `m/d/Y` mezcladas, y el conteo de filas por día
quedaba distorsionado por esa reconstrucción. **No hay nada que corregir.** Lo
que sí queda marcado como anómalo en agosto es el viernes 15 (razón 0,51) y el
viernes 1.º (0,70).

### 3.4 Los 25 días atípicos hay que contrastarlos contra el calendario

Definición: día hábil por debajo del 80 % de la mediana de los hábiles del
**mismo mes**. El criterio es intramensual porque la estacionalidad es fuerte;
contra la mediana anual saldría enero entero.

La forma de la lista es compatible con el calendario de feriados (1/1, 1/5,
25/12, el 24 y el 31, los lunes de carnaval, los puentes) **pero compatible no es
verificado**. El método detecta anomalías, no feriados: un paro o un corte de
servicio aparece igual, así que en este paso quedaba sin verificar contra una
fuente externa. Lo cerró el paso 4: la columna `Tipo Día` del dataset de
despachos es el calendario operativo del propio operador y confirma el criterio.
Los días atípicos quedan fuera del perfil de día hábil y no se reasignan a
domingo, que sería un supuesto sin sustento.

### 3.5 La concentración horaria: las dos cifras de la Línea F no cierran

**Es el control que la propuesta declaraba pendiente, y ya está hecho.**
La hora pico se busca como la ventana móvil de 60 min de mayor ingreso; fijarla
de antemano sería suponer el resultado.

| Nivel | Concentración en la hora pico |
|---|---|
| Red, día hábil típico | **9,9 %** (desvío 0,43 pp) |
| Línea más apuntada (E) | 12,0 % |
| Línea menos apuntada (H) | 9,0 % |
| Constitución [C] | 17,5 % |
| Estación más apuntada (Catalinas [E]) | 30,0 %, con 4.646 ingresos/día |

Para que los ≈73.900 ascensos de hora pico de SBASE fueran compatibles con los
270.000-300.000 pasajeros diarios anunciados, la Línea F tendría que concentrar
cerca del **25 %** de su demanda diaria en una hora. Dos lecturas del mismo
hecho:

1. Si la Línea F se pareciera a la red actual, esos 73.900 ascensos implicarían
   del orden de **743.000 pasajeros diarios**, entre 2 y 3 veces la cifra
   anunciada.
2. Si la cifra anunciada fuese correcta, la línea tendría que concentrar 2,5
   veces lo que concentra la red y 2,1 veces lo que concentra la línea E.

> **Las dos cifras no son conciliables entre sí. Al menos una está mal, y el
> trabajo no puede decidir cuál con la información disponible.**

El contraste más directo es **Constitución**, que es el nodo de carga máxima de
la Línea F según SBASE y hoy ya existe en la Línea C alimentada por el mismo
ferrocarril Roca: recibe 57.010 ingresos diarios y concentra 17,5 % en hora pico,
o sea unos 9.950 ingresos. SBASE proyecta **32.640 ascensos de hora pico en un
solo sentido**, 3,3 veces eso y el 57,3 % de todo el ingreso diario actual de la
estación. Los transbordos del ferrocarril **sí pasan por molinete** (son sistemas
tarifarios distintos), así que están contados: la comparación no subestima la
demanda ferroviaria.

Salvedad de unidades, que acota sin cambiar la conclusión: los molinetes miden
ingresos y los ascensos de SBASE incluyen además los transbordos entre líneas de
subte, así que la cifra diaria implicada del punto 1 es una **cota superior**. La
comparación de *concentración*, por ser una proporción, no se ve afectada por el
nivel.

### 3.6 Reparto por andén: reproduce el 70,5 % del paso 1

**145.556.349 de 206.458.952 ingresos con sentido identificable, o sea 70,5 %**,
el mismo número que midió el paso 1 por otra vía. Hay **62 estaciones de 90** con
algún ingreso atribuible; entre ellas la cobertura mediana es 98,6 %. Las 28
restantes no tienen el campo en ningún molinete.

Confirma la decisión de modelar la demanda por estación: el faltante no está repartido al azar, son estaciones
enteras. El contraste que queda es **parcial y sesgado por construcción**, útil
solo donde el dato existe.

### 3.7 Lo que este paso dejó abierto, y cómo se cerró

- **Contrastar los 25 días atípicos contra el calendario oficial.** Cerrado en
  el paso 4: la columna `Tipo Día` del dataset de despachos es el calendario del
  propio operador y confirma el criterio.
- **Declarar el hueco del 10/04/2025** junto con los otros defectos del dataset.
  Hecho.
- **Llevar el resultado de 3.5 a la propuesta.** Hecho: el documento reporta el
  9,9 % de la red, el contraste de Constitución y las dos lecturas del hecho.
- **Elegir los períodos de ajuste y validación.** Sigue abierto, pero la tabla
  diaria ya da los candidatos.

---

## 4. Intervalos entre despachos

`src/lib_despachos.py` y `src/05_despachos.py` · reporte en
`reports/05_despachos.md` · salidas `intervalos_despacho.csv` y
`despachos_diario.csv` en `data/processed/`.

### 4.1 El recurso agregado del portal no sirve

Teníamos anotado usar **"Formaciones despachadas - Total" (CSV,
2015 a la actualidad, archivo único)** y que *"su historia desde 2015 es
homogénea"*. **Las dos cosas son falsas**, verificado el 18/08/2026 sobre la copia
local y contra la API del portal:

- El contenido **termina el 22/10/2021**; el metadato dice
  `last_modified = 2019-06-04`.
- **Faltan 2016, 2017 y 2018 enteros**, y de 2015 hay 6 días.
- No es archivo único: el dataset publica **un recurso por año**, incluidos 2025
  y 2026.

Es el mismo patrón que `viajes_anual.csv`: un recurso agregado congelado mientras
el dataset siguió publicando por año. **Corregido en `contexto-del-proyecto.md`.**

Se descargaron `formaciones-despachadas-2025.csv` (45 MB) y
`formaciones-despachadas-2026.csv` (22 MB, hasta el 30/06/2026) de
`cdn.buenosaires.gob.ar/datosabiertos/datasets/sbase/subte-trenes-despachados/`.

El esquema anual es mejor que el del archivo Total: nombres legibles, causas en
texto y una columna **`Tipo Día`** con los valores `Habil`, `Sabado`, `Domingo` y
**`Feriado`**, el calendario operativo del propio operador.

### 4.2 Defectos de formato, resueltos en `lib_despachos.py`

Cuatro, todos no documentados por el publicador. **Usar siempre la librería.**

1. **Tres formatos de fecha en el archivo de 2025**: `d/m/aaaa` (75.535 filas),
   `dd/mm/aa` (395.488) y vacío. Ninguno es ambiguo (el componente de día llega a
   31 en los dos) pero el corte entre formatos **no es el mismo para todas las
   líneas** y hay dos pares (fecha, línea) presentes en los dos. Se verificó que
   no son duplicados sino partes distintas del mismo día: los números de orden no
   se solapan.
2. **Codificación por año**: 2025 es Latin-1 sin BOM, 2026 es UTF-8 con BOM. Cada
   archivo es internamente consistente. Se prueba UTF-8 estricto y se cae a
   Latin-1.
3. **24.696 filas completamente vacías** en 2025, en las veinte columnas.
4. **Causas con relleno de espacios**: sin recortar, "Falta de custodia policial"
   aparece como dos categorías distintas.

### 4.3 Intervalos en día hábil típico

Medidos **en cabecera**, sobre 663.709 intervalos de días hábiles completos, sin
despachos con causa. El intervalo que ve un pasajero en estación intermedia puede
degradarse por acumulación: eso es salida del modelo, no entrada.

| Línea | Pico (7-9 y 17-19) | Valle (11-15) | Trenes/h por sentido en pico |
|---|---:|---:|---:|
| C | 3,15 min | 4,28 min | 19,0 |
| A | 3,17 min | 3,82 min | 18,9 |
| H | 3,43 min | 4,10 min | 17,5 |
| D | 3,82 min | 4,27 min | 15,7 |
| B | 4,13 min | 4,38 min | 14,5 |
| E | 5,22 min | 5,88 min | 11,5 |

**Contraste con la Línea F.** El EsIA le fija un headway de **1,5 min, 40 trenes
por sentido y hora**. La mejor línea actual en hora pico es la C con 3,15 min:
**el diseño de la F supone despachar 2,1 veces más seguido que lo que hoy logra
la mejor línea de la red**. No es imposible (línea nueva, señalamiento nuevo) pero
es un supuesto fuerte del escenario futuro y **va como variable de escenario, no
como dato**. El documento ya declara 1,5 min como cota superior; esto le da la
magnitud.

### 4.4 Servicio no prestado

De 869.691 servicios de cabecera programados, **20.078 no se prestaron (2,31 %)**,
y el **100 %** tiene causa registrada. Principales: coche descompuesto (5.410),
huelga o paro general (3.122), conflicto gremial (1.924), falta de coches (1.733),
obra de modernización (1.631).

> **Trampa metodológica que conviene no repetir.** La primera versión de este paso
> filtraba los servicios no prestados antes de mirar las causas. El resultado era
> que las causas visibles eran las de los servicios **que sí se hicieron**, y un
> paro (que por definición cancela) desaparecía: la tabla mostraba 12 despachos
> gremiales en lugar de 5.060.

Las causas gremiales explican **5.060 servicios cancelados en 100 días**, el
25,2 % de todo el servicio no prestado del año. **Esos días no pueden entrar en
las ventanas de ajuste ni de validación**.

### 4.5 Marzo de 2025 no está

Faltan 30 de sus 31 días de despachos; solo sobrevive el 08/03. **Es un faltante
del publicador, no un mes sin servicio**: los molinetes registran demanda normal
en todo marzo (media de 710.875 pas./día en los hábiles no atípicos, razón 1,011
contra su propia mediana mensual), así que los trenes circularon. Marzo queda
fuera de cualquier ventana de ajuste o validación y deja sin verificar los cuatro días atípicos que
el paso 3 detectó ahí.

### 4.6 Dos correcciones cruzadas entre pasos

**El calendario del operador valida el criterio de días atípicos del paso 3.**
SBASE declara 13 feriados en 2025, 11 en día hábil. **El paso 3 detectó los 11,
sin conocer el calendario.** De los 14 días atípicos restantes: 6 están declarados
por SBASE como **servicio de sábado** pese a caer en día hábil (17/04, 02/05,
15/08, 21/11, 24/12, 31/12), o sea que el operador ya reconoce que no son
normales; 4 caen en marzo y no se pueden verificar; y 4 quedan sin explicación,
con servicio declarado normal (01/08, 26/12, 29/12, 30/12).

**El paso 4 corrige al paso 3 sobre el 10/04/2025.** El paso 3 lo había
clasificado como hueco de datos del publicador, con 66 pasajeros y 31 de 90
estaciones. **No lo era: fue un paro general.** Ese día hay 3.122 servicios
programados y **ninguno prestado**, todos con causa *Huelga / Paro General*. Dos
fuentes independientes que coinciden. El tratamiento no cambia (se excluye por no
ser representativo) pero la caracterización pasó de supuesta a verificada.

### 4.7 Coches por formación

Insumo directo de la capacidad del modelo: A y C y E despachan 5 coches (C y E con
algún 6), y B, D y H despachan 6. La capacidad por coche no sale de acá (depende
del modelo de material rodante) pero la cantidad sí.

### 4.8 Lo que este paso dejó abierto

- **Corregir lo que teníamos anotado sobre el recurso agregado** (punto 4.1).
  Hecho, en `contexto-del-proyecto.md`.
- **Los 4 días atípicos sin explicación** (01/08, 26/12, 29/12, 30/12): menor
  demanda con oferta declarada normal.
- **El contraste GTFS contra operación real sigue faltando.** Este paso mide
  despachos, no tiempos de recorrido; el GTFS da un perfil de marcha nominal
  único. El contraste completo necesita el modelo.
- Está descargado 2026 hasta el 30/06 y sin usar: sirve como segunda ventana si
  la elección de períodos la necesita.


---

## 5. Matriz origen-destino

`src/06_matriz_od.py`, con `src/lib_etapas.py` (extracción en streaming) y
`src/lib_complejos.py` (definición de la unidad espacial). Reporte en
`reports/06_matriz_od.md`. Salidas: `od_complejos.csv`, `matriz_od.csv`,
`od_ascensos.csv`, `factores_escalado.csv` y el intermedio
`molinetes_20241016.csv`.

**5.953 pares origen-destino** sobre 6.006 posibles (99,1 %), en **72.245
celdas** de (origen, destino, hora), que totalizan **740.568 etapas
expandidas** del 16/10/2024.

### 5.1 La unidad espacial es el complejo, y eso disuelve el residuo de ambigüedad

Registrábamos como residuo real de ambigüedad que las estaciones
superpuestas de un mismo complejo de combinación se confunden al matchear por
cercanía: Correo Central [E], Corrientes [H] y Santa Fe [H] no aparecen nunca, y
9 de Julio [D], Diagonal Norte [C] e Independencia [C] no aparecen como origen.

**El problema desaparece al cambiar de unidad.** Los 90 nodos se agrupan en
**78 complejos**, definidos como las componentes conexas del grafo de
transbordos del paso 2; las estaciones que se confunden son exactamente las que
el complejo agrupa. Y es la unidad correcta desde el modelo: el pasajero entra y
sale de un lugar físico, y por qué línea circula es resultado de la asignación
de ruta. Es el mismo criterio que usamos con los andenes.

Los 89 centroides h3 se asignan al complejo del **nodo más cercano**. Mediana
47 m, máximo 183 m, y (el control que importa) **margen mínimo de 89 m** contra
el complejo distinto más próximo.

> **Detalle que no es cosmético.** Matchear contra el centroide promedio del
> complejo en lugar del nodo más cercano baja ese margen mínimo de 89 m a **9 m**
> y deja Avenida de Mayo/Lima contra Piedras prácticamente empatado. Los
> complejos grandes se extienden más de 200 m y su promedio no representa a
> ninguna de sus estaciones.

### 5.2 La línea de ascenso resuelve el nodo exacto, y valida el grafo

`linea_etapa` es la línea del molinete que registró la transacción: dato
observado. **En las 587.980 etapas, sin una sola excepción, esa línea pertenece
al complejo de origen asignado.**

Dos consecuencias. El nodo de origen queda **completamente determinado** por el
par (complejo, línea de ascenso). Y es una **validación independiente de la
definición de complejo**, que sale del GTFS, contra una georreferenciación que
sale de otro organismo y otra metodología.

Aun así la línea de ascenso **no entra como insumo del modelo**: fijarla sería
fijar parte de la ruta, que es lo que la simulación tiene que producir. Queda
como contraste del reparto por línea que produzca el modelo, en paralelo exacto
con el contraste por andén.

### 5.3 El contraste se hace contra el mismo día, no contra 2025

Una etapa expandida es un **ingreso a la red**, directamente comparable con un
molinete. El contraste se hace contra el **16/10/2024**, el día que releva el
dataset, y no contra los niveles de 2025: octubre de 2024 es anterior al pago
sin contacto (01/12/2024), así que ambas fuentes miden el mismo universo de pago
y la comparación **no arrastra la ruptura de comparabilidad**. Cualquier
contraste contra 2025 mezclaría el desvío de la matriz con el corrimiento de
medios de pago y con la estacionalidad.

- Molinetes del día: **778.247 ingresos**. Cero sin match, cero centinelas.
- Matriz expandida: **740.568**.
- **Factor global 1,0509**: la matriz subregistra el 4,8 %.

### 5.4 Un defecto de imputación localizado: San Pedrito y San José de Flores

Es el hallazgo del paso. La matriz le pone a **San José de Flores 15.495
ingresos de más** y a **San Pedrito 14.848 de menos**; el neto del par es −647,
o sea que **el par cierra**. Son estaciones vecinas de la Línea A, a 664 m.

El matcheo está descartado como causa: cada centroide cae a 55 m de su estación
y a más de 600 m de la otra. Es la regla de imputación por parada más cercana
declarada por el organismo publicador, con tolerancia de 2,2 km, actuando sobre
dos estaciones próximas. **Este solo par explica el 35 % de todo el desvío
absoluto de la red**: excluyéndolo, el residuo de un factor único global cae de
11,2 % a 7,6 %.

### 5.5 Los nodos de trasbordo ferroviario subregistran de forma ordenada

Los cuatro puntos donde el subte toca un ferrocarril metropolitano quedan por
encima de la norma de la red, y en orden de importancia del ferrocarril:
**Constitución (Roca) 1,221**, Retiro 1,140, Once/Plaza Miserere 1,123,
Federico Lacroze 1,066, contra 1,015 de las estaciones simples. Concentran el
17,5 % de los ingresos del día.

Eso explica el único desvío de línea de la sección 4.1 del reporte: la **Línea C
con 1,263** contra 1,005-1,031 de las otras cinco. **El escalado por línea es,
en realidad, el escalado de los nodos ferroviarios visto de lejos.**

Es consistente con que el dataset reconstruya el viaje desde la transacción SUBE
y pierda parte de la etapa de subte cuando el viaje empieza en el ferrocarril.
Y toca directamente al trabajo: Constitución es el nodo de carga máxima
proyectada de la Línea F, y el EsIA destaca que el 70 % de los viajes con etapa
en la Línea C combinan con el ferrocarril.

### 5.6 Lo que este paso dejó abierto, y cómo se cerró

- **Cuál es la matriz del modelo.** Cerrado el 27/08/2026 a favor de la de
  SBASE, que viene expandida y no necesita escalado. Este paso ya había
  descartado el escalado por franja horaria, con un factor entre 1,035 y 1,082
  de 6 a 22 h y sin forma sistemática.
- **Las etapas incompletas.** Sigue abierto y se decide midiendo: `matriz_od.csv`
  trae `expandidas` y `expandidas_completas` en columnas separadas. Son 24.057
  etapas, el 4,1 %, que expanden a 30.491.
- **Qué hacer con el par San Pedrito / San José de Flores.** Dejó de importar:
  la matriz de SBASE no tiene el defecto, así que al cambiar de matriz no hay
  nada que reparar. Era un problema de imputación de la fuente y no un rasgo de
  la demanda.
- Las **84 etapas intracomplejo** (0,014 %) se descartan: son pares a distancia
  de caminata dentro de la misma combinación, no viajes de subte.


---

## 6. Caminos mínimos con penalización por transbordo

`src/07_caminos_minimos.py` con `src/lib_caminos.py`. Reporte en
`reports/07_caminos_minimos.md`. Salidas: `caminos_minimos.csv`,
`caminos_sensibilidad.csv` y `caminos_reparto_linea.csv`.

**6.006 pares ordenados** de complejos, todos alcanzables. Tiempo mediano
**16:04**, máximo 43:14. Reparto de transbordos: 22,1 % sin transbordo, 47,5 %
con uno, 30,5 % con dos. Media 1,08.

### 6.1 Los 24 s van por parada intermedia, no por tramo

Es el detalle que decide la corrección del costo. `t_s` del GTFS es marcha pura y
la detención de 24 s es columna aparte. El que asciende no espera la detención de
su estación de ascenso (esa es su ventana de abordaje) y el que desciende tampoco
espera la de la suya. **Contarlas por tramo abarataría en términos relativos los
caminos con muchas paradas**, que es justo el error que un grafo de subte no puede
darse.

Se implementa cargándole la detención a la arista de tramo y descontándosela a la
de transbordo. Para un camino cualquiera eso da el tiempo real más 24 s exactos
(la detención de la estación de descenso final), que es **la misma constante para
todo camino** y por lo tanto no altera el ordenamiento. Los pesos quedan todos
positivos porque el `min_transfer_time` más chico de la red es 58 s.

> **Verificado por recálculo independiente**: se recorrieron 400 caminos arista
> por arista aplicando la regla desde cero. Cero discrepancias en tiempo y en
> cantidad de transbordos.

### 6.2 Acceso y egreso dentro del complejo valen cero

El pasajero entra al complejo, no al andén: asciende en cualquiera de sus nodos y
desciende en cualquiera de los del complejo de destino, y se toma el mínimo. La
consecuencia buscada es que **caminar dentro del complejo de origen no cuente como
transbordo**, que sería falso. `pathways.txt` tiene los recorridos internos pero no
para toda la red; queda declarado como simplificación.

### 6.3 La penalización es un supuesto, y se recorre

El valor base de **120 s** sale de los despachos del paso 4: en hora pico los
intervalos van de 3,15 min (C) a 5,22 min (E), así que la espera esperada cae entre
95 y 157 s. Recorriendo de 0 a 300 s, los transbordos medios por camino van de 1,166
a 1,041 y cambian de camino hasta 495 pares (8,2 %) en el extremo. Es la decisión
**la penalización por transbordo**.

### 6.4 El contraste del reparto por línea, contra dos fuentes

La ruta nunca entró como insumo, así que el reparto por línea de ascenso que produce
se puede contrastar. Se hace contra **molinetes** (tercera fuente, independiente) y
contra `linea_etapa` del dataset O-D, porque ninguna de las dos es limpia y **donde
discrepan, discrepan por una razón identificable**.

- Error absoluto medio contra molinetes: **5,47 p.p.** sobre los diez complejos de
  combinación.
- Contra `linea_etapa`, excluyendo los dos complejos rotos: **4,71 p.p.**
- **Las dos fuentes observadas coinciden entre sí** en los ocho complejos sanos:
  difieren 0,74 p.p. en promedio. Eso le da piso al contraste.

**Hallazgo: en dos complejos el dataset O-D está roto y molinetes lo demuestra.** En
9 de Julio / Carlos Pellegrini / Diagonal Norte y en Independencia, el dataset
atribuye el 100 % de los ascensos a una sola línea. Molinetes reparte 62,8 / 18,6 /
18,6 en el primero y la ruta predice 59,7 / 15,6 / 24,8. **Molinetes le da la razón
al modelo, no al dataset.** Y son los mismos dos complejos que más subregistran en
el paso 5 (factores 1,635 y 1,374): el dataset colapsa el complejo sobre una
estación y en el camino pierde demanda.

Eso **refuerza la decisión de no meter la línea de ascenso como insumo**: si se
hubiera usado, el defecto entraba directo a la entrada del modelo.

### 6.5 Retiro: la única discrepancia real, con dos hipótesis descartadas

Las dos fuentes coinciden (85,5 % por la C en molinetes, 83,9 % en `linea_etapa`)
y la ruta predice 69,8 %. Se probaron dos explicaciones y las dos fallaron:

1. **El reparo de la Línea E.** Se regeneró el grafo con `REPARAR_LINEA_E =
   False`, con respaldo y verificación de restauración byte a byte. Cambian **58
   pares de 6.006 (1,0 %)** y 18 cambian de línea de ascenso; **el reparto de Retiro
   no se mueve**. Dato útil por sí solo: el reparo importa poco para la
   asignación.
2. **Penalización uniforme que no distingue frecuencias.** Se probó reemplazarla por
   la espera esperada de cada línea (mitad del intervalo de hora pico del paso 4: A y
   C 94 s, H 103, D 111, B 121, E 156). **Empeora el ajuste**, de 5,47 a 7,36 p.p.
   Se descarta y se conserva la uniforme.

Queda una explicación no verificable: el sesgo de las fuentes. Retiro [C] y Retiro
[E] están a 151 m y la terminal ferroviaria descarga sobre el acceso de la C. **Se
declara como discrepancia abierta y no se corrige**: corregirla sería ajustar la
ruta contra una fuente cuyo sesgo apunta justo en esa dirección.

### 6.6 Lo que este paso dejó abierto, y cómo se cerró

- **El valor de la penalización por transbordo.** Cerrado en el paso 10: se
  conservan los 120 s, pero ahora se sabe que el dato no alcanza para fijar el
  parámetro por encima de 30 s, y que el indicador central es poco sensible a
  él.
- La asignación es **todo-o-nada**: cada par manda todo su flujo por un camino.
  Está medido cuánto pesa: **50 pares** tienen una alternativa por otra línea a menos
  de 60 s, que es 0,8 % del total pero **6,5 % de los 770 pares que realmente tienen
  elección** (en los otros 5.236 el complejo de origen tiene una sola línea). Sigue
  siendo una simplificación declarada.
- **La discrepancia de Retiro** queda abierta y declarada.
- El paso 6 es **verificación, no validación**: comprueba una tabla precalculada
  contra fuentes observadas, no el comportamiento del modelo de simulación.

---

## 7. Matriz O-D y perfiles de carga de SBASE (paso 9 del plan, Ley 104)

No estaba en el plan. Lo abrió la respuesta a la solicitud Ley 104 N° 00866317/26,
llegada el 26 y el 27 de agosto de 2026. Código en `src/lib_sbase.py` y
`src/09_sbase_od_carga.py`; medición completa en `reports/09_sbase_od_carga.md`;
ficha documental de la respuesta en
`docs/respuestas-oficiales/respuesta-ley104-00866317.md`.

### 7.1 Las planillas venían dentro del PDF

El correo traía tres PDF y ningún XLSX. Las dos planillas de SBASE están **embebidas**
en `IF-2026-38553261-GCABA-SBASE.pdf` como `/Names /EmbeddedFiles`, guardadas sin
extensión y con nombre largo. Un visor que no muestre el panel de adjuntos no deja ver
que existen. Se extrajeron con `pypdf` a `data/raw/sbase-ley104/` y se versionan
además en `docs/respuestas-oficiales/adjuntos-sbase/`, porque no son datos abiertos y
no se pueden volver a descargar.

### 7.2 Dos mapas de identificador que no son el mismo

Los dos libros numeran las 90 estaciones de 1 a 90. **Coinciden hasta el id 75 y
difieren en los quince últimos**: la matriz O-D ubica la cola de la Línea E (Correo
Central, Catalinas, Retiro E) al final de todo, después de la Línea H, y el perfil de
carga la ubica antes. Usar el mapa de un libro con los datos del otro corre quince
estaciones y **no produce ningún error**: los totales cierran igual y el defecto solo
se ve mirando qué estación quedó dónde. `lib_sbase` tiene un lector de ids por libro y
falla si el cruce no da 90 de 90.

### 7.3 El cruce con el grafo es uno a uno

Las 90 estaciones de SBASE son exactamente los 90 nodos del paso 2: 18 A, 17 B, 9 C,
16 D, 18 E y 12 H. Los nombres vienen abreviados (`SnzPena`, `PJunta`, `Scal Ortiz`) y
los que se repiten entre líneas llevan sufijo (`CallaoB` / `CallaoD`, `RetiroE`,
`Independencia E`, `Mariano Moreno` para el de la C frente a `Moreno` para el de la
E). El cruce es la tabla `ALIAS`, declarada a mano, sin comparación difusa, igual que
en `lib_normalizacion`.

### 7.4 Qué significa cada columna del perfil de carga

Las columnas son `S`, `B` y `P` por sentido. `S` son ascensos y `B` descensos; **`P`
es la carga a bordo en el tramo que sale de esa estación**, no los pasajeros que
permanecen. Se verificó sobre el propio archivo: en la Línea A hacia Plaza de Mayo, la
carga en Piedras (5.104,7) menos los descensos de Perú (3.084,3) más los ascensos de
Perú (51) da 2.071,5, que es a la vez la carga en Perú y lo que baja en Plaza de Mayo,
donde la carga es cero.

Segundo detalle: **los dos sentidos de un bloque comparten una única lista de
estaciones**, en un solo orden. Para uno de los dos sentidos esa lista va al revés de
la marcha. Deducir el sentido del orden de las filas da el sentido invertido en la
mitad de los casos, y como el perfil de ida y el de vuelta tienen magnitudes
parecidas, el error no salta a la vista: se detecta solo porque la carga en la cabecera
de salida da cero, que es imposible. El sentido se resuelve por el **nombre de la
cabecera** que encabeza cada bloque.

### 7.5 Qué habilita

- **La ocupación a bordo pasa a tener contraparte empírica** en hora pico. Era la
  debilidad declarada más seria del trabajo.
- **La asignación de ruta del paso 6 queda validada**: cargar la matriz de hora pico
  sobre el grafo con los caminos precalculados reproduce la carga observada por tramo
  con correlación 0,994 (mañana) y 0,985 (tarde), error absoluto ponderado de 6,5 % y
  8,4 % y sesgo casi nulo.
- **La tasa de transbordo se puede medir**: 1,371 y 1,426 ascensos por viaje
  observados, contra 1,410 y 1,437 del modelo.
- **Cuarta fuente del reparto por línea** en los complejos de combinación, y la única
  que no comparte origen con las otras tres. Le da la razón a molinetes en Retiro y
  deja al modelo como el que se aparta.

### 7.6 Lo que este paso dejó abierto, y cómo se cerró

- **Cuál de las dos matrices es la del modelo.** Se decidió por la de SBASE, y
  el armado está en el paso 11.
- **La penalización ganó función objetivo**, o sea que se podía recorrer
  midiendo el error de carga. Es lo que hizo el paso 10.
- **La discrepancia de Retiro deja de ser una discrepancia entre fuentes** y pasa a
  ser un error del modelo, con tres fuentes coincidiendo en contra.
- Los perfiles son **solo de hora pico**; el resto del día de servicio sigue sin
  contraparte.

---

## 8. Calibración de la penalización por transbordo (paso 10 del plan)

`src/10_calibracion_penalizacion.py`; reporte en
`reports/10_calibracion_penalizacion.md`; salida `calibracion_penalizacion.csv`.

Criterio fijado **antes** de correr: penalización de 0 a 300 s de a 10 s, métrica el
error absoluto ponderado de la carga por tramo, **calibrando con la hora pico mañana y
validando con la tarde**. Esa partición no es decorativa: sin ella, el contraste de
carga del paso 7 dejaría de ser validación y pasaría a ser verificación circular.

**El resultado es que el dato no identifica el parámetro.** Entre 30 y 300 s el error
se mueve 0,26 puntos porcentuales; la muestra de calibración elige 30 s y la de reserva
elige 270 s; y el control de reparto por línea, que no participa del ajuste, empeora de
7,23 % a 9,00 % si se toma el argmin. Lo único que el dato fija es una **cota inferior
dura de 30 s**: por debajo, el modelo manda gente a combinar por caminos que nadie usa
y el reparto de Retiro por la Línea C se desploma a 29,4 %.

Se conservan los **120 s** del paso 6, ahora por una razón medida y no por defecto.

> **Consecuencia que hay que arrastrar al informe**: el contraste de carga en hora pico
> mañana **pasó a ser calibración**. La validación es la hora pico tarde. Es el mismo
> movimiento que ya hubo que hacer con los intervalos de despacho en el paso 4.

## 9. La matriz de demanda del modelo (paso 11 del plan)

`src/11_demanda_modelo.py`; reporte en `reports/11_demanda_modelo.md`; salidas
`demanda_modelo_od_hora.csv` y `demanda_modelo_intrahorario.csv`. Implementa la
decisión sobre la matriz del modelo.

Cuatro piezas, cada una de la fuente que mejor la mide: el **nivel y la distribución
espacial** de la matriz diaria de SBASE; las **horas 8-9 y 17-18** ancladas a las
matrices de hora pico de SBASE sin modificarlas; el **resto del día** desagregado con el
perfil horario por par del paso 5, reescalado para que el total del par cierre; y los
**bloques de 15 minutos** desde molinetes, que entran solo como forma.

Detalles de implementación que conviene no volver a deducir:

- El perfil intrahorario va en **archivo aparte**. Multiplicarlo dentro daría 450.000
  filas y mezclaría dos supuestos distintos en una sola tabla.
- **No hay residuos negativos**: para ningún par la suma de las dos horas pico supera el
  total diario. Se verifica en el script y aborta si aparece uno.
- 44 pares no tienen perfil horario en el paso 5 y 9 lo tienen concentrado enteramente
  dentro de las dos horas pico. Los dos casos caen al perfil horario de la red. Son el
  0,2 % de los viajes.
- Los 687 viajes diarios **entre nodos de un mismo complejo** quedan afuera: en el
  modelo son una caminata dentro de la estación, no un viaje en tren.

**El control que importa**: la hora más cargada del resultado queda en 9,7 %,
consistente con el 9,9 % que miden los molinetes y con el 9,0 % y 9,7 % de las matrices
de SBASE por separado. Mezclar dos matrices podía haber producido un perfil que ninguna
fuente respalda, y no lo produjo.
