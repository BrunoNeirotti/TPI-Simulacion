# Impacto de la Línea F sobre la red de Subte de Buenos Aires

**Evaluación mediante simulación del impacto de la Línea F sobre la operación de la red de
Subte de la Ciudad de Buenos Aires.** Trabajo Práctico Integrador de Simulación, Universidad
Tecnológica Nacional, Facultad Regional Rosario.

Grupo 3: Bruno Neirotti, Alexis Galasco, Tomás Salami, Giani Mesapelle y Francisco Lovatti.

La Línea F, hoy en licitación, tiene un objetivo oficial: descongestionar la Línea C. Este
trabajo mide si lo cumple. Se construyó en AnyLogic un modelo de toda la red de Subte que sigue
a cada pasajero y a cada tren durante un día hábil completo, alimentado con datos oficiales, y
se le agregó la Línea F con la traza y los parámetros de su proyecto.

**Resultado.** La Línea F cumple su objetivo: el tramo más cargado de la Línea C baja un 54 %,
a menos de la mitad, con cualquier frecuencia de la nueva línea. Para la red en conjunto la
mejora es moderada: el viaje medio baja unos 45 s (un 4 %), porque cuatro de cada cinco viajes
no cambian de ruta. La Línea F va con sus trenes a poco más de la mitad de su capacidad, y su
estación Constitución mueve a los pasajeros de las dos horas pico en menos de tres minutos.
Cada cifra lleva su intervalo de confianza del 95 % en el informe.

---

## Qué hay

| Parte | Dónde |
|---|---|
| Informe final | [`informe/informe-final.pdf`](informe/informe-final.pdf) (y su fuente LaTeX) |
| Modelos de AnyLogic | [`anylogic/`](anylogic/) |
| Resultados de las corridas | [`resultados-corridas.xlsx`](resultados-corridas.xlsx) |
| Datos oficiales de SBASE y propuesta del trabajo | [`fuentes/`](fuentes/) |

```
informe/                  Informe final (PDF), su fuente LaTeX y las figuras
resultados-corridas.xlsx  Todas las réplicas, con las medias e intervalos calculados con fórmulas
anylogic/
  RedSubte_mapa/          Modelo de la red con el mapa animado
    datos/                Las tablas que lee el modelo (red, rutas, demanda, trenes)
  RedSubte_red/           El mismo modelo sin mapa, para correr experimentos más rápido
  ConstitucionF_3D/       Submodelo peatonal de la estación Constitución de la Línea F, en 3D
  simulador-control/      Programa Java independiente que verifica el modelo de la red
fuentes/
  sbase/                  Matriz de viajes, carga por tramo y estudio de demanda de la Línea F
                          entregados por SBASE por pedido de acceso a la información
  propuesta.pdf           Propuesta del trabajo
```

---

## Cómo ver los modelos

Hace falta **AnyLogic 8.9 Personal Learning Edition** (gratuita). Se abre el `.alp`, se elige el
experimento y se corre con el botón de ejecutar; no hay que instalar nada más.

| Modelo | Qué se ve |
|---|---|
| `anylogic/RedSubte_mapa/RedSubte.alp` | El mapa de la red con los trenes en movimiento, su ocupación y los pasajeros esperando en cada estación. Los tramos se colorean por línea, por la carga de los últimos 15 minutos o por la diferencia con la red sin la Línea F. Al hacer clic en una estación se abre una ficha por andén. |
| `anylogic/RedSubte_red/RedSubte.alp` | El mismo modelo sin mapa, que carga más rápido. Lee los datos de la carpeta de `RedSubte_mapa`, así que las dos carpetas tienen que quedar juntas. |
| `anylogic/ConstitucionF_3D/ConstitucionF_3D.alp` | La estación Constitución de la Línea F en la hora pico de la mañana, en 3D: andén, entrepiso, vestíbulo, escaleras y trenes, con cámaras y botones para ocultar cada nivel. |

**El escenario** lo elige el parámetro `escenario` del agente `Main`: `0` es la red actual y `1` a
`5`, la red con la Línea F con un tren cada 90, 100, 120, 150 o 189 s. El escenario principal es
el `2`, un tren cada 100 s, y es el que abre `RedSubte_mapa`.

**Los experimentos** de los dos modelos de la red son:

- `Simulation`: un día, de 5 a 24 h, con la animación.
- `Replicas100`: cien días del escenario elegido; la consola muestra una línea por réplica y la
  ventana, los histogramas del viaje, la espera y los transbordos.
- `VariacionEscenario`: la red actual y las cinco frecuencias de la Línea F, diez días cada una.

---

## De dónde salen los datos

Todo el modelo se apoya en datos oficiales: los ingresos por molinete, los trenes despachados y
los horarios en formato GTFS de Buenos Aires Data; la encuesta de viajes y etapas del área
metropolitana; la matriz de viajes entre estaciones y la carga por tramo que entregó SBASE por
pedido de acceso a la información (en `fuentes/sbase/`); y el estudio de impacto ambiental, el
pliego de licitación y los planos de la Línea F. El informe cita cada fuente y explica cómo se
prepararon los datos.
