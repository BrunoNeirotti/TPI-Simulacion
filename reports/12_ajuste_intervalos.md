# Paso 12, Oferta del modelo: intervalos entre despachos y apertura

Generado por `src/12_ajuste_intervalos.py`. Salidas en `data/processed/`: `cabeceras_despacho.csv`, `apertura_formaciones.csv`, `intervalos_empiricos.csv` (lo que consume el modelo) y `distribuciones_despacho.csv` (ajuste teórico, de referencia). Figuras en `docs/figuras/ajuste-intervalos-*.png`.

## 1. Base

- formaciones-despachadas-2025.csv en Latin-1, 495,719 filas crudas, 24,696 vacias descartadas, 471,023 utiles, 0 con fecha invalida. Formatos de fecha -> d/m/aaaa: 75,535, dd/mm/aa: 395,488.
- **668.906 viajes prestados** en días hábiles típicos de 2025 (sin días parciales). Período: todo 2025; **depende de D4**, que sigue abierta.
- Un despacho desde cabecera es un viaje de **recorrido completo**. La columna `Km` da la distancia de cada viaje y la moda por línea es el recorrido completo. Los de recorrido parcial son formaciones que entran desde un punto intermedio: casi todos en la apertura. Fuera de ella son 2.792 viajes, menos del 1 % en cada hora entre las 6 y las 23 h, y se excluyen.
- **`Km` mezcla tres escrituras** (metros con punto de miles, metros sin separador y, en 2026, kilómetros con coma o redondeados). Se corrigió la lectura en `src/lib_despachos.py` (punto 7 de su encabezado); ningún paso anterior usaba la columna.

## 2. Qué cabecera es cada lado

El dataset llama **A** y **D** a los dos extremos de cada línea sin decir cuál es cuál, y `cabeceras-estaciones.csv` está desactualizado (la E todavía termina en Bolívar y la H en Las Heras). Se dedujo de los datos: una formación que arranca en la estación *i* recorre la distancia de *i* a la cabecera de destino, y eso solo coincide bajo una de las dos asignaciones.

| Línea | Lado | Sale de | Va a | Viajes de apertura | Error medio (km) | Con la otra asignación |
|---|---|---|---|---:|---:|---:|
| A | A | San Pedrito | Plaza de Mayo | 880 | 0,017 | 0,175 |
| A | D | Plaza de Mayo | San Pedrito | 836 | 0,017 | 0,137 |
| B | A | Juan Manuel de Rosas | Leandro N. Alem | 710 | 0,028 | 0,276 |
| B | D | Leandro N. Alem | Juan Manuel de Rosas | 712 | 0,022 | 0,253 |
| C | A | Constitucion | Retiro | 441 | 0,058 | 0,099 |
| C | D | Retiro | Constitucion | 185 | 0,066 | 0,176 |
| D | A | Congreso de Tucuman | Catedral | 860 | 0,043 | 0,106 |
| D | D | Catedral | Congreso de Tucuman | 752 | 0,024 | 0,272 |
| E | A | Retiro | Plaza de los Virreyes | 654 | 0,044 | 0,113 |
| E | D | Plaza de los Virreyes | Retiro | 839 | 0,029 | 0,129 |
| H | A | Facultad de Derecho | Hospitales | 624 | 0,074 | 0,146 |
| H | D | Hospitales | Facultad de Derecho | 440 | 0,046 | 0,139 |

En cinco líneas el lado A es la cabecera 1 de `cabeceras-estaciones.csv`. **En la E es al revés**: el lado A sale de Retiro. Por eso la correspondencia sale de los datos y no se supone. El error con la asignación elegida va de 17 a 74 m, contra 99 a 276 m con la otra. El caso menos marcado es el lado A de la C, pero el lado D de la misma línea, que tiene que ir en el otro sentido, es claro.

## 3. Apertura del servicio

La apertura es a las **5:30** en todas las líneas. Salen a la vez varias formaciones desde estaciones intermedias y cada una va hasta la cabecera de destino. **Decidido con el grupo el 21/09/2026 (D16): el modelo las ubica donde arrancan.** La configuración típica toma las *k* estaciones más frecuentes, con *k* el tamaño mediano del grupo de apertura.

| Línea | Lado | Hora | Días en esa hora | Formaciones (p10–p90) | Arrancan desde |
|---|---|---|---:|---|---|
| A | A | 05:30 | 100 % | 5 (5–5) | San Pedrito (96 %), Primera Junta (97 %), Loria (60 %), Pasco (100 %), Piedras (100 %) |
| A | D | 05:30 | 100 % | 5 (4–5) | Plaza de Mayo (99 %), Congreso (86 %), Loria (79 %), Rio de Janeiro (60 %), Carabobo (80 %) |
| B | A | 05:30 | 81 % | 5 (1–5) | Juan Manuel de Rosas (98 %), Federico Lacroze (67 %), Malabia (76 %), Medrano (66 %), Uruguay (42 %) |
| B | D | 05:30 | 81 % | 5 (1–5) | Leandro N. Alem (99 %), Carlos Pellegrini (67 %), Pueyrredon (67 %), angel Gallardo (66 %), Federico Lacroze (68 %) |
| C | A | 05:30 | 100 % | 3 (3–3) | Constitucion (97 %), Moreno (99 %), Lavalle (100 %) |
| C | D | 05:30 | 89 % | 2 (1–2) | Retiro (100 %), Avenida de Mayo (83 %) |
| D | A | 05:30 | 96 % | 5 (5–5) | Congreso de Tucuman (95 %), Ministro Carranza (96 %), Bulnes (94 %), Pueyrredon (96 %), 9 de Julio (96 %) |
| D | D | 05:30 | 95 % | 4 (4–5) | Catedral (95 %), Callao (95 %), Agüero (62 %), Plaza Italia (56 %) |
| E | A | 05:30 | 99 % | 4 (3–4) | Retiro (92 %), Belgrano (96 %), General Urquiza (99 %), Emilio Mitre (99 %) |
| E | D | 05:30 | 100 % | 5 (4–5) | Plaza de los Virreyes (81 %), Emilio Mitre (82 %), Boedo (82 %), Entre Rios (82 %), Bolivar (96 %) |
| H | A | 05:30 | 99 % | 4 (3–4) | Facultad de Derecho (98 %), Corrientes (99 %), Venezuela (82 %), Caseros (100 %) |
| H | D | 05:30 | 99 % | 3 (3–3) | Hospitales (98 %), Caseros (82 %), Humberto 1 (99 %) |

El porcentaje junto a cada estación es la fracción de días en que arranca una formación desde ahí. Las que quedan por debajo del 100 % muestran que la configuración cambia entre días (en la B hay dos que se alternan); se toma la típica y **se declara como supuesto**.

## 4. Intervalos entre despachos

**655.299 intervalos** entre despachos de recorrido completo, fuera de la apertura, sin despachos con causa registrada. El primer despacho regular se mide contra el último de la apertura.

### Cortes de servicio

Dentro de días hábiles típicos, sin causa registrada, hay intervalos de hasta 7 h: **180 de más de una hora**, a veces en los dos sentidos de la línea al mismo tiempo (la A el 18/12/2025, la D el 16/10/2025). Son cortes de servicio, no intervalos de operación. **Decidido con el grupo el 21/09/2026 (D18): se excluye el intervalo** si supera 5 veces la mediana de su celda, y se conserva el resto del día. Son **324 intervalos** (A 18, B 133, C 27, D 55, E 48, H 43). El modelo representa la operación normal, igual que al excluir los despachos con causa; los cortes se declaran y pueden ir como escenario aparte.

### 4.1 Ajuste teórico (procedimiento de la materia)

Se ajustaron 227 celdas (línea × lado × hora, de 5 a 23 h) con cinco familias por máxima verosimilitud, eligiendo por AIC.

| Familia | Celdas donde gana |
|---|---:|
| exponencial | 0 |
| gamma | 46 |
| lognormal | 175 |
| weibull | 0 |
| normal | 6 |

El coeficiente de variación tiene mediana **0,29**. La exponencial queda descartada de entrada: exige 1, y un servicio programado es mucho más regular que un proceso de Poisson.

Bondad de ajuste de la familia elegida, al 5 %: chi-cuadrado rechaza en **96,0 %** de las celdas y Kolmogorov-Smirnov en **77,5 %**. Con del orden de 3.066 intervalos por celda las dos pruebas rechazan cualquier distribución teórica frente a datos reales (Law, cap. 6), así que se mira además el **estadístico D de Kolmogorov-Smirnov**, que no depende de n: la máxima distancia entre la acumulada observada y la ajustada.

Sin la hora 5: D mediano **0,044**, y **39 de 215 celdas con D > 0,10**, de las cuales 30 son de la Línea H.

La H despacha con un horario muy rígido: en hora pico, la mitad de los intervalos cae en una franja de unos 15 s alrededor de 205 s. Además tiene **un segundo pico cerca de 290 s**. Esa forma bimodal no la reproduce ninguna familia unimodal; tampoco las versiones desplazadas de tres parámetros, que se probaron (en la H, cabecera D, 8 h, D baja de 0,233 a 0,208). Ver `docs/figuras/ajuste-intervalos-h-pico.png` contra `ajuste-intervalos-c-pico.png`.

#### Comparación de familias en hora pico, Líneas C y H

| Línea | Lado | Hora | Familia | AIC − mínimo | D de K-S |
|---|---|---:|---|---:|---:|
| C | A | 8 | lognormal | 0,0 | 0,100 |
| C | A | 8 | gamma | 288,3 | 0,113 |
| C | A | 8 | normal | 1.111,9 | 0,135 |
| C | A | 17 | lognormal | 0,0 | 0,095 |
| C | A | 17 | gamma | 340,7 | 0,105 |
| C | A | 17 | normal | 1.327,4 | 0,122 |
| C | D | 8 | lognormal | 0,0 | 0,037 |
| C | D | 8 | gamma | 128,8 | 0,053 |
| C | D | 8 | normal | 741,5 | 0,087 |
| C | D | 17 | lognormal | 0,0 | 0,048 |
| C | D | 17 | gamma | 204,6 | 0,065 |
| C | D | 17 | normal | 949,5 | 0,103 |
| H | A | 8 | lognormal | 0,0 | 0,142 |
| H | A | 8 | gamma | 329,1 | 0,157 |
| H | A | 8 | normal | 1.324,8 | 0,185 |
| H | A | 17 | lognormal | 0,0 | 0,124 |
| H | A | 17 | gamma | 243,8 | 0,139 |
| H | A | 17 | normal | 974,8 | 0,167 |
| H | D | 8 | lognormal | 0,0 | 0,231 |
| H | D | 8 | gamma | 346,3 | 0,243 |
| H | D | 8 | normal | 1.301,4 | 0,264 |
| H | D | 17 | lognormal | 0,0 | 0,164 |
| H | D | 17 | gamma | 219,2 | 0,178 |
| H | D | 17 | normal | 913,1 | 0,204 |

### 4.2 Lo que usa el modelo: la distribución empírica

**Decidido con el grupo el 21/09/2026 (D17): distribución empírica en todas las celdas.** Es la continua lineal por tramos de Law (cap. 6): una tabla de 501 cuantiles por celda (paso de 0,2 %), que el modelo muestrea por transformada inversa: `u = uniform()`, se interpola el cuantil. Reproduce la forma observada sin elegir familia; el costo es que no extrapola más allá del mínimo y el máximo observados en cada celda, que con miles de datos por celda no es una restricción práctica.

- Celdas con menos de 50 intervalos, que toman la hora vecina: E-A 23 h (n = 9, usa 22 h).
- **Verificación**: 100.000 valores muestreados de cada tabla contra los datos de su celda. D de Kolmogorov-Smirnov máximo **0,008**; diferencia de medias máxima 0,27 %.

| Línea | Lado | Hora | n | Media (s) | Mediana (s) | Coef. de variación |
|---|---|---:|---:|---:|---:|---:|
| A | A | 8 | 4.138 | 193,2 | 188 | 0,26 |
| A | A | 17 | 4.000 | 198,8 | 187 | 0,28 |
| A | D | 8 | 4.114 | 193,9 | 182 | 0,29 |
| A | D | 17 | 3.982 | 200,2 | 187 | 0,29 |
| B | A | 8 | 3.115 | 256,2 | 244 | 0,32 |
| B | A | 17 | 3.170 | 246,7 | 237 | 0,34 |
| B | D | 8 | 3.045 | 264,5 | 249 | 0,35 |
| B | D | 17 | 3.078 | 254,3 | 239 | 0,35 |
| C | A | 8 | 4.054 | 197,0 | 183 | 0,25 |
| C | A | 17 | 3.971 | 200,0 | 182 | 0,30 |
| C | D | 8 | 4.040 | 197,3 | 192 | 0,26 |
| C | D | 17 | 3.983 | 201,6 | 194 | 0,27 |
| D | A | 8 | 3.497 | 227,6 | 220 | 0,34 |
| D | A | 17 | 3.469 | 228,5 | 221 | 0,29 |
| D | D | 8 | 3.444 | 229,1 | 221 | 0,33 |
| D | D | 17 | 3.539 | 223,8 | 219 | 0,33 |
| E | A | 8 | 2.411 | 330,3 | 319 | 0,32 |
| E | A | 17 | 2.397 | 329,0 | 314 | 0,32 |
| E | D | 8 | 2.360 | 333,6 | 308 | 0,44 |
| E | D | 17 | 2.365 | 332,2 | 309 | 0,36 |
| H | A | 8 | 3.697 | 217,2 | 206 | 0,23 |
| H | A | 17 | 3.760 | 217,5 | 206 | 0,22 |
| H | D | 8 | 3.720 | 217,4 | 206 | 0,20 |
| H | D | 17 | 3.728 | 217,2 | 206 | 0,21 |

## 5. Lo que este paso no resuelve

- **Los intervalos consecutivos no son independientes**: un despacho atrasado acorta el siguiente. Muestrear intervalos independientes pierde esa correlación. Se ve en la verificación del modelo.
- **La configuración de apertura es la típica**, no la de cada día.
- **El período depende de D4.**
- **Las formaciones que se retiran al final del servicio** (horas 0 y 1, con recorrido parcial) quedan fuera: el modelo corta a las 24 h.
