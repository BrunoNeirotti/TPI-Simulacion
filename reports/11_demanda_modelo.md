# Paso 11: La matriz de demanda del modelo

Quedo decidido el 27/08/2026: **la matriz de SBASE es la base y la del paso 5 
aporta el perfil horario**. Este es el armado y sus controles.


## 1. De donde sale cada pieza

| Pieza | Fuente | Por que |
|---|---|---|
| Nivel y distribucion espacial | Matriz diaria de SBASE | Viene expandida: no 
hay escalado que decidir, y no tiene el defecto de San Pedrito / San Jose de Flores |
| Horas 8-9 y 17-18 | Matrices HPM y HPT de SBASE | Direccionalidad **medida**, 
no impuesta por simetria diaria |
| Resto del dia | Perfil horario por par del paso 5 | Es la unica fuente con 
apertura horaria completa |
| Bloques de 15 min | Molinetes, dias habiles tipicos (paso 3) | Unica fuente con 
resolucion intrahoraria; entra solo como forma, no como nivel |


## 2. Que salio

- **827.289 viajes** en el dia habil, sobre 
  5.839 pares de 
  complejos y 71.686 celdas de (par, hora).
- Perfil intrahorario: 6.140 filas de (complejo, hora, bloque).
- **El total cierra con la matriz diaria de SBASE**: diferencia de 0,000000 
  viajes, que es error de redondeo de punto flotante.
- **La hora pico mañana reproduce exactamente la matriz de SBASE**: 
  74.323 viajes contra 74.323.
- **La hora pico tarde reproduce exactamente la matriz de SBASE**: 
  80.132 viajes contra 80.132.
- 44 pares no tienen perfil horario en el paso 5 y 
  9 lo tienen concentrado enteramente en las 
  dos horas pico. Los dos casos usan el perfil horario de la red como respaldo. 
  Son el 0,2 % de los viajes.


## 3. Perfil horario resultante

| Hora | Viajes | Share | Origen del valor |
|---:|---:|---:|---|
| 05 | 4.179 | 0,5 % | paso 5, reescalado |
| 06 | 25.317 | 3,1 % | paso 5, reescalado |
| 07 | 68.757 | 8,3 % | paso 5, reescalado |
| 08 | 74.323 | 9,0 % | **SBASE, medido** |
| 09 | 62.750 | 7,6 % | paso 5, reescalado |
| 10 | 41.310 | 5,0 % | paso 5, reescalado |
| 11 | 41.715 | 5,0 % | paso 5, reescalado |
| 12 | 49.944 | 6,0 % | paso 5, reescalado |
| 13 | 53.514 | 6,5 % | paso 5, reescalado |
| 14 | 45.884 | 5,5 % | paso 5, reescalado |
| 15 | 51.788 | 6,3 % | paso 5, reescalado |
| 16 | 63.831 | 7,7 % | paso 5, reescalado |
| 17 | 80.132 | 9,7 % | **SBASE, medido** |
| 18 | 67.958 | 8,2 % | paso 5, reescalado |
| 19 | 38.155 | 4,6 % | paso 5, reescalado |
| 20 | 27.502 | 3,3 % | paso 5, reescalado |
| 21 | 18.979 | 2,3 % | paso 5, reescalado |
| 22 | 9.932 | 1,2 % | paso 5, reescalado |
| 23 | 1.318 | 0,2 % | paso 5, reescalado |


La hora mas cargada concentra el **9,7 %** de la demanda diaria, 
consistente con el 9,9 % que el paso 3 midio sobre molinetes y con el 9,0 % y 
9,7 % que dan las matrices de SBASE por separado. **El armado no introdujo un 
perfil que ninguna fuente respalde**, que era el riesgo de mezclar dos matrices.


## 4. Que queda como supuesto propio

El supuesto central del trabajo **cambio de lugar**. Antes era el criterio de 
escalado de la matriz a los niveles de molinetes, que afectaba el nivel de toda 
la demanda. Ahora es la **desagregacion temporal fuera de las dos horas pico**: 
el nivel diario y las dos horas criticas son dato medido, y lo que se supone es 
como se reparte el resto del dia. Es un supuesto mas chico, y ademas afecta 
justamente las horas en las que la red no esta al limite.


Es lo que el analisis de sensibilidad tiene que recorrer. Tres variantes 
naturales, todas baratas porque el pipeline ya esta armado:

1. Perfil horario del paso 5 por par O-D, que es la version base.
2. Perfil horario **de la red**, igual para todos los pares: mide cuanto aporta 
   tener perfil propio por par.
3. Perfil horario **por complejo de origen** tomado de molinetes, que es una 
   fuente independiente del paso 5.


## 5. Lo que este paso no arregla

- **La matriz sigue siendo de un dia habil.** Sabado y domingo no tienen matriz 
  O-D de SBASE; si el modelo los necesita, hay que escalar con molinetes y 
  declararlo.
- **Los 687 viajes diarios entre nodos de un mismo complejo quedan afuera.** En 
  el modelo son una caminata dentro de la estacion.
- **La matriz es de septiembre de 2024.** No describe la red de 2026.
- **Lo de las etapas incompletas sigue sin decidirse**, y este paso lo deja listo para medirse: el perfil 
  horario usa la columna `expandidas`, y correrlo con `expandidas_completas` es 
  cambiar una constante.
