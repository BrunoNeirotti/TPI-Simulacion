# Diseño del modelo base (paso 7)

Documento de trabajo, iniciado el 21/09/2026. La especificación
(`docs/especificacion-modelo.md`) dice **qué** se modela: entidades, recursos, procesos,
eventos. Este documento dice **cómo** se implementa en AnyLogic 8.9.9 PLE, dentro de los
topes medidos en `docs/pruebas-anylogic-topes.md`.

Las cuatro decisiones de modelado de la sección 6 (6.1 a 6.4) se tomaron con el grupo
el 21/09/2026 y están registradas en `decisiones.md` como D12 a D15. Se conservan las
opciones descartadas para que se vea contra qué se eligió.

---

## 1. Restricciones que condicionan todo

| Restricción | Consecuencia de diseño |
|---|---|
| 5 h de tiempo simulado, salvo Process Modeling Library (PML) | Toda la lógica que avanza el reloj tiene que vivir en bloques PML. **Falta verificar** si un `Event` o un diagrama de estados sueltos hacen perder la exención (ver 7.1) |
| 200 bloques de flowchart por tipo de agente | Un solo flowchart genérico por tipo de agente. La topología se lee de los CSV, no se dibuja |
| 10 tipos de agente por modelo | Alcanza: `Main`, `Pasajero`, `Formacion`, y a lo sumo dos o tres auxiliares |
| 50.000 creaciones dinámicas por corrida | Pasajeros y formaciones salen de poblaciones declaradas y se reciclan con `Enter`/`Exit`. Nunca `Source` |
| Concurrencia máxima de 27.796 pasajeros vivos (simulador de referencia; la estimación estática era 20.722) | Población declarada de **32.000** pasajeros (la prueba D instanció 60.000) |

## 2. Tipos de agente

| Tipo | Cantidad | Qué guarda |
|---|---|---|
| `Main` | 1 | Las tablas leídas de los CSV, los andenes, los generadores, los contadores de indicadores |
| `Pasajero` | Población de 32.000, reciclada | Origen, destino, hora de generación, la ruta como lista de tramos por línea (subir en X, bajar en Y), el índice de la etapa actual, marcas de tiempo |
| `Formacion` | Población declarada por línea (flota), reciclada | Línea, sentido, capacidad, ocupación, la lista de pasajeros a bordo, la posición en la línea |

Los **andenes** no son agentes: son objetos Java livianos dentro de `Main` (uno por nodo
y sentido), cada uno con su cola de pasajeros esperando. Así no consumen tipos de agente
ni bloques.

## 3. Flowchart del pasajero (genérico, ~6 bloques)

```
Enter ──► Wait "enAnden" ──► Wait "aBordo" ──► SelectOutput ¿llegó? ──sí──► Exit
              ▲                                      │ no (transbordo)
              └────────── Delay "caminata" ◄─────────┘
```

- **Enter**: `Main` toma un pasajero libre de la población, le carga origen, destino y
  ruta, y lo inyecta.
- **Wait `enAnden`**: el pasajero queda ahí sin avanzar el reloj por su cuenta. Al
  entrar se anota en la cola del andén que le corresponde (nodo de ascenso y sentido).
  Sale solo cuando una formación lo libera con `free(pasajero)`.
- **Wait `aBordo`**: ídem; la formación lo libera al llegar al nodo donde tiene que
  bajar.
- **Delay `caminata`**: el transbordo, con el tiempo del GTFS (`t_s` de la arista de
  tipo transbordo). Después vuelve a `enAnden` para la línea siguiente.
- **Exit**: registra el tiempo total y devuelve el agente a la población libre.

El pasajero **no hace nada activo**: toda la dinámica de subir y bajar la dispara la
formación. Eso es lo que permite que un flowchart de seis bloques sirva para los 90
nodos.

## 4. Flowchart de la formación (genérico, ~6 bloques)

```
Enter ──► Delay "detencion" ──► SelectOutput ¿cabecera final? ──sí──► Exit
              ▲                        │ no
              └──── Delay "tramo" ◄────┘
```

- **Enter**: el despachador de la línea toma una formación libre y la inyecta en la
  cabecera. **En la apertura** (5:30) inyecta además las formaciones de
  `apertura_formaciones.csv` en su estación de arranque (D16): entran al flowchart en
  `detencion` con el índice de tramo de esa estación, y a partir de ahí recorren igual
  que cualquier otra.
- **Delay `detencion`**, en cada estación:
  1. al entrar, libera de `aBordo` a los pasajeros que bajan ahí;
  2. sube pasajeros de la cola del andén, en orden de llegada, hasta llenar la
     capacidad; los que no entran se quedan en la cola;
  3. la duración es la detención (ver 6.2).
- **Delay `tramo`**: `t_s` del tramo, leído de `grafo_aristas.csv` por línea, sentido y
  orden.
- **Exit** en la cabecera opuesta: la formación vuelve a la población libre (ver 6.3).

## 5. Generación de la demanda

- Un generador por complejo de origen, no por par: 78 procesos de llegada en lugar de
  ~5.800. La tasa de cada complejo en cada bloque de 15 min es
  `viajes de la hora × share del bloque / 900 s` (de `demanda_modelo_od_hora.csv` y
  `demanda_modelo_intrahorario.csv`).
- Llegadas de **Poisson no homogéneo**: tiempo entre llegadas exponencial con la tasa del
  bloque vigente. Es lo que la especificación declara (sección 13).
- El destino se sortea con la distribución de destinos de ese complejo en esa hora, y la
  ruta se lee de `caminos_minimos.csv`.
- **Cómo se implementa sin perder la exención de PML**: ver 7.1.

## 6. Decisiones de modelado

### 6.1 Pasajero que no entra en la formación: **espera la próxima** (D12)

La especificación (sección 15) dejó una regla escrita pero sin confirmar.

| Opción | Consecuencia |
|---|---|
| **a. Espera la próxima de la misma línea y sentido** (la de la especificación) | Simple, no requiere datos que no hay. Si la red se satura, las colas crecen, y eso es justamente lo que se quiere medir |
| b. Tras N intentos fallidos, recalcula la ruta | Más realista, pero N no tiene fuente y obliga a tener rutas alternativas cargadas |
| c. Tras N intentos, abandona el sistema | Esconde la saturación: el pasajero que se va no suma espera |

**Decidido: a.** No agrega parámetros sin fuente y deja visible la saturación.

### 6.2 Detención en estación: **fija primero, endógena después** (D13)

La especificación dice "endógena, con piso de 24 s", pero no da la fórmula. Hace falta
un coeficiente de segundos por pasajero que **no tiene fuente propia**.

| Opción | Consecuencia |
|---|---|
| a. Fija: 24 s (líneas actuales), 30 s (Línea F) | Dato oficial, cero supuestos nuevos. No capta que en hora pico la estación cargada demora más |
| **b. `max(piso, a + b × (suben + bajan) / puertas)`** con `b` de bibliografía | Capta el efecto de la carga sobre la detención, que es parte de lo que la Línea F alivia. Suma un supuesto declarado y va al análisis de sensibilidad |
| c. Empezar con a y pasar a b en el paso de calibración | Permite verificar el modelo sin ruido antes de agregar el mecanismo |

**Decidido: c.** Primero se verifica que el modelo reproduce lo básico con la
detención fija y después se agrega el término endógeno, con el coeficiente como supuesto
declarado.

### 6.3 Circulación de las formaciones: **despachos independientes** (D14)

| Opción | Consecuencia |
|---|---|
| **a. Despachos independientes por cabecera, sin tope de flota**. Cada formación sale, recorre, y en la cabecera opuesta vuelve a la población libre | Lo que dice la especificación. Los intervalos salen de la distribución medida y ya reflejan la flota real. Simple |
| b. Circulación cerrada: la formación que llega a una cabecera es la próxima que sale en sentido contrario, tras un tiempo de vuelta | Respeta la flota (25 formaciones en la Línea F). Obliga a modelar el tiempo de vuelta en cabecera, que no está medido, y acopla los dos sentidos |

**Decidido: a.** Para la Línea F se verifica aparte que la flota de 25 formaciones
sostiene el intervalo del escenario, y se declara en vez de modelarlo.

> **Verificado el 21/09/2026** (`reports/12_ajuste_intervalos.md`, sección 5). La vuelta
> en cabecera se midió en las líneas actuales: mediana en pico de 72 s (C) a 430 s (B).
> Con 18 min de viaje por sentido, 25 formaciones sostienen como mínimo **92 s** con una
> vuelta como la de la C, 95 s como la de la H y 100 s como la de la A. **Los 90 s exigen
> una vuelta de 45 s o menos**, que ninguna línea actual logra en mediana. No reabre D7
> (90 s es el valor de diseño oficial), pero hay que declararlo al informar ese
> extremo.

### 6.4 Adelantamiento: **separación mínima por tramo** (D15)

Con despachos aleatorios y detenciones variables, una formación podría alcanzar y pasar a
la que va adelante, lo que en una vía única es físicamente imposible.

| Opción | Consecuencia |
|---|---|
| **a. Separación mínima por tramo**: una formación no entra a un tramo hasta que la anterior lo dejó. Se implementa con un `ResourcePool` o un `Hold` por tramo | Físicamente correcto y produce el apelotonamiento real de hora pico. Suma un bloque al flowchart |
| b. No controlarlo | Con detención fija (6.2 a) casi no ocurre, porque todas las formaciones tardan lo mismo en cada tramo. Con detención endógena sí |

**Decidido: a.** Entra junto con la detención endógena (paso 5 del orden de
construcción); mientras la detención sea fija se cuenta cuántas veces ocurriría y se
verifica que es cero.

### 6.5 Intervalos de despacho de las líneas actuales: **hecho** (paso 12, D16 a D18)

Resuelto el 21/09/2026 en `src/12_ajuste_intervalos.py` (`reports/12_ajuste_intervalos.md`).
Lo que entra a AnyLogic:

- **`intervalos_empiricos.csv`**: distribución empírica por línea, cabecera y hora (D17),
  como tabla de 501 cuantiles por celda. Se muestrea por transformada inversa:
  ```java
  double u = uniform();                      // 0..1
  int i = (int) Math.floor(u * 500);         // tramo de la tabla
  double f = u * 500 - i;
  double intervalo = q[i] + f * (q[i + 1] - q[i]);
  ```
  con `q` el arreglo de 501 cuantiles de la celda (línea, cabecera, hora vigente).
- **`cabeceras_despacho.csv`**: qué cabecera es A y cuál D, y en qué `direction_id` del
  grafo circula cada una. **No suponer que A es la cabecera 1**: en la E es al revés.
- **`apertura_formaciones.csv`**: desde qué estación arranca cada formación a las 5:30
  (D16).

Excluidos de los intervalos: la apertura, los viajes de recorrido parcial y los cortes de
servicio (D18). El período es todo 2025 y depende de D4 (`FILTRO_FECHAS` en el script).

### 6.6 Capacidad por formación

Coches medidos (A 5, B 6, C 5, D 6, E 5, H 6) × 179 pasajeros por coche (supuesto de la
especificación, sección 15). Sin cambios.

## 7. Riesgos a despejar antes de construir

### 7.1 Qué conserva la exención de las 5 h

La prueba A usó un modelo 100 % PML (`Source → Queue → Delay → Sink`). El modelo real
necesita al menos un temporizador para generar pasajeros y despachar formaciones sin
`Source`. Hay dos formas:

- con un `Event` (o evento dinámico) de `Main` que llame a `enter.take(...)`;
- con un agente "reloj" que da vueltas en un `Delay` PML y, al salir, inyecta.

La segunda es PML pura y seguro conserva la exención, pero es un truco. **Prueba F**,
de diez minutos: el modelo de la prueba A, sin `Source`, con un `Event` cíclico que
inyecta por `Enter` desde una población, corriendo 20 h. Si pasa, se usa `Event`; si
corta a las 5 h, se usa el agente reloj. Sirve además para confirmar lo que la prueba E
dejó pendiente: que `Enter` desde una población no cuenta como creación.

### 7.2 Costo de los pasajeros activos: **medido** con el simulador de referencia

La prueba C tuvo 1.137 activos a la vez. El simulador de referencia
(`anylogic/biblioteca/referencia/`, 21/09/2026), que corre esta misma lógica en Java
plano, midió **hasta 27.796 pasajeros vivos a la vez**, más que los 20.722 de la
asignación estática, porque suma las esperas en andén. Por eso el pool pasa a 32.000. En
Java plano un día completo tarda alrededor de 1 s; en AnyLogic será más lento, y se mide
en el primer prototipo.

## 8. Orden de construcción propuesto

1. **Prueba F** (7.1).
2. **Una línea sola** (la C, que es la del corredor): formaciones con detención fija,
   pasajeros con origen y destino sobre la C, sin transbordos. Se verifica conservación
   (ingresados = arribados + a bordo + en andén) y que la ocupación en hora pico tenga
   el orden de magnitud del perfil de SBASE.
3. **Las seis líneas con transbordos**, con la demanda completa.
4. **Intervalos empíricos y apertura** (6.5) reemplazando los intervalos fijos. Los
   insumos ya están generados.
5. **Detención endógena y control de adelantamiento** (6.2, 6.4).
6. **Indicadores y experimento de diez replicaciones.**
7. D4 y calibración del corredor.

Los pasos 2 y 3 se arman en la interfaz de AnyLogic con guía paso a paso; la carga de
los CSV y el código Java de los bloques (liberar, subir, bajar) se escriben aparte y se
pegan.
