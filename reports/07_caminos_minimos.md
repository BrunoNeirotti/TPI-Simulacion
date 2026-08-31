# Paso 6: Caminos minimos con penalizacion por transbordo

Generado por `src/07_caminos_minimos.py`, con `src/lib_caminos.py`. Precalcula el camino de menor tiempo percibido para cada par ordenado de complejos, sobre el grafo dirigido del paso 2.

## 1. Como se cuenta el tiempo

El costo de un camino es

```
t = marcha de cada tramo
  + 24 s por cada PARADA INTERMEDIA
  + min_transfer_time de cada transbordo
  + P por cada transbordo
```

Los 24 s son la detencion de diseno del GTFS, que el paso 2 mostro constante en toda parada de toda linea. **Van por parada intermedia, no por tramo recorrido**: el que asciende no espera la detencion de su estacion de ascenso (esa es su ventana de abordaje) y el que desciende tampoco espera la de la suya. Contarlas por tramo abarataria en terminos relativos los caminos con muchas paradas, que es justo el error que un grafo de subte no puede darse.

**El acceso y el egreso dentro de un complejo valen cero.** El pasajero entra al complejo, no a un anden: asciende en cualquiera de sus nodos y desciende en cualquiera de los del complejo de destino, y se toma el minimo. Caminar dentro del complejo de origen **no cuenta como transbordo**. `pathways.txt` tiene los recorridos internos, pero no para toda la red; queda declarado como simplificacion.

**La penalizacion P es un supuesto, no un dato.** El valor base es **120 s** y sale de los despachos del paso 4: en hora pico los intervalos van de 3,15 min (C) a 5,22 min (E), de modo que la espera esperada (la mitad del intervalo) cae entre 95 y 157 s. Por eso la seccion 4 recorre el rango completo en lugar de fijar el valor.

## 2. La tabla

- **6.006 pares ordenados** de complejos, todos alcanzables (78 x 77).
- Tiempo de viaje: mediana **16:04**, maximo **43:14** (Plaza de los Virreyes -> Congreso de Tucuman).
- Transbordos por camino: **0**: 1.326 pares (22,1 %), **1**: 2.851 pares (47,5 %), **2**: 1.829 pares (30,5 %).
- Media de 1,08 transbordos por par.

> **Control de coherencia con el paso 2.** El grafo es fuertemente conexo, asi que los 6.006 pares tienen camino. Que ninguno quede aislado no es un resultado del paso 6: es la confirmacion de que el grafo dirigido con Alberti y Pasco servidas en un solo sentido sigue permitiendo ir de cualquier estacion a cualquier otra.

## 3. Cuan disputada esta la asignacion

La asignacion es todo-o-nada: cada par manda todo su flujo por un unico camino. Para saber cuanto pesa esa simplificacion se calcula, por cada par, **el mejor camino que asciende por una linea distinta** y la brecha de tiempo contra el elegido.

- Pares con alternativa por otra linea de ascenso: **770** de 6.006.
- Brecha mediana: **3:26**.
- Pares con la alternativa a menos de 60 s: **50**, que son 0,8 % del total pero **6,5 % de los pares que realmente tienen eleccion**. La segunda cifra es la que corresponde mirar: en los otros 5.236 pares el complejo de origen tiene una sola linea y no hay nada que elegir.

> Esos son los pares donde mandar el 100 % del flujo por un camino es una decision que los datos no respaldan, y donde una asignacion por reparto daria distinto. Es una limitacion declarada del diseno, ahora con magnitud.

## 4. Sensibilidad a la penalizacion

| P (s) | Transbordos medios | Pares sin transbordo | Tiempo medio | Cambian de camino | Cambian de linea de ascenso |
|---:|---:|---:|---:|---:|---:|
| 0 | 1,166 | 1.322 | 16:31 | 495 | 25 |
| 60 | 1,139 | 1.326 | 16:32 | 329 | 15 |
| 120 | 1,084 | 1.326 | 16:36 | 0 | 0 |
| 180 | 1,068 | 1.326 | 16:39 | 95 | 2 |
| 300 | 1,041 | 1.326 | 16:45 | 257 | 4 |

Las columnas de cambio se miden contra el caso base de 120 s.

## 5. Contraste del reparto por linea de ascenso

La ruta nunca entro al modelo como insumo, asi que el reparto por linea que produce se puede contrastar. Solo tiene sentido en los diez complejos con mas de una linea, que son los unicos donde el pasajero elige, y se hace contra **dos fuentes observadas a la vez** porque ninguna de las dos es limpia:

- **Molinetes** del 16/10/2024, por estacion del complejo. Es una tercera fuente, independiente del dataset O-D. Su sesgo: mide la estacion **de ingreso**, no la linea de ascenso, asi que quien entra por un molinete y camina hasta el anden de la otra linea queda mal atribuido. Es el mismo sesgo que declaramos para el contraste por anden.
- **`linea_etapa`** del dataset O-D, que si es la linea del molinete que registro la transaccion. Su defecto es otro y aparece abajo.

| Complejo | Linea | Molinetes | O-D | Predicho | Dif. vs molinetes |
|---|---|---:|---:|---:|---:|
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | B | 62,8 % | 100,0 % ⚠ | 59,7 % | -3,1 p.p. |
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | C | 18,6 % | 0,0 % ⚠ | 15,6 % | -3,1 p.p. |
| 9 de Julio / Carlos Pellegrini / Diagonal Norte | D | 18,6 % | 0,0 % ⚠ | 24,8 % | 6,1 p.p. |
| Avenida de Mayo / Lima | A | 61,2 % | 61,5 % | 60,2 % | -1,0 p.p. |
| Avenida de Mayo / Lima | C | 38,8 % | 38,5 % | 39,8 % | 1,0 p.p. |
| Bolivar / Catedral / Peru | A | 22,0 % | 23,0 % | 23,9 % | 1,8 p.p. |
| Bolivar / Catedral / Peru | D | 52,8 % | 52,9 % | 57,8 % | 5,0 p.p. |
| Bolivar / Catedral / Peru | E | 25,2 % | 24,1 % | 18,3 % | -6,9 p.p. |
| Correo Central / Leandro N. Alem | B | 70,4 % | 70,6 % | 71,9 % | 1,5 p.p. |
| Correo Central / Leandro N. Alem | E | 29,6 % | 29,4 % | 28,1 % | -1,5 p.p. |
| Corrientes / Pueyrredon | B | 64,9 % | 65,3 % | 61,8 % | -3,0 p.p. |
| Corrientes / Pueyrredon | H | 35,1 % | 34,7 % | 38,2 % | 3,0 p.p. |
| Humberto 1 / Jujuy | E | 31,9 % | 31,4 % | 26,2 % | -5,8 p.p. |
| Humberto 1 / Jujuy | H | 68,1 % | 68,6 % | 73,8 % | 5,8 p.p. |
| Independencia | C | 30,5 % | 0,0 % ⚠ | 45,3 % | 14,8 p.p. |
| Independencia | E | 69,5 % | 100,0 % ⚠ | 54,7 % | -14,8 p.p. |
| Once / Plaza Miserere | A | 51,6 % | 50,4 % | 53,5 % | 1,8 p.p. |
| Once / Plaza Miserere | H | 48,4 % | 49,6 % | 46,5 % | -1,8 p.p. |
| Pueyrredon / Santa Fe | D | 39,8 % | 37,5 % | 43,3 % | 3,6 p.p. |
| Pueyrredon / Santa Fe | H | 60,2 % | 62,5 % | 56,7 % | -3,6 p.p. |
| Retiro | C | 85,5 % | 83,9 % | 69,8 % | -15,7 p.p. |
| Retiro | E | 14,5 % | 16,1 % | 30,2 % | 15,7 p.p. |

- Error absoluto medio contra **molinetes**: **5,47 p.p.** sobre los diez complejos.
- Error absoluto medio contra **`linea_etapa`**, excluyendo los complejos marcados: **4,71 p.p.**

> **Las dos fuentes observadas coinciden entre si donde ninguna esta rota**: en los ocho complejos sanos difieren en promedio 0,89 p.p. Son fuentes independientes (una es el conteo de molinetes, la otra la reconstruccion de viajes a partir de transacciones SUBE) y que se corroboren da piso al contraste. Donde discrepan fuerte, discrepan por una razon identificable, que es de lo que tratan las dos secciones que siguen.

### 5.1 Dos complejos donde el dataset O-D esta roto, y molinetes lo demuestra

En **9 de Julio / Carlos Pellegrini / Diagonal Norte** y en **Independencia** el dataset O-D atribuye el 100 % de los ascensos a una sola linea. Ya lo teniamos anotado (9 de Julio [D], Diagonal Norte [C] e Independencia [C] no aparecen nunca como origen) y aca se ve el efecto.

**Molinetes le da la razon al modelo, no al dataset.** En 9 de Julio / Carlos Pellegrini / Diagonal Norte los molinetes reparten 62,8 / 18,6 / 18,6 entre B, C y D, y la ruta predice 59,7 / 15,6 / 24,8; el dataset O-D dice 100 / 0 / 0. Es la confirmacion de que la degeneracion es un defecto de la fuente y no un comportamiento real, y de paso **refuerza la decision de no meter la linea de ascenso como insumo del modelo**: si se hubiera usado, ese defecto entraba directo a la entrada.

Los dos complejos degenerados son ademas **los dos complejos de combinacion que mas subregistran** en el paso 5 (factores 1,635 y 1,374). Los dos hechos apuntan al mismo mecanismo: el dataset colapsa el complejo sobre una estacion y en el camino pierde parte de la demanda.

### 5.2 Retiro es la discrepancia real, y no se explica por lo obvio

Es el unico desajuste grande que **no** es defecto de fuente: las dos fuentes coinciden (molinetes 85,5 % por la C, `linea_etapa` 83,9 %) y la ruta predice 69,8 %. Sobreasigna a la Linea E.

Se probaron dos explicaciones y **las dos quedaron descartadas**:

1. **El reparo de la Linea E.** Se regenero el grafo con `REPARAR_LINEA_E = False` y se recalcularon los caminos: cambian **58 pares de 6.006 (1,0 %)** y 18 cambian de linea de ascenso. El reparto de Retiro **no se mueve**. El reparo importa poco para la asignacion; sigue abierto pero no es la causa de esto.
2. **Que la penalizacion sea uniforme y no distinga frecuencias.** Se probo reemplazarla por la espera esperada de cada linea, calculada como la mitad del intervalo de hora pico medido en el paso 4 (A y C 94 s, H 103, D 111, B 121, E 156). **Empeora el ajuste**, de 5,47 a 7,36 p.p. de error medio, y tampoco mueve a Retiro. Se descarta y se conserva la penalizacion uniforme.

Queda una explicacion no verificable con los datos disponibles: el sesgo de las fuentes. Retiro [C] y Retiro [E] estan a 151 m, y la terminal ferroviaria descarga sobre el acceso de la C, de modo que el molinete sobreatribuye a la C gente que despues camina hasta la E. **Se declara como discrepancia abierta**, no se corrige: corregirla seria ajustar la ruta contra una fuente cuyo sesgo apunta justo en esa direccion.

### 5.3 Que puede y que no puede este contraste

Es **parcial y sesgado por construccion**, igual que el de anden: cubre diez complejos y compara un reparto todo-o-nada contra uno observado que por definicion esta repartido. Un par que la ruta manda entero por una linea nunca va a reproducir un 60/40 observado. **Sirve para detectar que la asignacion mande flujo por la linea equivocada; no sirve para medir precision.** Y no es validacion del modelo de simulacion: es verificacion de una tabla precalculada.
