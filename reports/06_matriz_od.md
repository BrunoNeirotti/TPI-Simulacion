# Paso 5: Matriz origen-destino

Generado por `src/06_matriz_od.py`. Dia relevado: **16/10/2024**, un miercoles habil. Fuente: `etapas_BAdata_20241016.csv` (Viajes y Etapas del AMBA), contrastada contra `molinetes-2024.zip` del mismo dia.

## 1. La unidad espacial es el complejo, no el nodo

La red tiene **90 nodos** (par linea-estacion) agrupados en **78 complejos** de estacion, definidos como las componentes conexas del grafo de transbordos del paso 2. Diez complejos tienen mas de un nodo.

Teniamos registrado como residuo de ambiguedad que las estaciones superpuestas de un mismo complejo se confunden al matchear por cercania: Correo Central [E], Corrientes [H] y Santa Fe [H] no aparecen nunca, y 9 de Julio [D], Diagonal Norte [C] e Independencia [C] no aparecen como origen. **Al nivel del complejo el problema no existe**, porque las estaciones que se confunden son exactamente las que el complejo agrupa. Es ademas la unidad correcta desde el modelo: el pasajero entra y sale de un lugar fisico, y por que linea circula es resultado de la asignacion de ruta, no dato de entrada. Mismo criterio que usamos con los andenes.

### 1.1 El matcheo es univoco

Los **89 centroides h3 distintos** se asignan al complejo del nodo mas cercano. Distancia mediana **47 m**, maxima **183 m**.

El control que importa no es esa distancia sino el **margen contra el complejo distinto mas proximo**: minimo **89 m**, percentil 5 **212 m**, mediana **473 m**. Ningun centroide queda disputado.

Los dos casos mas ajustados de la red:

| Centroide asignado a | Distancia | Complejo rival | Margen |
|---|---:|---|---:|
| Avenida de Mayo / Lima | 61 m | Piedras | 89 m |
| Piedras | 53 m | Avenida de Mayo / Lima | 119 m |

> Matchear contra el centroide promedio del complejo en lugar del nodo mas cercano reduce ese margen minimo de 89 m a **9 m** y deja el par Avenida de Mayo / Lima contra Piedras practicamente empatado. Los complejos grandes se extienden mas de 200 m y su promedio no representa a ninguna de sus estaciones. Es la clase de detalle que un control agregado no detecta.

### 1.2 La linea de ascenso resuelve el nodo exacto

El campo `linea_etapa` es la linea del molinete que registro la transaccion: dato observado, no imputado. **En las 587.980 etapas, sin una sola excepcion, esa linea pertenece al complejo de origen asignado** (100,00 %).

Dos consecuencias. Primera, el nodo de origen queda **completamente determinado** por el par (complejo, linea de ascenso): la ambiguedad de origen que dabamos por abierta esta resuelta. Segunda, es una **validacion independiente de la definicion de complejo**, que sale del GTFS, contra una georreferenciacion que sale de otro organismo y otra metodologia.

Aun asi la linea de ascenso **no entra como insumo del modelo**. Fijarla seria fijar parte de la ruta, que es justamente lo que la simulacion tiene que producir. Queda como **contraste del reparto por linea que produzca el modelo**, en paralelo exacto con el contraste por anden.

## 2. Que se descarta

| Concepto | Etapas | % |
|---|---:|---:|
| Etapas de subte del dataset | 587.980 | 100,0 % |
| Origen y destino en el mismo complejo | 84 | 0,014 % |
| **Utiles para la matriz** | **587.896** | **99,986 %** |

Las 84 etapas intracomplejo no son viajes de subte: son pares de estaciones a distancia de caminata dentro de la misma combinacion. Al nivel de estacion el dataset no tenia ninguna etapa con origen igual a destino; al nivel de complejo aparecen estas, que es el precio (minimo) de agrupar. Se descartan.

### 2.1 Las etapas incompletas no mueven la matriz

Las etapas marcadas `viaje_incompleto = t` son **24.057** (4,1 %) y expanden a **30.491** (4,1 % del total expandido).

`matriz_od.csv` trae las dos versiones en columnas separadas, `expandidas` y `expandidas_completas`, para que **se decida midiendo y no discutiendo**.

## 3. La matriz

- **72.245 celdas** de (origen, destino, hora).
- **5.953 pares origen-destino distintos** sobre 6.006 posibles (99,1 %).
- **740.568 etapas expandidas** en el dia.
- Rango horario cubierto: 5 a 23 h.

Los diez pares mas cargados del dia:

| Origen | Destino | Expandidas |
|---|---|---:|
| Constitucion | Retiro | 10.579 |
| Retiro | Constitucion | 9.874 |
| Bolivar / Catedral / Peru | Congreso de Tucuman | 2.816 |
| Congreso de Tucuman | Bolivar / Catedral / Peru | 2.665 |
| Lavalle | Constitucion | 2.594 |
| Plaza de Mayo | Once / Plaza Miserere | 2.441 |
| Facultad de Medicina | Constitucion | 2.313 |
| Constitucion | Once / Plaza Miserere | 2.205 |
| Correo Central / Leandro N. Alem | Federico Lacroze | 2.191 |
| Constitucion | Lavalle | 2.155 |

## 4. Contraste contra molinetes del mismo dia: evidencia para decidir la matriz del modelo

Una etapa de subte es el trayecto puerta a puerta dentro de la red, de modo que **una etapa expandida es un ingreso a la red** y es directamente comparable con un molinete. El contraste se hace contra el **16/10/2024**, el mismo dia que releva el dataset. Es anterior al pago sin contacto (01/12/2024), asi que ambas fuentes miden el mismo universo de pago y la comparacion no arrastra la ruptura de comparabilidad.

- Molinetes del dia: **778.247 ingresos**.
- Matriz O-D expandida: **740.568 etapas**.
- **Factor global: 1,0509**, la matriz subregistra 4,8 % de la demanda medida.

### 4.1 Por linea de ascenso

| Linea | O-D expandida | Molinetes | Factor |
|---|---:|---:|---:|
| B | 179.791 | 180.670 | 1,005 |
| E | 77.926 | 79.552 | 1,021 |
| A | 147.002 | 150.138 | 1,021 |
| D | 161.679 | 166.383 | 1,029 |
| H | 79.799 | 82.299 | 1,031 |
| C | 94.371 | 119.205 | 1,263 |

Recorrido entre lineas: de 1,005 a 1,263, una razon de **1,26**.

### 4.2 Por hora

| Hora | O-D expandida | Molinetes | Factor |
|---|---:|---:|---:|
| 05:00 | 3.681 | 4.196 | 1,140 |
| 06:00 | 21.829 | 22.884 | 1,048 |
| 07:00 | 58.624 | 61.286 | 1,045 |
| 08:00 | 69.793 | 72.493 | 1,039 |
| 09:00 | 53.305 | 55.842 | 1,048 |
| 10:00 | 36.330 | 39.095 | 1,076 |
| 11:00 | 36.704 | 39.707 | 1,082 |
| 12:00 | 44.888 | 47.866 | 1,066 |
| 13:00 | 47.536 | 50.442 | 1,061 |
| 14:00 | 41.581 | 43.965 | 1,057 |
| 15:00 | 47.331 | 49.817 | 1,053 |
| 16:00 | 58.998 | 61.890 | 1,049 |
| 17:00 | 72.396 | 75.067 | 1,037 |
| 18:00 | 60.945 | 63.057 | 1,035 |
| 19:00 | 34.779 | 36.328 | 1,045 |
| 20:00 | 25.187 | 26.178 | 1,039 |
| 21:00 | 16.710 | 17.426 | 1,043 |
| 22:00 | 8.788 | 9.362 | 1,065 |
| 23:00 | 1.163 | 1.346 | 1,158 |

### 4.3 Por complejo

Complejos con dato en ambas fuentes: **78** de 78. Factor mediano **1,015**, rango de 0,387 a 2,711.

Los cinco complejos donde la matriz mas subregistra y los cinco donde mas sobreregistra:

| Complejo | O-D expandida | Molinetes | Factor |
|---|---:|---:|---:|
| San Pedrito | 8.945 | 24.248 | 2,711 |
| Facultad de Derecho | 2.113 | 4.300 | 2,035 |
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | 12.970 | 21.201 | 1,635 |
| Independencia | 11.925 | 16.385 | 1,374 |
| Constitucion | 54.630 | 66.708 | 1,221 |
| … | | | |
| Uruguay | 9.107 | 8.498 | 0,933 |
| Tronador - Villa Ortuzar | 3.960 | 3.691 | 0,932 |
| Florida | 10.879 | 10.121 | 0,930 |
| Parque Patricios | 9.409 | 8.685 | 0,923 |
| San Jose de Flores | 23.349 | 9.042 | 0,387 |

## 5. Lo que la evidencia dice sobre el escalado

La pregunta es si el escalado de la matriz a los niveles de molinetes es un factor unico, por linea, por estacion o por franja horaria. Las tres secciones anteriores responden tres partes de esa pregunta y dejan la cuarta abierta.

### 5.1 La franja horaria no necesita factor propio

Entre las 6 y las 22 h el factor se mueve entre **1,035** y **1,082**, sin ninguna forma sistematica: no crece en el pico ni en el valle. Las dos horas de borde (05:00 y 23:00) se despegan, pero entre las dos suman 0,7 % de los ingresos del dia.

> **Un factor por franja horaria no esta justificado por los datos.** El perfil intrahorario sigue saliendo de molinetes, como estaba previsto; lo que esta seccion descarta es escalar *ademas* por hora.

### 5.2 El desvio por estacion no es todo de la misma naturaleza

| Categoria de complejo | Complejos | O-D | Molinetes | Factor | Peso |
|---|---:|---:|---:|---:|---:|
| Trasbordo ferroviario | 4 | 116.981 | 136.013 | **1,163** | 17,5 % |
| Complejo de combinacion | 8 | 119.919 | 130.686 | **1,090** | 16,8 % |
| Par San Pedrito / San Jose de Flores | 2 | 32.294 | 33.290 | **1,031** | 4,3 % |
| Estacion simple | 64 | 471.374 | 478.258 | **1,015** | 61,5 % |

Hay **tres fenomenos distintos** metidos en la dispersion por estacion, y solo el primero es un desvio de nivel:

1. **Los cuatro nodos de trasbordo ferroviario subregistran de forma sistematica y ordenada** por importancia del ferrocarril: Constitucion (Roca) 1,221, Retiro 1,140, Once / Plaza Miserere 1,123, Federico Lacroze 1,066. Concentran 17,5 % de los ingresos del dia y explican la mayor parte del desvio de la Linea C, que es la unica linea fuera de norma en la seccion 4.1. Es consistente con que el dataset O-D reconstruya el viaje a partir de la transaccion SUBE y pierda parte de la etapa de subte cuando el viaje empieza en el ferrocarril.
2. **El par San Pedrito / San Jose de Flores no es un desvio de nivel sino de asignacion.** Son estaciones vecinas de la Linea A, a 664 m. La matriz le pone a San Jose de Flores 15.495 ingresos de mas y a San Pedrito 14.848 de menos: el neto de las dos es -647, es decir que **el par cierra**. El matcheo esta descartado como causa: cada centroide cae a 55 m de su estacion y a mas de 600 m de la otra. Es la regla de imputacion por parada mas cercana declarada por el organismo publicador, con su tolerancia de 2,2 km, actuando sobre dos estaciones proximas. **Este solo par explica el 35 % de todo el desvio absoluto de la red.**
3. **Los complejos de combinacion no se comportan como grupo.** Su factor promedio (1,090) esconde un recorrido de 0,945 a 1,635: 9 de Julio / Carlos Pellegrini / Diagonal Norte e Independencia subregistran fuerte, mientras Bolivar / Catedral / Peru y Correo Central / Leandro N. Alem sobreregistran. **La categoria no predice nada** y no sirve como criterio.

### 5.3 El residuo no alcanza para elegir

Ingresos mal asignados que sobreviven a cada criterio, sobre 778.247 ingresos del dia:

| Criterio de escalado | Residuo absoluto | % |
|---|---:|---:|
| Factor unico global | 86.909 | 11,2 % |
| Factor por categoria de complejo | 76.269 | 9,8 % |
| Factor por complejo | 0 | 0,0 % (por construccion) |

> El factor por complejo lleva el residuo a cero **por definicion**, no porque represente mejor la realidad: hay un parametro libre por complejo y 78 observaciones. Elegirlo por esta tabla seria elegir el criterio que mas sobreajusta. La pregunta correcta no es cual deja menos residuo sino **que fenomeno se quiere corregir**: el punto 1 de la seccion 5.2 es una subregistracion sistematica que vale la pena corregir, el punto 2 es un defecto de imputacion que un factor por estacion congelaria en el modelo en lugar de repararlo, y el punto 3 no tiene patron.

Dato de contexto: si se excluye el par San Pedrito / San Jose de Flores, el residuo de un factor unico global cae de 11,2 % a **7,6 %**.

### 5.4 Lo que queda para decidir

La decision es de la catedra y del grupo, no de este reporte. Lo que el paso 5 aporta es que **el escalado por franja horaria queda descartado**, que **el escalado por linea es en realidad el escalado de los nodos ferroviarios visto de lejos**, y que el escalado por estacion **corrige y congela al mismo tiempo**. El analisis de sensibilidad tiene que recorrer esa eleccion; sigue siendo el supuesto propio central del trabajo.
