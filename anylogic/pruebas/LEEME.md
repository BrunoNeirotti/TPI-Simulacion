# Modelos de prueba de los topes de PLE

Cinco modelos descartables que usamos para medir los límites de AnyLogic Personal
Learning Edition antes de empezar el modelo de verdad. Corrieron el 25/08/2026 y las
conclusiones están cerradas.

**Los resultados y el razonamiento completo están en
`docs/pruebas-anylogic-topes.md`.** Este archivo solo dice qué prueba cada modelo, por
si hay que rehacerlos o adaptarlos.

Los genera `src/08_generar_pruebas_anylogic.py` a partir de `MM1.alp` del TP 3, que ya
sabíamos que compilaba. Lo único que cambia en cada uno son los parámetros de `source`,
`queue` y `delay`, el tiempo final y el modo de ejecución. Todos son
`Source -> Queue -> Delay -> Sink` de Process Modeling Library; D y E agregan además una
población declarada sin conectar.

| Modelo | Qué prueba | Contador esperado |
|---|---|---|
| `PruebaA_PML_20h.alp` | Si PML corre más de 5 h simuladas | ~720 si corre las 20 h, ~180 si se corta |
| `PruebaB_Tope50k.alp` | Si el tope de 50.000 cuenta creaciones o entidades vivas | ~50.000 si cuenta creaciones, ~72.000 si cuenta vivas |
| `PruebaC_Rendimiento.alp` | Cuánto tarda una corrida realista | ~40.014 con unos 1.170 vivos a la vez |
| `PruebaD_PoblacionDeclarada.alp` | Si una población declarada consume el tope | Corre con `poblacion [60000]` viva |
| `PruebaE_PoolRealista.alp` | Si un pool de 25.000 entra en memoria | Corre, y `Replicas10` completa las 10 iteraciones |

## Cómo correrlos

Se abren y se corren, no hay que construir nada.

Que terminen al instante y no se vea nada moverse es lo esperado: corren en virtual
time, o sea a máxima velocidad y sin animación, así que simulan 19 o 20 horas en menos
de un segundo. Todo se lee cuando dice `Finished`.

El número que importa es el **contador que aparece debajo del bloque `source`**. Como la
tasa de llegada es constante y conocida, ese contador funciona de reloj: si el modelo se
cortó antes de tiempo, por el tope de 5 h o por el de 50.000 agentes, el número lo
delata. Los otros dos útiles son el contenido del `delay`, arriba del bloque, que dice
cuántos agentes hay vivos a la vez, y el del `sink`, que dice cuántos completaron.

Una cosa a tener en cuenta: AnyLogic no recarga un archivo que cambió en disco mientras
estaba abierto. Hay que cerrar el proyecto en el panel *Projects* (botón derecho,
*Close*) y abrirlo de nuevo, o se ve la versión vieja.
