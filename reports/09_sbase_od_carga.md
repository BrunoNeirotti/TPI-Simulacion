# Paso 9 — Matriz O-D y perfiles de carga de SBASE (Ley 104)

Fuente: `IF-2026-38553261-GCABA-SBASE.pdf`, del 26/08/2026, respuesta a la 
solicitud 00866317/26. Las dos planillas venian **embebidas dentro del PDF** 
(`/Names /EmbeddedFiles`), no como adjuntos del correo; se extrajeron a 
`data/raw/sbase-ley104/`. Se leen con `src/lib_sbase.py`.


## 1. Que trae

| Periodo | Pares con flujo | Viajes |
|---|---:|---:|
| Dia habil completo | 7.699 de 8.010 | 827.976 |
| Hora pico manana (8–9 h) | 4.812 de 8.010 | 74.351 |
| Hora pico tarde (17–18 h) | 5.868 de 8.010 | 80.197 |

La unidad espacial es el **nodo**, no el complejo: las 90 estaciones de la 
planilla son los 90 pares linea-estacion del grafo del paso 2 y cruzan una a 
una con el. Retiro [C] y Retiro [E] son dos filas distintas, igual que 
Callao [B] y Callao [D].


### Dos mapas de identificador, y no son el mismo

Los dos libros numeran las estaciones de 1 a 90 y **coinciden solo hasta el 
75**. La matriz O-D pone la cola de la Linea E (Correo Central, Catalinas, 
Retiro E) al final de todo; el perfil de carga la pone antes de la Linea H. 
Cruzar una planilla con el mapa de la otra corre 15 estaciones sin dar ningun 
error visible. `lib_sbase` usa siempre el mapa del propio libro.


## 2. Concentracion horaria: coincide con lo que miden los molinetes

La hora pico manana concentra el **9,0 %** de los viajes del dia y 
la tarde el **9,7 %**. El paso 3 habia medido sobre molinetes de 
2025 una concentracion de 9,9 % en la hora pico de la red. **Las dos fuentes 
coinciden**, y son independientes entre si.


Eso vuelve a cerrar el mismo contraste sobre la Linea F, ahora con la propia 
fuente que produjo la cifra en discusion: para que los ~73.900 ascensos de hora 
pico del *Analisis de Demanda Linea F* (SBASE, 2019) fueran compatibles con los 
270.000–300.000 viajes diarios anunciados, la Linea F tendria que concentrar en 
una hora cerca del 25 % de su demanda diaria — dos veces y media lo que concentra 
la red que la propia SBASE mide.


## 3. La matriz no es simetrica por construccion

| Periodo | Asimetria |
|---|---:|
| diaria | 7,4 % |
| hpm | 66,0 % |
| hpt | 43,2 % |

Es la diferencia de fondo con la matriz del paso 5. Aquella hereda del dataset 
de Viajes y Etapas una **imputacion por simetria diaria**, y por eso su 
direccionalidad horaria es una construccion, no una medicion. Esta se midio 
sobre transacciones: en hora pico manana el flujo es abrumadoramente hacia el 
centro y en hora pico tarde se invierte. Para un modelo de eventos discretos 
esa direccionalidad es la variable que decide todo.


Ascensos y descensos en hora pico manana, cinco primeros:

| Ascensos | | Descensos | |
|---|---:|---|---:|
| Constitucion [C] | 12.007 | Catedral [D] | 3.712 |
| Juan Manuel de Rosas [B] | 3.672 | Leandro N. Alem [B] | 2.921 |
| San Pedrito [A] | 3.611 | Plaza de Mayo [A] | 2.897 |
| Congreso de Tucuman [D] | 3.226 | Florida [B] | 2.511 |
| Federico Lacroze [B] | 3.098 | Retiro [C] | 2.125 |


## 4. Contraste con la matriz del paso 5 y con molinetes

| Fuente | Dia | Viajes o ingresos |
|---|---|---:|
| Molinetes | miercoles 16/10/2024 | 778.247 |
| Matriz del paso 5 (Viajes y Etapas, expandida) | miercoles 16/10/2024 | 740.568 |
| Matriz de SBASE (EMOVA, transacciones SUBE) | dia habil de septiembre 2024 | 827.289 |

La cifra de SBASE de esta tabla deja afuera los 687 viajes diarios entre dos 
nodos de un mismo complejo, que en el modelo son una caminata y no un viaje en 
tren; el total de la matriz es 827.976 (ver seccion 8).

La matriz de SBASE queda **6,3 % por encima** de 
los molinetes del 16/10/2024 y la del paso 5 queda 4,8 % por debajo. No son el 
mismo dia ni el mismo mes —septiembre corre mas alto que octubre en la serie de 
molinetes— y SBASE declara que su base son transacciones SUBE, que en septiembre 
de 2024 concentraban mas del 95 % de los pagos: expandir ese 95 % al total 
explica un factor de 1,05 por si solo.


A nivel de par de complejos, las dos matrices correlacionan **0,926** 
sobre 5.997 pares con flujo en alguna de las dos; 
5.795 tienen flujo en ambas.


Ascensos por complejo contra molinetes del 16/10/2024, ocho mayores desvios 
de la matriz de SBASE:

| Complejo | Molinetes | SBASE | Factor SBASE | Factor paso 5 |
|---|---:|---:|---:|---:|
| Piedras | 3.736 | 5.575 | 1,492 | 1,066 |
| Facultad de Medicina | 14.418 | 7.745 | 0,537 | 1,013 |
| Alberti | 3.554 | 5.176 | 1,456 | 0,944 |
| Venezuela | 4.159 | 5.875 | 1,413 | 0,995 |
| Callao [B] | 10.055 | 13.297 | 1,322 | 1,063 |
| San Jose | 2.565 | 1.748 | 0,681 | 0,986 |
| Corrientes / Pueyrredon | 11.498 | 14.691 | 1,278 | 0,978 |
| Lavalle | 4.956 | 6.322 | 1,276 | 1,008 |


### El par San Pedrito / San Jose de Flores, que abrio la decision D8

El paso 5 encontro que el dataset de Viajes y Etapas reparte mal la demanda entre 
esas dos estaciones vecinas de la Linea A: el total del par cierra bien pero el 
reparto esta corrido, y eso explica el 35 % del desvio absoluto de toda la red. 
**La matriz de SBASE no tiene ese defecto.**


| Complejo | Molinetes | SBASE | Factor | Paso 5 | Factor |
|---|---:|---:|---:|---:|---:|
| San Pedrito | 24.248 | 24.971 | 1,030 | 8.945 | 0,369 |
| San Jose de Flores | 9.042 | 10.684 | 1,182 | 23.349 | 2,582 |

Es un argumento fuerte a favor de la matriz de SBASE en D2, y de paso vuelve 
innecesaria la reparacion que D8 planteaba: el defecto es de una fuente, no del 
fenomeno.


## 5. Reparto por linea en los complejos de combinacion

La matriz de SBASE es por nodo, asi que dice directamente por que linea sube 
cada pasajero en un complejo de varias lineas. Es la **cuarta fuente** del mismo 
reparto, despues de molinetes, `linea_etapa` y la prediccion del paso 6, y la 
unica que no comparte origen con ninguna de las otras.


| Complejo | Linea | Molinetes | `linea_etapa` | Modelo (paso 6) | SBASE |
|---|---|---:|---:|---:|---:|
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | B | 62,8 % | 100,0 % * | 59,7 % | 65,0 % |
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | D | 18,6 % | 0,0 % * | 24,8 % | 17,0 % |
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | C | 18,6 % | 0,0 % * | 15,6 % | 18,0 % |
| Avenida de Mayo / Lima | A | 61,2 % | 61,5 % | 60,2 % | 62,2 % |
| Avenida de Mayo / Lima | C | 38,8 % | 38,5 % | 39,8 % | 37,8 % |
| Bolivar / Catedral / Peru | D | 52,8 % | 52,9 % | 57,8 % | 53,3 % |
| Bolivar / Catedral / Peru | E | 25,2 % | 24,1 % | 18,3 % | 24,4 % |
| Bolivar / Catedral / Peru | A | 22,0 % | 23,0 % | 23,9 % | 22,3 % |
| Correo Central / Leandro N. Alem | B | 70,4 % | 70,6 % | 71,9 % | 73,3 % |
| Correo Central / Leandro N. Alem | E | 29,6 % | 29,4 % | 28,1 % | 26,7 % |
| Corrientes / Pueyrredon | B | 64,9 % | 65,3 % | 61,8 % | 67,5 % |
| Corrientes / Pueyrredon | H | 35,1 % | 34,7 % | 38,2 % | 32,5 % |
| Humberto 1 / Jujuy | H | 68,1 % | 68,6 % | 73,8 % | 69,1 % |
| Humberto 1 / Jujuy | E | 31,9 % | 31,4 % | 26,2 % | 30,9 % |
| Independencia | E | 69,5 % | 100,0 % * | 54,7 % | 70,2 % |
| Independencia | C | 30,5 % | 0,0 % * | 45,3 % | 29,8 % |
| Once / Plaza Miserere | A | 51,6 % | 50,4 % | 53,5 % | 50,0 % |
| Once / Plaza Miserere | H | 48,4 % | 49,6 % | 46,5 % | 50,0 % |
| Pueyrredon / Santa Fe | H | 60,2 % | 62,5 % | 56,7 % | 62,0 % |
| Pueyrredon / Santa Fe | D | 39,8 % | 37,5 % | 43,3 % | 38,0 % |
| Retiro | C | 85,5 % | 83,9 % | 69,8 % | 86,0 % |
| Retiro | E | 14,5 % | 16,1 % | 30,2 % | 14,0 % |

`*` marca los complejos donde el dataset de Viajes y Etapas atribuye el 100 % de 
los ascensos a una sola linea, defecto ya declarado en el paso 6.


El modelo del paso 6 se aparta de SBASE a lo sumo 16,2 % en un 
complejo (Retiro) y 5,5 % en la mediana.


**Retiro, la discrepancia que abrio la decision D9.** El paso 6 predecia 
69,8 % de los ascensos por la Linea C contra 85,5 % 
de molinetes. SBASE mide 86,0 %: le da la razon a molinetes y 
confirma que el modelo manda demasiada gente a la Linea E en ese nodo.


## 6. Perfiles de carga: la ocupacion a bordo deja de ser inobservable

El trabajo declara la ocupacion a bordo como indicador central y 
**sin contraparte empirica en ninguna fuente publica**. La planilla de perfiles 
la trae: ascensos, descensos y pasajeros a bordo por tramo, para las seis 
lineas, los dos sentidos y las dos horas pico.


Carga maxima por linea y periodo, con el tramo donde ocurre:

| Linea | Periodo | Sentido | Tramo que sale de | Pas./h a bordo |
|---|---|---|---|---:|
| A | HPM | hacia PMayo | Miserere | 10.481 |
| A | HPT | hacia SanPedrito | Miserere | 8.744 |
| B | HPM | hacia Alem | Gardel | 11.777 |
| B | HPT | hacia JMRosas | Pueyr | 10.785 |
| C | HPM | hacia Retiro | SanJuan | 12.249 |
| C | HPT | hacia Constitucion | Mariano Moreno | 10.280 |
| D | HPM | hacia Catedral | Aguero | 8.066 |
| D | HPT | hacia CongresoTuc | Pueyrredon | 7.663 |
| E | HPM | hacia RetiroE | Independencia E | 4.783 |
| E | HPT | hacia Virreyes | Jujuy | 4.751 |
| H | HPM | hacia Fderecho | Once | 6.728 |
| H | HPT | hacia Hospitales | Corrientes | 6.459 |


El tramo mas cargado de toda la red actual lleva **12.249 
pas./h** (Linea C, HPM, saliendo de SanJuan 
hacia Retiro). El *Analisis de Demanda Linea F* proyecta 
**35.742 pas./h** en el tramo Constitucion → Cochabamba: 
**2,9 veces** el tramo mas cargado 
que hoy tiene la red. El contraste ya no es contra una cifra anunciada de 
prensa sino contra la medicion de la propia SBASE sobre su propia red.


## 7. Validacion de la asignacion todo-o-nada del paso 6

Se cargo la matriz de SBASE de cada hora pico sobre el grafo del paso 2 usando 
los caminos minimos del paso 6 —asignacion todo-o-nada, penalizacion por 
transbordo de 120 s— y se comparo la carga que resulta en cada tramo contra la 
que mide SBASE. **Es la primera validacion de la asignacion de ruta contra un 
observado**; hasta ahora solo se podia contrastar el reparto por linea de ascenso.


De las 360 filas del perfil quedan 332 
comparables. Se excluyen las cabeceras de llegada, que no tienen tramo saliente 
y donde el observado es cero, y Alberti y Pasco en el sentido en que el tren 
pasa sin detenerse: ahi el observado es real pero el grafo no tiene un tramo que 
salga de esa estacion, sino uno mas largo que la contiene (28 filas 
en total).


**HPM**: correlacion 0,994 sobre 166 tramos; error absoluto ponderado 6,5 % de los pasajeros-tramo observados; la asignacion produce 1,4 % mas pasajeros-tramo que lo observado.


**HPT**: correlacion 0,985 sobre 166 tramos; error absoluto ponderado 8,4 % de los pasajeros-tramo observados; la asignacion produce 0,3 % mas pasajeros-tramo que lo observado.


Diez tramos comparables con mayor diferencia absoluta:

| Periodo | Linea | Sentido | Sale de | Observado | Asignado | Dif. |
|---|---|---|---|---:|---:|---:|
| HPT | H | hacia Hospitales | Venezuela | 4.025 | 5.276 | 1.251 |
| HPT | H | hacia Hospitales | Once | 4.414 | 5.660 | 1.246 |
| HPT | H | hacia Hospitales | Corrientes | 6.459 | 7.582 | 1.123 |
| HPT | D | hacia CongresoTuc | Palermo | 4.970 | 6.067 | 1.097 |
| HPT | D | hacia CongresoTuc | Carranza | 4.341 | 5.382 | 1.041 |
| HPT | A | hacia SanPedrito | Miserere | 8.744 | 9.760 | 1.016 |
| HPT | A | hacia SanPedrito | Loria | 8.469 | 9.460 | 991 |
| HPT | C | hacia Retiro | SanMartin | 2.385 | 1.403 | -982 |
| HPM | H | hacia Fderecho | Once | 6.728 | 7.692 | 964 |
| HPT | D | hacia CongresoTuc | Juramento | 1.604 | 2.560 | 956 |


La comparacion tiene una holgura que no es del modelo y hay que declararla: 
SBASE avisa en el propio informe que *"los valores presentados en la matriz 
origen-destino y en los diagramas de carga pueden presentar diferencias"*, 
porque los diagramas de carga pasan por un ajuste iterativo sobre ascensos y 
descensos para que la carga cierre en cero en la cabecera. La matriz y el perfil 
no son, entonces, dos vistas exactas del mismo dato.


### La tasa de transbordo, medida por segunda vez

Las dos planillas estan en unidades distintas y conviene no confundirlas: la 
matriz cuenta **viajes** y el perfil cuenta **ascensos a bordo**, de modo que un 
pasajero que combina aparece una vez en la primera y dos en el segundo. El 
cociente entre ambas es la tasa de transbordo observada, y es otra validacion 
independiente de la asignacion del paso 6.


| Periodo | Ascensos por viaje, SBASE | Ascensos por viaje, modelo |
|---|---:|---:|
| HPM | 1,371 | 1,410 |
| HPT | 1,426 | 1,437 |

El modelo transborda un poco de mas en la hora pico manana y practicamente lo 
mismo en la tarde. Es consistente con el sesgo por linea de la seccion 5.


## 8. Que queda declarado

- **Viajes dentro de un mismo complejo.** La matriz diaria trae 687 
  viajes (0,08 % del total) entre dos nodos del mismo complejo — Retiro [C] a 
  Retiro [E] y equivalentes. En el modelo son una caminata dentro de la estacion, 
  no un viaje en tren, y quedan fuera de la asignacion. Se declaran, no se 
  reparten.
- **Los perfiles de carga son de hora pico, no de dia completo.** La ocupacion a 
  bordo tiene contraparte empirica en las dos horas pico y sigue sin tenerla en 
  el resto del dia de servicio, que es el horizonte del modelo.
- **La aglomeracion de anden sigue sin contraparte.** Ninguna de las dos planillas 
  la mide; sigue siendo salida del modelo sin validacion posible.
- **La matriz de SBASE es de septiembre de 2024 y la del paso 5 del 16/10/2024.** 
  Las dos son anteriores a la apertura de medios de pago del 01/12/2024, asi que 
  ninguna arrastra esa ruptura, pero tampoco describen la red de 2025 o 2026.
- **El perfil pasa por un ajuste iterativo de SBASE**, declarado por ellos en el 
  propio informe. No es un conteo directo a bordo.
