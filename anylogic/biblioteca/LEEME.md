# Biblioteca `subte`

Iniciada el 21/09/2026. La lógica del modelo que no depende de AnyLogic, en Java 17
plano: lee los insumos de `data/processed/`, arma rutas, demanda y oferta, y ofrece los
contenedores del andén y de la formación. AnyLogic la usa como dependencia
(`subte.jar`); cómo se conecta está en `anylogic/modelo/GUIA_CONSTRUCCION.md`.

**Por qué está afuera de AnyLogic.** Se puede compilar y probar contra los datos reales
sin abrir la interfaz, y el modelo queda con muy poco código propio: dos flowcharts de
seis bloques y tres eventos. Con el tope de 200 bloques por tipo de agente, la
topología no puede vivir en el dibujo (D11); vive acá.

## Clases

| Clase | Qué hace | Lee |
|---|---|---|
| `Red` | Nodos, un `Recorrido` por línea y sentido, tiempos de transbordo | `grafo_nodos.csv`, `grafo_aristas.csv` |
| `Recorrido` | Secuencia de nodos y tiempo de cada tramo; detención por parada (24 s, D13) | — |
| `Ruta` | El camino de cada par de complejos partido en etapas a bordo, con la caminata previa a cada una | `caminos_minimos.csv` |
| `Demanda` | Llegadas de Poisson no homogéneo (tasa constante por bloque de 15 min), sorteo de origen y de destino | `demanda_modelo_od_hora.csv`, `demanda_modelo_intrahorario.csv` |
| `Oferta` | Cabeceras (qué lado es cada una), apertura (D16), intervalos empíricos por transformada inversa (D17) | `cabeceras_despacho.csv`, `apertura_formaciones.csv`, `intervalos_empiricos.csv` |
| `Anden<T>` | Cola en orden de llegada; sube hasta llenar y el resto sigue esperando (D12) | — |
| `Carga<T>` | Pasajeros a bordo agrupados por estación de bajada | — |
| `Datos` | Carga todo en una llamada; capacidad por línea (coches × 179) | — |

`Anden` y `Carga` son genéricos para no depender de la clase de agente de AnyLogic: en el
modelo son `Anden<Pasajero>` y `Carga<Pasajero>`.

**Demanda en un solo proceso.** Los 78 complejos se pueden generar por separado o en un
único proceso de la red: la superposición de procesos de Poisson independientes es un
Poisson con la suma de las tasas, y el origen se sortea en proporción a la tasa de cada
complejo en el bloque. Son equivalentes (la prueba lo verifica) y el segundo necesita un
solo evento en AnyLogic.

## Compilar y probar

Con Git Bash, desde esta carpeta:

```bash
./compilar.sh
```

Usa el JDK 17 que trae AnyLogic 8.9 (`C:\Program Files\AnyLogic 8.9 Personal Learning
Edition\jre`), arma `subte.jar` y corre `prueba/PruebaBiblioteca.java` contra los CSV
reales. Si AnyLogic está en otro lado: `JDK="/ruta/al/jre" ./compilar.sh`.

`subte.jar` se versiona ya armado, así que para usar el modelo no hace falta compilar.
Después de cambiar la biblioteca o de regenerar los CSV, hay que volver a correr
`compilar.sh`.

## Qué verifica la prueba

Resultado al 21/09/2026: **todo OK**.

| Verificación | Resultado |
|---|---|
| Red | 90 nodos, 12 recorridos, 166 tramos, 28 transbordos, 178 andenes |
| Rutas | Las 6.006 se reconstruyen; **el tiempo coincide exacto con `tiempo_s`** (diferencia 0,000 s) y las etapas con `n_transbordos` |
| Rutas con cambio de sentido | 142 (ver abajo); el tiempo coincide salvo los 24 s de la vuelta |
| Demanda | Suma 827.289; un día simulado da 827.639 llegadas (z = 0,38), cada hora dentro de 2,2 desvíos, dos picos |
| Proceso unido y separado | Dan lo mismo en el complejo de más demanda (Constitución) |
| Despachos por día | Simulados contra la media observada en las 12 cabeceras: peor diferencia 1,1 % |
| Andén y carga | Suben en orden de llegada hasta llenar, bajan en su estación |

**La comparación de despachos es contra la media, no la mediana.** La cantidad diaria
de despachos tiene cola hacia abajo (días con demoras): en la H, cabecera D, la mediana
es 283 y la media 268. Muestrear intervalos independientes reproduce la media, que es lo
que corresponde.

## Simulador de referencia

`referencia/SimuladorReferencia.java` es un simulador de eventos discretos en Java plano
que corre **la misma lógica** que la guía de construcción, con esta biblioteca. Sirve para
verificar la lógica antes de armarla en AnyLogic y, después, para la verificación
cruzada: con los mismos insumos, AnyLogic tiene que dar lo mismo dentro del error de
muestreo. No reemplaza al modelo de AnyLogic, que es el entregable.

```bash
./referencia/correr.sh          # 10 replicaciones, unos 10 s en total
./referencia/correr.sh --solo C # solo la Linea C
```

Deja `data/processed/referencia_*.csv` y genera `reports/13_verificacion_referencia.md`
con `src/13_verificacion_referencia.py`. Resultados al 21/09/2026: conservación OK en las
10 réplicas; carga por tramo contra SBASE con correlación 0,993 en hora pico mañana y
0,983 en la tarde; y un hallazgo, **el pool de 25.000 pasajeros no alcanza** (hasta 27.796
vivos a la vez), que pasa a 32.000.

## Rutas con cambio de sentido

142 rutas (6.398 viajes por día, el 0,8 %) van a Alberti o salen de Pasco, que la A
sirve en un solo sentido. El camino mínimo del paso 6 sigue de largo hasta Congreso o
Plaza Miserere y vuelve: el grafo no distingue sentido en los nodos, así que la vuelta no
pagó costo en la elección de ruta, y `tiempo_s` cuenta la detención de 24 s en el nodo de
la vuelta como si el pasajero siguiera a bordo. `Ruta` la parte en dos etapas que
comparten ese nodo, donde el pasajero baja y espera una formación en sentido contrario.
**Decidido el 21/09/2026 (D19): se dejan los caminos y se declara.** Medido con un grafo
con sentido donde la vuelta cuesta como un transbordo, solo 4 pares (15 viajes por día)
cambiarían de camino. La vuelta cuenta como un ascenso más en la tasa de transbordo.
