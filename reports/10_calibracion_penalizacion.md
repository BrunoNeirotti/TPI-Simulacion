# Paso 10 — Calibracion de la penalizacion por transbordo (D9)

El paso 6 fijo la penalizacion en **120 s** por un argumento indirecto: en hora 
pico los intervalos entre despachos van de 3,15 a 5,22 min, asi que la espera 
esperada —la mitad del intervalo— cae entre 95 y 157 s. Era un supuesto sin nada 
contra que medirse. Los perfiles de carga que entrego SBASE (paso 9) dan por 
primera vez un observado por tramo, y con eso el valor se puede elegir midiendo.


## 1. Criterio, fijado antes de correr

- Penalizacion recorrida de 0 a 300 s de a 10 s.
- Metrica: error absoluto ponderado (WAPE) de la carga por tramo, con la matriz 
  de **hora pico manana** de SBASE cargada sobre el grafo por asignacion 
  todo-o-nada.
- **Se calibra con la manana y se valida con la tarde.** La hora pico tarde no 
  participa de la eleccion: es la muestra de reserva. Sin esa particion el 
  contraste del paso 9 dejaria de ser validacion y pasaria a ser verificacion 
  circular, que es el mismo problema que ya obligo a reclasificar el contraste de 
  intervalos en el paso 4.
- El reparto por linea de ascenso y la tasa de transbordo se informan como 
  control y **no entran en el criterio**.


## 2. La curva

| Penalizacion | WAPE HPM (calibracion) | WAPE HPT (reserva) | Error medio de reparto | Transbordos medios | Retiro por la C |
|---:|---:|---:|---:|---:|---:|
| 0 s | 9,17 % | 11,26 % | 12,07 % | 0,517 | 29,4 % |
| 10 s | 9,11 % | 11,24 % | 12,25 % | 0,516 | 29,4 % |
| 20 s | 9,11 % | 11,18 % | 12,06 % | 0,515 | 31,4 % |
| 30 s min HPM | 6,29 % | 8,68 % | 9,00 % | 0,491 | 65,7 % |
| 40 s | 6,32 % | 8,72 % | 8,99 % | 0,489 | 65,7 % |
| 50 s | 6,34 % | 8,66 % | 8,99 % | 0,487 | 65,7 % |
| 60 s | 6,48 % | 8,62 % | 8,92 % | 0,483 | 65,7 % |
| 70 s | 6,52 % | 8,49 % | 7,14 % | 0,476 | 65,7 % |
| 80 s | 6,50 % | 8,47 % | 7,14 % | 0,475 | 65,7 % |
| 90 s | 6,53 % | 8,41 % | 7,14 % | 0,456 | 65,7 % |
| 100 s | 6,53 % | 8,41 % | 7,23 % | 0,436 | 65,7 % |
| 110 s | 6,53 % | 8,41 % | 7,23 % | 0,436 | 65,7 % |
| 120 s **elegida** | 6,54 % | 8,40 % | 7,23 % | 0,435 | 65,7 % |
| 130 s | 6,51 % | 8,39 % | 7,23 % | 0,435 | 65,7 % |
| 140 s | 6,49 % | 8,39 % | 7,19 % | 0,433 | 65,7 % |
| 150 s | 6,41 % | 8,35 % | 7,19 % | 0,432 | 65,7 % |
| 160 s | 6,41 % | 8,35 % | 7,19 % | 0,432 | 65,7 % |
| 170 s | 6,41 % | 8,30 % | 7,19 % | 0,432 | 65,7 % |
| 180 s | 6,41 % | 8,31 % | 7,19 % | 0,431 | 65,7 % |
| 190 s | 6,32 % | 8,25 % | 7,19 % | 0,430 | 65,7 % |
| 200 s | 6,32 % | 8,24 % | 7,15 % | 0,430 | 65,7 % |
| 210 s | 6,32 % | 8,18 % | 7,15 % | 0,430 | 65,7 % |
| 220 s | 6,32 % | 8,18 % | 7,15 % | 0,430 | 65,7 % |
| 230 s | 6,37 % | 8,18 % | 7,15 % | 0,429 | 65,7 % |
| 240 s | 6,49 % | 8,19 % | 7,15 % | 0,427 | 65,7 % |
| 250 s | 6,49 % | 8,19 % | 7,15 % | 0,427 | 65,7 % |
| 260 s | 6,51 % | 8,18 % | 7,15 % | 0,426 | 65,7 % |
| 270 s min HPT | 6,51 % | 8,16 % | 7,15 % | 0,425 | 65,7 % |
| 280 s | 6,51 % | 8,16 % | 7,15 % | 0,425 | 65,7 % |
| 290 s | 6,51 % | 8,16 % | 7,15 % | 0,425 | 65,7 % |
| 300 s | 6,51 % | 8,16 % | 7,15 % | 0,425 | 65,7 % |


## 3. El dato no identifica el parametro

El criterio pre-registrado apunta a **30 s**, con un WAPE de 
6,29 % en la hora pico manana. Hay tres razones para no tomarlo, 
y las tres salen de la misma tabla:

1. **La curva es plana.** Entre 30 y 300 s el WAPE de calibracion se mueve entre 
   6,29 % y 6,54 %: una amplitud 
   de 0,26 % sobre un error del 
   orden del 6,5 %. Todo ese rango es indistinguible.
2. **Las dos muestras apuntan a extremos opuestos.** La calibracion elige 
   30 s y la reserva elige 270 s (8,16 %). 
   Cuando dos muestras del mismo fenomeno se van a los dos extremos de un rango 
   plano, lo que dicen es que **no identifican el parametro**, no que el optimo 
   sea el minimo de una de las dos.
3. **El control independiente empeora en el minimo.** En 30 s el error 
   medio de reparto por linea es 9,00 % contra 
   7,23 % en 120 s. Tomar el argmin mejoraria 
   0,26 pp la muestra de calibracion empeorando casi dos puntos un control que no 
   participa del ajuste. Eso es sobreajuste, no calibracion.


### Lo que el dato si dice: una cota inferior dura

Por debajo de 30 s el modelo se rompe. Con penalizacion cero el WAPE salta a 
9,17 % y el reparto del complejo Retiro por la Linea C cae a 
29,4 % contra el 86,0 % observado: sin costo de transbordo la 
asignacion manda gente a combinar por caminos que nadie usa. **El salto entre 20 
y 30 s es el unico rasgo nitido de toda la curva.**


## 4. Decision

**Se conserva la penalizacion de 120 s**, ahora con fundamento en vez de 
por defecto:

- cae dentro de la zona plana, donde el observado no discrimina;
- esta muy por encima de la cota inferior de 30 s, que es lo unico que el dato fija;
- coincide con el argumento fisico del paso 6, que es la mitad del intervalo 
  medido en hora pico (95–157 s), y ese argumento es el que corresponde usar 
  cuando el ajuste no discrimina.

Rinde 6,54 % de WAPE en calibracion y 8,40 % fuera 
de muestra. **No se reescribe `caminos_minimos.csv`**: la tabla del paso 6 ya 
estaba calculada con este valor y queda vigente tal cual.


**Lo que cambia no es el numero sino su estatus.** Deja de ser un supuesto 
declarado y pasa a ser un parametro cuyo rango admisible se midio, con la 
salvedad —que hay que escribir en el informe— de que **el indicador central es 
poco sensible a el**. Eso es un resultado, no una limitacion: significa que la 
carga por tramo que produzca el modelo no depende de la parte mas discutible de 
la asignacion.


## 5. Retiro no se arregla con esto

El reparto de ascensos del complejo Retiro por la Linea C va de 
29,4 % a 65,7 % en todo el rango 
recorrido, contra **86,0 % que mide SBASE**, 85,5 % de molinetes y 83,9 % de 
`linea_etapa`. **Ninguna penalizacion llega al valor observado**, asi que la 
discrepancia no es del valor del parametro.


(El 65,7 % de esta tabla no contradice el 69,8 % del paso 6: aquel reparto se 
pondera con la matriz del paso 5 y este con la de SBASE. La conclusion es la 
misma con las dos.)


Queda declarada como **error residual del modelo**, no como discrepancia entre 
fuentes ni como consecuencia de un supuesto mal elegido. La explicacion mas 
probable sigue siendo geometrica: Retiro [C] y Retiro [E] estan a 151 m y el 
grafo trata ese transbordo como cualquier otro. **No se corrige a mano**: ajustar 
el costo de ese transbordo hasta reproducir el 86 % seria calibrar un parametro 
contra el mismo dato que despues se usa para validar.


## 6. Que queda declarado

- La penalizacion **ya no es un supuesto ciego**: se midio su rango admisible con 
  criterio fijado de antemano y con muestra de reserva.
- **El dato no la identifica** por encima de 30 s. Se informa el rango, no un 
  valor finamente determinado.
- **El contraste de carga en hora pico manana pasa a ser calibracion**, no 
  validacion. La validacion es la hora pico tarde.
- **Retiro sigue mal** y queda como limitacion del modelo.
