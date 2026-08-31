# Pruebas de topes: cómo correrlas

> **Las cinco corrieron el 25/08/2026 y están CERRADAS.** Resultados y razonamiento
> completo en `docs/pruebas-anylogic-topes.md`. Este archivo queda como referencia de
> cómo está armada cada una, por si hay que rehacerlas o adaptarlas.

Cinco modelos generados por `src/08_generar_pruebas_anylogic.py`. **No hay que
construir nada**: se abren y se corren.

Salieron de `MM1.alp` del TP 3, que ya se sabe que compila y corre. Lo único que
cambia en cada uno son los parámetros de `source`, `queue` y `delay`, el tiempo final
y el modo de ejecución. Todos son `Source → Queue → Delay → Sink` de Process Modeling
Library; D y E agregan además una población declarada sin conectar.

---

## Dos cosas antes de correr

**Que termine al instante y no se vea nada moverse es lo esperado.** Todos corren
en **virtual time**, o sea a máxima velocidad y sin animación: el modelo simula 19 o
20 horas en menos de un segundo de reloj. No hay nada que mirar mientras corre; todo
se lee **cuando dice `Finished`**.

**AnyLogic no recarga un archivo que cambió en disco mientras estaba abierto.** Cerrá
el proyecto en el panel *Projects* (botón derecho → *Close*) y abrilo de nuevo. Si
abrís sin cerrar, ves la versión vieja.

---

## Cómo se lee el resultado: el contador del `source`

No hace falta ver el reloj del modelo. **El contador que aparece debajo del bloque
`source` es el reloj**, porque la tasa de llegada es constante y conocida.

Si el modelo se corta antes de tiempo (por el tope de 5 h o por el de 50.000
agentes), ese número lo delata. Cada prueba de abajo trae el valor que debería dar si
todo está bien y el que daría si se topeó.

Los otros contadores útiles: el de **contenido del `delay`** (arriba del bloque) dice
cuántos agentes hay vivos a la vez, y el del **`sink`** cuántos completaron.

---

## A: `PruebaA_PML_20h.alp`

**Pregunta.** ¿Process Modeling Library corre más de 5 h de tiempo simulado?

**Cómo está armada.** Una llegada cada ~100 s en promedio, durante **72.000 s = 20 h**.
Son unos **720 agentes** en toda la corrida: lejísimos del tope de 50.000, para que el
tope de agentes no pueda contaminar el resultado. Lo único que se mide es el reloj.

**Qué mirar: el contador del `source`.**

| Si da | Significa |
|---:|---|
| **~720** | Corrió las 20 h. **PML está exenta del tope de 5 h**, como dice la documentación y como asume todo el diseño. |
| **~180** | Se cortó a las 5 h. La documentación está mal y **el día completo es imposible en PLE**: hay que replantear el horizonte. |

> Es la prueba que **sostiene todo lo demás**. Si salía mal, ninguna otra importaba.

**Resultado: 734.** PML corrió las 20 h. El tope de 5 h no la alcanza.

---

## B: `PruebaB_Tope50k.alp`

**Pregunta.** El tope de 50.000, ¿cuenta **creaciones acumuladas** o **entidades vivas
a la vez**?

**Cómo está armada.** Una llegada por segundo, con un retardo de media 1 s y capacidad
infinita: en todo momento hay **~1 agente vivo**, pero el **acumulado** llega a 72.000
si nada lo frena. Los dos números están separados por cuatro órdenes de magnitud, así
que el resultado no admite interpretación.

**Qué mirar: el contador del `source`.**

| Si da | Significa |
|---:|---|
| **~50.000** | Cuenta **creaciones**. Con un solo agente vivo el modelo igual se cortó, así que **reciclar una población** en lugar de crear y destruir es una salida real: el tamaño de grupo `k` puede bajar mucho. |
| **~72.000** | Cuenta **entidades vivas**. Reciclar no cambia nada y `k` queda gobernado por la tabla de escala: k=25 son 32.711 agentes por corrida. |

**Anotá también el texto exacto** de cualquier mensaje que aparezca, en la consola o
en ventana. Sirve para saber si el modelo se frena del todo o solo deja de crear.

**Resultado: 50.027, con un solo agente vivo.** El tope cuenta **creaciones**.

> Y su `Replicas10` falló con `RuntimeException ... during iteration 2`, mientras que el
> de la prueba C completó diez iteraciones de 39.773 agentes (397.730 acumulados). De
> ahí sale el hallazgo lateral más útil: **el presupuesto de 50.000 se reinicia en cada
> replicación**. Ojo con el matiz: al tocar el tope, la corrida simple **degrada con
> elegancia** y parece andar, pero el experimento de replicaciones **aborta**.

### B.2: confirmación por otro camino, seis clics

**Ya la respondió la prueba D**, pero con bloques de biblioteca y no con un tipo de
agente propio. Si alguna vez hace falta confirmarlo con el caso exacto:

1. Nuevo modelo.
2. Crear un tipo de agente `Pasajero` (*Agent type*, con población).
3. Población inicial **60.000** (por encima del tope) y **ningún `Source`**.
4. Correr, aunque no haga nada.

Si arranca, las poblaciones iniciales no cuentan y el reciclado queda confirmado por
dos caminos independientes.

---

## C: `PruebaC_Rendimiento.alp`

**Pregunta.** ¿Cuánto tarda en tiempo de reloj una corrida realista?

**Cómo está armada.** Calibrada contra la escala real del TPI: **40.014 agentes** en
**68.400 s = 19 h**, con retardo `triangular(600, 1800, 3600)` de media 2.000 s, lo
que deja **~1.170 agentes vivos a la vez**, el orden de los grupos simultáneos con
k=25 en hora pico. Memoria en 2.048 MB.

**Qué medir.** Cronometrá desde que arranca hasta que dice `Finished`. Anotá el pico de
memoria (el Administrador de tareas alcanza) y el **contenido del `delay`**, que
debería rondar los 1.170.

**Cómo leerlo.** El TPI se comprometió a diez replicaciones por escenario, con dos
escenarios más el barrido de sensibilidad: del orden de **60 corridas**.

| Si tarda | Significa |
|---|---|
| menos de ~30 s | Cómodo. `k` puede incluso bajar. |
| ~30 s a 2 min | Trabajable. 60 corridas son de 30 min a 2 h. |
| más de ~2 min | Hay que subir `k` o recortar el horizonte. El límite deja de ser la licencia y pasa a ser la máquina. |

**Anotá en qué máquina lo corriste.** Esta medición no se traslada entre equipos.

**Resultado: 39.773 creados, 1.137 vivos a la vez** contra 1.170 previstos, y terminó
casi al instante. El límite operativo es la licencia, no la máquina.

---

## D: `PruebaD_PoblacionDeclarada.alp`

**Pregunta.** ¿Una población **declarada** en la inicialización cuenta contra el tope de
50.000, o solo cuentan las creaciones dinámicas?

**Cómo está armada.** 60.000 bloques `Sink` replicados y sin conectar, por encima del
tope, más el flowchart de siempre con llegadas ralas. Una hora simulada: el reloj no
interesa.

**Resultado: no cuentan.** El modelo corrió con `poblacion [60000]` instanciada y el
flowchart normal, sin error de licencia.

**Pero apareció otro límite.** Su `Replicas10` murió con
`OutOfMemoryError ... in thread "Frame Collector"`. **Es memoria, no licencia**: 60.000
bloques con presentación no entran en 2 GB. Y 60.000 era casi el triple de lo necesario,
de ahí la prueba E.

---

## E: `PruebaE_PoolRealista.alp`

**Pregunta.** ¿Entra en memoria el pool que el modelo **realmente** necesita?

**Cómo está armada.** Igual que D pero con **25.000** en lugar de 60.000, y 4 GB. Ese
número sale de la ley de Little sobre la demanda real: con una permanencia media de
1.030 s y una hora pico de 72.396 etapas, la **concurrencia máxima a k=1 es de 20.722
pasajeros vivos a la vez**. El acumulado del día es 740.568, pero eso no es lo que hay
que sostener a la vez.

**Resultado: entra.** La corrida simple instanció `poblacion [25000]` sin problema, y el
**`Replicas10` completó las diez iteraciones sin `OutOfMemoryError`**, con `L = 0,109`,
que es exactamente lo que predice su configuración.

> **Es un resultado conservador.** Un bloque `Sink` arrastra puertos, estadísticas y
> presentación: pesa **más** que un agente `Pasajero` mínimo. Si entran 25.000 `Sink`,
> un pasajero liviano entra con holgura.
>
> **Salvedad:** esos 25.000 estaban quietos. Lo que la prueba demuestra es que el costo
> de *instanciación* no es problema, no que el de *actividad* tampoco. Eso lo acota la
> prueba C por el otro lado.

---

## Historial de defectos, para no repetirlos

**1. Referencias de conector rotas al renombrar el paquete** *(corregido)*. Los
`<Connector>` no referencian los bloques por `Id` sino por la terna
`(PackageName, ClassName, ItemName)`, y ese `PackageName` es el paquete Java del
modelo. Renombrar `JavaPackageName` sin propagar el cambio dejaba las referencias
colgadas: AnyLogic devolvía `null` y fallaba con
`NullPointerException: Cannot invoke "OMEmbeddedObject.isReplicatedFlag()"`. El
síntoma visible era **los cuatro bloques sueltos, sin flechas**. El generador ahora
valida la integridad referencial de los conectores antes de escribir.

**2. El `delay` heredaba capacidad 1** *(corregido)*. En MM1 el `delay` es el
**servidor único** de un M/M/1, así que su capacidad es 1. Heredado sin tocar, la cola
absorbía todo y solo un agente estaba en servicio. Se vio en la primera corrida de C:
`queue` con **39.768** acumulados y `sink` con **38**. Eso arruinaba la prueba B, que
necesita ~1 agente vivo para separar "creaciones" de "vivas". Las tres pruebas ahora
ponen el `delay` en capacidad infinita, para que se comporte como retardo puro.

> **Dato preliminar que dejó esa corrida fallida, y que igual sirve:** con **39.807
> agentes creados y ~39.768 vivos a la vez**, 19 h simuladas, la corrida terminó
> **casi instantáneamente** y llegó a `Finished`. No es la configuración buscada
> (estaban parados en una cola, no en un retardo con temporizador propio) pero muestra
> que **40.000 agentes vivos no son un problema de memoria ni de tiempo**. La prueba C
> bien configurada va a cargar más el planificador de eventos; el número que vale es
> el de la corrida nueva.

---

## Lo que estas pruebas NO responden

**Si inyectar un agente con `Enter` cuenta como creación dinámica.** La prueba B contó
creaciones **de `Source`**; `Enter` no crea, toma un agente que ya existe en el pool. Es
lo más probable, pero no está verificado. **Se ve de inmediato al construir el modelo
real**: si contara, el contador se dispara en la primera corrida.

**Si un modelo sin ninguna biblioteca queda alcanzado por el tope de 5 h.** Estaba en el
plan original y **dejó de ser decisivo**: la arquitectura elegida vive dentro de PML, que
es la única exenta. La pregunta quedó sin consecuencia práctica.
