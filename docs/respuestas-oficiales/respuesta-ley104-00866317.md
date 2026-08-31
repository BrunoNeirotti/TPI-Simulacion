# Respuesta a la solicitud Ley 104 N° 00866317/26

Expediente EX-2026-35399949-GCABA-DGAIGA. Llegó por correo de
`legalesdgtalmi@buenosaires.gob.ar` con tres informes adjuntos. Es la solicitud que
habíamos presentado por BA Colaborativa y vencía alrededor del 27/08/2026. Se contestó en
término y, a diferencia de la otra, contestó de verdad.

| Informe | Organismo | Fecha | Apartados que contesta |
|---|---|---|---|
| `IF-2026-38553261-GCABA-SBASE` | Subterráneos de Buenos Aires S.E. | 26/08/2026 | 1 y 2 |
| `IF-2026-37530623-GCABA-MMIGC` | Asesor Técnico, Min. de Movilidad e Infraestructura | 20/08/2026 | 5, 6 y 7 |
| `IF-2026-38751180-GCABA-DGDPM` | D.G. Diseño y Planificación de la Movilidad | 27/08/2026 | 3 y 4 |

Copia local de los tres PDF en este mismo directorio.

Las planillas no venían como archivos del correo: el PDF de SBASE las lleva embebidas,
en `/Names /EmbeddedFiles`, sin extensión y con nombre largo. Son dos XLSX. Las
extrajimos a `data/raw/sbase-ley104/` y también se versionan en `adjuntos-sbase/`. Quien
abra el PDF en un visor que no muestre adjuntos no se entera de que están.

---

## 1. SBASE: matriz origen-destino de la red y perfiles de carga

Firmado por German Bussi, Gerente. Es la pieza que cierra el hueco más grande del
trabajo.

### 1.1 Qué entregó

`matrices-od-sbase-emova-2024.xlsx`, una matriz origen-destino de 90 por 90 estaciones,
en tres hojas:

| Hoja | Período | Pares con flujo | Viajes |
|---|---|---:|---:|
| `Diaria` | día hábil representativo | 7.699 de 8.010 | 827.976 |
| `HPM` | hora pico mañana, 8 a 9 h | 4.812 | 74.351 |
| `HPT` | hora pico tarde, 17 a 18 h | 5.868 | 80.197 |

Y `perfil-carga-2024-lineas-actuales.xlsx`, que da para cada una de las seis líneas, los
dos sentidos y las dos horas pico cuánta gente sube, cuánta baja y cuántos pasajeros van
a bordo en el tramo que sale de cada estación. Son 360 filas.

### 1.2 Procedencia y método, según el propio informe

- Es un estudio de EMOVA S.A. de septiembre de 2024, sobre conteo y análisis de
  transacciones SUBE.
- SBASE declara que en septiembre de 2024 SUBE concentraba más del 95 % de las
  transacciones del subte y del resto del transporte público del AMBA.
- Declara además que desde diciembre de 2024 los nuevos medios de pago (débito, crédito
  y QR) son el 35 % de las transacciones del subte y no permiten trazabilidad de etapas,
  porque la estrategia de pago varía con las promociones bancarias. Por eso "para la
  planificación resulta procedente tomar como base los valores de los meses de
  septiembre y octubre 2024".
- Advierte que la matriz y los diagramas de carga pueden no coincidir: los diagramas
  pasan por "un proceso de ajuste e iteración sobre la distribución de ascensos y
  descensos" para que la carga cierre en cero en la terminal.

Eso confirma desde la fuente la decisión de fondo del paso 5. Nuestra matriz se
construyó sobre el 16/10/2024 justamente para no cruzar la apertura de medios de pago, y
SBASE eligió septiembre y octubre de 2024 por la misma razón y casi con las mismas
palabras.

### 1.3 Los dos libros numeran las estaciones distinto

Los dos numeran de 1 a 90 y coinciden solo hasta el id 75. La matriz O-D pone la cola de
la Línea E (Correo Central, Catalinas y Retiro E) al final de todo, y el perfil de carga
la pone antes de la Línea H. Usar el mapa de un libro con los datos del otro corre 15
estaciones sin producir ningún error visible. `src/lib_sbase.py` usa siempre el mapa del
propio libro y falla si el cruce no da 90 de 90.

### 1.4 El cruce con nuestro grafo es uno a uno

Las 90 estaciones de SBASE son exactamente los 90 nodos del grafo del paso 2, o sea el
par línea-estación: 18 de la A, 17 de la B, 9 de la C, 16 de la D, 18 de la E y 12 de la
H. Retiro de la C y Retiro de la E son dos filas distintas, igual que Callao de la B y
Callao de la D. El cruce está declarado a mano en la tabla `ALIAS` de `lib_sbase.py`, sin
comparación difusa.

---

## 2. MMIGC: parámetros y trazado de la Línea F

Firmado por Sergio Fernando Sour, Asesor Técnico. Referencia
`RE-2026-35400191-GCABA-DGAIGA`.

### 2.1 Distancias entre estaciones, que era el dato que faltaba

| Tramo | Metros | Progresiva acumulada |
|---|---:|---:|
| Brandsen - Constitución | 1.300 | 1.300 |
| Constitución - Cochabamba | 1.500 | 2.800 |
| Cochabamba - Chile | 700 | 3.500 |
| Chile - Congreso | 800 | 4.300 |
| Congreso - Corrientes | 600 | 4.900 |
| Corrientes - Pizzurno | 600 | 5.500 |
| Pizzurno - Junín | 800 | 6.300 |
| Junín - Pueyrredón | 700 | 7.000 |
| Pueyrredón - Parque Las Heras | 1.000 | 8.000 |
| Parque Las Heras - Ecoparque | 1.000 | 9.000 |
| Ecoparque - Palermo / Pacífico | 800 | 9.800 |

La suma da 9.800 m exactos, que es la longitud de línea comercial del pliego. Con eso
queda cerrada la cuestión de las tres longitudes: 9,8 km es la línea, 10,9 km son los
túneles y 8,6 km era la traza del PETERS de 2015.

Lo verificamos contra el EsIA: las progresivas por estación de la ficha del expediente
(Brandsen en 393 m, Pizzurno en 5.950, Junín en 6.850, Ecoparque en 9.535) quedan a 57,
157 y 142 m de las que salen de esta tabla sumando el offset de Brandsen. Dos fuentes
independientes coinciden dentro de 150 m sobre 9,8 km.

El informe explica además el criterio de emplazamiento: "en todos los casos dónde la
línea F cruza a diferente nivel una Línea de Subte existente, se ha previsto la necesidad
de una Estación", y donde no hay cruce la ubicación salió del estudio de demanda.

### 2.2 Parámetros operativos, con una cifra nueva

- Intervalo de diseño de 100 segundos, "de requerirse". El EsIA declaraba 1,5 min, o sea
  90 s. Los dos son valores de diseño, no de operación.
- Velocidad máxima de 90 km/h, "en algún tramo".
- Tiempo de viaje entre cabeceras de unos 18 minutos para 9,8 km, o sea una velocidad
  comercial de 32,7 km/h.
- Formaciones de seis coches, con el Alstom Serie 300 como parámetro de diseño. El
  material rodante se licita aparte.

Lo más importante del informe es lo que dice que no existe: "El responsable de la
Operación, que no forma parte del alcance de esta Licitación, definirá la Operación […]
decidirá la frecuencia de viajes para diferentes franjas horarias en función de atender
la demanda así como los tiempos finales de detención". O sea que no hay plan de servicio
y no va a haberlo hasta que exista operador. Todo lo que el trabajo diga sobre frecuencia
y detención de la Línea F es necesariamente un escenario, y esta es una cita oficial que
lo justifica.

### 2.3 La habilitación es en una sola etapa

"En el Portal BA Obras se encuentra publicado el Cronograma de la Línea F, la que se
desarrollara en UNA (1) única Etapa, desde Brandsen a Palermo / Pacífico". Por la
metodología de tuneladora con pozo de ataque en Brandsen, "no se prevé en principio la
habilitación parcial de funcionamiento de la Línea F antes de la finalización completa de
las obras"; una apertura parcial del tramo sur, de justificarse, sería "durante los
últimos 6 meses".

Choca con el EsIA, que parte la obra en Tramo A hasta Pizzurno y Tramo B. La lectura que
las concilia es que la partición del EsIA es constructiva y esta respuesta es sobre
habilitación al servicio: se construye por tramos y se abre de una sola vez.

Por esto sacamos de la propuesta el escenario de "primer tramo" Brandsen a Pizzurno, que
figuraba en Resultados esperados, y citamos esta respuesta en su lugar. Queda un solo
escenario futuro, que es la traza completa con variantes de frecuencia.

### 2.4 Combinaciones

"En la información gráfica suministrada a los Oferentes en el Portal BA Obras se
encuentran las Estaciones con combinación". Salvo Pizzurno, que se ubica equidistante
entre la actual Callao de la D y la futura estación de la Línea G, todas las estaciones de
combinación se emplazan "a la menor distancia posible" de la existente.

No entrega tiempos de transbordo, que era lo que pedía el apartado 6.2. Agrega que los
modelos de simulación de la combinación son parte de la ingeniería de detalle del
adjudicatario, o sea que todavía no existen.

---

## 3. DGDPM: estudio de demanda y escenarios con y sin proyecto

Firmado por Martín Álvarez del Rivero, Director General. Es el apartado que menos se
contestó.

Remite otra vez al portal BA Obras: "se encuentra publicado el estudio de demanda de la
Línea F, donde puede consultarse la documentación técnica correspondiente". Es la tercera
remisión al pliego, después de la otra respuesta, y sigue sin ser cierta en el sentido
pedido: el índice maestro de la licitación tiene 1.866 documentos y los únicos que
mencionan demanda son el `IN-003` y el `IN-004`, que dimensionan medios de salida y
evacuación de andenes, no demanda de viajes. Está desarrollado en
`docs/pliego-licitacion-linea-f.md`, sección 7.

Describe el análisis comparativo pero sin publicar una sola cifra. Declara tres niveles
de análisis: el área de influencia de las estaciones proyectadas, la red de subtes con la
derivación de etapas actuales y las etapas nuevas sin cobertura previa, y la futura
extensión del FFCC Belgrano Sur hasta Constitución. Y dice que la comparación se hizo "a
partir de la situación actual y extrapolados al año 2019, tomado como referencia por
tratarse de un período previo a la pandemia con un mayor nivel de demanda".

Confirma cualitativamente el efecto buscado: "una redistribución de la demanda hacia la
nueva línea y un alivio de determinados tramos de la red existente, particularmente en
las líneas C y D", y destaca el nodo Constitución por su vínculo con la Línea C, el Roca
y la futura extensión del Belgrano Sur, "verificando una elevada carga asociada a este
tramo de la nueva línea".

Hay un dato metodológico que sirve y conviene citar: el organismo declara que sus propias
proyecciones de la Línea F están extrapoladas a 2019 por ser prepandemia y de mayor
demanda. Es la confirmación oficial de que las cifras de demanda de la Línea F no
describen la red actual, que es exactamente la salvedad que veníamos declarando sobre el
perfil de carga de SBASE 2019.

---

## 4. Qué se obtuvo y qué sigue faltando

Lo que se obtuvo:

1. La matriz O-D de la red a nivel de estación, con hora pico mañana y tarde, y no
   simétrica por construcción.
2. Los perfiles de carga por tramo de las seis líneas, con lo que la ocupación a bordo
   deja de ser un indicador sin contraparte empírica.
3. Las distancias entre las doce estaciones de la Línea F, que suman los 9,8 km.
4. Cuatro parámetros operativos nuevos o precisados de la Línea F.
5. La constancia oficial de que no hay plan de servicio.
6. La constancia oficial de que la habilitación es en una sola etapa.

Lo que sigue faltando:

- El *Análisis de Demanda Línea F* de SBASE 2019, o su derivado, el *Informe Strans*.
  Ninguno de los tres informes lo adjunta, así que la ficha del EsIA sigue siendo la
  única vía a sus tablas.
- Los resultados numéricos de los escenarios con y sin proyecto. La DGDPM describe el
  método y el sentido del resultado, pero no publica cifras.
- Los tiempos de transbordo de las combinaciones de la Línea F, que se contestaron con
  una remisión a los gráficos del pliego.

Decidimos no reclamar por lo que falta. Lo que queda es chico, acotado a los apartados 3
y 4, y tiene poco valor para el trabajo: el perfil de carga de la Línea F ya está en la
ficha del EsIA, y los escenarios con y sin proyecto son justamente lo que el TPI produce,
así que tenerlos de antemano no lo mejoraría.
