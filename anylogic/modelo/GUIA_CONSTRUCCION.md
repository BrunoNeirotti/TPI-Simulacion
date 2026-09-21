# Guía de construcción del modelo base (paso 7)

Iniciada el 21/09/2026. Implementa `docs/diseno-modelo-base.md` con la biblioteca
`anylogic/biblioteca/subte.jar`, que ya carga y verifica todos los insumos (ver
`anylogic/biblioteca/LEEME.md`). Lo que se arma en la interfaz de AnyLogic es poco: dos
tipos de agente, dos flowcharts de unos seis bloques y tres eventos dinámicos. El código
de cada bloque está acá, listo para pegar.

> **Depende de la prueba F** (`anylogic/pruebas/PruebaF_guia.md`). Esta guía usa
> **eventos dinámicos** para generar pasajeros y despachar formaciones. Si la variante
> F2 corta a las 5 h, los eventos se reemplazan por un agente reloj con un `Delay`; el
> resto de la guía no cambia.

Los nombres de elementos de AnyLogic (`Enter`, `Wait`, *Dynamic Event*, etc.) van como
aparecen en la interfaz, en inglés.

---

## 0. Qué se construye primero

El orden de `docs/diseno-modelo-base.md`, sección 8. Esta guía cubre los pasos 2 y 3:

- **Paso 2, solo la Línea C.** Con el parámetro `soloLinea = "C"` se despachan solo las
  dos cabeceras de la C y se generan solo los viajes cuya ruta es una única etapa en la
  C. Se esperan **57.134 viajes por día** (6.090 a las 8 h, 5.591 a las 17 h).
- **Paso 3, toda la red.** Es el mismo modelo con `soloLinea = ""`. No hay que cambiar
  nada más: la topología, las rutas y los transbordos vienen de los CSV.

Los intervalos empíricos y la apertura (paso 4 del orden) **ya vienen incluidos**:
están en la biblioteca.

---

## 1. Modelo nuevo y biblioteca

1. `File → New → Model`. Nombre `RedSubte`, carpeta **`anylogic/modelo/`** del
   repositorio. *Model time units*: **seconds**.
2. Agregar la biblioteca: clic en el modelo en el panel *Projects* → en sus propiedades,
   sección **Dependencies** → *Jar files and class folders* → **Add** →
   `anylogic/biblioteca/subte.jar`. (Si AnyLogic ofrece copiarlo dentro del modelo,
   elegir que **no**: así, al recompilar la biblioteca, el modelo toma la versión nueva.)
3. Los CSV se leen de `data/processed/` del repositorio, con ruta relativa a la
   carpeta del modelo: `../../data/processed`. No hay que copiarlos.

---

## 2. Tipos de agente

### `Pasajero`

*New → Agent type*, nombre `Pasajero`, sin animación (se crea como población en el paso
3). En sus propiedades, **Advanced Java → Imports section**:

```java
import subte.*;
```

y en **Additional class code**:

```java
Ruta ruta;               // camino precalculado (caminos_minimos.csv)
int etapa;               // indice de la etapa en curso
boolean transbordando;   // true si al bajar le queda otra etapa
double tIngreso;         // s desde medianoche
double tLlegoAnden;      // cuando empezo a esperar en el anden actual
double tEspera;          // espera acumulada en andenes

void iniciar(Ruta r, double t) {
    ruta = r;
    etapa = 0;
    transbordando = false;
    tIngreso = t;
    tLlegoAnden = t;
    tEspera = 0;
}

Ruta.Etapa etapaActual() {
    return ruta.etapas[etapa];
}
```

### `Formacion`

*New → Agent type*, nombre `Formacion`. **Imports section**: `import subte.*;`.
**Additional class code**:

```java
Recorrido recorrido;
int indice;              // estacion donde esta (0 = cabecera)
boolean recienSale;      // primera parada: no hay detencion
Carga<Pasajero> carga;

void iniciar(Recorrido r, int desde, int capacidad) {
    recorrido = r;
    indice = desde;
    recienSale = true;
    carga = new Carga<Pasajero>(r.largo(), capacidad);
}
```

---

## 3. `Main`: datos, poblaciones y colecciones

**Imports section** de `Main`: `import subte.*;` y `import java.util.*;`.

**Additional class code** de `Main`:

```java
Datos datos;
Map<String, Anden<Pasajero>> andenes;
Random rng;

// contadores de verificacion
long ingresados, arribados, descartados;
double sumaTiempoViaje, sumaEspera;

Anden<Pasajero> andenDe(Pasajero p) {
    return andenes.get(Datos.claveAnden(p.etapaActual()));
}

Anden<Pasajero> andenDe(Formacion f) {
    return andenes.get(Datos.claveAnden(f.recorrido, f.indice));
}

boolean correEnEstaCorrida(Ruta r) {
    if (soloLinea.isEmpty()) return true;
    return r.etapas.length == 1 && r.etapas[0].recorrido.linea.equals(soloLinea);
}
```

Elementos a agregar en `Main` (paleta *Agent*):

| Elemento | Nombre | Configuración |
|---|---|---|
| Parameter | `soloLinea` | Tipo `String`, valor `"C"` (paso 2) o `""` (paso 3) |
| Parameter | `carpetaDatos` | Tipo `String`, valor `"../../data/processed"` |
| Population | `pasajeros` | Tipo `Pasajero`, **cantidad inicial 32000** |
| Population | `formaciones` | Tipo `Formacion`, **cantidad inicial 150** |
| Collection | `pasajerosLibres` | `LinkedList` de `Pasajero` |
| Collection | `formacionesLibres` | `LinkedList` de `Formacion` |

**32.000 pasajeros, no 25.000.** El simulador de referencia midió una concurrencia máxima
de 26.499 a 27.240 pasajeros vivos a la vez (`reports/13_verificacion_referencia.md`): con
las esperas en andén es más que los 20.722 de la asignación estática con que se había
fijado el pool (D10). La prueba D ya instanció 60.000 sin problemas.
150 formaciones alcanza con holgura: el simulador de referencia llega a 83 a la vez.

**On startup** de `Main`:

```java
rng = getDefaultRandomNumberGenerator();
datos = Datos.leer(carpetaDatos);
andenes = datos.crearAndenes();
for (Pasajero p : pasajeros) pasajerosLibres.add(p);
for (Formacion f : formaciones) formacionesLibres.add(f);

// demanda: un solo proceso de llegadas para toda la red
double t0 = datos.demanda.proximaLlegadaRed(time(), rng);
if (t0 < Demanda.FIN_S) create_LlegadaPasajero(t0 - time());

// apertura (D16): cada formacion arranca en su estacion a las 5:30
for (Oferta.Arranque a : datos.oferta.arranques()) {
    if (soloLinea.isEmpty() || a.cabecera.linea.equals(soloLinea)) {
        create_Arranque(a.hora - time(), a);
    }
}
traceln("Datos leidos: " + datos.rutas.size() + " rutas, "
        + Math.round(datos.demanda.viajesDelDia()) + " viajes/dia");
```

---

## 4. Eventos dinámicos

Paleta *Agent → Dynamic Event*, los tres en `Main`.

### `LlegadaPasajero` (sin argumentos)

```java
String o = datos.demanda.sortearOrigen(time(), rng);
String d = datos.demanda.sortearDestino(o, (int) (time() / 3600), rng);
Ruta r = datos.ruta(o, d);
if (correEnEstaCorrida(r)) {
    Pasajero p = pasajerosLibres.poll();
    if (p == null) error("Se agoto el pool de pasajeros a las " + time());
    p.iniciar(r, time());
    ingresados++;
    enterPasajero.take(p);
} else {
    descartados++;
}
double prox = datos.demanda.proximaLlegadaRed(time(), rng);
if (prox < Demanda.FIN_S) create_LlegadaPasajero(prox - time());
```

### `Arranque`, argumento `a` de tipo `Oferta.Arranque`

```java
lanzarFormacion(a.cabecera, a.indice);
// la que arranca en la cabecera abre la secuencia de despachos regulares
if (a.indice == 0) {
    double s = datos.oferta.proximaSalida(a.cabecera, time(), rng);
    if (s < Double.POSITIVE_INFINITY) create_Despacho(s - time(), a.cabecera);
}
```

### `Despacho`, argumento `c` de tipo `Oferta.Cabecera`

```java
lanzarFormacion(c, 0);
double s = datos.oferta.proximaSalida(c, time(), rng);
if (s < Double.POSITIVE_INFINITY) create_Despacho(s - time(), c);
```

Y en el **Additional class code** de `Main`, la función que usan los dos:

```java
void lanzarFormacion(Oferta.Cabecera c, int desde) {
    Formacion f = formacionesLibres.poll();
    if (f == null) error("Se agoto el pool de formaciones a las " + time());
    f.iniciar(c.recorrido, desde, Datos.capacidad(c.linea));
    enterFormacion.take(f);
}
```

---

## 5. Flowchart del pasajero

En `Main`, paleta *Process Modeling Library*. En **todos** los bloques, *Agent type*:
`Pasajero`.

```
enterPasajero ─► enAnden ─► aBordo ─► llego ─(true)─► salePasajero
                    ▲                   │ (false)
                    └──── caminata ◄────┘
```

| Bloque | Tipo | Configuración |
|---|---|---|
| `enterPasajero` | `Enter` | — |
| `enAnden` | `Wait` | *Capacity*: **maximum capacity** tildado. *On enter*: ver abajo |
| `aBordo` | `Wait` | *Capacity*: **maximum capacity** tildado |
| `llego` | `SelectOutput` | *Select true output*: **If condition is true**. *Condition*: `!agent.transbordando` |
| `caminata` | `Delay` | *Delay time*: `agent.etapaActual().caminataPrevia` segundos. *Capacity*: **maximum capacity** tildado |
| `salePasajero` | `Exit` | *On enter*: ver abajo |

`enAnden`, **On enter**:

```java
agent.tLlegoAnden = time();
andenDe(agent).llega(agent);
```

`salePasajero`, **On enter**:

```java
arribados++;
sumaTiempoViaje += time() - agent.tIngreso;
sumaEspera += agent.tEspera;
pasajerosLibres.add(agent);
```

El pasajero no hace nada por su cuenta: la formación lo saca de `enAnden` al subir y de
`aBordo` al bajar (sección 6). Por eso nunca se llama `free` desde el flowchart del
pasajero.

---

## 6. Flowchart de la formación

En `Main`. En todos los bloques, *Agent type*: `Formacion`.

```
enterFormacion ─► detencion ─► final ─(true)─► saleFormacion
                     ▲            │ (false)
                     └── tramo ◄──┘
```

| Bloque | Tipo | Configuración |
|---|---|---|
| `enterFormacion` | `Enter` | — |
| `detencion` | `Delay` | *Delay time*: ver abajo. *Capacity*: **maximum capacity**. *On enter* y *On exit*: ver abajo |
| `final` | `SelectOutput` | *Condition*: `agent.indice == agent.recorrido.largo() - 1` |
| `tramo` | `Delay` | *Delay time*: `agent.recorrido.tramo[agent.indice]` segundos. *Capacity*: **maximum capacity**. *On exit*: `agent.indice++;` |
| `saleFormacion` | `Exit` | *On enter*: ver abajo |

`detencion`, **Delay time** (D13: fija; no hay detención en la primera parada ni en la
última):

```java
(agent.recienSale || agent.indice == agent.recorrido.largo() - 1) ? 0 : agent.recorrido.detencion
```

`detencion`, **On enter**: bajan los que llegaron a su estación.

```java
for (Pasajero p : agent.carga.bajar(agent.indice)) {
    p.transbordando = p.etapa < p.ruta.etapas.length - 1;
    if (p.transbordando) p.etapa++;
    aBordo.free(p);
}
```

`detencion`, **On exit**: suben los que esperan, al partir (así suben también los que
llegaron al andén durante la detención). Los que no entran siguen esperando (D12).

```java
agent.recienSale = false;
if (agent.indice < agent.recorrido.largo() - 1) {
    for (Pasajero p : andenDe(agent).subir(agent.carga.lugares())) {
        agent.carga.subir(p, p.etapaActual().baja);
        p.tEspera += time() - p.tLlegoAnden;
        enAnden.free(p);
    }
}
```

`saleFormacion`, **On enter**:

```java
if (agent.carga.aBordo() != 0) error("Formacion llega a la cabecera con pasajeros");
formacionesLibres.add(agent);
```

**El orden importa**: el pasajero que baja pasa por `llego`; si transborda, camina y
entra a `enAnden` de la línea siguiente. Si la etapa siguiente sale del mismo nodo en
sentido contrario (las 142 rutas con cambio de sentido, ver sección 8), la caminata vale
0 s y el pasajero espera en el andén opuesto.

---

## 7. Experimento

En el experimento `Simulation`:

- *Model time → Start time*: **18000** (5:00). *Stop time*: **86400** (24:00). Así
  `time()` son segundos desde medianoche, que es lo que usa la biblioteca.
- *Randomness*: **Fixed seed**, para que las corridas de verificación se puedan repetir.
- *Execution mode*: **virtual time**.

**On destroy** de `Main` (control de conservación):

```java
long enSistema = enAnden.size() + aBordo.size() + caminata.size();
traceln("Ingresados " + ingresados + ", arribados " + arribados
        + ", en el sistema " + enSistema + ", descartados " + descartados);
traceln("Conservacion: " + (ingresados == arribados + enSistema ? "OK" : "FALLA"));
if (arribados > 0) {
    traceln("Tiempo medio de viaje " + Math.round(sumaTiempoViaje / arribados)
            + " s, espera media " + Math.round(sumaEspera / arribados) + " s");
}
```

---

## 8. Qué verificar en el paso 2 (solo la C)

Los valores esperados salen del **simulador de referencia**, que corre esta misma lógica
en Java plano con la misma biblioteca (`anylogic/biblioteca/referencia/`,
`reports/13_verificacion_referencia.md`). AnyLogic tiene que dar lo mismo dentro del
error de muestreo: eso es la verificación cruzada.

| Control | Qué se espera |
|---|---|
| Arranca y lee los datos | La consola muestra `6006 rutas, 827289 viajes/dia` |
| Viajes generados | `ingresados` cerca de **57.134** (en 10 réplicas de referencia: 56.645 a 57.611) |
| Conservación | `OK` |
| No se agotan los pools | Sin error de pool |
| Espera media | **110 a 119 s** (referencia) |
| Tiempo de viaje medio | **619 a 629 s** (referencia) |

Después, en el paso 3, sin cambiar nada más que `soloLinea = ""`:

| Control | Qué se espera |
|---|---|
| Viajes generados | `ingresados` cerca de **827.289**, `descartados` 0 |
| Conservación | `OK` |
| Pasajeros vivos a la vez | Máximo de **26.500 a 27.300** (el pool es de 32.000) |
| Formaciones a la vez | Máximo de **80 a 83** |
| Tiempo de viaje medio | **1.110,0 ± 0,9 s** (referencia, 10 réplicas) |
| Espera media por viaje | **187,9 ± 1,0 s** |
| Ascensos por viaje | **1,443** en el día; 1,419 en la hora pico mañana |
| Carga por tramo contra SBASE | Hora pico mañana: correlación 0,993, error ponderado 7,6 %; tarde: 0,985 y 8,3 % |

Las cifras completas están en `reports/13_verificacion_referencia.md`.

**Sobre las 142 rutas con cambio de sentido** (6.398 viajes por día, el 0,8 %): el
camino mínimo del paso 6 llega a Alberti y sale de Pasco (servidas en un solo sentido)
siguiendo de largo hasta Congreso o Plaza Miserere y volviendo. El grafo no distingue
sentido en los nodos, así que esa vuelta no pagó ningún costo en la elección de ruta. El
modelo la simula como dos etapas con espera en el nodo de la vuelta, y la vuelta cuenta
como un ascenso más. Decidido el 21/09/2026 (D19, ver `decisiones.md`): medido, si la
vuelta pagara costo de transbordo solo 4 pares cambiarían de camino.

---

## 9. Lo que viene después

- Paso 5 del orden: detención endógena y separación mínima por tramo (D13, D15).
- Indicadores (ocupación por tramo, espera, aglomeración de andén) y el experimento de
  diez replicaciones.
- Paso 8: la Línea F entra como un recorrido más en los CSV; la biblioteca no cambia.
