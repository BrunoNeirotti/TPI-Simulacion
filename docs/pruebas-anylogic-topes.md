# Límites de AnyLogic PLE: qué medimos

AnyLogic Personal Learning Edition tiene topes que podían hacer imposible el modelo,
así que antes de escribir nada corrimos cinco pruebas para medirlos en vez de
suponerlos. Todas el 25/08/2026, sobre AnyLogic 8.9.9 PLE, en la máquina de trabajo.

Los modelos están en `anylogic/pruebas/` y los genera
`src/08_generar_pruebas_anylogic.py`. Salen de `MM1.alp` del TP 3, que ya sabíamos que
compilaba, cambiándole solo los parámetros que cada prueba necesita. Los cinco son
`Source -> Queue -> Delay -> Sink` de Process Modeling Library.

El resultado corto: se puede simular el día completo con un agente por pasajero.

---

## 1. Los topes de la edición

Salen de la comparación oficial de ediciones:

| Tope | Valor |
|---|---|
| Agentes creados dinámicamente | 50.000 |
| Tiempo de modelado | 5 h, en todas las bibliotecas salvo Process Modeling Library |
| Tipos de agente por modelo | 10 |
| Poblaciones y bloques de flowchart por tipo de agente | 200 |
| OptQuest | 500 iteraciones, 7 parámetros |

Teníamos anotado que la licencia University Researcher levantaba los topes. Es falso:
tiene los mismos 50.000 agentes y las mismas 5 h, así que no es una salida al problema
de escala. La salvedad es que `anylogic.help` devuelve 403 a los fetchers, así que esto
viene de dos búsquedas independientes que coinciden y no de la página leída directo.
Igual no cambia nada, porque el diseño no depende de esa licencia.

Lo que la documentación no aclara, y estas pruebas resuelven, es si la exención de PML
es real, si el tope de 50.000 cuenta creaciones o entidades vivas, y si la máquina
aguanta decenas de miles de agentes en un tiempo de reloj razonable.

---

## 2. Resultados

| Prueba | Contador del `source` | Esperado | Qué establece |
|---|---:|---|---|
| A | 734 | ~720 si corre 20 h, ~180 si corta a las 5 h | PML corre las 20 h |
| B | 50.027 | ~72.000 si cuenta vivas, ~50.000 si cuenta creaciones | El tope cuenta creaciones |
| C | 39.773 | ~40.014 | El rendimiento no es el límite |
| D | 31, con `poblacion [60000]` viva | - | Las poblaciones declaradas no cuentan |
| E | 31, con `poblacion [25000]` viva | - | El pool reciclado entra en memoria |

### 2.1 A: Process Modeling Library está exenta del tope de 5 h

734 llegadas con media de 100 s son 73.400 s de reloj de modelo, o sea que corrió las 20
horas completas. Si el tope la hubiera alcanzado, el contador se habría quedado en unos
180.

Esto es lo que sostiene todo el resto: el día de servicio son unas 19 h contra un tope
de 5, así que sin la exención el horizonte de día completo era imposible. PML queda como
la base obligada del modelo.

### 2.2 B: el tope de 50.000 cuenta creaciones, no entidades vivas

El modelo se detuvo en 50.027 creaciones teniendo un solo agente vivo, con el contenido
del `delay` en 1. Los dos números están separados por cuatro órdenes de magnitud, así
que no hay otra lectura posible: lo que se cuenta es la creación y no la coexistencia.

O sea que el presupuesto de agentes de una corrida se gasta y no se recupera al destruir
entidades. Reciclar en vez de crear y destruir podría ser la salida, y eso es lo que
mide la prueba D.

### 2.3 El tope se reinicia entre replicaciones

Esto no lo buscábamos. El experimento `Replicas10` de la prueba C completó las diez
iteraciones con 39.773 agentes cada una, o sea 397.730 acumulados, casi ocho veces el
tope, sin un solo error. Si el presupuesto fuera acumulado por experimento habría muerto
en la segunda iteración.

La prueba B lo confirma por el otro lado: su `Replicas10` sí falló, con
`RuntimeException: Error in the model during iteration 2` desde
`ExperimentParamVariation`. Falla porque una sola corrida suya quiere crear 72.000.

Es el resultado que más tranquiliza: las diez replicaciones por escenario que el TPI se
comprometió a correr no compiten por el mismo presupuesto, cada corrida arranca con sus
50.000.

Hay un detalle operativo que conviene recordar. Al tocar el tope, una corrida simple
degrada sin romperse: el `source` deja de crear y el modelo sigue hasta el final, como
se ve en B, donde el `sink` quedó en 50.026 y el reloj llegó a 72.000 s. Pero en un
experimento de variación de parámetros lanza excepción y aborta. Un modelo que roza el
tope puede parecer que anda en corrida simple y romperse recién al replicar, así que
conviene dejar margen.

### 2.4 C: el rendimiento no es el problema

39.773 agentes creados, 1.137 vivos a la vez, 19 h simuladas. Y una corrida previa mal
configurada, con unos 39.768 agentes vivos al mismo tiempo, también terminó casi
instantáneamente. Nos falta el cronómetro de la corrida buena, pero que `Replicas10`
completara diez iteraciones ya acota el orden de magnitud.

El límite operativo es la licencia, no la máquina.

### 2.5 D: las poblaciones declaradas no cuentan

El modelo corrió con `poblacion [60000]` instanciada y el flowchart funcionando, con 31
llegadas en la hora simulada contra unas 36 esperadas, sin ningún error de licencia. El
tope de 50.000 alcanza solo a los agentes creados dinámicamente, no a los declarados en
la inicialización.

Eso vuelve viable el reciclado: un pool declarado que se redespacha en vez de crear y
destruir no gasta presupuesto de licencia.

Pero apareció otro límite, y es la memoria. El `Replicas10` de esta prueba murió con
`java.lang.OutOfMemoryError` en el hilo `Frame Collector`. No es un error de licencia:
son 60.000 bloques `Sink` con presentación gráfica que no entran en los 2 GB
configurados.

### 2.6 Cuántos agentes hacen falta en realidad

Acá está el punto que cambió el diseño. Lo que rompe el tope de 50.000 no es la cantidad
de gente simultánea sino el acumulado del día, y son dos números muy distintos que
veníamos tratando como uno solo.

Con el tiempo de viaje medio ponderado por la demanda real, 910 s según
`caminos_minimos.csv`, más unos 120 s de espera de andén, la permanencia media en el
sistema es de 1.030 s, o sea unos 17 minutos. Por la ley de Little, sobre la hora pico
de 72.396 etapas:

| `k` | Llegadas en hora pico | Vivos a la vez | Creaciones en el día |
|---:|---:|---:|---:|
| 1 | 72.396 | 20.722 | 740.568 |
| 5 | 14.479 | 4.144 | 148.113 |
| 10 | 7.239 | 2.072 | 74.056 |
| 25 | 2.895 | 828 | 29.622 |

Con un agente por pasajero la concurrencia máxima es de 20.722, muy por debajo de los
50.000. Lo único que lo impedía eran las 740.568 creaciones, y las poblaciones
declaradas no cuentan. Los 60.000 de la prueba D eran casi el triple de lo necesario.

### 2.7 E: el pool reciclado entra

Pasó las dos corridas. La simple instanció `poblacion [25000]` con el flowchart
funcionando, y el `Replicas10` completó las diez iteraciones sin quedarse sin memoria,
con `L = 0,109`, que es exactamente lo que predice su configuración: 0,01 llegadas por
segundo por 10 s de retardo medio. El resultado es consistente, no casualidad.

Lo que mató a la prueba D no era el diseño sino el dimensionamiento.

---

## 3. Lo que queda establecido

| Pregunta | Respuesta | De dónde sale |
|---|---|---|
| ¿PML corre el día completo? | Sí, 20 h simuladas | A |
| ¿Qué cuenta el tope de 50.000? | Creaciones dinámicas, no entidades vivas | B |
| ¿Se reinicia entre replicaciones? | Sí, cada corrida tiene su presupuesto | C, `Replicas10` |
| ¿Aguanta la máquina unos 40.000 agentes? | Sí, y termina casi al instante | C |
| ¿Cuentan las poblaciones declaradas? | No | D |
| ¿Entra un pool de 25.000 en memoria? | Sí, incluso con 10 replicaciones | E |

Con eso, la arquitectura queda así: Process Modeling Library, horizonte de día completo,
y un pool declarado de unos 25.000 pasajeros que se recicla con `Enter` y `Exit` en vez
de `Source` y `Sink`. El objetivo es un agente por pasajero.

Si el modelo real resulta más pesado de lo previsto, el plan B ya está verificado:
agrupar de a 25 pasajeros con `Source` y `Sink` funciona sin reciclado, con 29.622
creaciones contra un tope de 50.000.

La fidelidad visual de detalle va al submodelo peatonal de Constitución en hora pico,
con 9.951 ingresos y una figura por persona, que entra holgado en los dos topes.

### Dos salvedades

Los 25.000 de la prueba E estaban quietos: son bloques `Sink` instanciados que no hacen
nada. Los pasajeros reales van a tener estado, atributos y ruta, y se van a mover por
los bloques, así que el costo por agente va a ser mayor. Lo que E demuestra es que el
costo de instanciar no es problema, no que el de la actividad tampoco lo sea. Igual eso
ya está bastante acotado por C, donde 39.773 agentes con 1.137 activos a la vez
terminaron casi al instante, y por la corrida fallida previa, que tuvo unos 39.768 vivos
al mismo tiempo sin problemas.

Falta confirmar que inyectar desde el pool no cuente como creación. La prueba B contó
creaciones de `Source`, y `Enter` no crea sino que toma un agente que ya existe. Es lo
más probable, pero no lo verificamos. Se va a ver de inmediato al construir el modelo
real: si contara, el contador se dispara en la primera corrida.

---

## 4. Un hallazgo lateral que sirve para el modelo

AnyLogic 8.9.9 trae un API de diseño en Python en `anylogic_design_time_api/`, que se
conecta por py4j a una instancia abierta y permite crear marcación espacial por código:
caminos, nodos, redes, vías de tren, andenes, escaleras y paredes.

No sirvió para estas pruebas, porque no crea bloques de flowchart ni eventos, pero sí
sirve para el modelo: la marcación de las 90 estaciones y el agregado de la Línea F se
pueden dibujar desde `grafo_nodos.csv` y `grafo_aristas.csv` en lugar de a mano. Va en
la misma dirección que impone el tope de 200 bloques por tipo de agente, que ya obliga a
que la topología viva en los datos y no en el dibujo. Y abarata el paso 8, que es la
prueba de diseño que el plan se puso a sí mismo.
