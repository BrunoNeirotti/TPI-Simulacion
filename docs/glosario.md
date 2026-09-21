# Glosario

Términos del TPI tal como se usan en este proyecto. Iniciado el 21/09/2026 a partir del
glosario de la especificación (`docs/especificacion-modelo.tex`), que queda como versión
corta para la entrega.

**Criterio.** Se usa el término en español cuando existe uno claro y ya usado por las
fuentes oficiales del proyecto (el EsIA, el pliego, SBASE). Se conservan en inglés los
nombres propios de software, de bloques y de campos de datos, y los tecnicismos sin
traducción establecida. Las entradas marcadas **(reemplaza a …)** son traducciones
elegidas en lugar de un anglicismo. El registro histórico de `CLAUDE.md` y
`decisiones.md` no se reescribe: el criterio vale para el texto nuevo.

---

## 1. Red y operación

| Término | Qué es en este proyecto |
|---|---|
| **Andén** | Lugar donde esperan los pasajeros de un nodo en un sentido. En el modelo hay 178 (uno por nodo y sentido); es una cola en orden de llegada (`Anden` en la biblioteca). |
| **Apertura del servicio** | Inicio de la operación diaria: a las 5:30 en todas las líneas. Salen a la vez de 2 a 5 formaciones por lado desde estaciones intermedias, no desde la cabecera (D16, paso 12). |
| **Cabecera** | Estación terminal de una línea, desde donde se despacha. El dataset de despachos las llama **lado A** y **lado D** sin decir cuál es cuál; la correspondencia se dedujo de los datos (`cabeceras_despacho.csv`). En la E el lado A es Retiro, al revés que en el resto. |
| **Cambio de sentido (vuelta)** | En 142 rutas hacia Alberti o desde Pasco, el camino sigue de largo hasta Congreso o Plaza Miserere y vuelve en sentido contrario. En el modelo son dos etapas con espera en el nodo de la vuelta (D19). No confundir con *vuelta en cabecera*. |
| **Capacidad de formación** | Coches por formación (medidos: A 5, B 6, C 5, D 6, E 5, H 6) por 179 pasajeros por coche (supuesto, tomado de la Línea F: 1.075 / 6). Línea F: 1.075 por formación. |
| **Combinación** | Estación física donde se cruzan dos o más líneas. Nodo con `es_combinacion = True` (22 nodos). Ver *transbordo*. |
| **Complejo** | Estación física: componente conexa del grafo de transbordos. Los 90 nodos forman **78 complejos**. Es la unidad de la demanda y de las rutas; el pasajero entra y sale del sistema por un complejo. Acceso y egreso dentro del complejo valen cero. |
| **Corte de servicio** | Intervalo anormalmente largo entre despachos en un día típico, sin causa registrada (hasta 7 h). Se excluyen del ajuste los de más de 5 veces la mediana de su celda: 144 intervalos en la ventana de ajuste, julio a diciembre de 2025 (D18, D4). |
| **Despacho** | Salida de una formación desde una cabecera. Se mide en cabecera; el intervalo en estaciones intermedias es salida del modelo. |
| **Detención** | Tiempo que la formación queda detenida en una parada intermedia: 24 s de diseño del GTFS (idéntico en toda la red, no medido), 30 s en la Línea F (EsIA). Primero fija, después endógena en la calibración (D13). Va por parada intermedia, no por tramo. **(reemplaza a *dwell time*)** |
| **Día hábil típico** | Día hábil que no está entre los 25 atípicos, el paro general del 10/04/2025, los días con datos parciales ni los días con cancelaciones gremiales. Base de los perfiles y de los intervalos. |
| **Etapa** | Tramo de una ruta hecho a bordo de una sola línea y sentido, entre el nodo donde sube y el nodo donde baja (`Ruta.Etapa`). Entre etapas hay un transbordo o un cambio de sentido. En el dataset de viajes y etapas, *etapa* es además la unidad de registro (una transacción de un modo). |
| **Flota** | Formaciones disponibles. Línea F: 25 (EsIA). Con 18 min de viaje por sentido, sostienen como mínimo unos 92 s de intervalo; 90 s exige vuelta en cabecera de 45 s o menos (paso 12). |
| **Formación** | Tren. Agente del modelo que recorre un recorrido tramo a tramo y sube y baja pasajeros. |
| **Intervalo entre trenes** | Tiempo entre dos despachos sucesivos de una misma línea y cabecera. En la Línea F es variable de escenario, de 90 a 189 s (D7). **(reemplaza a *headway*)**: es el término del EsIA y del pliego. **Intervalo de diseño**: el valor de capacidad que fija la fuente oficial (90 s EsIA, 100 s "de requerirse" según el Ministerio). |
| **Línea F** | Línea proyectada, 12 estaciones y 9,8 km de línea comercial (10,9 km de túneles) entre Brandsen y Palermo; una sola etapa de habilitación. |
| **Nodo** | Par línea-estación (90). Unidad de la topología por la que circulan los trenes; no coincide con el complejo (Constitución es dos nodos). Identificador `Linea<X>:<gtfs_stop_id>`. |
| **Recorrido** | Una línea en un sentido: la secuencia ordenada de nodos y el tiempo de cada tramo. Hay 12 en la red actual (`Recorrido` en la biblioteca). |
| **Ruta (camino)** | Secuencia de nodos precalculada para cada par ordenado de complejos (6.006, `caminos_minimos.csv`), con asignación todo-o-nada. |
| **Sentido** | Dirección de circulación de una línea, `direction_id` 0 o 1 del GTFS. Alberti y Pasco se sirven en un solo sentido, por eso el grafo es dirigido. |
| **Tramo** | Viaje entre dos estaciones contiguas de una misma línea y sentido (166 aristas de tipo `tramo`). Su tiempo `t_s` es de marcha, sin detención. |
| **Transbordo** | Caminata entre andenes de distintas líneas dentro de un complejo (28 aristas de tipo `transbordo`). Su tiempo es el `min_transfer_time` del GTFS, un mínimo de diseño. |
| **Vuelta en cabecera** | Tiempo entre que una formación llega a la cabecera y sale en sentido contrario. Medido en las líneas actuales como cota superior: mediana en hora pico de 72 s (C) a 430 s (B). **(reemplaza a *turnaround*)** |

## 2. Demanda

| Término | Qué es en este proyecto |
|---|---|
| **Concentración horaria** | Fracción de los ingresos diarios que cae en la hora más cargada: 9,9 % en la red (molinetes), ninguna línea por encima de 12,0 %. |
| **Desagregación temporal** | Reparto de la demanda fuera de las horas 8 y 17 con el perfil horario del paso 5. Es el supuesto propio del trabajo desde D2 y va al análisis de sensibilidad. |
| **Etapas incompletas** | Etapas marcadas `viaje_incompleto` (4,1 %). Se conservan: solo mueven la forma horaria, el 1,33 % del día (D1). |
| **Factor de expansión** | Peso de cada registro del dataset de viajes y etapas para llevarlo al total del día (topeado en 3 por el publicador). |
| **Franja (bloque de 15 min)** | Cuarto de hora. El reparto dentro de cada hora sale de molinetes (`demanda_modelo_intrahorario.csv`). La tasa de llegadas es constante dentro de cada bloque. |
| **Hora pico mañana / tarde (HPM / HPT)** | Horas 8 a 9 y 17 a 18, las dos que mide SBASE. La HPM se usa para calibrar y la HPT para validar (D9). |
| **Matriz origen-destino (O-D)** | Viajes entre pares de estaciones o complejos. La del modelo es la de SBASE (septiembre de 2024) con el perfil horario del paso 5 (D2). **(reemplaza a *OD matrix*)** |
| **Molinete** | Barrera de acceso; el dataset de molinetes cuenta ingresos por estación en bloques de 15 min, sin destino. Cuenta pasadas, no medios de pago. |
| **Perfil de carga** | Pasajeros a bordo, suben y bajan por tramo, línea, sentido y hora pico (SBASE). Contraparte empírica de la ocupación a bordo. |
| **Perfil horario** | Reparto de la demanda diaria entre las horas del día. |
| **Proporción** | Fracción de la demanda de una hora que cae en un bloque (columna `share`, que se conserva como nombre de campo). **(reemplaza a *share* en el texto)** |
| **Tasa de transbordo** | Ascensos por viaje: 1,371 observado en HPM y 1,426 en HPT. En el modelo, el cambio de sentido cuenta como un ascenso más (D19). |
| **Viaje / etapa de subte** | Un viaje del modelo es el trayecto de un pasajero dentro de la red, de complejo a complejo; puede tener varias etapas a bordo. |

## 3. Simulación y estadística

| Término | Qué es en este proyecto |
|---|---|
| **AIC** | Criterio de información de Akaike, `2k − 2 ln L`. Se usó para elegir entre familias teóricas en el ajuste de intervalos (paso 12). |
| **Análisis de sensibilidad** | Recorrer los supuestos propios (desagregación temporal, coeficiente de detención por pasajero, regla del pasajero que no aborda) y el intervalo de la Línea F para ver cuánto mueven los indicadores. |
| **Asignación todo-o-nada** | Cada par origen-destino manda el 100 % de su demanda por un único camino (D9). Validada contra la carga de SBASE (correlación 0,994 en HPM). |
| **Bondad de ajuste** | Pruebas de chi-cuadrado (clases equiprobables, `k = ⌈2 n^(2/5)⌉`) y Kolmogorov-Smirnov. Con unos 3.000 datos por celda rechazan casi todo, por eso se informa además el estadístico D. |
| **Calentamiento** | Período inicial de la corrida que no entra en los indicadores. Con horizonte de día completo, el arranque vacío antes de la apertura funciona como calentamiento natural (D11). **(reemplaza a *warm-up*)** |
| **Calibración** | Ajustar un parámetro contra un observado. La penalización por transbordo se calibró contra la carga de HPM. No se calibra contra el mismo dato que después valida (caso Retiro). |
| **Distribución empírica** | La continua lineal por tramos de Law (cap. 6), guardada como 501 cuantiles por celda. Es la que usa el modelo para los intervalos entre despachos (D17). |
| **Estadístico D (de Kolmogorov-Smirnov)** | Máxima distancia entre la función de distribución acumulada observada y la ajustada. No depende del tamaño de muestra; D = 0,05 son 5 puntos de diferencia en el peor punto. |
| **Evento** | Suceso que cambia el estado del sistema (llegada de un pasajero, llegada de una formación, etc.). Ver *Event* y *Dynamic Event* en la sección 4. |
| **Máxima verosimilitud** | Método de estimación de parámetros usado para ajustar las cinco familias (exponencial, gamma, lognormal, Weibull, normal). |
| **Penalización por transbordo** | Costo de 120 s que se suma al tiempo real para elegir la ruta; no es tiempo simulado. El dato no la identifica por encima de 30 s (D9). |
| **Poisson no homogéneo** | Proceso de llegadas con tasa variable en el tiempo; en el modelo, constante por bloque de 15 min, con reinicio en cada borde (exacto por la falta de memoria de la exponencial). |
| **Réplica (replicación)** | Corrida independiente del modelo con otra semilla; al menos diez por escenario, con intervalos de confianza. |
| **Superposición** | Propiedad por la que la suma de procesos de Poisson independientes es un Poisson con la suma de las tasas. Permite generar los 78 complejos con un solo proceso y sortear el origen (biblioteca, `Demanda`). |
| **Supuesto declarado** | Valor o regla sin medición que se explicita en el informe y, si pesa, va a sensibilidad. |
| **Transformada inversa** | Método de muestreo: se sortea `u` uniforme y se toma el cuantil `F⁻¹(u)`, interpolando entre cuantiles de la tabla. |
| **Validación** | Contrastar el modelo contra datos observados que no se usaron para calibrarlo (la HPT de SBASE). |
| **Verificación** | Comprobar que el modelo hace lo que el diseño dice (conservación de pasajeros, rutas reconstruidas, despachos por día). |
| **WAPE** | Error absoluto ponderado (*weighted absolute percentage error*): suma de errores absolutos sobre suma de observados. Métrica de la calibración de la penalización. Sigla técnica, se conserva. |

## 4. AnyLogic y software

Nombres propios de la herramienta y de campos de datos: **se conservan en inglés**.

| Término | Qué es y cómo se usa |
|---|---|
| **Biblioteca `subte`** | Código Java propio (`anylogic/biblioteca/subte.jar`) con la lógica que no depende de AnyLogic: red, rutas, demanda, oferta, andén, carga. |
| **`Delay`** | Bloque PML que retiene al agente un tiempo. En el modelo: detención y tramo de la formación, caminata del pasajero. |
| **`direction_id`** | Campo del GTFS con el sentido (0 o 1). Se conserva como nombre de campo; en el texto, *sentido*. |
| **Dynamic Event** | Evento dinámico de AnyLogic, que se programa y reprograma por código con `create_…()`. Lo usa el modelo para llegadas, despachos y apertura (prueba F2). |
| **`Enter` / `Exit`** | Bloques PML que inyectan en el flowchart un agente que ya existe y lo sacan sin destruirlo. Permiten el reciclado desde una población declarada. |
| **Event** | Evento estático de AnyLogic (por tiempo, cíclico o único). Probado en la prueba F. |
| **Flowchart** | Diagrama de bloques de PML por el que pasan los agentes. Se conserva por ser el nombre del elemento; en el texto puede decirse *diagrama de flujo de proceso*. Tope de 200 bloques por tipo de agente. |
| **`min_transfer_time`** | Campo del GTFS con el tiempo mínimo de transbordo entre andenes (42 a 258 s). Mínimo de diseño, no caminata medida. |
| **Pool (población reciclada)** | Población declarada de agentes que se reutilizan con `Enter`/`Exit` en vez de crearse y destruirse: 32.000 pasajeros (la concurrencia medida llega a unos 27.000) y 150 formaciones. Las poblaciones declaradas no cuentan contra el tope de 50.000 creaciones (prueba D). |
| **Population** | Población de agentes de AnyLogic con cantidad inicial fija. |
| **`SelectOutput`** | Bloque PML que deriva al agente según una condición (¿llegó?, ¿cabecera final?). |
| **`Source` / `Sink`** | Bloques PML que crean y destruyen agentes. **No se usan** en el modelo (cuentan contra el tope de creaciones); son el plan B con grupos de 25 pasajeros. |
| **`Wait`** | Bloque PML que retiene al agente hasta que otro lo libera con `free()`. En el modelo: el pasajero en el andén y a bordo. |

## 5. Siglas

| Sigla | Significado |
|---|---|
| **BA Data** | Portal de datos abiertos de la Ciudad (`data.buenosaires.gob.ar`). |
| **D1 … D19** | Decisiones de modelado registradas en `decisiones.md`. |
| **EIA** | Evaluación de Impacto Ambiental: el procedimiento (Ley 123, expediente EX-2026-20211143). |
| **EsIA** | Estudio de Impacto Ambiental: el documento técnico de la Línea F dentro de la EIA. |
| **EMOVA** | Operadora del subte, autora del estudio del que salen la matriz O-D y los perfiles de carga que entregó SBASE. |
| **GTFS** | *General Transit Feed Specification*, formato estándar de datos de transporte público. De ahí salen topología, tiempos de tramo y transbordo. Nombre propio, no se traduce. |
| **HPM / HPT** | Hora pico mañana (8 a 9) / hora pico tarde (17 a 18). |
| **O-D** | Origen-destino. |
| **PLE** | *Personal Learning Edition*, licencia gratuita de AnyLogic 8.9 con topes de 5 h simuladas (salvo PML), 50.000 creaciones de agentes y 200 bloques por tipo de agente. |
| **PML** | *Process Modeling Library*, biblioteca de AnyLogic elegida por estar exenta del tope de 5 h (D11). |
| **SBASE** | Subterráneos de Buenos Aires Sociedad del Estado. |
| **SUBE** | Sistema Único de Boleto Electrónico. |
| **WAPE** | Ver sección 3. |

---

## 6. Anglicismos en textos vigentes

**Corregidos el 21/09/2026**, en los documentos, en los reportes y en los scripts que
escriben esos reportes (los reportes se corrigieron a mano, sin regenerarlos, para no
pisar retoques previos):

| Término | Se reemplazó por |
|---|---|
| *headway* | intervalo entre trenes; intervalo de diseño cuando es el valor de la fuente oficial |
| *matchear*, *matcheo*, *no-matcheos* | cruzar, asignar, registros sin cruzar |
| *argmin* | el valor que minimiza el error |
| *share* en el texto corrido | proporción (la columna `share` se conserva) |

Los identificadores de código se conservan (`HEADWAY_F_S`, `matchear_centroides`, el
`argmin` de numpy): son nombres técnicos.

**Tecnicismos que se aceptan en inglés** (decidido el 21/09/2026), por estar muy
extendidos y sin un equivalente corto que se use en el área:

| Término | Qué es en este proyecto |
|---|---|
| *dataset* | Conjunto de datos publicado como unidad en BA Data (p. ej. "Subte: Trenes despachados"), con uno o varios recursos |
| *pipeline* | La cadena de scripts `src/01` a `src/13`, que va de los datos crudos a los insumos del modelo |
| *feed* | La publicación GTFS del Subte (los 14 archivos `.txt`) |
