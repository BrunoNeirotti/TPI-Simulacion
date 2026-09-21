# Especificación del modelo

TPI de Simulación, UTN FRRo. Entrega "Evaluación de control de avance del TPI — Etapa
1/2" (Classroom, Juan Ignacio Torres, vence 27/09/2026). Documento de trabajo: la
versión final va como `EspecificacionModelo_GRUPO_XX.pdf`.

La pregunta que este documento tiene que poder contestar, en los términos de la
consigna, es: **¿la especificación está suficientemente desarrollada, o todavía falta
definir algún componente del sistema?** Cada sección cita de dónde sale el dato para
que se pueda verificar contra `CLAUDE.md`, `decisiones.md` y `docs/guia-del-modelo.md`,
que son la fuente de verdad.

---

## 1. Sistema seleccionado

La red de Subte de la Ciudad Autónoma de Buenos Aires: seis líneas en operación (A, B,
C, D, E, H), 90 estaciones (por línea; 78 complejos si se agrupan las estaciones
físicamente unidas por transbordo), operada por SBASE. Se modelan dos escenarios sobre
el mismo sistema:

- **Escenario base**: la red actual, sus seis líneas.
- **Escenario futuro**: la red actual más la **Línea F**, un corredor nuevo de 12
  estaciones y 9,8 km entre Barracas y Palermo, hoy en licitación
  (proceso 10241-0094-LPU25), con inicio de servicio proyectado para 2031.

## 2. Descripción del problema

La red es fuertemente radial: la mayoría de los viajes entre el sur y el norte de la
ciudad se resuelven transbordando en el macrocentro, lo que concentra la carga en
tramos y estaciones de combinación mientras otros sectores circulan holgados. La Línea
F se proyectó como corredor transversal para aliviar esa concentración, en particular
sobre la Línea C: el 70 % de los viajes que incluyen una etapa en la C combinan con el
ferrocarril Roca, que la Línea F también vincula.

El problema es que **no existe, en ninguna fuente pública ni en el expediente oficial
del proyecto, una evaluación del efecto de la Línea F sobre el conjunto de la red**. El
Estudio de Impacto Ambiental dimensiona la línea nueva y publica su perfil de demanda
propio, pero no compara el funcionamiento de la red con y sin el proyecto, no publica
una matriz origen-destino de la red completa, y no dice qué frecuencia de servicio haría
falta para lograr el alivio que se anuncia. El TPI construye esa evaluación: un modelo
de simulación de eventos discretos de la red actual, calibrado con datos públicos, al
que se le agrega la Línea F para medir la diferencia.

## 3. Límites del sistema

**Dentro del sistema:**

- Las seis líneas actuales, sus 90 nodos (par línea-estación) y sus 194 aristas (166
  tramos, 28 transbordos), con calibración a dos velocidades (ver D3 abajo).
- En el escenario futuro, la Línea F completa (traza única, sin habilitación
  parcial — ver `decisiones.md`, "Escenario futuro").
- La demanda de pasajeros que entra al sistema por cualquier estación, su elección de
  ruta, su espera en andén, su viaje a bordo, sus transbordos y su salida por la
  estación de destino.
- El despacho de formaciones desde cada cabecera y su circulación por la línea.

**Fuera del sistema:**

- El Premetro (declarado fuera de alcance desde la propuesta).
- Los ferrocarriles Roca y San Martín y el transporte de superficie: son fuente de
  parte de la demanda de transferencia en los nodos de combinación (p. ej.
  Constitución), pero su operación no se simula. Entran como generador exógeno de
  pasajeros, no como subsistema modelado.
- La obra civil y las etapas constructivas de la Línea F: el modelo simula la
  operación de la línea terminada, no la construcción.
- Los accesos peatonales fuera de la red (calles, veredas): la caminata que se modela
  es solo la interna a cada complejo de estación (transbordo).

**Profundidad diferenciada (D3, decidida el 16/09/2026):** el corredor de la Línea F y
las líneas con las que combina (A, C, D, H) se calibran y validan a fondo; el resto de
la red (B, E, y los tramos de A/C/D/H sin combinación con la F) se representa con
verificación agregada (totales, reparto por línea) pero sin el mismo nivel de ajuste
tramo a tramo. Ver `decisiones.md`, sección "D3".

**Horizonte temporal:** un día hábil típico completo, servicio de punta a punta
(~19 horas), excluyendo sábados, domingos, feriados y los días atípicos identificados
en el pipeline (25 días hábiles con anomalías, el 10/04/2025 de paro general, marzo de
2025 sin datos de despachos).

## 4. Entidades

| Entidad | Qué es | Atributos principales |
|---|---|---|
| **Pasajero** | La entidad dinámica principal. Un agente = un pasajero (D10) | Complejo de origen, complejo de destino, hora de generación, ruta asignada (secuencia de nodos, de `caminos_minimos.csv`), línea(s) de ascenso y descenso, estado actual |
| **Formación** | Tren que circula por una línea, despachado desde una cabecera | Línea, sentido, cantidad de coches, capacidad total, hora de despacho, posición en la red |

Los **nodos** (estación-línea) y **complejos** (estación física) no son entidades que
fluyen por el sistema, sino la topología fija sobre la que se mueven las entidades. Ver
sección 12.

## 5. Recursos

| Recurso | Qué limita | Capacidad |
|---|---|---|
| **Capacidad de coche de una formación** | Cuántos pasajeros aborda una formación en un tramo | Coches por formación (medido, por línea) × capacidad por coche (supuesto, ver sección 15) |
| **Andén** | Espacio donde se acumulan los pasajeros que esperan o transbordan | Sin tope físico modelado por ahora; se mide la ocupación para reportar aglomeración, no se restringe el ingreso |

El pasajero **seiza** la capacidad de una formación al abordar en un tramo y la
**libera** al bajar (sea por transbordo o por llegar a destino). Si la formación llega
llena, el pasajero no aborda y queda en el andén para el próximo evento de llegada de
formación en esa línea y sentido (ver sección 15, supuesto de comportamiento).

## 6. Procesos

**Proceso del pasajero:**

1. Generación en un complejo, según la tasa de la hora y el reparto intrahorario
   (`demanda_modelo_od_hora.csv` + `demanda_modelo_intrahorario.csv`).
2. Asignación de ruta: se lee de `caminos_minimos.csv`, precalculada fuera del modelo
   (Dijkstra con penalización de transbordo, ya resuelto en el pipeline). No hay
   asignación dinámica dentro de la simulación.
3. Acceso al andén de ascenso (tiempo cero dentro del complejo de origen).
4. Espera en andén hasta la llegada de una formación de la línea/sentido que
   corresponde.
5. Intento de embarque: si hay capacidad disponible, aborda; si no, permanece en
   andén esperando la próxima formación.
6. Viaje a bordo: recorre uno o más tramos con el tiempo de cada uno (`t_s` +
   detención endógena).
7. En cada nodo de la ruta: decide si baja (transbordo o destino) o continúa a bordo,
   según la ruta ya asignada.
8. Si transborda: caminata interna al complejo (tiempo del `min_transfer_time` del
   GTFS como piso) y vuelve al paso 4 para la línea siguiente.
9. Si llega a destino: sale del sistema.

**Proceso de la formación:**

1. Despacho desde una cabecera, con intervalo tomado de la distribución empírica
   medida por línea, cabecera y hora (líneas actuales, D17) o de la variable de
   escenario de intervalo entre trenes (Línea F, D7). En la apertura del servicio
   (5:30) las formaciones arrancan desde las estaciones intermedias donde lo hacen
   en la operación real, medidas en el dataset de despachos (D16).
2. Recorrido tramo a tramo: tiempo de viaje + detención en cada estación intermedia
   (mínimo de diseño 24 s para las líneas actuales, 30 s para la Línea F, endógeno
   según ascensos/descensos).
3. En cada estación: descenso de los pasajeros que bajan ahí, ascenso de los que
   esperan en andén hasta llenar la capacidad disponible.
4. Llegada a la cabecera opuesta: la formación se recicla al pool (arquitectura de
   pool declarado y reciclado, D11) y queda disponible para un nuevo despacho.

## 7. Colas

| Cola | Dónde | Disciplina |
|---|---|---|
| Pasajeros esperando abordar | En cada andén, por complejo, línea y sentido | FIFO dentro de cada llegada de formación; se agregan los que no lograron subir en la formación anterior |
| Pasajeros en transbordo | Caminando dentro de un complejo, entre el andén de descenso y el de ascenso de la línea siguiente | No es cola de espera por recurso, es un retardo de tiempo fijo (piso del GTFS) |

No hay cola de formaciones: se despachan según la distribución de intervalos, no
esperan un recurso compartido para salir de cabecera.

## 8. Variables

**Variables de estado** (cambian durante la corrida, se leen para calcular
indicadores):

- Cantidad de pasajeros esperando en cada andén (por complejo, línea, sentido).
- Ocupación de cada formación en circulación.
- Cantidad de formaciones circulando por línea en un instante dado.
- Contador acumulado de pasajeros que no lograron abordar en el primer intento.

**Variables de decisión / de escenario** (se fijan antes de cada corrida y se recorren
en el análisis de sensibilidad, ver sección 4.3 de `guia-del-modelo.md`):

- Intervalo entre trenes de la Línea F, entre 90 y 189 s (D7).
- Detención de la Línea F, con piso de 30 s.
- Criterio de reparto de demanda fuera de las horas pico (perfil por par, perfil de
  red, o perfil por complejo de origen).

## 9. Parámetros

Se listan en detalle en `docs/guia-del-modelo.md`, sección 4. Resumen por categoría:

- **Fijos** (dato medido o de diseño oficial): topología (90 nodos, 166 tramos, 28
  transbordos), tiempo y distancia de cada tramo (GTFS), demanda por par y hora
  (SBASE + paso 5), ruta de cada par, intervalos de despacho de las líneas actuales,
  coches por formación, y los parámetros oficiales de la Línea F (distancias,
  capacidad de 1.075 pas./formación, velocidades 90/70/45 km/h, aceleración 1 m/s²,
  frenado 1,1 m/s², flota de 25 formaciones).
- **Calibrado**: penalización por transbordo, 120 s (D9).
- **Variable de escenario**: ver sección 8.
- **Supuesto**: capacidad por coche de las líneas actuales, comportamiento del
  pasajero que no aborda (sección 15).

## 10. Eventos

| Evento | Dispara |
|---|---|
| Generación de un pasajero | Entra a la cola del andén de su complejo de origen |
| Llegada de una formación a una estación | Descenso de pasajeros, luego ascenso hasta capacidad |
| Partida de una formación de una estación | Fin de la detención, la formación pasa al siguiente tramo |
| Pasajero completa un transbordo | Se reincorpora a la cola de andén de la línea siguiente |
| Pasajero llega a destino | Sale del sistema, se registra el tiempo total de viaje |
| Formación llega a cabecera | Se recicla al pool (Enter/Exit), disponible para nuevo despacho |
| Cambio de franja horaria | Cambia la tasa de generación de pasajeros (perfil intrahorario) |
| Fin del período de calentamiento | Empiezan a contar los indicadores de la corrida |
| Fin de la corrida (día completo) | Se cierra la réplica; conservación de entidades: ingresados = arribados + a bordo + en andén al corte |

## 11. Estados

**Estado del pasajero** (máquina de estados simple): generado → esperando en andén →
a bordo → (transbordando → esperando en andén → a bordo)\* → arribado.

**Estado de la formación**: en cabecera (esperando despacho) → en tránsito (entre
estaciones) → detenida (en estación) → en cabecera opuesta (reciclada).

**Estado del sistema** en un instante dado: el vector completo de pasajeros esperando
por andén, pasajeros a bordo por formación y formaciones en circulación por línea. Es
lo que el motor de eventos discretos actualiza en cada evento.

## 12. Relaciones entre componentes

- La topología es un **grafo dirigido**: nodos = par línea-estación (90), aristas =
  tramo (166) o transbordo (28). Alberti y Pasco obligan a que sea dirigido: se sirven
  en un solo sentido cada una.
- Los 90 nodos se agrupan en **78 complejos** (componentes conexas del grafo de
  transbordos): un complejo es donde el pasajero entra y sale del sistema; el nodo es
  por donde circula el tren. `demanda_modelo_od_hora.csv` y `caminos_minimos.csv` usan
  complejos; `grafo_nodos.csv` y `grafo_aristas.csv` usan nodos.
- El pasajero **usa** la capacidad de la formación mientras está a bordo de un tramo
  (relación de recurso compartido).
- El andén **conecta** la demanda que llega caminando (generación o transbordo) con
  las formaciones que llegan circulando.
- El transbordo **conecta** dos líneas dentro de un mismo complejo; caminar dentro del
  complejo de origen o destino no cuenta como transbordo (vale cero).
- En el escenario futuro, la Línea F se **agrega** como nodos y aristas nuevos,
  conectados a la red existente en las estaciones de combinación (seis declaradas por
  el EsIA, dos adicionales solo en el mapa oficial). Se recalcula `caminos_minimos`
  con el mismo procedimiento: la redistribución de pasajeros es resultado del cambio
  de topología, no un supuesto impuesto línea por línea. El reparto que resulte se
  contrasta después contra las matrices origen-destino de SBASE 2019 en los nodos de
  combinación (ver sección 15 y `decisiones.md`), nunca al revés.

## 13. Datos de entrada

Los cinco archivos que el pipeline de datos deja listos (ver README y
`docs/guia-del-modelo.md`, sección 2), todos en `data/processed/`:

| Archivo | Qué aporta al modelo |
|---|---|
| `grafo_nodos.csv` | Los 90 nodos con sus atributos |
| `grafo_aristas.csv` | Los 194 tramos/transbordos con tiempos y distancias |
| `caminos_minimos.csv` | La ruta de cada uno de los 6.006 pares ordenados |
| `demanda_modelo_od_hora.csv` | 827.289 viajes/día, 71.686 celdas de (par, hora) |
| `demanda_modelo_intrahorario.csv` | Reparto de cada hora en bloques de 15 min |

A eso se suman, para el modelo en AnyLogic:

- **Distribuciones de intervalos de despacho** (paso 12): sobre 319.792 intervalos
  medidos entre julio y diciembre de 2025 (D4) se hizo el procedimiento de la materia (histogramas, máxima verosimilitud
  de cinco familias y bondad de ajuste). La lognormal gana en la mayoría de las
  celdas, pero la Línea H es bimodal y ninguna familia teórica la reproduce, así que
  el modelo usa la **distribución empírica** en todas (D17). Se excluyen los cortes
  de servicio sin causa registrada (D18).
- **Distribución de llegada de pasajeros**, derivada de la tasa horaria e intrahoraria
  (no homogénea).
- **Parámetros de la Línea F**, tomados directamente del expediente oficial (sección 9
  de este documento).

## 14. Indicadores de desempeño

| Indicador | ¿Tiene contraparte observable? |
|---|---|
| Ocupación a bordo por tramo | Sí, contra `sbase_perfil_carga.csv` (dos horas pico, 2024, con ajuste declarado por SBASE) |
| Reparto de ascensos por línea en combinaciones | Sí, parcial, contra molinetes y `linea_etapa` |
| Tasa de transbordo | Sí, contra el observado (1,371 mañana, 1,426 tarde) |
| Concentración horaria | Sí, 9,9 % medido sobre molinetes |
| Tiempo de viaje puerta a puerta | Es salida directa del modelo; se compara entre escenarios, no hay observado de referencia |
| Tiempo de espera en andén | Salida del modelo, sin observado de referencia |
| Aglomeración de andén | No, ninguna fuente la registra |
| Pasajeros que no logran abordar | No, depende del supuesto de comportamiento |
| Detención real (líneas actuales) | No, solo hay piso de diseño (24 s) |

Todos se reportan **comparados entre escenarios** (red actual vs. red con Línea F, y
por variante de intervalo entre trenes de la Línea F dentro de D7), con un mínimo de diez
replicaciones por escenario, descartando el período de calentamiento e informando
intervalos de confianza.

## 15. Supuestos

- **Capacidad por coche de las líneas actuales**: no hay dato oficial; se toma de
  referencia la capacidad por coche de la Línea F (1.075 pasajeros / 6 coches ≈ 179
  por coche), aclarando que para las líneas de 5 coches es una extrapolación.
- **Detención de las líneas actuales**: endógena (según ascensos y descensos), con
  piso de 24 s de diseño del GTFS. El modelo se verifica primero con la detención
  fija en ese piso, y el término por pasajero se agrega en la calibración, con su
  coeficiente como supuesto declarado (D13). No hay fuente pública para validar el valor
  resultante.
- **Comportamiento del pasajero que no aborda**: espera la próxima formación de la
  misma línea y sentido en el mismo andén; no cambia de ruta ni abandona el sistema.
  Es una regla declarada, no medida, confirmada por el grupo el 21/09/2026 (D12).
- **Caminata de transbordo**: se usa el `min_transfer_time` del GTFS como piso; no es
  una caminata cronometrada.
- **Sentido 1 de la Línea E** (D6): en el GTFS publicado, sus distancias son copia de
  las del sentido 0 y sus tiempos no se corresponden con ellas. Se toman los tiempos
  del sentido 0, que es lo que hacen las otras cinco líneas del mismo archivo. Afecta
  al 1,0 % de los caminos.
- **Etapas marcadas como incompletas** (D1, 4,1 %): se conservan. Solo entran en la
  forma de la curva horaria fuera de las horas pico, no en el nivel de la demanda;
  medido, excluirlas cambia de hora el 1,33 % de los viajes del día.
- **Asignación de ruta todo-o-nada** (D9): cada par origen-destino manda todo su
  flujo por un único camino precalculado; no se reparte entre alternativas cercanas
  en tiempo (hay 50 pares, el 0,8 %, con una alternativa a menos de 60 s).
- **Demanda del modelo** (D2): SBASE (matriz diaria + horas pico 8 y 17, medida) como
  base, con el resto del día desagregado según el perfil del dataset de viajes y
  etapas del paso 5 (supuesto propio, sujeto a análisis de sensibilidad).
- **Penalización de transbordo fija en 120 s** (D9): el dato no identifica el
  parámetro por encima de 30 s; 120 s se sostiene por argumento físico (mitad del
  intervalo medido, 95–157 s).
- **Profundidad de calibración diferenciada** (D3): corredor Línea F + A/C/D/H a
  fondo, B y E con verificación agregada.
- **Intervalo entre trenes de la Línea F como variable de escenario, no como dato fijo** (D7): la
  fuente oficial dice explícitamente que el plan de servicio no existe.
- **Demanda futura de la Línea F**: no hay medición posible; la nota técnica *Análisis
  de Demanda Línea F* (SBASE, 2019) —obtenida en fuente primaria por la solicitud
  N° 00934682/26, no solo citada por el EsIA— se usa **solo como contraste, nunca
  como insumo del modelo** (decidido el 16/09/2026, ver `decisiones.md`), con tres
  salvedades: implica una concentración horaria (~25 % de la demanda diaria en la
  hora pico) que la red actual no exhibe (9,9 %); su cuadro de intervalos de entrada
  para las líneas actuales es un supuesto de mejora de frecuencia de 2019 que no se
  concretó (los despachos medidos de 2025 son más espaciados en las seis líneas); y
  su trazado tiene **13 estaciones con terminal sur en California**, no las 12
  vigentes con terminal en Brandsen, así que la correspondencia estación por estación
  con el diseño actual debe verificarse por geometría antes de comparar, no darse por
  sentada.

## 16. Preguntas de simulación

1. ¿Qué tan bien reproduce el modelo, en el escenario base, la ocupación a bordo por
   tramo y el reparto de ascensos por línea que mide SBASE en hora pico? (Verificación
   del modelo antes de comparar escenarios.)
2. ¿Cómo cambian la ocupación de coche, la aglomeración de andén, el tiempo de viaje y
   la tasa de transbordo al incorporar la Línea F con su traza completa, frente al
   escenario base?
3. Dentro del rango de intervalo entre trenes 90–189 s (D7), ¿qué frecuencia de la Línea F es
   necesaria para lograr un alivio medible en la Línea C y en el corredor de
   combinación, y a partir de qué punto los indicadores dejan de mejorar de forma
   apreciable?
4. ¿Cómo se redistribuye la demanda entre las seis líneas existentes y la Línea F
   (cambios en el reparto por línea, en la tasa de transbordo y en los tiempos de
   viaje agregados de la red)?
5. ¿Qué tan sensibles son los indicadores centrales a los supuestos propios del
   trabajo: la desagregación temporal fuera de las horas pico (D2), el coeficiente de
   detención por pasajero (D13), y la regla de comportamiento del pasajero que no
   aborda?

## 17. Diagrama conceptual final

Generado con la skill `archify` (workflow de dos carriles). Fuente de la
especificación y artefacto entregado:

- Especificación: [`docs/figuras/diagrama-conceptual-modelo.workflow.json`](figuras/diagrama-conceptual-modelo.workflow.json)
  (schema v2 de `archify`). Editable y regenerable con
  `archify deliver workflow diagrama-conceptual-modelo.workflow.json diagrama-conceptual-modelo.html --quality standard`
  si hace falta ajustar el diagrama.
- Artefacto final: [`docs/figuras/diagrama-conceptual-modelo.html`](figuras/diagrama-conceptual-modelo.html),
  HTML autocontenido, explorable (zoom, pan, cambio de tema claro/oscuro, foco por
  camino) y con botón de exportación a PNG/SVG/WebM para incrustar en el PDF final.
  Pasó verificación de composición (9/9 checks, 0 errores) y evidencia de navegador
  real en 1440×900, 1600×1000, 1920×1080 y 2048×1320, en ambos temas.

Muestra, en dos carriles paralelos sincronizados por el recurso compartido
("capacidad de coche"):

- **Flujo del pasajero**: generación → ruta asignada → espera en andén (cola) →
  intento de abordaje (con lazo de vuelta si no hay lugar) → a bordo → sale del
  sistema (con lazo de vuelta a la espera en andén si transborda).
- **Flujo de la formación**: despacho → llega a estación → suben y bajan pasajeros →
  cabecera opuesta → se recicla en el pool (lazo de vuelta al despacho, arquitectura
  Enter/Exit).
- Una nota visual sobre el despacho de la Línea F marcando el intervalo entre trenes
  como variable de escenario (90–189 s), y cuatro tarjetas al pie con el detalle de cada paso y la
  aclaración de que el mismo proceso corre en los dos escenarios (base y con
  Línea F).

Para el PDF final: abrir el HTML, exportar a PNG o SVG con el botón "Export" de la
esquina superior derecha, y embeberlo como figura de esta sección.

---

## Elementos que la consigna dice que podrían no ser aplicables

Todos los ítems del checklist tienen contenido en este TPI: es un sistema de colas con
recursos limitados (capacidad de coche) y una topología no trivial (red, no una sola
línea), así que entidades, recursos, colas y relaciones entre componentes están todos
presentes y no hay ninguno para declarar "no aplicable".
