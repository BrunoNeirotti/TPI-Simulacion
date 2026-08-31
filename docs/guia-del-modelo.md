# Guía del modelo

Lo que hace falta para armar el modelo en AnyLogic sin tener que volver a los datasets
crudos: qué archivos consume, qué significa cada columna, qué valores son dato y no se
tocan, cuáles hay que variar por escenario, qué hay que suponer porque no existe la
medición, y contra qué se compara el resultado.

Acá está el qué y el cómo. El por qué de cada decisión está en
[`contexto-del-proyecto.md`](contexto-del-proyecto.md).

---

## 1. Mapa del repositorio

Adónde ir según qué se necesite. Si un dato no está en alguno de estos archivos, no lo
usamos.

| Necesito... | Está en |
|---|---|
| Por qué se decidió algo y con qué fuente | `docs/contexto-del-proyecto.md` |
| Los insumos del modelo | `data/processed/`, sección 2 de esta guía |
| Cómo se armó cada insumo | `docs/preparacion-de-datos.md` |
| El resultado y las verificaciones de un paso | `reports/`, un archivo por paso |
| Cifras oficiales de la Línea F | `docs/expediente-eia-linea-f.md` |
| Datos de la licitación (presupuesto, plazos) | `docs/pliego-licitacion-linea-f.md` |
| Lo que contestaron los organismos | `docs/respuestas-oficiales/respuesta-ley104-00866317.md` |
| Los límites de AnyLogic que medimos | `docs/pruebas-anylogic-topes.md` y `anylogic/pruebas/` |
| Cómo leer un dataset crudo | `src/lib_molinetes.py`, `lib_despachos.py`, `lib_sbase.py` |

Para cifras de la Línea F conviene ir siempre a la ficha del expediente y no a los PDF
sueltos ni a los diarios. La ficha ya tiene las tablas pasadas en limpio y las
contradicciones marcadas.

---

## 2. Los cinco insumos del modelo

Están todos en `data/processed/`. Los tiempos van en segundos, las distancias en
kilómetros y la demanda en viajes. Se regeneran corriendo el pipeline; no se editan a
mano.

### 2.1 `grafo_nodos.csv`, 90 filas

Un nodo es un par línea-estación, no una estación física. Constitución aparece dos
veces, una por la C y otra por la E.

| Columna | Qué es |
|---|---|
| `nodo_id` | Clave primaria, con formato `Linea<X>:<gtfs_stop_id>`. La usan todos los demás archivos |
| `linea` | `LineaA` hasta `LineaH` |
| `gtfs_stop_id` | Id de la estación en el GTFS |
| `nombre` | Nombre de la estación |
| `lat`, `lon` | Coordenadas, para el dibujo |
| `sentidos` | `01` si la estación se sirve en los dos sentidos, `0` o `1` si se sirve en uno solo |
| `orden_dir0`, `orden_dir1` | Posición en la secuencia de la línea en cada sentido |
| `n_andenes_gtfs`, `andenes_servidos` | Andenes declarados y andenes que se usan |
| `es_terminal` | Cabecera de línea. Son 14 |
| `es_combinacion` | El nodo participa de un transbordo. Son 22 |

Nodos por línea: A 18, B 17, C 9, D 16, E 18, H 12.

Alberti y Pasco tienen un andén cada una y se sirven en un solo sentido: Alberti hacia
San Pedrito (`sentidos = 0`) y Pasco hacia Plaza de Mayo (`sentidos = 1`). Por eso la
red tiene 90 nodos y no 89, y por eso el grafo hay que tratarlo como dirigido.

### 2.2 `grafo_aristas.csv`, 194 filas

Son 166 de tipo `tramo` y 28 de tipo `transbordo`. El grafo es dirigido y fuertemente
conexo: desde cualquier nodo se llega a cualquier otro.

| Columna | Qué es |
|---|---|
| `tipo` | `tramo` (viaje entre estaciones contiguas) o `transbordo` (caminata entre andenes) |
| `de_nodo`, `a_nodo` | `nodo_id` de origen y destino |
| `linea`, `direction_id` | Solo en las de tipo `tramo` |
| `orden` | Posición del tramo en la secuencia de la línea |
| `t_s` | Tiempo de recorrido del tramo en segundos. En las de transbordo es el `min_transfer_time` del GTFS |
| `t_detencion_s` | 24 s en todos los tramos. Ver abajo |
| `km` | Longitud del tramo |
| `de_anden`, `a_anden` | Andenes del GTFS |

Los 24 s de `t_detencion_s` son un valor de diseño del horario, no algo medido: son
idénticos en toda parada de toda línea, con desvío cero sobre los 166 tramos. Lo mismo
pasa con el `t_s` de los transbordos, que es un `min_transfer_time`, o sea un mínimo de
diseño y no una caminata cronometrada. En el modelo la detención tiene que salir de
cuánta gente sube y baja, usando los 24 s como piso.

### 2.3 `caminos_minimos.csv`, 6.006 filas

Un camino precalculado por cada par ordenado de complejos. Todos los pares son
alcanzables.

| Columna | Qué es |
|---|---|
| `comp_origen`, `comp_destino` | Complejos, no nodos. Ver 3.1 |
| `tiempo_s` | Tiempo real de viaje. Es el que usa el modelo |
| `costo_s` | Tiempo percibido, que se usó para elegir el camino. Verificamos que `costo_s = tiempo_s + 120 × n_transbordos` |
| `n_transbordos` | 0 en 1.326 pares, 1 en 2.851, 2 en 1.829 |
| `nodo_ascenso`, `linea_ascenso` | Por dónde entra al sistema |
| `nodo_descenso`, `linea_descenso` | Por dónde sale |
| `n_estaciones` | Estaciones del camino, contando las dos puntas |
| `camino` | La secuencia de `nodo_id`, separados por espacio |

Tiempos de viaje: mínimo 0,6 min, mediana 16,1 min, máximo 43,2 min.

Cuidado con usar `costo_s` como tiempo. Los 120 s de penalización por transbordo son un
costo que sirve para elegir el camino, no tiempo que el pasajero pase adentro del
sistema. Sumarlos al tiempo simulado infla el viaje del 78 % de los pares, que son los
que hacen al menos un transbordo.

### 2.4 `demanda_modelo_od_hora.csv`, 71.686 filas

El qué y el cuándo de la demanda: 827.289 viajes en el día hábil.

| Columna | Qué es |
|---|---|
| `comp_origen`, `comp_destino` | Complejos. Hay 5.839 pares distintos |
| `hora` | Hora entera, de 5 a 23 |
| `viajes` | Viajes de esa hora para ese par. Es un número con decimales |
| `fuente` | `sbase_pico` (8.589 celdas, dato medido de las horas 8 y 17) o `perfil_paso5` (63.097 celdas, desagregado) |

`viajes` tiene decimales en 63.031 de las 71.686 celdas y va de 0,0019 a 1.887,1.
Conviene no redondear a entero: se usa como tasa de llegada, y truncar haría desaparecer
todos los pares chicos, que son la mayoría.

La columna `fuente` sirve para el análisis de sensibilidad. Las celdas `sbase_pico` son
demanda medida y quedan fijas; las `perfil_paso5` son el supuesto que pusimos nosotros y
son las que hay que variar. Ver 4.3.

### 2.5 `demanda_modelo_intrahorario.csv`, 6.140 filas

Cómo se reparte cada hora en cuatro bloques de 15 minutos.

| Columna | Qué es |
|---|---|
| `complejo` | Complejo de origen. Los 78 tienen perfil |
| `hora` | Hora entera, de 0 a 23 |
| `franja` | `HH:00`, `HH:15`, `HH:30`, `HH:45` |
| `share` | Fracción de la demanda de esa hora que cae en ese bloque |

Hay un detalle a tener en cuenta: en las horas 0 a 4 el `share` no suma 1 en 50 grupos,
porque a esa hora no hay pasajeros y el script repartió 0,25 uniforme sin que existan los
cuatro bloques. No afecta al modelo, porque esas horas no tienen demanda: la matriz O-D
va de 5 a 23. En las 1.482 celdas de (complejo, hora) que sí se usan el `share` suma 1
exacto. Igual conviene leer solo las horas 5 a 23, o normalizar por las dudas.

El perfil es por complejo de origen, no por par. Todos los viajes que salen de un
complejo en una hora comparten la misma forma dentro de la hora.

---

## 3. La red

Estos hechos salen de los datos, no los elegimos nosotros, así que el modelo los tiene
que respetar.

### 3.1 Dos unidades espaciales que conviene no mezclar

| Unidad | Cuántas | Para qué |
|---|---|---|
| Nodo (`nodo_id`) | 90 | La red física, por donde circulan los trenes. Es la unidad de `grafo_nodos` y `grafo_aristas` |
| Complejo (`comp_*`) | 78 | El lugar donde el pasajero entra y sale. Es la unidad de la demanda y de los caminos |

Un complejo agrupa los nodos que están unidos por una caminata interna, o sea las
componentes conexas del grafo de transbordos. El mapeo está en
`data/processed/od_complejos.csv`, con las columnas `complejo, nombre, lineas, n_nodos,
nodos, lat, lon`. El identificador del complejo es el `nodo_id` de uno de sus nodos, así
que un `comp_origen` se parece a un `nodo_id` pero no siempre lo es: hay que resolverlo
con esa tabla.

Esto importa porque el pasajero llega a un complejo y después el modelo decide por qué
nodo asciende. Esa decisión ya viene resuelta en `caminos_minimos.csv`, en la columna
`nodo_ascenso`. Caminar dentro del complejo de origen no cuenta como transbordo y vale
cero: el acceso y el egreso son gratis por como está armado el grafo.

### 3.2 Cobertura

- 5.839 pares tienen demanda y los caminos cubren 6.006. Los 167 pares que tienen camino
  y no tienen demanda son normales: existe la ruta pero nadie la usó ese día.
- No hay ningún par con demanda y sin camino. Está verificado.
- Los 687 viajes diarios entre nodos de un mismo complejo quedan afuera de la matriz. En
  el modelo son una caminata dentro de la estación, no un viaje.

---

## 4. Qué es fijo y qué es variable

Es la parte central de la guía. Van cuatro categorías, y lo que las separa es qué
respaldo tiene cada número.

### 4.1 Fijo: dato medido o de diseño oficial

| Parámetro | Valor | De dónde sale |
|---|---|---|
| Topología de la red | 90 nodos, 166 tramos, 28 transbordos | GTFS, paso 2 |
| Tiempo de recorrido de cada tramo | `grafo_aristas.t_s` | GTFS |
| Longitud de cada tramo | `grafo_aristas.km` | GTFS |
| Demanda por par y hora | `demanda_modelo_od_hora.csv` | SBASE en las horas 8 y 17, paso 5 en el resto |
| Perfil dentro de la hora | `demanda_modelo_intrahorario.csv` | Molinetes, días hábiles típicos |
| Ruta de cada par | `caminos_minimos.csv` | Paso 6, comparado contra SBASE |
| Intervalo entre despachos de las líneas actuales | `intervalos_despacho.csv`, por línea, cabecera y hora | Medido sobre 663.709 intervalos |
| Coches por formación | A 5, B 6, C 5, D 6, E 5, H 6 (medianas) | `reports/05_despachos.md`, sección 6 |
| Línea F: distancias entre las 12 estaciones | 9.800 m en total | `IF-2026-37530623-GCABA-MMIGC` |
| Línea F: capacidad por formación | 1.075 pasajeros | EsIA |
| Línea F: velocidades | 90 / 70 / 45 km/h | EsIA |
| Línea F: aceleración y frenado | 1 m/s² y 1,1 m/s² | EsIA |
| Línea F: flota | 25 formaciones de 6 coches | EsIA e `IF-2026-37530623` |
| Línea F: tiempo entre cabeceras | Unos 18 min, o sea 32,7 km/h comerciales | `IF-2026-37530623` |

Intervalo mediano en hora pico, promediando las dos cabeceras, en minutos:

| Hora | A | B | C | D | E | H |
|---|---:|---:|---:|---:|---:|---:|
| 8 | 3,08 | 4,11 | 3,12 | 3,67 | 5,20 | 3,43 |
| 17 | 3,12 | 3,96 | 3,13 | 3,67 | 5,18 | 3,43 |

### 4.2 Calibrado: medido contra un observado

La penalización por transbordo quedó en **120 s**. La recorrimos de 0 a 300 s comparando
contra la carga por tramo de SBASE, y el resultado fue que el dato no alcanza para fijar
el parámetro: la curva es plana entre 30 y 300 s, con errores de 6,29 % a 6,54 %. Lo
único que el dato deja claro es que por debajo de 30 s el modelo se rompe. Los 120 s
salen de un argumento físico, la mitad del intervalo medido, que va de 95 a 157 s, y caen
dentro de esa zona plana.

Para el informe esto es un resultado y no una limitación: el indicador central es poco
sensible a este parámetro. El barrido completo está en
`data/processed/calibracion_penalizacion.csv`.

### 4.3 Variable de escenario: hay que recorrerlas

| Variable | Rango | Por qué |
|---|---|---|
| Headway de la Línea F | Piso de 90 a 100 s de diseño, techo de 189 s (3,15 min, lo mejor que hoy logra la C) | No hay plan de servicio y no va a haberlo hasta que haya operador. Es una cita oficial, no una elección nuestra. Los 90 s suponen despachar 2,1 veces más seguido que la mejor línea actual |
| Detención de la Línea F | Piso de 30 s según el EsIA | El mismo informe dice que el operador va a definir los tiempos finales de detención |
| Reparto de la demanda fuera de las horas pico | Tres variantes: perfil por par del paso 5 (la base), perfil de la red igual para todos, y perfil por complejo de origen sacado de molinetes | Es el supuesto que pusimos nosotros. Afecta solo a las celdas con `fuente = perfil_paso5`; las horas 8 y 17 son dato medido y quedan fijas |
| Etapas marcadas como incompletas | Con y sin ellas, son el 4,1 % (30.491 viajes expandidos) | Se resuelve corriendo las dos versiones y midiendo si cambia algo. `matriz_od.csv` ya trae las dos en columnas separadas |

### 4.4 Supuestos: no existe la medición

Estos hay que fijarlos con criterio y aclarar en el informe que son supuestos.

| Parámetro | Qué sabemos y qué no |
|---|---|
| Capacidad por coche de las líneas actuales | Sabemos los coches por formación, que están medidos, pero no la capacidad de cada coche, que depende del material rodante. La única capacidad oficial es la de la Línea F: 1.075 por formación de 6 coches, unos 179 por coche. Tomarla de referencia para las líneas de 6 coches se puede defender; para las de 5 hay que aclararlo |
| Detención de las líneas actuales | Tiene que salir de cuánta gente sube y baja, con 24 s de piso. No hay fuente pública para compararlo |
| Qué hace el pasajero que no entra al tren | Si espera el siguiente, cambia de ruta o abandona. No hay dato, hay que elegir una regla y declararla |
| Caminata en transbordo | El `min_transfer_time` del GTFS es un mínimo de diseño, no una caminata medida. Sirve de piso |

---

## 5. Qué tiene que producir el modelo

Y si cada indicador se puede validar o no, que es algo que va al informe.

| Indicador | ¿Se puede comparar contra un dato? |
|---|---|
| Ocupación a bordo por tramo | Sí. `data/processed/sbase_perfil_carga.csv` da suben, bajan y carga saliente por línea, sentido y hora pico. Con tres salvedades: cubre solo las dos horas pico, pasa por un ajuste iterativo que SBASE declara, y es de 2024 |
| Reparto de ascensos por línea en las combinaciones | Sí, parcial. Contra molinetes y contra `linea_etapa`, que coinciden entre sí en 0,74 p.p. en los ocho complejos sanos |
| Tasa de transbordo | Sí. El observado es 1,371 en la mañana y 1,426 en la tarde, en ascensos por viaje |
| Concentración horaria | Sí. 9,9 % en la hora más cargada, medido sobre molinetes |
| Aglomeración de andén | No. Ninguna fuente la registra |
| Pasajeros que no logran subir | No. Depende de un supuesto de comportamiento |
| Detención real | No. Solo tenemos el piso de diseño |

### 5.1 Lo que el pipeline ya logra

El paso 6 reproduce la carga observada con estos números. El modelo no debería
empeorarlos, y si lo hace conviene entender por qué:

| | Hora pico mañana | Hora pico tarde |
|---|---|---|
| Correlación sobre 166 tramos | 0,994 | 0,985 |
| Error absoluto ponderado | 6,5 % | 8,4 % |

Ojo con un detalle: la hora pico de la mañana se usó para calibrar la penalización, así
que dejó de servir como validación. La validación es la hora pico de la tarde.

### 5.2 Escala del escenario futuro

El tramo más cargado de la red actual lleva 12.249 pas./h, en la Línea C en hora pico
mañana, entre San Juan y Retiro. El tramo más cargado que se proyecta para la Línea F
lleva 35.742 pas./h entre Constitución y Cochabamba, o sea 2,9 veces el máximo actual de
toda la red.

---

## 6. Límites de AnyLogic y arquitectura

Los medimos en vez de suponerlos. El detalle está en `docs/pruebas-anylogic-topes.md`.

| Límite de PLE | Qué medimos |
|---|---|
| 5 horas simuladas | PML está exenta. Corrió 20 h, y el día de servicio son unas 19 h |
| 50.000 agentes | Cuenta creaciones y no agentes vivos, y se reinicia en cada replicación |
| Poblaciones declaradas | No cuentan contra el tope |
| 200 bloques de flowchart por tipo de agente | Es el límite que más condiciona el diseño |

La arquitectura que decidimos:

- Un agente es un pasajero. La cantidad máxima de pasajeros vivos a la vez es 20.722, no
  las 740.568 etapas del día, así que entra.
- Pool declarado y reciclado, con `Enter` y `Exit` en lugar de `Source` y `Sink`. Un pool
  de 25.000 entra en memoria incluso con diez replicaciones.
- Horizonte de día completo.
- Un submodelo peatonal de Constitución en hora pico para la parte visual de detalle. Con
  9.951 ingresos entra a escala real.
- Si el modelo termina pesando más de lo previsto, ya probamos que agrupar de a 25
  pasajeros con `Source` y `Sink` funciona sin reciclado.

La consecuencia de diseño más importante es que con 90 nodos no se puede dibujar un
flowchart por estación. La topología se lee de los CSV mientras corre el modelo, y el
flowchart es uno solo, genérico, parametrizado por el agente. Si el modelo arranca
dibujando estaciones, después hay que rehacerlo.

La licencia University Researcher no levanta los topes, tiene los mismos, así que no
vale la pena gestionarla esperando que destrabe la escala.

---

## 7. Cosas que ya nos costaron encontrar

Están acá para no repetirlas.

1. Los 24 s de detención van por parada intermedia y no por tramo. El que sube no espera
   la detención de su estación de origen, y el que baja tampoco la de destino. Contarlas
   por tramo abarata los caminos con muchas paradas. Lo verificamos recalculando 400
   caminos aparte, sin ninguna discrepancia.
2. `costo_s` no es tiempo. Ver 2.3.
3. `viajes` tiene decimales, así que no conviene redondear. Ver 2.4.
4. El grafo es dirigido, por Alberti y Pasco. Ver 2.1.
5. Complejo y nodo no son lo mismo aunque el identificador se parezca. Ver 3.1.
6. El `share` de las horas 0 a 4 no suma 1, aunque esas horas no tienen demanda. Ver 2.5.
7. Los datasets crudos se leen con las librerías del repo y no a mano. Resuelven una
   docena de problemas de formato que el publicador no documenta.
8. Los dos libros de SBASE numeran las estaciones distinto: coinciden hasta el id 75 y
   difieren en los últimos 15. Cruzar una planilla con el mapa de la otra corre 15
   estaciones sin dar ningún error. `lib_sbase.py` usa el mapa de cada libro.
9. Cuando se filtra conviene preguntarse qué desaparece. Filtrar los servicios no
   prestados antes de mirar las causas hacía invisible un paro general: la tabla mostraba
   12 despachos gremiales en lugar de 5.060.

---

## 8. Lo que falta decidir

Ninguna de estas frena el arranque del modelo.

| Qué falta | Cómo pega en el modelo |
|---|---|
| Qué hacer con el 4,1 % de etapas incompletas | Cambia el nivel de la demanda en un 4,1 %. Se decide midiendo |
| Si calibramos toda la red por igual o solo el corredor de la F | Define dónde poner el esfuerzo de ajuste, no la estructura del modelo |
| Qué períodos usar para ajustar y para validar | Los dos tienen que ser posteriores a diciembre de 2024, sin marzo de 2025, sin el 10/04/2025, sin los 25 días hábiles atípicos y sin los 100 días con cancelaciones gremiales |
| Si dejamos el reparo del sentido 1 de la Línea E | Está aplicado (`REPARAR_LINEA_E = True`). Apagarlo cambia 58 pares de 6.006, o sea el 1,0 %. Afecta los tiempos de viaje sobre la E |
| Qué rango de headway recorrer para la Línea F | Es la variable de escenario principal del trabajo. Ver 4.3 |

---

## 9. Un tema abierto: Retiro

El pipeline predice que el 69,8 % de los ascensos en Retiro son por la Línea C, pero
cuatro fuentes distintas dicen otra cosa: SBASE mide 86,0 %, molinetes 85,5 % y
`linea_etapa` 83,9 %.

Durante un tiempo pensamos que el molinete le atribuía de más a la C, pero esa hipótesis
se cayó cuando llegó SBASE, que no pasa por molinetes. Lo que corresponde es revisar el
costo del transbordo entre Retiro de la C y Retiro de la E. Si el modelo repite el mismo
sesgo es esperable y ya está declarado; si lo corrige solo, hay que entender por qué.
