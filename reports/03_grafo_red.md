# Paso 2: Grafo de la red

Generado por `src/03_grafo_red.py`. Fuente: GTFS de Subte (`data/raw/gtfs/`). Salidas: `data/processed/grafo_nodos.csv` y `data/processed/grafo_aristas.csv`.

## 1. Tamaño del grafo

- **Nodos**: 90 pares (línea, estación).
- **Aristas de tramo**: 166 dirigidas.
- **Aristas de transbordo**: 28 dirigidas, es decir 14 combinaciones.
- Fuera de alcance (Premetro): 56 tramos y 2 transbordos, excluidos del grafo.

| Línea | Estaciones | Tramos | km por sentido | Marcha (min) | Punta a punta (min) | Velocidad comercial (km/h) |
|---|---:|---:|---:|---:|---:|---:|
| A | 18 | 32 | 9.63 | 19.5 | 25.5 | 22.7 |
| B | 17 | 32 | 11.77 | 20.4 | 26.4 | 26.8 |
| C | 9 | 16 | 4.25 | 9.7 | 12.5 | 20.4 |
| D | 16 | 30 | 10.29 | 19.8 | 25.4 | 24.3 |
| E | 18 | 34 | 11.71 | 22.3 | 28.7 | 24.5 |
| H | 12 | 22 | 7.82 | 14.5 | 18.5 | 25.4 |

La velocidad comercial no incluye la detención en las cabeceras ni el tiempo de retorno, así que es la del recorrido, no la del ciclo.

## 2. El tiempo de detención es una constante, no una medición

El feed declara **24 s de detención en toda parada de toda línea, sin una sola excepción** (166 tramos, desvío 0.0). No hay diferencia entre Constitución y Pasco, ni entre hora pico y valle (el GTFS no tiene bandas horarias), ni entre cabecera y estación intermedia.

> **Consecuencia.** Los 24 s son un **valor nominal de diseño del horario**, no una detención observada. Los teníamos anotados como tiempo de detención tomado del GTFS, y lo son, pero conviene precisar qué clase de dato son: sirven como punto de partida y como cota inferior, mientras que la detención real depende del volumen que sube y baja, que es justamente lo que el modelo produce. **En el modelo la detención tiene que ser endógena, con los 24 s como piso.**

## 3. Dos defectos del feed, y qué hace el grafo con cada uno

### 3.1 La Línea A no es simétrica, y está bien que no lo sea

Alberti y Pasco tienen **un solo andén cada una y se sirven en un único sentido**. Por eso la A tiene 18 estaciones pero 17 paradas por sentido, y por eso la red tiene 90 nodos y no 89.

| Estación | Línea | Único sentido servido |
|---|---|---|
| Alberti | A | hacia San Pedrito |
| Pasco | A | hacia Plaza de Mayo |

No es un error del feed sino la operación real, y **obliga a que el grafo sea dirigido**: en cada una de esas dos estaciones se puede subir y bajar en un solo sentido de circulación. Un grafo no dirigido habría inventado cuatro servicios que no existen.

### 3.2 El sentido 1 de la Línea E está corrupto en el feed

La columna `shape_dist_traveled` del sentido 1 de la E es **copia literal** de la del sentido 0: los 18 valores coinciden posición por posición. Eso haría que Plaza de los Virreyes → Varela midiera lo mismo que Retiro → Catalinas. Es la única ruta del feed con ese defecto: en las otras siete la comprobación da negativa.

Los tiempos del mismo sentido tampoco se salvan. Correlación entre tiempo de marcha y distancia, tramo a tramo:

| Conjunto | Correlación t~km | Desvío de la velocidad |
|---|---:|---:|
| Resto de la red y E sentido 0 | 0,863 | 4,3 km/h |
| E sentido 1, contra su distancia publicada | **0,010** | 11,4 km/h |
| E sentido 1, contra la distancia real | 0,425 | 7,9 km/h |

La correlación de 0,010 dice que el sentido 1 de la E está **desacoplado de su propia geometría**: no es que las distancias estén mal y los tiempos bien, están mal las dos columnas. El total sí cierra (11,71 km y 29 min 28 s en los dos sentidos), así que el defecto es de reparto interno y pasa desapercibido en cualquier control agregado.

Los cinco tramos donde más se aparta el dato publicado:

| Tramo | t publicado | t reparado | km publicado | km real |
|---|---:|---:|---:|---:|
| San Jose → Independencia | 121 s | 60 s | 0.72 | 0.83 |
| La Plata → Boedo | 60 s | 105 s | 0.83 | 0.72 |
| Boedo → General Urquiza | 62 s | 103 s | 0.65 | 0.56 |
| Independencia → Belgrano | 96 s | 59 s | 0.6 | 0.81 |
| Entre Rios → San Jose | 104 s | 72 s | 0.56 | 0.65 |

> **Reparo aplicado.** El sentido 1 de la E se reemplaza por el espejo del sentido 0, que es exactamente lo que hacen las otras cinco líneas del feed: de 81 tramos emparejados entre sentidos, 64 tienen diferencia exacta cero en tiempo y en distancia, y los 17 restantes son todos de la E. El interruptor es `REPARAR_LINEA_E` en `src/03_grafo_red.py`. **Es una decisión a confirmar**, ver sección 6.

## 4. Transbordos

28 aristas dirigidas construidas sobre 104 pares de andenes. El tiempo de nodo a nodo es la **mediana** de los pares de andén del complejo, porque la demanda se modela por estación y el andén de origen es resultado de la asignación de ruta, no un dato de entrada. El mínimo y el máximo quedan en el CSV para el análisis de sensibilidad.

Rango sobre pares de andén: 42-258 s. Mediana de las medianas: 146 s.

**Los tiempos son direccionales**, y la diferencia no es despreciable:

| Combinación | Ida | Vuelta | Diferencia | Pares de andén |
|---|---:|---:|---:|---:|
| Pueyrredon [D] ↔ Santa Fe [H] | 90 s | 112 s | 22 s | 8 |
| Lima [A] ↔ Avenida de Mayo [C] | 159 s | 171 s | 12 s | 8 |
| Pueyrredon [B] ↔ Corrientes [H] | 110 s | 116 s | 6 s | 8 |
| Carlos Pellegrini [B] ↔ 9 de Julio [D] | 105 s | 99 s | 6 s | 8 |
| Leandro N. Alem [B] ↔ Correo Central [E] | 58 s | 64 s | 6 s | 4 |
| Plaza Miserere [A] ↔ Once [H] | 163 s | 168 s | 5 s | 8 |
| Peru [A] ↔ Bolivar [E] | 151 s | 154 s | 3 s | 8 |
| Independencia [C] ↔ Independencia [E] | 118 s | 120 s | 2 s | 8 |
| Peru [A] ↔ Catedral [D] | 150 s | 150 s | 0 s | 8 |
| Carlos Pellegrini [B] ↔ Diagonal Norte [C] | 243 s | 243 s | 0 s | 8 |
| Diagonal Norte [C] ↔ 9 de Julio [D] | 72 s | 72 s | 0 s | 8 |
| Retiro [C] ↔ Retiro [E] | 180 s | 180 s | 0 s | 4 |
| Catedral [D] ↔ Bolivar [E] | 220 s | 220 s | 0 s | 8 |
| Jujuy [E] ↔ Humberto 1 [H] | 141 s | 141 s | 0 s | 8 |

Esto reemplaza al *tiempo de caminata como parámetro declarado* que figuraba en la metodología: el transbordo deja de ser un supuesto del grupo y pasa a ser un dato del feed, distinto para cada combinación y para cada sentido.

## 5. Verificaciones

- **Los tres `service_id` son idénticos**: una sola firma por ruta y sentido, sin excepciones. Se usa el día hábil (`service_id=5`). Consecuencia: **el GTFS no distingue hábil de sábado ni de domingo**, así que la variación por tipo de día tiene que salir de molinetes y de despachos, nunca de acá.
- **Conectividad fuerte**: sí, 1 componente fuertemente conexa. Todo nodo alcanza a todo otro nodo, que es la condición para que el paso 6 (caminos mínimos) tenga solución para los 7.102 pares O-D observados.
- **Cruce contra la tabla maestra del paso 1**: los 90 nodos coinciden uno a uno, sin faltantes ni sobrantes.
- **Tramos con tiempo o distancia no positivos**: 0 y 0.

## 6. Lo que este paso deja abierto

- **El reparo de la Línea E hay que confirmarlo** (sección 3.2). Las alternativas son usar el dato publicado tal cual, que está desacoplado de la geometría, o promediar ambos sentidos. Afecta solo a la E, pero la E combina con la A, la C, la D y la H.
- **La detención tiene que ser endógena en el modelo** (sección 2), con los 24 s como piso y no como valor de operación.
- **El GTFS no tiene bandas horarias ni tipos de día** (sección 5). Los tiempos de marcha son un único perfil nominal. Si la marcha se degrada en hora pico, este grafo no lo sabe: lo tiene que producir el modelo.
- Los tiempos de transbordo son `min_transfer_time`, es decir un **mínimo de diseño**, no un tiempo de caminata observado. Igual que la detención, funcionan como piso.
- El paso 4 (intervalos entre despachos) dirá si estos tiempos nominales son compatibles con la operación real.
