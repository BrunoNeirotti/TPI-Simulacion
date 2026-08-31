# Respuesta a la solicitud Ley 104 N° 00866317/26

Expediente **EX-2026-35399949-GCABA-DGAIGA**. Llegó por correo de
`legalesdgtalmi@buenosaires.gob.ar` con tres informes adjuntos. Es la
solicitud 2.b, la que se había presentado por
BA Colaborativa y vencía alrededor del 27/08/2026. **Se contestó en término y,
a diferencia de la 2.a, contestó de verdad.**

| Informe | Organismo | Fecha | Apartados que contesta |
|---|---|---|---|
| `IF-2026-38553261-GCABA-SBASE` | Subterráneos de Buenos Aires S.E. | 26/08/2026 | 1 y 2 |
| `IF-2026-37530623-GCABA-MMIGC` | Asesor Técnico, Min. de Movilidad e Infraestructura | 20/08/2026 | 5, 6 y 7 |
| `IF-2026-38751180-GCABA-DGDPM` | D.G. Diseño y Planificación de la Movilidad | 27/08/2026 | 3 y 4 |

Copia local de los tres PDF en este mismo directorio.

> **Las planillas no venían como archivos del correo.** El PDF de SBASE las
> lleva **embebidas** (`/Names /EmbeddedFiles`), sin extensión y con nombre
> largo. Son dos XLSX. Se extrajeron a `data/raw/sbase-ley104/` y también se
> versionan en `adjuntos-sbase/`. Quien abra el PDF en un visor que no muestre
> adjuntos no ve que están.

---

## 1. SBASE — matriz origen-destino de la red y perfiles de carga

Firmado por German Bussi, Gerente. Es la pieza que cierra el hueco más grande
del trabajo.

### 1.1 Qué entregó

**`matrices-od-sbase-emova-2024.xlsx`** — matriz origen-destino de **90 × 90
estaciones**, en tres hojas:

| Hoja | Período | Pares con flujo | Viajes |
|---|---|---:|---:|
| `Diaria` | día hábil representativo | 7.699 de 8.010 | 827.976 |
| `HPM` | hora pico mañana, 8–9 h | 4.812 | 74.351 |
| `HPT` | hora pico tarde, 17–18 h | 5.868 | 80.197 |

**`perfil-carga-2024-lineas-actuales.xlsx`** — por cada una de las seis líneas,
los dos sentidos y las dos horas pico: **suben, bajan y pasajeros a bordo** en
el tramo que sale de cada estación. 360 filas.

### 1.2 Procedencia y método, según el propio informe

- Estudio de **EMOVA S.A., septiembre de 2024**, sobre conteo y análisis de
  transacciones **SUBE**.
- SBASE declara que en septiembre de 2024 SUBE concentraba **más del 95 %** de
  las transacciones del subte y del resto del transporte público del AMBA.
- Declara además que desde diciembre de 2024 los nuevos medios de pago
  (débito, crédito, QR) son el **35 %** de las transacciones del subte y **no
  permiten trazabilidad de etapas**, porque la estrategia de pago varía con las
  promociones bancarias. Por eso *"para la planificación resulta procedente
  tomar como base los valores de los meses de septiembre y octubre 2024"*.
- Advierte que la matriz y los diagramas de carga **pueden no coincidir**: los
  diagramas pasan por *"un proceso de ajuste e iteración sobre la distribución
  de ascensos y descensos"* para que la carga cierre en cero en la terminal.

> **Esto confirma, desde la fuente, la decisión de fondo del paso 5.** La matriz
> del trabajo se construyó sobre el 16/10/2024 justamente para no cruzar la
> apertura de medios de pago. SBASE eligió septiembre–octubre de 2024 por la
> misma razón y con las mismas palabras.

### 1.3 La trampa de los dos mapas de identificador

Los dos libros numeran las estaciones de 1 a 90 y **coinciden solo hasta el
id 75**. La matriz O-D pone la cola de la Línea E (Correo Central, Catalinas,
Retiro E) al final de todo; el perfil de carga la pone antes de la Línea H.
Usar el mapa de un libro con los datos del otro corre 15 estaciones sin producir
ningún error visible. `src/lib_sbase.py` usa siempre el mapa del propio libro y
falla si el cruce no da 90 de 90.

### 1.4 El cruce con nuestro grafo es uno a uno

Las 90 estaciones de SBASE son exactamente los **90 nodos** del grafo del paso 2
(par línea-estación): 18 A, 17 B, 9 C, 16 D, 18 E, 12 H. Retiro [C] y Retiro [E]
son dos filas distintas, igual que Callao [B] y Callao [D]. El cruce está
declarado a mano en la tabla `ALIAS` de `lib_sbase.py`, sin comparación difusa.

---

## 2. MMIGC — parámetros y trazado de la Línea F

Firmado por Sergio Fernando Sour, Asesor Técnico. Referencia
`RE-2026-35400191-GCABA-DGAIGA`.

### 2.1 Distancias entre estaciones: el dato que faltaba para el paso 8

| Tramo | Metros | Progresiva acumulada |
|---|---:|---:|
| Brandsen – Constitución | 1.300 | 1.300 |
| Constitución – Cochabamba | 1.500 | 2.800 |
| Cochabamba – Chile | 700 | 3.500 |
| Chile – Congreso | 800 | 4.300 |
| Congreso – Corrientes | 600 | 4.900 |
| Corrientes – Pizzurno | 600 | 5.500 |
| Pizzurno – Junín | 800 | 6.300 |
| Junín – Pueyrredón | 700 | 7.000 |
| Pueyrredón – Parque Las Heras | 1.000 | 8.000 |
| Parque Las Heras – Ecoparque | 1.000 | 9.000 |
| Ecoparque – Palermo / Pacífico | 800 | **9.800** |

**La suma da 9.800 m exactos**, que es la longitud de línea comercial del
pliego. Cierra la cuestión de las tres longitudes: 9,8 km es la línea, 10,9 km
son los túneles y 8,6 km era la traza del PETERS de 2015.

Verificación cruzada con el EsIA: las progresivas por estación de la ficha del
expediente (Brandsen en 393 m, Pizzurno 5.950, Junín 6.850, Ecoparque 9.535)
quedan a **57, 157 y 142 m** de las que salen de esta tabla sumando el offset de
Brandsen. Dos fuentes independientes coinciden dentro de 150 m sobre 9,8 km.

El informe explica además el criterio de emplazamiento: *"en todos los casos
dónde la línea F cruza a diferente nivel una Línea de Subte existente, se ha
previsto la necesidad de una Estación"*, y donde no hay cruce, la ubicación
salió **del estudio de demanda**.

### 2.2 Parámetros operativos, con una cifra nueva

- **Intervalo de diseño: 100 segundos**, *"de requerirse"*. El EsIA declaraba
  1,5 min (90 s). Los dos son valores de diseño, no de operación.
- **Velocidad máxima 90 km/h**, *"en algún tramo"*.
- **Tiempo de viaje entre cabeceras: ~18 minutos** para 9,8 km, es decir una
  velocidad comercial de **32,7 km/h**.
- **Formaciones de seis coches**, con **Alstom Serie 300** como parámetro de
  diseño. El material rodante se licita aparte.

> **Lo más importante del informe es lo que dice que no existe.** *"El
> responsable de la Operación, que no forma parte del alcance de esta
> Licitación, definirá la Operación […] decidirá la frecuencia de viajes para
> diferentes franjas horarias en función de atender la demanda así como los
> tiempos finales de detención"*. Es decir: **no hay plan de servicio y no lo va
> a haber hasta que exista operador**. Todo lo que el trabajo diga sobre
> frecuencia y detención de la Línea F es necesariamente un escenario. Esto es
> una cita oficial que justifica el tratamiento por sensibilidad, y no una
> limitación del grupo.

### 2.3 Etapas: contradice la partición del EsIA

*"En el Portal BA Obras se encuentra publicado el Cronograma de la Línea F, la
que se desarrollara en **UNA (1) única Etapa**, desde Brandsen a Palermo /
Pacífico"*. Por la metodología de tuneladora con pozo de ataque en Brandsen,
*"no se prevé en principio la habilitación parcial de funcionamiento de la Línea
F antes de la finalización completa de las obras"*; una apertura parcial del
tramo sur, de justificarse, sería *"durante los últimos 6 meses"*.

**Choca con el EsIA**, que parte la obra en Tramo A (hasta Pizzurno) y Tramo B.
La lectura que las concilia es que la partición del EsIA es **constructiva** y
esta respuesta es sobre **habilitación al servicio**: se construye por tramos,
se abre de una sola vez.

> **Afecta al documento.** `docs/definitivo-main.tex`, en Resultados esperados,
> habla del *"primer tramo"* Brandsen–Pizzurno como un escenario. Con esta
> respuesta ese escenario deja de tener sentido operativo: no va a haber
> servicio parcial. Hay que decidir si se quita, si se reformula como análisis
> de sensibilidad sobre la traza, o si se mantiene declarando esta cita.

### 2.4 Combinaciones

*"En la información gráfica suministrada a los Oferentes en el Portal BA Obras
se encuentran las Estaciones con combinación"*. Salvo **Pizzurno**, que se
ubica equidistante entre la actual Callao [D] y la futura estación de la Línea
G, todas las estaciones de combinación se emplazan *"a la menor distancia
posible"* de la existente. **No entrega tiempos de transbordo**, que era lo que
el apartado 6.2 pedía. Agrega que los modelos de simulación de la combinación
son parte de la ingeniería de detalle del adjudicatario, o sea que todavía no
existen.

---

## 3. DGDPM — estudio de demanda y escenarios con y sin proyecto

Firmado por Martín Álvarez del Rivero, Director General. Es el apartado que
menos se contestó.

- **Remite otra vez al portal BA Obras**: *"se encuentra publicado el estudio de
  demanda de la Línea F, donde puede consultarse la documentación técnica
  correspondiente"*. Es la **tercera remisión al pliego**, después de la
  respuesta 2.a. Sigue sin ser cierto en el sentido pedido: el índice maestro de
  la licitación tiene 1.866 documentos y los únicos que mencionan demanda son
  `IN-003` e `IN-004`, que dimensionan **medios de salida y evacuación de
  andenes**, no demanda de viajes (ver `docs/pliego-licitacion-linea-f.md`,
  sección 7).
- **Describe el análisis comparativo, pero sin una sola cifra.** Declara tres
  niveles de análisis —área de influencia de las estaciones proyectadas, red de
  subtes (derivación de etapas actuales y etapas nuevas sin cobertura previa) y
  la futura extensión del FFCC Belgrano Sur hasta Constitución— y dice que la
  comparación se hizo *"a partir de la situación actual y extrapolados al año
  2019, tomado como referencia por tratarse de un período previo a la pandemia
  con un mayor nivel de demanda"*.
- **Confirma cualitativamente el efecto buscado**: *"una redistribución de la
  demanda hacia la nueva línea y un alivio de determinados tramos de la red
  existente, particularmente en las líneas C y D"*, y destaca el **nodo
  Constitución** por su vínculo con la Línea C, el Roca y la futura extensión
  del Belgrano Sur, *"verificando una elevada carga asociada a este tramo de la
  nueva línea"*.

> **Dato metodológico que sirve y hay que citar:** el organismo declara que sus
> propias proyecciones de la Línea F están **extrapoladas a 2019** por ser
> prepandemia y de mayor demanda. Es la confirmación oficial de que las cifras
> de demanda de la Línea F no describen la red actual, que es exactamente la
> salvedad que el trabajo venía declarando sobre el perfil de carga de SBASE
> 2019.

---

## 4. Qué se obtuvo y qué sigue faltando

**Obtenido:**

1. Matriz O-D de la red a nivel de estación, con hora pico mañana y tarde, no
   simétrica por construcción.
2. Perfiles de carga por tramo de las seis líneas: la ocupación a bordo deja de
   ser un indicador sin contraparte empírica.
3. Distancias entre las doce estaciones de la Línea F, que suman los 9,8 km.
4. Cuatro parámetros operativos nuevos o precisados de la Línea F.
5. La constancia oficial de que **no hay plan de servicio** de la Línea F.
6. La constancia oficial de que la habilitación es **en una sola etapa**.

**Sigue faltando, y es lo mismo de siempre:**

- El ***Análisis de Demanda Línea F* (SBASE, 2019)** o su derivado, *Informe
  Strans*. Ninguno de los tres informes lo adjunta. La ficha del EsIA sigue
  siendo la única vía a sus tablas.
- Los **resultados numéricos** de los escenarios con y sin proyecto. La DGDPM
  describe el método y el sentido del resultado, pero no publica cifras.
- Los **tiempos de transbordo** de las combinaciones de la Línea F (apartado
  6.2, contestado con una remisión a los gráficos del pliego).

**Consecuencia sobre el reclamo ante el OGDAI.** El borrador de
`borrador-reclamo-ogdai.md` estaba pensado para cubrir las dos solicitudes con
un solo reclamo. Ya no corresponde en esos términos: esta solicitud se contestó
sustantivamente. Lo que queda es un reclamo mucho más chico y mejor fundado,
acotado a los apartados 3 y 4 —el estudio de demanda y los resultados numéricos
de los escenarios—, y con un argumento nuevo: la propia DGDPM describe un
análisis comparativo que hizo y cuyos valores no entrega. **Es una decisión del
grupo, no una tarea automática.**
