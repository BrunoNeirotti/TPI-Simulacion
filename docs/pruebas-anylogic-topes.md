# Pruebas de topes de AnyLogic PLE

> **Estado: CERRADAS.** Protocolo y resultados del 25/08/2026, sobre AnyLogic
> 8.9.9 PLE. Las cinco pruebas corrieron y las cinco preguntas quedaron respondidas.
>
> Son tres pruebas descartables, ~30 minutos en total. **Las tres cambian decisiones
> de diseño del modelo**, así que se corren antes de escribir nada y antes de registrar
> las decisiones sobre la unidad de demanda y la biblioteca en `contexto-del-proyecto.md`, sección 7.
>
> Anotar los resultados en la sección 5 de este mismo archivo.

---

## 0. Lo que ya está verificado, y lo que no

**Verificado contra la comparación oficial de ediciones (25/08/2026):**

| Tope | Valor |
|---|---|
| Agentes creados dinámicamente | **50.000** |
| Tiempo de modelado | **5 h**, en todas las bibliotecas **salvo Process Modeling Library** |
| Tipos de agente por modelo | 10 |
| Poblaciones y bloques de flowchart por tipo de agente | 200 |
| OptQuest | 500 iteraciones, 7 parámetros |

**Hallazgo que corrige lo que teníamos anotado:** la licencia **University Researcher tiene los
mismos topes** de 50.000 agentes y 5 h. **No es una salida al problema de escala.** La
memoria del proyecto decía que "levanta los topes"; es falso. Salvedad: `anylogic.help`
devuelve 403 a los fetchers, así que esto viene de dos búsquedas independientes que
coinciden, no de la página leída directamente. **No hace falta resolverlo para avanzar: el diseño no depende de esa licencia.**

**Lo que NO está verificado y estas pruebas resuelven:**

1. Que la exención de PML sea real, y no solo lo que dice la documentación. Todo el
   diseño se apoya en eso: el día de servicio son ~19 h contra un tope de 5.
2. Si el tope de 50.000 cuenta **creaciones** o **entidades vivas**, de lo que depende
   que sirva reciclar una población, y con ella la posibilidad de bajar el tamaño de
   grupo `k` y ganar fidelidad visual.
3. Si la máquina banca 40.000 agentes en tiempo de reloj razonable. El tope de licencia
   no es el único límite: está el de la computadora.

---

## 1. Los tres modelos ya estan generados

**No hay que construir nada en la interfaz.** `src/08_generar_pruebas_anylogic.py`
genera los tres `.alp` en `anylogic/pruebas/`, partiendo de `MM1.alp` del TP 3 (que ya
se sabe que compila y corre) y cambiandole solo los parametros que cada prueba
necesita. Los tres son `Source -> Queue -> Delay -> Sink` de Process Modeling Library.

**Instrucciones de corrida en `anylogic/pruebas/LEEME.md`**, con la tabla de como leer
cada resultado. Resumen:

| Modelo | Pregunta | Como esta armado |
|---|---|---|
| `PruebaA_PML_20h.alp` | ¿PML corre mas de 5 h simuladas? | 720 agentes en 20 h: el tope de agentes no puede contaminar el resultado |
| `PruebaB_Tope50k.alp` | ¿El tope cuenta creaciones o entidades vivas? | ~1 agente vivo, pero el acumulado cruza 50.000 en t=50.000 s |
| `PruebaC_Rendimiento.alp` | ¿Cuanto tarda una corrida realista? | 40.014 agentes en 19 h, ~1.170 vivos a la vez |

**La prueba A es la que sostiene todo lo demas.** Si PML resulta alcanzada por el tope
de 5 h, el dia completo es imposible en PLE y hay que replantear el horizonte, que ya
fue decidido. Las otras dos dejan de importar.

**La prueba B es la que mas puede cambiar el diseño**, porque toca la fidelidad visual:
si el tope cuenta creaciones, reciclar una poblacion permite bajar mucho el tamaño de
grupo `k`, y cuanto mas chico `k`, mas figuras se ven.

---

## 2. Lo que dejo de ser decisivo

El plan original incluia probar si un modelo **sin ninguna biblioteca** queda alcanzado
por el tope de 5 h. **Ya no hace falta**: las tres arquitecturas candidatas (grupos de
pasajeros, pasajeros como cantidades con trenes como agentes, e hibrido por corredor)
se pueden construir **todas dentro de PML**, que es la unica exenta. La pregunta quedo
sin consecuencia practica y se saca del protocolo.

---

## 3. Un hallazgo lateral, para el modelo de verdad

AnyLogic 8.9.9 trae un **API de diseño en Python** en
`anylogic_design_time_api/`, que se conecta por py4j a una instancia abierta y permite
crear **marcacion espacial por codigo**: caminos, nodos, redes, vias de tren, andenes,
escaleras, paredes.

**No sirve para estas pruebas** (no crea bloques de flowchart ni eventos) pero **si
sirve para el modelo**: la marcacion de las 90 estaciones y el agregado de la Linea F
se pueden dibujar desde `grafo_nodos.csv` y `grafo_aristas.csv` en vez de a mano. Va
justo en la direccion que impone el tope de **200 bloques por tipo de agente**, que ya
obliga a que la topologia viva en los datos y no en el dibujo. Y abarata el paso 8, que
era la prueba de diseño que el plan se puso a si mismo.

---

## 4. Antes de empezar

**AnyLogic 8.9.9 PLE esta instalado** en `C:\Program Files\AnyLogic 8.9 Personal
Learning Edition\` (verificado el 25/08/2026).

Si las pruebas se corren en otra maquina, **anotar cual**: la prueba C mide rendimiento
y ese resultado no se traslada entre equipos.

---

## 5. Resultados: corridas del 25/08/2026

**Máquina:** la de trabajo, `C:\Program Files\AnyLogic 8.9 Personal Learning Edition\`.
**Versión:** AnyLogic 8.9.9 Personal Learning Edition.

| Prueba | Contador del `source` | Esperado | Veredicto |
|---|---:|---|---|
| **A** | **734** | ~720 si corre 20 h, ~180 si corta a las 5 h | **PML corre las 20 h.** El tope de 5 h no la alcanza |
| **B** | **50.027** | ~72.000 si cuenta vivas, ~50.000 si cuenta creaciones | **El tope cuenta creaciones**, con un solo agente vivo |
| **C** | **39.773** | ~40.014 | Configuración correcta: contenido del `delay` = **1.137** contra 1.170 previstos |
| **D** | 31, con `poblacion [60000]` viva | - | **Las poblaciones declaradas NO cuentan** contra el tope |
| **E** | 31, con `poblacion [25000]` viva | - | **Entra, y `Replicas10` completó las 10 iteraciones sin OOM** |

### 5.1 A: Process Modeling Library está exenta del tope de 5 h

734 llegadas con media de 100 s son 73.400 s de reloj de modelo: **corrió las 20 horas
completas**. Si el tope de 5 h la hubiera alcanzado, el contador se habría quedado en
~180.

**Consecuencia:** el horizonte de **día completo** que se eligió es viable, y PML queda
confirmada como la base obligada del modelo. El supuesto sobre el que se apoyaba todo
el diseño resultó cierto.

### 5.2 B: El tope de 50.000 cuenta creaciones acumuladas, no entidades vivas

El modelo se detuvo en **50.027 creaciones** teniendo **un solo agente vivo**
(contenido del `delay` = 1). Los dos números están separados por cuatro órdenes de
magnitud, así que no hay interpretación posible: **lo que se cuenta es la creación, no
la coexistencia**.

**Consecuencia:** el presupuesto de agentes de una corrida es un recurso que se gasta y
no se recupera al destruir entidades. Reciclar en vez de crear y destruir **podría** ser
una salida, eso es lo que mide la prueba D.

### 5.3 Hallazgo no buscado: el tope se reinicia entre replicaciones

**El experimento `Replicas10` de la prueba C completó las diez iteraciones**, con
39.773 agentes cada una: **397.730 agentes acumulados**, casi ocho veces el tope, sin
un solo error. Si el presupuesto fuera acumulado por experimento, habría muerto en la
segunda iteración.

Y la prueba B lo confirma por el otro lado: **su `Replicas10` sí falló**, con
`RuntimeException: Error in the model during iteration 2` desde
`ExperimentParamVariation`. Falla porque **una sola corrida suya** quiere crear 72.000.

**Consecuencia, y es la que más alivio trae:** las **diez replicaciones por escenario**
que el TPI se comprometió a correr **no compiten por el mismo presupuesto**. Cada
corrida arranca con sus 50.000. El plan de replicaciones no estaba en riesgo.

> **Matiz operativo que conviene recordar.** Al tocar el tope, la corrida simple
> **degrada con elegancia** (el `source` deja de crear y el modelo sigue hasta el final,
> como se ve en B: `sink` = 50.026 y el reloj llegó a 72.000 s) pero en un experimento
> de variación de parámetros **lanza excepción y aborta**. O sea: un modelo que roza el
> tope puede parecer que anda en corrida simple y romperse recién al replicar. Hay que
> dejar margen, no quedarse al borde.

### 5.4 C: El rendimiento no es un problema

39.773 agentes creados, **1.137 vivos a la vez**, 19 h simuladas. Y la corrida previa
mal configurada, con **~39.768 agentes vivos simultáneamente**, también terminó casi
instantáneamente.

*Falta el cronómetro de la corrida buena, pero el hecho de que `Replicas10` completara
diez iteraciones ya acota el orden de magnitud.*

**Consecuencia:** el límite operativo es la licencia, no la máquina.

---

## 6. D: Las poblaciones declaradas no cuentan, y el límite se mudó de lugar

**El modelo corrió.** Con `poblacion [60000]` instanciada y el flowchart funcionando
(31 llegadas en la hora simulada, contra ~36 esperadas), **sin un solo error de
licencia**. La conclusión es directa: **el tope de 50.000 alcanza solo a los agentes
creados dinámicamente, no a los declarados en la inicialización**.

Eso vuelve viable el **reciclado**: un pool declarado que se redespacha en vez de crear
y destruir no gasta presupuesto de licencia.

### 6.1 Pero apareció un límite nuevo, y es la memoria

El `Replicas10` de la prueba D murió con:

```
Exception: java.lang.OutOfMemoryError thrown from the UncaughtExceptionHandler
in thread "Frame Collector"
```

**No es un error de licencia.** Son 60.000 bloques `Sink` con presentación gráfica, que
no entran en los 2 GB configurados. El límite se mudó de la licencia a la memoria.

### 6.2 Y 60.000 era mucho más de lo necesario

Acá está el punto que cambia el diseño. **Lo que rompe el tope de 50.000 no es la
cantidad de gente simultánea sino el acumulado del día.** Son dos números muy
distintos, y hasta ahora los estábamos tratando como uno solo.

Con el tiempo de viaje medio ponderado por la demanda real (**910 s**, de
`caminos_minimos.csv`) más unos 120 s de espera de andén, la permanencia media en el
sistema es de **1.030 s ≈ 17 minutos**. Por la ley de Little, sobre la hora pico de
72.396 etapas:

| `k` | Llegadas en hora pico | **Vivos a la vez** | Creaciones en el día |
|---:|---:|---:|---:|
| **1** | 72.396 | **20.722** | 740.568 |
| 5 | 14.479 | 4.144 | 148.113 |
| 10 | 7.239 | 2.072 | 74.056 |
| 25 | 2.895 | 828 | 29.622 |

**A k = 1 (un agente, un pasajero) la concurrencia máxima es de 20.722.** Está muy por
debajo de los 50.000. Lo único que impedía k=1 eran las **740.568 creaciones**, y las
poblaciones declaradas no cuentan.

> **Es decir: un pool declarado de unos 25.000 pasajeros, reciclado, permitiría simular
> el día completo con un agente por pasajero.** Que es exactamente la fidelidad que
> pediste. Lo que falta saber es si esos 25.000 entran en memoria.

---

## 7. E: El pool reciclado es viable

**Pasó las dos corridas.** La simple instanció `poblacion [25000]` con el flowchart
funcionando, y el **`Replicas10` completó las diez iteraciones sin `OutOfMemoryError`**,
con `L = 0,109`: exactamente lo que predice su configuración (0,01 llegadas/s por 10 s
de retardo medio). El resultado es consistente, no es casualidad.

Lo que mató a la prueba D no era el diseño sino el dimensionamiento: **60.000 era casi
el triple de lo que el modelo necesita.**

### 7.1 Lo que queda establecido, juntando todo

| Pregunta | Respuesta | De dónde sale |
|---|---|---|
| ¿PML corre el día completo? | **Sí**, 20 h simuladas | A |
| ¿Qué cuenta el tope de 50.000? | **Creaciones dinámicas**, no entidades vivas | B |
| ¿Se reinicia entre replicaciones? | **Sí**, cada corrida tiene su presupuesto | C, `Replicas10` |
| ¿Aguanta la máquina ~40.000 agentes? | **Sí**, y termina casi al instante | C |
| ¿Cuentan las poblaciones declaradas? | **No** | D |
| ¿Entra un pool de 25.000 en memoria? | **Sí**, incluso con 10 replicaciones | E |

**Conclusión de diseño: se puede simular el día completo con un agente por pasajero**,
mediante un **pool declarado de ~25.000 pasajeros que se recicla**. La concurrencia
máxima medida por la ley de Little es de **20.722** a k=1, y el pool no gasta
presupuesto de licencia porque no es creación dinámica.

### 7.2 Dos salvedades honestas

**1. Los 25.000 de la prueba estaban quietos.** Son bloques `Sink` instanciados que no
hacen nada. Los pasajeros reales van a tener estado, atributos, ruta y van a moverse por
bloques, así que **el costo por agente va a ser mayor**. Lo que E demuestra es que el
costo de *instanciación* no es problema; no que el costo de *actividad* tampoco lo sea.

Pero eso ya está acotado por la prueba C: **39.773 agentes con 1.137 activos a la vez
terminaron casi al instante**, y la corrida fallida previa tuvo **~39.768 vivos
simultáneos** sin despeinarse. Entre las dos, la concurrencia de ~20.000 activos queda
razonablemente cubierta.

**2. Falta confirmar que inyectar desde el pool no cuenta como creación.** El patrón es
`Enter` para meter un agente que ya existe al flowchart y `Exit` para devolverlo al
pool, en lugar de `Source`/`Sink`. La prueba B contó creaciones **de `Source`**; `Enter`
no crea, toma un agente existente. **Es lo más probable, pero no está verificado**, y se
va a ver de inmediato al construir el modelo real: si contara, el contador se dispara en
la primera corrida.

---

## 8. Qué queda decidido

- **Arquitectura**: PML, día completo, pool declarado de pasajeros con `Enter`/`Exit`.
- **`k` es un parámetro**, y el objetivo es **k = 1**: un agente, un pasajero.
- **Plan B, ya verificado**: si el modelo real resulta más pesado de lo previsto,
  k = 25 con `Source`/`Sink` funciona sin reciclado, 29.622 creaciones contra un tope
  de 50.000.
- **La fidelidad visual de detalle** sigue yendo al submodelo peatonal de Constitución
  en hora pico (9.951 ingresos, 1 persona = 1 persona), que entra holgado en ambos topes.

**Estas pruebas están cerradas.** Los modelos de `anylogic/pruebas/` quedan como
respaldo reproducible de cada afirmación; el generador es
`src/08_generar_pruebas_anylogic.py`.
