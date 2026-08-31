# Contexto del proyecto

Documento de referencia del grupo. Junta qué estamos haciendo, con qué datos, qué
sabemos de la Línea F y con qué respaldo, qué decidimos y por qué, y cómo trabajamos
en el repositorio. Si una cifra no está acá o en las fichas que este documento
referencia, no la usamos.

---

## 1. Qué es este trabajo

Trabajo Práctico Integrador de la materia Simulación, UTN Facultad Regional Rosario.
Grupo de cinco integrantes.

El objetivo es armar un modelo de simulación de eventos discretos en AnyLogic de la red
de Subte de la Ciudad de Buenos Aires, calibrado con datos públicos, para comparar cómo
funciona la red actual contra un escenario futuro que incluya la Línea F.

El título del trabajo es *Evaluación mediante simulación del impacto de la Línea F sobre
la operación de la red de Subte de Buenos Aires*.

El enfoque con el que arrancamos, que era la regularidad de despachos y la congestión de
una sola línea, quedó descartado. Todo lo que escribamos responde al enfoque actual, que
es la red completa y la evaluación de una obra de infraestructura.

### La propuesta

El documento de propuesta es `docs/definitivo-main.tex`: 8 páginas más referencias, 16
entradas bibliográficas y dos figuras. Compila limpio y ya está cerrado. La estructura es
Introducción, Propuesta (Problema, Objetivos, Metodología y Resultados esperados) y
Referencias. No lleva marco teórico.

Necesita el paquete `enumitem`; sin él no compila.

El informe final del TPI va a ser un documento aparte, que todavía no empezamos.

---

## 2. Estado

El pipeline de datos está cerrado. Lo que falta es el modelo.

| Bloque | Estado |
|---|---|
| Propuesta escrita | Cerrada |
| Pipeline de datos (pasos 1 a 6, y 9 a 11) | Cerrado |
| Insumos que consume el modelo | Generados y verificados |
| Límites de AnyLogic PLE | Medidos |
| Modelo en AnyLogic (pasos 7 y 8) | Pendiente |

Del pipeline, el modelo consume cinco archivos, todos en `data/processed/`:

| Archivo | Contenido |
|---|---|
| `grafo_nodos.csv` | Los 90 nodos de la red (par línea-estación) |
| `grafo_aristas.csv` | 166 aristas de tramo y 28 de transbordo, con sus tiempos |
| `caminos_minimos.csv` | La ruta de menor tiempo percibido para cada uno de los 6.006 pares |
| `demanda_modelo_od_hora.csv` | 827.289 viajes del día hábil, en 71.686 celdas de (par, hora) |
| `demanda_modelo_intrahorario.csv` | Reparto en bloques de 15 minutos |

El detalle de cada columna está en `docs/guia-del-modelo.md`. Cómo se armó cada uno está
en `docs/preparacion-de-datos.md`, y los resultados de cada paso en `reports/`.

---

## 3. La Línea F

Todo lo de esta sección sale del expediente de evaluación ambiental, del pliego de
licitación o de respuestas oficiales. Las fichas de detalle son
`docs/expediente-eia-linea-f.md`, `docs/pliego-licitacion-linea-f.md` y
`docs/respuestas-oficiales/respuesta-ley104-00866317.md`.

Para cualquier cifra de la Línea F conviene ir a esas fichas y no a los PDF sueltos ni a
los diarios. Las fichas ya tienen las tablas pasadas en limpio, las verificaciones hechas
y las contradicciones marcadas.

### 3.1 El proyecto

- Proyecto "Línea F, Sistema Integrado de Movilidad". La titularidad es de la
  Subsecretaría de Proyectos y Obras del Ministerio de Movilidad e Infraestructura del
  GCBA. SBASE quedó al margen del proceso.
- La traza está establecida por la Ley 670/2001 de la Legislatura porteña y sus
  modificatorias. El antecedente de planificación es el PETERS, que hizo SBASE con el BID
  y elaboró AC&A, publicado en 2015.
- Recorrido: desde Gral. Hornos y Aráoz de Lamadrid, en Barracas, por debajo de Gral.
  Hornos, Av. Juan de Garay, Solís, Av. Entre Ríos, Av. Callao hasta Pacheco de Melo, Av.
  Gral. Las Heras y Av. Santa Fe, hasta Av. Int. Bullrich y Juan B. Justo, en Palermo.
  Pasa por las comunas 1, 2, 3, 4 y 14.
- Combina con las seis líneas existentes y con los ferrocarriles Roca y San Martín.
- La licitación es pública nacional e internacional, proceso 10241-0094-LPU25, expediente
  EX-2025-43793855-GCABA-DGTALMI, en el portal BA Obras. Es por ajuste alzado, con
  anticipo financiero del 20 %.
- La evaluación de impacto ambiental va por Ley 123, Resolución 195-2026-GCABA-APRA,
  expediente EX-20211143-GCABA-APRA/26. La audiencia pública fue el 18/08/2026.

### 3.2 Cifras confirmadas

| Dato | Valor | Procedencia |
|---|---|---|
| Estaciones | 12 | EsIA |
| Longitud de línea comercial | 9,8 km | Pliego de licitación |
| Longitud de túneles | 10,9 km | Convocatoria a audiencia pública |
| Presupuesto oficial | USD 1.350.000.000 | RESOL-2026-175-GCABA-MMIGC y PLIEG-2026-30055586 |
| Apertura de ofertas | 10/09/2026, 13:00 | RESOL-2026-175-GCABA-MMIGC |
| Inicio de servicio previsto | 2031 | Cronograma oficial |

Las tres longitudes que circulan no se contradicen, son magnitudes distintas. Los 9,8 km
son la línea comercial y es la cifra que usamos para dimensionar el servicio. Los 10,9 km
son de túneles. Y los 8,6 km que aparecen en la tabla de reparto de demanda del PETERS
que reproduce el EsIA son la traza del PETERS de 2015, no la del proyecto actual.

Cuidado con el "ocho de ellas de combinación" que salió en los diarios: no figura en el
expediente, y el EsIA declara seis combinaciones.

Sobre los nombres de estación, el propio EsIA usa denominaciones dobles y triples y lo
aclara: "se presentan todas las posibles denominaciones asignadas hasta la fecha sobre
cada estación". Para el modelo lo que importa es el número de orden 1 a 12; los nombres
son alias. El listado completo con todos los alias está en la ficha del expediente.

### 3.3 Distancias entre estaciones

Es dato oficial desde el 20/08/2026, del informe IF-2026-37530623-GCABA-MMIGC, en metros:

| Tramo | m | Tramo | m |
|---|---:|---|---:|
| Brandsen a Constitución | 1.300 | Pizzurno a Junín | 800 |
| Constitución a Cochabamba | 1.500 | Junín a Pueyrredón | 700 |
| Cochabamba a Chile | 700 | Pueyrredón a Parque Las Heras | 1.000 |
| Chile a Congreso | 800 | Parque Las Heras a Ecoparque | 1.000 |
| Congreso a Corrientes | 600 | Ecoparque a Palermo/Pacífico | 800 |
| Corrientes a Pizzurno | 600 | | |

Suman 9.800 m exactos, que es la longitud comercial del pliego, y coinciden dentro de 150
m con las progresivas del EsIA. Es el insumo que nos faltaba para armar el escenario
futuro.

### 3.4 Parámetros operativos

Son dato oficial, no supuestos nuestros. Todos están en la ficha del expediente con
número de página: 1.075 pasajeros por formación, 40 trenes por sentido y hora, headway de
1,5 min, detención de 30 s, velocidades de 90, 70 y 45 km/h, aceleración de 1 m/s²,
frenado de 1,1 m/s², flota de 25 formaciones, andén central y combinación peatonal de
hasta 100 m.

El IF-2026-37530623-GCABA-MMIGC agregó cuatro precisiones: un intervalo de diseño de 100
s "de requerirse", que no contradice los 1,5 min del EsIA porque las dos son capacidades
de diseño; velocidad máxima de 90 km/h "en algún tramo"; tiempo de viaje entre cabeceras
de unos 18 min para 9,8 km, o sea 32,7 km/h comerciales; y formaciones de seis coches,
con el Alstom Serie 300 como parámetro de diseño.

Hay algo importante en ese mismo informe: no hay plan de servicio de la Línea F y no va a
haberlo hasta que haya operador. Textual: "El responsable de la Operación, que no forma
parte del alcance de esta Licitación, definirá la Operación […] decidirá la frecuencia de
viajes para diferentes franjas horarias en función de atender la demanda así como los
tiempos finales de detención". Es una cita oficial que respalda tratar la frecuencia y la
detención como variables de escenario, así que no es una limitación que nos pongamos
nosotros.

### 3.5 Etapas y habilitación

El EsIA parte la obra en dos tramos constructivos. El Tramo A va desde el inicio de la
traza hasta Pizzurno, o sea Brandsen, Constitución, Cochabamba, Chile, Congreso,
Corrientes y Pizzurno. El Tramo B va desde Pizzurno hasta Palermo/Pacífico. El "primer
tramo" de los anuncios previos, que terminaba en una estación "Tucumán", no coincide con
esta partición, así que usamos la del EsIA.

Pero el IF-2026-37530623-GCABA-MMIGC dice otra cosa sobre la habilitación: la línea "se
desarrollara en UNA (1) única Etapa, desde Brandsen a Palermo / Pacífico" y no se prevé
habilitación parcial antes de terminar toda la obra. Si se justificara una apertura
parcial del tramo sur, sería en los últimos 6 meses.

La lectura que concilia las dos fuentes es que la partición del EsIA es constructiva y
esta respuesta es sobre habilitación al servicio. En la práctica esto significa que hay un
solo escenario futuro, la traza completa, con variantes de frecuencia. El escenario de
"primer tramo" lo sacamos de la propuesta.

### 3.6 Demanda: dos cifras que no cierran

El EsIA publica el perfil de carga por estación, sentido y hora pico, con cuánta gente
sube, baja y permanece. Lo tomó del *Análisis de Demanda Línea F* de SBASE, 2019. Está
transcripto en la ficha del expediente, sección 4, y es nuestro punto de comparación para
el escenario futuro.

La cifra anunciada de 270.000 a 300.000 pasajeros diarios no tiene respaldo documental:
no aparece en ninguna pieza del expediente. La citamos como estimación anunciada, nunca
como insumo del modelo.

Y las dos cifras no cierran entre sí. Los ascensos de hora pico de las tablas de SBASE
suman unos 73.900 pas./h. Para que eso sea compatible con 270.000 a 300.000 diarios, la
hora pico tendría que concentrar cerca del 25 % de la demanda diaria. Medimos la red real
sobre molinetes y concentra 9,9 %, con ninguna línea por encima del 12,0 %. Se puede leer
de dos maneras:

- Si la Línea F se pareciera a la red actual, sus 73.900 ascensos de hora pico
  implicarían del orden de 743.000 pasajeros diarios, entre 2 y 3 veces lo anunciado.
- Si la cifra anunciada fuese correcta, la línea tendría que concentrar 2,5 veces lo que
  concentra la red.

Al menos una de las dos está mal y el trabajo no puede decidir cuál. Está escrito así en
la propuesta.

La comparación más directa, y la que conviene usar, es la de Constitución de la Línea C,
que es el mismo nodo y el mismo ferrocarril Roca. Hoy recibe 57.010 ingresos diarios y
concentra 17,5 % en hora pico, unos 9.950 ingresos. SBASE proyecta 32.640 ascensos de
hora pico en un solo sentido para la Constitución de la F, que son 3,3 veces eso y el
57 % de todo el ingreso diario actual de la estación. Los transbordos del ferrocarril
pasan por molinete, así que la comparación no los subestima.

### 3.7 El objetivo de descongestionar la Línea C

Figura en comunicación oficial del GCBA, así que se puede citar y no es una inferencia
nuestra. El expediente lo refuerza:

- El PETERS "plantea a la Línea F como la alternativa para que la Línea C opere sin
  congestión con proyección de la demanda para 2030".
- La Secretaría de Transporte amplía el objetivo: el proyecto "contribuirá a descomprimir
  las líneas C y D".
- Un dato que se puede contrastar con nuestra matriz O-D: "el setenta por ciento (70 %)
  de los viajes que incluyen una etapa en esta línea [la C] corresponden a combinaciones
  con el ferrocarril".

---

## 4. Fuentes de datos

Las públicas están todas en `data.buenosaires.gob.ar`. Esta sección documenta también los
problemas de cada fuente, que en varios casos el publicador no documenta y nos costó
encontrarlos.

### 4.1 GTFS de Subte

Es el más importante, porque de acá salen la topología y los tiempos.

Cuidado con la descarga: `subte-gtfs-zip.zip` contiene un único archivo sin extensión
llamado `subte_gtfs`, que a su vez es el ZIP con los 14 `.txt`. Hay que desanidar dos
veces.

| Archivo | Aporta |
|---|---|
| `stop_times.txt` (715 filas, 48 viajes) | Secuencia de estaciones, horarios por parada y `shape_dist_traveled`. Tiempos de tramo, tiempo de detención y distancias |
| `transfers.txt` (112 pares, tipo 2) | `min_transfer_time` por par de andenes: de 42 a 258 s, mediana 132 s |
| `stops.txt` (709) | 108 estaciones, 214 andenes y 386 accesos, con `parent_station`. Los andenes van codificados por sentido |
| `pathways.txt` (967) | Recorridos internos de estación |
| `routes.txt` | 6 líneas más el Premetro, que queda fuera de alcance |
| `frequencies.txt` (150) | No lo usamos. Los headways van de 170 a 1160 s y son prepandemia |

Sobre la vigencia: `feed_info.txt` declara `feed_end_date=20191231` y `calendar.txt`
termina el 20211231. El portal avisa que "todos los datasets con Formato API y GTFS, están
suspendidos. Se encuentran en revisión y corrección". Igual la topología sigue vigente,
porque incluye la extensión de la E a Retiro y la H hasta Facultad de Derecho, y los
tiempos son magnitudes físicas estables. Usamos topología y tiempos, pero no las
frecuencias.

El feed no distingue día hábil de sábado ni de domingo: los tres `service_id` son
idénticos. La variación por tipo de día sale de molinetes y despachos.

### 4.2 Viajes Molinetes

Son ZIP anuales, con una fila por molinete, estación y bloque de 15 minutos, separando
pasajeros pagos, con pase y franquiciados. Registra ingresos, no destinos. No usamos 2020
ni 2021.

Hay un cambio de comparabilidad a tener en cuenta. Los archivos de 2024 de enero a
noviembre se llaman `PAX15min-ABC.csv` y desde diciembre de 2024 pasan a
`PAX15min-ABC-INCLUYEOTROMODOSDEPAGO.csv`. El esquema de columnas es el mismo, lo que
cambia es qué se cuenta, por la apertura a medios de pago distintos de SUBE: pago sin
contacto desde el 01/12/2024 y QR desde el 12/05/2025. Hacia septiembre de 2025 un tercio
de los viajes ya se pagaba fuera de SUBE. Por eso los dos períodos de trabajo tienen que
caer después de diciembre de 2024.

Lo medimos y el salto no aparece. Sumando `pax_TOTAL` mes a mes sobre los dos ZIP
anuales, 2024 va de 435.534 a 639.412 pasajeros por día según el mes y 2025 va de 405.577
a 653.865, sin ningún salto entre noviembre y diciembre de 2024: pasa de 556.596 a
501.527, que es la estacionalidad de diciembre, y enero de 2025 baja igual que enero de
2024. La serie de 2025 corre entre 7 % y 10 % por encima de la de 2024, y eso es
crecimiento y no un escalón de un tercio. Lo que mejor lo explica es que el molinete
cuenta pasadas y no medios de pago. Lo respalda SBASE, que declara que en septiembre de
2024 SUBE ya era más del 95 % de las transacciones.

No levantamos la restricción, porque conviene seguir tomando las dos ventanas después de
diciembre de 2024, que además es lo que hace SBASE. Pero deja de ser un riesgo grande y
no corresponde citarla como si valiera un tercio del nivel.

El ID de molinete codifica el andén, con formato tipo `LineaB_Gardel_S_Turn02`, lo que
permitiría trabajar la demanda por andén. El problema es que el formato es inconsistente:
hay `N`, `S`, `E` y `O`, también `Oeste` y `Este` escritos completos, `HALL`, `NE`, y
molinetes sin sufijo. Lo normalizamos con reporte de los que no matchean.

### 4.3 Trenes despachados

Informa día, tipo de día, horario, línea, tipo de viaje y causa. El mismo dataset incluye
"Estado de flota", que sirve para justificar la flota disponible por línea.

No conviene usar "Formaciones despachadas - Total". Lo verificamos contra la copia local y
contra `package_show` de la API del portal: ese recurso está congelado, con
`last_modified = 2019-06-04`, su contenido termina el 22/10/2021 y le faltan 2016, 2017 y
2018 enteros. Es el segundo recurso agregado del portal que encontramos muerto.

Hay que usar los recursos por año, que el dataset sí mantiene: hay uno por cada año hasta
2026, en `cdn.buenosaires.gob.ar/datosabiertos/datasets/sbase/subte-trenes-despachados/`.

El esquema anual además es mejor: nombres de columna legibles, causas en texto en vez de
códigos, y una columna `Tipo Día` con los valores `Habil`, `Sabado`, `Domingo` y
`Feriado`, que es el calendario operativo del propio operador.

Falta marzo de 2025 entero, 30 de 31 días. No es un mes sin servicio, porque los molinetes
registran demanda normal: es un faltante del publicador, y condiciona qué períodos podemos
elegir.

### 4.4 Estaciones y agregados

Bajamos "Estaciones de Subte" en CSV y GeoJSON, y "Líneas de Subte" en GeoJSON. El CSV
trae 90 filas con `id, estacion, linea, geometry`, o sea una lista de puntos, sin
topología. La adyacencia y el orden salen del GTFS.

`viajes_anual.csv` está discontinuado. Lo verificamos contra la API del portal: el recurso
"Total de pasajeros de cada línea de subte por año. Desde junio 2013" tiene
`last_modified = 2020-09-07` y trae 48 filas, de 2013 a 2020. El "desde junio 2013" del
título y la fecha de actualización que muestra la página son del dataset, no del recurso.

Eso deja al trabajo sin control agregado de pasajeros por línea y año para el período que
necesitamos. En su lugar contrastamos el reparto de demanda entre líneas contra el dataset
de viajes y etapas, que es fuente independiente.

También usamos "Cronograma de servicio", que trae cabeceras, cronograma de invierno y
verano y cantidad de coches, y sirve para la capacidad de formación; "Frecuencia del
subte", como contraste nominal; y "Bocas de Subte", con la localización de accesos.

### 4.5 Viajes y etapas en transporte público del AMBA

Es la única fuente de destinos abierta. Usamos Viajes 2024, Etapas 2024, el diccionario de
datos y el documento de metodología.

Lo que verificamos sobre `etapas_BAdata_20241016.csv`, con un barrido completo:

- 8.701.427 filas: 7.095.528 de colectivo, 1.017.919 de tren y 587.980 de subte.
- Las etapas de subte expanden a 740.675 en el día tipo. El sufijo `20241016` es la fecha
  del día relevado, o sea el 16 de octubre de 2024, no la de publicación.
- Reparto por línea de ascenso: B 142.543, D 128.001, A 116.988, C 75.375, H 63.353 y E
  61.720. No hay etapas de Premetro aunque la metodología dice incluirlo.
- 7.102 pares O-D distintos sobre 8.100 posibles, y ninguna etapa con origen igual a
  destino.
- Asimetría de la matriz del 19,8 %. La regla de simetría diaria no la fuerza a ser
  simétrica, así que hay direccionalidad real.
- Doble pico horario, con máximo a las 17 h (72.405) y a las 8 h (69.795).
- 4,1 % de etapas marcadas con `viaje_incompleto = t`.
- Una ventaja que no es obvia: el 16/10/2024 es anterior al pago sin contacto, así que la
  cobertura SUBE de esta edición es casi completa. Las ediciones futuras van a
  subregistrar.

### 4.6 Matriz O-D y perfiles de carga de SBASE

No es un dataset abierto, llegó por Ley 104. Son dos XLSX que venían embebidos dentro del
PDF `IF-2026-38553261-GCABA-SBASE.pdf`, no como adjuntos del correo. La copia está en
`docs/respuestas-oficiales/adjuntos-sbase/`.

| Planilla | Aporta |
|---|---|
| `matrices-od-sbase-emova-2024.xlsx` | Matriz O-D de 90 por 90 estaciones en tres hojas: `Diaria` (827.976 viajes), `HPM` de 8 a 9 h (74.351) y `HPT` de 17 a 18 h (80.197). Es un día hábil representativo de septiembre de 2024, de un estudio de EMOVA S.A. sobre transacciones SUBE |
| `perfil-carga-2024-lineas-actuales.xlsx` | Suben, bajan y pasajeros a bordo por tramo, por línea, sentido y hora pico. 360 filas |

Tres cosas que hay que saber antes de tocarlas:

- Los dos libros numeran las estaciones distinto. Coinciden hasta el id 75 y difieren en
  los últimos 15, porque la matriz pone la cola de la Línea E al final y el perfil la pone
  antes de la H. Cruzar una planilla con el mapa de la otra corre 15 estaciones sin dar
  ningún error.
- Las 90 estaciones cruzan una a una con los 90 nodos de nuestro grafo.
- La matriz y el perfil no son dos vistas exactas del mismo dato. SBASE declara que los
  diagramas de carga pasan por "un proceso de ajuste e iteración" para que la carga cierre
  en cero en la terminal. Y están en unidades distintas: la matriz cuenta viajes y el
  perfil cuenta ascensos a bordo.

### 4.7 Fuentes que descartamos

La API de Transporte Público está suspendida. La Encuesta de Movilidad Domiciliaria 2018
es demasiado antigua y está a nivel hogar. El Premetro queda fuera del alcance del modelo.

---

## 5. Información obtenida por pedidos oficiales

Buena parte de lo que usamos no estaba publicado y hubo que pedirlo. Los originales están
en `docs/respuestas-oficiales/` y en las carpetas de documentación oficial, y las fichas
de análisis en `docs/`.

El frente de pedidos está cerrado. Lo que falta tiene poco valor y los escenarios con y
sin proyecto son justamente lo que el TPI produce.

### 5.1 Expediente del EIA

Pedimos vista al expediente EX-2026-20211143-GCABA-APRA y nos respondieron el mismo día,
con 98 documentos. La copia está en `docs/Documentos-EX-2026-20211143/` y la extracción en
`docs/expediente-eia-linea-f.md`.

De ahí salieron el trazado, los parámetros operativos, el perfil de carga por tramo y las
etapas constructivas. No trae la matriz O-D de la red, ni los escenarios con y sin
proyecto, ni parámetros de las líneas existentes.

### 5.2 Pliego de licitación

No hizo falta trámite: está en el portal Buenos Aires Obras, no en BAC. El proceso tiene
numeración BAC (10241-0094-LPU25) pero los adjuntos están en BA Obras, con más de 260
documentos de descarga libre. La copia está en `docs/Documentos-BA-Obras/` y el análisis
en `docs/pliego-licitacion-linea-f.md`.

Lo principal: el presupuesto de USD 1.350 millones quedó confirmado por dos fuentes
oficiales independientes; el Pliego de Especificaciones Técnicas, de 606 páginas, no trae
plan de servicio, así que los parámetros operativos siguen viniendo del EsIA; apareció un
factor de superpico de 1,1 que sirve para contrastar el perfil dentro de la hora; y los
tres anexos que el Ministerio citó son Rev. 0 mientras la vigente es Rev. 1.

Del pliego salió además un argumento propio: extrajimos el índice maestro embebido en la
Planilla Integradora, con 1.866 documentos, y verificamos que no hay ningún estudio de
demanda en toda la licitación. Los únicos que mencionan demanda son dos informes de medios
de salida, que dimensionan evacuación de andenes y escaleras, no demanda de viajes.

### 5.3 Solicitud Ley 104 N° 00866317/26, la que sirvió

Expediente EX-2026-35399949-GCABA-DGAIGA. La respondieron en término tres organismos, que
entre los tres cubren los siete apartados del pedido. La ficha completa está en
`docs/respuestas-oficiales/respuesta-ley104-00866317.md`.

- IF-2026-38553261-GCABA-SBASE: matriz O-D de la red a nivel de estación, diaria y de las
  dos horas pico, y perfiles de carga por tramo de las seis líneas. Ver 4.6.
- IF-2026-37530623-GCABA-MMIGC: distancias entre las doce estaciones de la Línea F,
  intervalo de diseño de 100 s, 18 min entre cabeceras, formaciones de seis coches, una
  sola etapa de habilitación y la constancia de que no hay plan de servicio.
- IF-2026-38751180-GCABA-DGDPM: es el que menos contesta. Remite al pliego por el estudio
  de demanda y describe el análisis comparativo con y sin proyecto sin publicar una sola
  cifra. Aporta un dato metodológico que se puede citar: sus proyecciones de la Línea F
  están "extrapolados al año 2019" por ser prepandemia y de mayor demanda.

De los dos ítems que eran el núcleo del pedido llegó uno. La matriz O-D de la red llegó
completa; los escenarios con y sin proyecto siguen sin cifras.

### 5.4 Solicitud Ley 104 N° 00868015/26, una negativa con forma de remisión

IF-2026-38342377-GCABA-DGTALMMI. Contesta que "toda documentación técnica relativa a
'Ingeniería, construcción y equipamiento línea de Subterráneo F' se encuentra disponible"
en la vista previa de pliego ciudadano de BA Obras, y cita tres anexos.

Los tres ya los teníamos descargados desde antes del pedido, y coinciden uno a uno por
número de IF con archivos de `docs/Documentos-BA-Obras/`. No aporta nada nuevo y no
contesta lo que se pidió: la respuesta lee el pedido como documentación licitatoria,
cuando lo que pedimos es información de operación. Remitir al pliego es remitir a un
corpus donde ya verificamos que lo pedido no está (ver 5.2).

### 5.5 Lo que sigue sin ser público

Un solo documento: la nota técnica *Análisis de Demanda Línea F* de SBASE, 2019, o su
derivado, el *Informe Strans Demanda de la Línea F*. Es el único eslabón de la cadena que
no es público. Sus tablas de perfil de carga están transcriptas en la ficha del
expediente, así que no frena nada.

No hay que confundirlo con el LF-GL-GEN-GNR-IN-003: ese código es el informe "Demandas
Etapa I, Medios de Salida" del pliego, que ya está descargado. Son documentos distintos.

---

## 6. Debilidades metodológicas

Las identificamos a propósito y las tratamos de frente en el documento, no las
disimulamos.

- La aglomeración de andén no es observable. Ninguna fuente la registra, así que es una
  salida del modelo sin validación posible y hay que declararlo.
- La ocupación a bordo sí tiene con qué compararse, con tres salvedades. Los perfiles de
  carga de SBASE dan pasajeros a bordo por tramo, y nuestra asignación de ruta los
  reproduce con correlación 0,994 en hora pico mañana y error ponderado del 6,5 %. Pero
  el perfil cubre solo las dos horas pico y el modelo simula el día completo, pasa por un
  ajuste iterativo que declara SBASE, así que no es un conteo directo a bordo, y es de
  2024.
- Los destinos del dataset abierto son imputados, no observados. El publicador los imputa
  con dos reglas declaradas: parada más cercana con tolerancia de 2,2 km, y simetría
  diaria. Son supuestos heredados: los declaramos, no los reemplazamos. Además se pierde
  el 27,5 % de las transacciones en el proceso, corregido por factores de expansión
  topeados en 3. Esto vale para nuestra matriz del paso 5, no para la de SBASE.
- Las dos matrices son de un solo día. El dataset abierto corresponde al 16/10/2024 y la
  de SBASE a un día hábil representativo de septiembre de 2024, así que ninguna es un
  promedio anual. La de SBASE además solo abre dos horas pico.
- El supuesto propio del trabajo es cómo se reparte la demanda fuera de las dos horas
  pico. Antes era el criterio de escalado, que afectaba el nivel de toda la demanda; como
  la matriz de SBASE viene expandida, el supuesto se achicó y ahora afecta justo las horas
  en que la red no está al límite. Es lo que el análisis de sensibilidad tiene que
  recorrer.
- El escenario futuro no tiene dato observable, pero sí con qué contrastarlo. El perfil de
  carga del EsIA es exigente, pero no es una medición: es la salida de otro modelo, de
  2019, previo a la pandemia y a la apertura de medios de pago, con un supuesto de
  simetría diaria incorporado, porque las tablas de hora pico mañana y tarde son la imagen
  especular exacta una de la otra. A eso se le suma lo de la concentración horaria de 3.6.
- Los indicadores del modelo tienen piso pero no techo observable. El tiempo de detención
  del GTFS es un valor de diseño de 24 s, idéntico en toda parada de toda línea, y el
  `min_transfer_time` es un mínimo de diseño. Ninguno de los dos es una medición. En el
  modelo la detención tiene que salir de cuánta gente sube y baja, con esos valores como
  piso.
- El alcance creció. Pasamos de una línea a seis más una hipotética, y calibrar las seis
  con la misma profundidad no es viable en el cuatrimestre.

Dos debilidades que teníamos anotadas resultaron falsas al verificarlas, así que no
conviene reintroducirlas:

- La agregación en hexágonos h3 no es un problema. La metodología oficial del dataset
  declara hexágonos h3 de resolución 10, de unos 150 m de diámetro, y verificamos sobre el
  archivo completo que los 89 centroides distintos de las etapas de subte están a una
  mediana de 44 m y un máximo de 70 m de alguna de las 90 estaciones. La correspondencia
  entre celda y estación es unívoca, así que no hay criterio de reparto que elegir.
- Sí existe matriz O-D a nivel estación. El dataset publica, por cada etapa de subte,
  origen, destino, línea de ascenso, hora y factor de expansión. La imputación oficial
  trata a las seis líneas como ramales de una sola, así que la matriz es estación a
  estación para toda la red y ya contiene los viajes con combinación: el 48,8 % de las
  etapas termina en una línea distinta de la de ascenso. Eso deja la ruta y los
  transbordos como resultado de la simulación y no como dato de entrada.

---

## 7. Decisiones que tomamos

Son once decisiones de método. Seis están cerradas, y son las que importaban para poder
escribir el modelo; las que quedan abiertas no lo frenan.

Ninguna decisión la toma alguien por su cuenta: se proponen las opciones con sus
consecuencias, se elige entre todos, y recién ahí se registra con fecha y evidencia.

### 7.1 Cerradas

**Cuál es la matriz de demanda del modelo.** Usamos la de SBASE como base y el perfil
horario del paso 5. El nivel y la distribución espacial salen de la matriz diaria de
SBASE; las horas 8 a 9 y 17 a 18 se anclan a sus matrices de hora pico medidas; el resto
del día se desagrega con el perfil por par del paso 5; y los bloques de 15 minutos salen
de molinetes. La pregunta original era cómo escalar la matriz a los niveles medidos, y se
disolvió cuando llegó la de SBASE, que viene expandida. Quedó descartado el escalado por
franja horaria, con factor entre 1,035 y 1,082 de 6 a 22 h y sin forma sistemática, y
quedó visto que el escalado por línea es el escalado de los nodos ferroviarios visto de
lejos.

**La demanda se modela por estación y no por andén.** Solo el 70,5 % de la demanda tiene
sentido de circulación identificable, y lo que falta no está repartido al azar. El reparto
entre andenes queda como resultado de la asignación de ruta. Ese 70,5 % lo usamos además
para contrastar el reparto que produce el modelo en las estaciones donde el dato existe;
es un contraste parcial y sesgado por como está construido, y hay que declararlo así.

**El par San Pedrito y San José de Flores dejó de ser un problema.** El dataset abierto
reparte mal la demanda entre esas dos estaciones vecinas de la Línea A: le pone 15.495 de
más a una y 14.848 de menos a la otra, con el total del par cerrando en 647 de menos. Eso
explica el 35 % del desvío absoluto de toda la red. La matriz de SBASE no tiene el
defecto, porque mide 1,030 y 1,182 contra molinetes frente a 0,369 y 2,582 del dataset
abierto. Como la matriz del modelo es la de SBASE, no hay nada que reparar: era un defecto
de imputación de la fuente y no un rasgo de la demanda.

**La penalización por transbordo queda en 120 s, ahora medidos.** La recorrimos de 0 a
300 s calibrando contra la carga por tramo de hora pico mañana y validando con la tarde.
El dato no alcanza para fijar el parámetro: la curva es plana entre 30 y 300 s, con
errores de 6,29 % a 6,54 %, la calibración elige 30 s y la muestra de reserva elige 270 s,
y el control de reparto por línea empeora de 7,23 % a 9,00 % si se toma el mínimo. Lo
único que el dato fija es una cota inferior dura de 30 s: por debajo de eso el modelo se
rompe. Dentro de la zona plana decide el argumento físico, que es la mitad del intervalo
medido, entre 95 y 157 s, y 120 s cae ahí. Lo que cambió no es el número sino su estatus,
y hay que escribir en el informe que el indicador central es poco sensible a él.

La otra mitad de esa decisión sigue como estaba: la asignación es todo o nada, o sea que
cada par manda todo su flujo por un camino. Hay 50 pares, el 0,8 %, con una alternativa
por otra línea a menos de 60 s. Probamos afinar la penalización con la espera por línea
medida en el paso 4 y lo descartamos, porque empeora el ajuste de 5,47 a 7,36 p.p.

**Un agente es un pasajero, con pool declarado y reciclado.** Las pruebas de topes
mostraron que la cantidad máxima de pasajeros vivos a la vez es 20.722, no las 740.568
etapas del día, y que las poblaciones declaradas no cuentan contra el tope. Un pool de
25.000 entra en memoria incluso con diez replicaciones. Si el modelo real pesa más de lo
previsto, ya verificamos que agrupar de a 25 con `Source` y `Sink` funciona sin reciclado.

**Process Modeling Library, día completo y un submodelo peatonal.** PML está exenta del
tope de 5 h, lo verificamos corriendo 20 h simuladas, y el día de servicio son unas 19 h,
así que es la base obligada. El horizonte es el día completo. La fidelidad visual de
detalle va en un submodelo peatonal de Constitución en hora pico, que con 9.951 ingresos
entra a escala real.

### 7.2 Abiertas

Ninguna frena el arranque del modelo.

**Qué hacer con el 4,1 % de etapas marcadas como incompletas.** Son 24.057 etapas que
expanden a 30.491. Se decide corriendo el modelo con las dos versiones y viendo si cambia
algo, no discutiéndola: `matriz_od.csv` ya trae las dos en columnas separadas,
`expandidas` y `expandidas_completas`.

**Profundidad de calibración.** Si calibramos toda la red por igual o solo el corredor de
la Línea F y las líneas con las que combina, representando el resto de forma más gruesa.
La propuesta ya declara la segunda opción, falta confirmarla.

**Períodos de ajuste y validación.** Ya no es una elección libre: las dos ventanas tienen
que ser posteriores a diciembre de 2024 y no pueden tocar marzo de 2025, que no tiene
datos de despachos, el 10/04/2025, que fue un paro general con cero servicios prestados,
los 25 días hábiles atípicos ni los 100 días con cancelaciones gremiales. Queda disponible
`formaciones-despachadas-2026.csv` hasta el 30/06/2026, por si conviene tomar la
validación en 2026 en vez de partir 2025 en dos.

**Si dejamos el reparo del sentido 1 de la Línea E en el GTFS.** La columna de distancias
del sentido 1 es copia literal de la del sentido 0, y sus tiempos tienen correlación 0,010
con esas distancias contra 0,863 en el resto de la red, o sea que el sentido está
desacoplado de su geometría. El total sí cierra, así que ningún control agregado lo
detecta. Hay tres opciones: espejar el sentido 0, que es lo que hacen las otras cinco
líneas del feed, con 64 de 81 tramos con diferencia exacta cero entre sentidos; usar el
dato publicado tal cual; o promediar los dos sentidos, que no tiene fundamento porque
promediar una serie buena con una corrupta contamina la buena.

Está aplicada la primera, con el interruptor `REPARAR_LINEA_E` en `src/03_grafo_red.py`.
Lo medimos: regenerando el grafo sin el reparo cambian 58 pares de 6.006, o sea el 1,0 %,
y 18 cambian de línea de ascenso. Para la elección de ruta pesa poco, pero sigue abierta
porque afecta los tiempos de viaje sobre la E, que sí entran al modelo.

**Qué rango de headway recorrer para la Línea F.** El EsIA fija 1,5 min y 40 trenes por
sentido y hora, y el IF-2026-37530623 agrega 100 s "de requerirse". Medimos que la mejor
línea actual en hora pico es la C con 3,15 min, o sea que el diseño supone despachar 2,1
veces más seguido que lo que hoy se logra. Como el plan de servicio no existe y lo va a
fijar el futuro operador, tratarlo como variable de escenario es la única lectura fiel de
la fuente. Lo que falta decidir es el rango: piso de 90 a 100 s de diseño, techo los 3,15
min de la Línea C.

### 7.3 Un tema abierto: Retiro

El modelo predice que el 69,8 % de los ascensos en Retiro son por la Línea C, pero cuatro
fuentes dicen otra cosa: SBASE mide 86,0 %, molinetes 85,5 % y `linea_etapa` 83,9 %.
Durante un tiempo pensamos que el molinete le atribuía de más a la C, pero esa hipótesis se
cayó cuando llegó SBASE, que es una cuarta fuente y no pasa por molinetes. Lo que
corresponde es revisar el costo del transbordo entre Retiro de la C y Retiro de la E.
Queda declarado.

---

## 8. Plan de trabajo

1. Tabla maestra de estaciones. Hecho. `src/01_tabla_maestra_estaciones.py`, reporte en
   `reports/01_tabla_maestra.md`. Cruzamos 90 de 90 estaciones sin ninguna huérfana, y los
   no-matcheos residuales suman 80 pasajeros sobre 206,5 millones. Las 12 equivalencias
   están declaradas a mano en `src/lib_normalizacion.py`, así que el cruce es
   determinístico y sin comparación difusa. Dos hallazgos que cambian decisiones: siete
   estaciones aparecen con dos nombres simultáneos y hay que consolidarlas o la demanda
   queda partida en dos, y solo el 70,5 % de la demanda se puede atribuir a un andén.
2. Grafo de la red. Hecho. `src/03_grafo_red.py`, reporte en `reports/03_grafo_red.md`.
   Son 90 nodos, 166 aristas de tramo y 28 de transbordo, con 14 combinaciones. El grafo
   es dirigido y fuertemente conexo. Tres hallazgos: los 24 s de detención son un valor de
   diseño y no una medición; Alberti y Pasco obligan a un grafo dirigido, porque tienen un
   andén cada una y se sirven en un solo sentido, y por eso la red tiene 90 nodos y no 89;
   y el sentido 1 de la Línea E está corrupto en el feed.
3. Demanda por estación, bloque de 15 minutos y tipo de día. Hecho.
   `src/04_demanda_molinetes.py`, reporte en `reports/04_demanda.md`. Son 19.931 celdas de
   tipo de día, franja y estación, con media y desvío entre días, sobre 206.616.377
   pasajeros. Los perfiles se construyen solo con días típicos: excluimos 25 días hábiles
   atípicos y el 10/04/2025.
4. Intervalos reales entre despachos. Hecho. `src/05_despachos.py` y
   `src/lib_despachos.py`, reporte en `reports/05_despachos.md`. Son 663.709 intervalos de
   días hábiles completos, medidos en cabecera. En hora pico: C 3,15 min, A 3,17, H 3,43,
   D 3,82, B 4,13 y E 5,22. Hay 20.078 servicios no prestados, el 2,31 %, todos con causa
   registrada; las gremiales explican 5.060 en 100 días.
5. Matriz O-D. Hecho. `src/06_matriz_od.py`, con `src/lib_etapas.py` y
   `src/lib_complejos.py`, reporte en `reports/06_matriz_od.md`. Son 5.953 pares O-D sobre
   6.006 posibles, en 72.245 celdas de origen, destino y hora, con 740.568 etapas
   expandidas. Cuatro hallazgos:
   - La unidad espacial es el complejo de estación y no el nodo. Los 90 nodos se agrupan
     en 78 complejos, que son las componentes conexas del grafo de transbordos. Eso
     disuelve la ambigüedad que teníamos al matchear por cercanía, porque las estaciones
     que se confundían son justo las que el complejo agrupa.
   - `linea_etapa` determina el nodo exacto de origen: en las 587.980 etapas, sin una sola
     excepción, la línea de ascenso pertenece al complejo asignado. Es además una
     validación independiente del grafo. No entra como insumo del modelo, porque sería
     fijar parte de la ruta, sino como contraste.
   - El escalado se mide contra el mismo día y no contra 2025, así la comparación no
     arrastra el cambio de medios de pago. El factor global es 1,0509.
   - Dos defectos de fuente de naturaleza distinta: los nodos de trasbordo ferroviario
     subregistran de forma ordenada, con Constitución 1,221, Retiro 1,140, Once 1,123 y
     Lacroze 1,066 contra 1,015 de las simples; y el par San Pedrito y San José de Flores
     tiene la demanda mal repartida entre sí.
6. Caminos mínimos con penalización por transbordo, precalculados fuera del modelo. Hecho.
   `src/07_caminos_minimos.py` y `src/lib_caminos.py`, reporte en
   `reports/07_caminos_minimos.md`. Son 6.006 pares ordenados, todos alcanzables, con
   tiempo mediano de 16:04, y 22,1 % sin transbordo, 47,5 % con uno y 30,5 % con dos.
   Cuatro cosas a retener:
   - Los 24 s de detención van por parada intermedia y no por tramo: el que sube no espera
     la detención de su estación y el que baja tampoco. Contarlas por tramo abarataría los
     caminos con muchas paradas. Lo verificamos recalculando 400 caminos aparte, sin
     ninguna discrepancia.
   - El acceso y el egreso dentro del complejo valen cero, así que caminar dentro del
     complejo de origen no cuenta como transbordo.
   - El reparto por línea lo contrastamos contra dos fuentes que coinciden entre sí en
     0,74 p.p. en los ocho complejos sanos. El error del modelo es 5,47 p.p. contra
     molinetes.
   - En dos complejos el dataset O-D está roto y molinetes le da la razón al modelo: 9 de
     Julio con Carlos Pellegrini y Diagonal Norte, e Independencia, atribuyen el 100 % de
     los ascensos a una sola línea.
7. AnyLogic: escenario base, verificación y validación. Pendiente.
8. Escenario con Línea F: agregar nodos y aristas al grafo y repetir los pasos 6 y 7. Si
   el pipeline está bien armado este paso sale barato, y eso mismo es la prueba de que el
   diseño es correcto. Pendiente.
9. Matriz O-D y perfiles de carga de SBASE. Hecho. No estaba en el plan, lo abrió la
   respuesta por Ley 104. `src/09_sbase_od_carga.py` y `src/lib_sbase.py`, reporte en
   `reports/09_sbase_od_carga.md`. Cuatro cosas a retener:
   - La asignación todo o nada del paso 6 queda validada contra un observado, con
     correlación 0,994 en hora pico mañana y 0,985 en la tarde sobre 166 tramos, y error
     absoluto ponderado de 6,5 % y 8,4 %. Es la primera validación de ruta del trabajo.
   - La concentración horaria de las dos fuentes coincide: SBASE da 9,0 % en la hora pico
     mañana y 9,7 % en la tarde, contra el 9,9 % que medimos sobre molinetes.
   - El tramo más cargado de la red actual lleva 12.249 pas./h, en la C en hora pico
     mañana entre San Juan y Retiro. La Línea F proyecta 35.742 pas./h entre Constitución
     y Cochabamba, o sea 2,9 veces eso.
   - Los dos libros de SBASE numeran las estaciones distinto (ver 4.6).
10. Calibración de la penalización por transbordo. Hecho. Tampoco estaba en el plan, lo
    habilitaron los perfiles de carga. `src/10_calibracion_penalizacion.py`, reporte en
    `reports/10_calibracion_penalizacion.md`. El dato no alcanza para fijar el parámetro
    por encima de 30 s, así que conservamos los 120 s por el argumento físico. Hay una
    consecuencia a tener en cuenta: el contraste de carga en hora pico mañana pasó a ser
    calibración y no validación, y la validación es la hora pico tarde.
11. Matriz de demanda del modelo. Hecho. `src/11_demanda_modelo.py`, reporte en
    `reports/11_demanda_modelo.md`. Es el insumo que consume AnyLogic, junto con
    `caminos_minimos.csv`. Los controles cierran: el total coincide con SBASE al redondeo,
    las dos horas pico reproducen exactamente sus matrices y la hora más cargada da 9,7 %.

El ajuste de distribuciones va según el procedimiento que vimos en la materia:
histogramas, estimación de parámetros por máxima verosimilitud y pruebas de bondad de
ajuste. Cada escenario se corre con un mínimo de diez replicaciones, descartando el
período de calentamiento e informando intervalos de confianza.

---

## 9. Límites de AnyLogic PLE

Los medimos en vez de suponerlos. Los modelos de prueba están en `anylogic/pruebas/` y el
detalle en `docs/pruebas-anylogic-topes.md`.

| Lo que se temía | Lo que medimos |
|---|---|
| El tope de 5 h simuladas impide simular un día de servicio | PML está exenta. Corrió 20 h simuladas |
| El tope de 50.000 agentes no alcanza | Cuenta creaciones y no agentes vivos, y se reinicia en cada replicación: diez iteraciones de 39.773 agentes, 397.730 acumulados, sin error |
| Las poblaciones declaradas consumen el tope | No cuentan. Un pool de 25.000 entra en memoria incluso con diez replicaciones |
| La licencia University Researcher levantaría los topes | No los levanta, tiene exactamente los mismos |

Hay una restricción que obliga a diseñar distinto: son 200 bloques de flowchart por tipo
de agente. Con 90 nodos no se puede dibujar un flowchart por estación, así que la
topología vive en los CSV y se lee mientras corre el modelo.

---

## 10. Cómo trabajamos

- No inventamos datos. Ni cifras del proyecto, ni resultados, ni parámetros operativos. Si
  un dato no está en las fuentes listadas, decimos que no está.
- No prometemos resultados. La sección de resultados esperados describe qué se va a medir,
  nunca qué valores se van a obtener.
- Distinguimos siempre lo confirmado de lo estimado, y citamos la fuente de cada cifra
  oficial.
- En `data/raw/` van los archivos tal como se descargaron, sin modificar nunca, y en
  `data/processed/` todo lo derivado.
- Los datasets se leen siempre con las librerías del repositorio y nunca parseando a mano:
  - `src/lib_molinetes.py` lee en streaming y resuelve cinco problemas de formato que no
    están documentados: dos formatos de fila en el mismo ZIP, codificación mezclada entre
    UTF-8 y Latin-1, fechas en `d/m/Y` mezcladas con `m/d/Y` en agosto de 2025, valores
    centinela y estaciones espurias.
  - `src/lib_despachos.py` resuelve otros cuatro: tres formatos de fecha conviviendo en el
    archivo de 2025 con corte distinto por línea, codificación distinta por año, 24.696
    filas completamente vacías, y causas con relleno de espacios que duplican categorías.
  - `src/lib_sbase.py` usa el mapa de estaciones propio de cada libro, que es lo que evita
    el corrimiento de 15 estaciones que mencionamos en 4.6.
- Los ZIP anuales de molinetes son de varios millones de filas, así que hay que filtrar al
  leer y no cargar el año completo en memoria.
- Conviene desconfiar de los recursos "agregados" del portal. Ya encontramos dos
  congelados: `viajes_anual.csv`, muerto desde 2020, y "Formaciones despachadas - Total",
  con contenido hasta 2021. Antes de usar cualquier recurso que se presente como archivo
  único o histórico completo, conviene consultar `package_show` de la API de BA Data y
  comparar contra los recursos por año.
- Al filtrar conviene preguntarse qué desaparece. En el paso 4, filtrar los servicios no
  prestados antes de mirar las causas hacía que las causas visibles fueran las de los
  servicios que sí se hicieron, y un paro, que por definición cancela, se volvía invisible:
  la tabla mostraba 12 despachos gremiales en lugar de 5.060.
- El documento LaTeX vive en `docs/` del mismo repositorio y se versiona junto al código.
- La redacción del informe es académica, técnica y sobria, sin lenguaje promocional.
