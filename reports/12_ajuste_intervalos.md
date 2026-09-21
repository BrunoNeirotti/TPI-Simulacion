# Paso 12, Oferta del modelo: intervalos entre despachos y apertura

Generado por `src/12_ajuste_intervalos.py`. Salidas en `data/processed/`: `cabeceras_despacho.csv`, `apertura_formaciones.csv`, `intervalos_empiricos.csv` (lo que consume el modelo) y `distribuciones_despacho.csv` (ajuste teórico, de referencia). Figuras en `docs/figuras/ajuste-intervalos-*.png`.

## 1. Base

- formaciones-despachadas-2025.csv en Latin-1, 495,719 filas crudas, 24,696 vacias descartadas, 471,023 utiles, 0 con fecha invalida. Formatos de fecha -> d/m/aaaa: 75,535, dd/mm/aa: 395,488.
- **326.529 viajes prestados** en días hábiles típicos de 2025 (sin días parciales). Período: 2025-07-01 a 2025-12-31 (D4, opción A: el régimen vigente, sin horario de verano; ver `docs/preparacion-d4.md`). Los días con cancelaciones gremiales se excluyen solo de la línea afectada.
- Un despacho desde cabecera es un viaje de **recorrido completo**. La columna `Km` da la distancia de cada viaje y la moda por línea es el recorrido completo. Los de recorrido parcial son formaciones que entran desde un punto intermedio: casi todos en la apertura. Fuera de ella son 1.539 viajes, menos del 1 % en cada hora entre las 6 y las 23 h, y se excluyen.
- **`Km` mezcla tres escrituras** (metros con punto de miles, metros sin separador y, en 2026, kilómetros con coma o redondeados). Se corrigió la lectura en `src/lib_despachos.py` (punto 7 de su encabezado); ningún paso anterior usaba la columna.

## 2. Qué cabecera es cada lado

El dataset llama **A** y **D** a los dos extremos de cada línea sin decir cuál es cuál, y `cabeceras-estaciones.csv` está desactualizado (la E todavía termina en Bolívar y la H en Las Heras). Se dedujo de los datos: una formación que arranca en la estación *i* recorre la distancia de *i* a la cabecera de destino, y eso solo coincide bajo una de las dos asignaciones.

| Línea | Lado | Sale de | Va a | Viajes de apertura | Error medio (km) | Con la otra asignación |
|---|---|---|---|---:|---:|---:|
| A | A | San Pedrito | Plaza de Mayo | 449 | 0,018 | 0,172 |
| A | D | Plaza de Mayo | San Pedrito | 449 | 0,020 | 0,128 |
| B | A | Juan Manuel de Rosas | Leandro N. Alem | 216 | 0,029 | 0,282 |
| B | D | Leandro N. Alem | Juan Manuel de Rosas | 215 | 0,019 | 0,246 |
| C | A | Constitucion | Retiro | 200 | 0,059 | 0,098 |
| C | D | Retiro | Constitucion | 100 | 0,066 | 0,176 |
| D | A | Congreso de Tucuman | Catedral | 449 | 0,044 | 0,106 |
| D | D | Catedral | Congreso de Tucuman | 437 | 0,023 | 0,255 |
| E | A | Retiro | Plaza de los Virreyes | 347 | 0,044 | 0,114 |
| E | D | Plaza de los Virreyes | Retiro | 468 | 0,029 | 0,111 |
| H | A | Facultad de Derecho | Hospitales | 321 | 0,075 | 0,138 |
| H | D | Hospitales | Facultad de Derecho | 211 | 0,036 | 0,142 |

En cinco líneas el lado A es la cabecera 1 de `cabeceras-estaciones.csv`. **En la E es al revés**: el lado A sale de Retiro. Por eso la correspondencia sale de los datos y no se supone. El error con la asignación elegida va de 18 a 75 m, contra 98 a 282 m con la otra. El caso menos marcado es el lado A de la C, pero el lado D de la misma línea, que tiene que ir en el otro sentido, es claro.

## 3. Apertura del servicio

La apertura es a las **5:30** en todas las líneas. Salen a la vez varias formaciones desde estaciones intermedias y cada una va hasta la cabecera de destino. **Decidido con el grupo el 21/09/2026 (D16): el modelo las ubica donde arrancan.** La configuración típica toma las *k* estaciones más frecuentes, con *k* el tamaño mediano del grupo de apertura.

| Línea | Lado | Hora | Días en esa hora | Formaciones (p10–p90) | Arrancan desde |
|---|---|---|---:|---|---|
| A | A | 05:30 | 100 % | 5 (5–5) | San Pedrito (97 %), Primera Junta (96 %), Loria (66 %), Pasco (100 %), Piedras (100 %) |
| A | D | 05:30 | 100 % | 5 (5–5) | Plaza de Mayo (98 %), Congreso (76 %), Loria (66 %), Rio de Janeiro (66 %), Carabobo (100 %) |
| B | A | 05:30 | 77 % | 5 (1–5) | Juan Manuel de Rosas (99 %), Federico Lacroze (77 %), Malabia (73 %), Medrano (77 %), Uruguay (40 %) |
| B | D | 05:30 | 77 % | 5 (1–5) | Leandro N. Alem (100 %), Carlos Pellegrini (77 %), Pueyrredon (76 %), angel Gallardo (77 %), Federico Lacroze (77 %) |
| C | A | 05:30 | 100 % | 3 (3–3) | Constitucion (98 %), Moreno (100 %), Lavalle (100 %) |
| C | D | 05:30 | 99 % | 2 (2–2) | Retiro (100 %), Avenida de Mayo (100 %) |
| D | A | 05:30 | 96 % | 5 (5–5) | Congreso de Tucuman (94 %), Ministro Carranza (96 %), Bulnes (96 %), Pueyrredon (96 %), 9 de Julio (96 %) |
| D | D | 05:30 | 95 % | 5 (4–5) | Catedral (94 %), Callao (93 %), Bulnes (61 %), Palermo (67 %), Jose Hernandez (88 %) |
| E | A | 05:30 | 97 % | 4 (3–4) | Retiro (92 %), Belgrano (98 %), General Urquiza (98 %), Emilio Mitre (99 %) |
| E | D | 05:30 | 99 % | 5 (4–5) | Plaza de los Virreyes (77 %), Emilio Mitre (100 %), Boedo (100 %), Entre Rios (99 %), Bolivar (97 %) |
| H | A | 05:30 | 99 % | 4 (4–4) | Facultad de Derecho (98 %), Corrientes (99 %), Venezuela (99 %), Caseros (99 %) |
| H | D | 05:30 | 97 % | 3 (3–3) | Hospitales (97 %), Caseros (98 %), Humberto 1 (97 %) |

El porcentaje junto a cada estación es la fracción de días en que arranca una formación desde ahí. Las que quedan por debajo del 100 % muestran que la configuración cambia entre días (en la B hay dos que se alternan); se toma la típica y **se declara como supuesto**.

## 4. Intervalos entre despachos

**319.792 intervalos** entre despachos de recorrido completo, fuera de la apertura, sin despachos con causa registrada. El primer despacho regular se mide contra el último de la apertura.

### Cortes de servicio

Dentro de días hábiles típicos, sin causa registrada, hay intervalos de hasta 7 h: **72 de más de una hora**, a veces en los dos sentidos de la línea al mismo tiempo (la A el 18/12/2025, la D el 16/10/2025). Son cortes de servicio, no intervalos de operación. **Decidido con el grupo el 21/09/2026 (D18): se excluye el intervalo** si supera 5 veces la mediana de su celda, y se conserva el resto del día. Son **144 intervalos** (A 11, B 48, C 11, D 38, E 22, H 14). El modelo representa la operación normal, igual que al excluir los despachos con causa; los cortes se declaran y pueden ir como escenario aparte.

### 4.1 Ajuste teórico (procedimiento de la materia)

Se ajustaron 227 celdas (línea × lado × hora, de 5 a 23 h) con cinco familias por máxima verosimilitud, eligiendo por AIC.

| Familia | Celdas donde gana |
|---|---:|
| exponencial | 0 |
| gamma | 38 |
| lognormal | 181 |
| weibull | 2 |
| normal | 6 |

El coeficiente de variación tiene mediana **0,28**. La exponencial queda descartada de entrada: exige 1, y un servicio programado es mucho más regular que un proceso de Poisson.

Bondad de ajuste de la familia elegida, al 5 %: chi-cuadrado rechaza en **85,5 %** de las celdas y Kolmogorov-Smirnov en **68,7 %**. Con del orden de 1.379 intervalos por celda las dos pruebas rechazan cualquier distribución teórica frente a datos reales (Law, cap. 6), así que se mira además el **estadístico D de Kolmogorov-Smirnov**, que no depende de n: la máxima distancia entre la acumulada observada y la ajustada.

Sin la hora 5: D mediano **0,049**, y **40 de 215 celdas con D > 0,10**, de las cuales 26 son de la Línea H.

La H despacha con un horario muy rígido: en hora pico, la mitad de los intervalos cae en una franja de unos 15 s alrededor de 205 s. Además tiene **un segundo pico cerca de 290 s**. Esa forma bimodal no la reproduce ninguna familia unimodal; tampoco las versiones desplazadas de tres parámetros, que se probaron (en la H, cabecera D, 8 h, D baja de 0,233 a 0,208). Ver `docs/figuras/ajuste-intervalos-h-pico.png` contra `ajuste-intervalos-c-pico.png`.

#### Comparación de familias en hora pico, Líneas C y H

| Línea | Lado | Hora | Familia | AIC − mínimo | D de K-S |
|---|---|---:|---|---:|---:|
| C | A | 8 | lognormal | 0,0 | 0,116 |
| C | A | 8 | gamma | 98,6 | 0,128 |
| C | A | 8 | normal | 389,3 | 0,149 |
| C | A | 17 | lognormal | 0,0 | 0,099 |
| C | A | 17 | gamma | 155,4 | 0,106 |
| C | A | 17 | normal | 589,9 | 0,126 |
| C | D | 8 | lognormal | 0,0 | 0,042 |
| C | D | 8 | gamma | 53,2 | 0,048 |
| C | D | 8 | normal | 330,0 | 0,082 |
| C | D | 17 | lognormal | 0,0 | 0,051 |
| C | D | 17 | gamma | 92,7 | 0,065 |
| C | D | 17 | normal | 441,9 | 0,099 |
| H | A | 8 | lognormal | 0,0 | 0,111 |
| H | A | 8 | gamma | 101,4 | 0,123 |
| H | A | 8 | normal | 433,5 | 0,148 |
| H | A | 17 | lognormal | 0,0 | 0,093 |
| H | A | 17 | gamma | 110,2 | 0,106 |
| H | A | 17 | normal | 491,9 | 0,135 |
| H | D | 8 | lognormal | 0,0 | 0,184 |
| H | D | 8 | gamma | 146,3 | 0,196 |
| H | D | 8 | normal | 583,0 | 0,223 |
| H | D | 17 | lognormal | 0,0 | 0,128 |
| H | D | 17 | gamma | 54,0 | 0,138 |
| H | D | 17 | normal | 334,7 | 0,163 |

### 4.2 Lo que usa el modelo: la distribución empírica

**Decidido con el grupo el 21/09/2026 (D17): distribución empírica en todas las celdas.** Es la continua lineal por tramos de Law (cap. 6): una tabla de 501 cuantiles por celda (paso de 0,2 %), que el modelo muestrea por transformada inversa: `u = uniform()`, se interpola el cuantil. Reproduce la forma observada sin elegir familia; el costo es que no extrapola más allá del mínimo y el máximo observados en cada celda, que con miles de datos por celda no es una restricción práctica.

- Celdas con menos de 50 intervalos, que toman la hora vecina: E-A 23 h (n = 6, usa 22 h).
- **Verificación**: 100.000 valores muestreados de cada tabla contra los datos de su celda. D de Kolmogorov-Smirnov máximo **0,012**; diferencia de medias máxima 0,31 %.

| Línea | Lado | Hora | n | Media (s) | Mediana (s) | Coef. de variación |
|---|---|---:|---:|---:|---:|---:|
| A | A | 8 | 2.157 | 187,6 | 182 | 0,25 |
| A | A | 17 | 2.084 | 192,9 | 181 | 0,28 |
| A | D | 8 | 2.148 | 188,5 | 173 | 0,29 |
| A | D | 17 | 2.069 | 194,9 | 181 | 0,30 |
| B | A | 8 | 1.023 | 244,1 | 237 | 0,29 |
| B | A | 17 | 1.036 | 236,8 | 228 | 0,34 |
| B | D | 8 | 1.011 | 249,0 | 235 | 0,32 |
| B | D | 17 | 1.001 | 244,7 | 230 | 0,33 |
| C | A | 8 | 1.872 | 191,6 | 177 | 0,23 |
| C | A | 17 | 1.827 | 194,8 | 179 | 0,28 |
| C | D | 8 | 1.874 | 192,2 | 189 | 0,26 |
| C | D | 17 | 1.834 | 197,4 | 194 | 0,25 |
| D | A | 8 | 1.970 | 210,6 | 199 | 0,33 |
| D | A | 17 | 1.968 | 209,8 | 198 | 0,29 |
| D | D | 8 | 1.918 | 214,7 | 202 | 0,34 |
| D | D | 17 | 2.025 | 204,9 | 192 | 0,34 |
| E | A | 8 | 1.342 | 314,8 | 307 | 0,29 |
| E | A | 17 | 1.317 | 317,7 | 305 | 0,31 |
| E | D | 8 | 1.327 | 318,1 | 293 | 0,45 |
| E | D | 17 | 1.306 | 317,2 | 296 | 0,35 |
| H | A | 8 | 1.910 | 206,2 | 205 | 0,16 |
| H | A | 17 | 1.925 | 205,9 | 204 | 0,17 |
| H | D | 8 | 1.924 | 206,7 | 205 | 0,14 |
| H | D | 17 | 1.933 | 205,7 | 205 | 0,16 |

## 5. Vuelta en cabecera y flota de la Línea F

D14 dejó pendiente verificar que la flota de la Línea F alcanza para cada intervalo del escenario (D7: de 90 a 189 s). Con despachos independientes por cabecera el modelo no lo impone, así que se verifica aparte.

**La vuelta en cabecera se mide en las líneas actuales.** Cada fila del dataset es una formación que sale de A y después de D (así en 100 % de las filas), de modo que la diferencia entre sus dos salidas es el viaje de A a D más la vuelta en D. Restando el tiempo de viaje del GTFS queda la vuelta **más el desvío del viaje real respecto del programado**: es una cota superior de la maniobra.

| Línea | Viaje GTFS (s) | Vuelta en pico, mediana (p10–p90) | Vuelta en valle, mediana |
|---|---:|---|---:|
| A | 1.529 | 170 s (67–306) | 116 s |
| B | 1.587 | 430 s (279–660) | 408 s |
| C | 751 | 72 s (7–161) | 103 s |
| D | 1.527 | 314 s (192–537) | 382 s |
| E | 1.720 | 277 s (160–452) | 254 s |
| H | 1.112 | 105 s (68–200) | 107 s |

**Intervalo mínimo que sostienen 25 formaciones** en la Línea F, con 18 min de viaje por sentido: `(2 × 1080 + 2 × vuelta) / 25`, tomando como vuelta la mediana en pico de cada línea actual.

| Vuelta como la de la línea | Vuelta (s) | Intervalo mínimo (s) |
|---|---:|---:|
| C | 72 | 92,2 |
| H | 105 | 94,8 |
| A | 170 | 100,0 |
| E | 277 | 108,6 |
| D | 314 | 111,5 |
| B | 430 | 120,8 |

**Para sostener 90 s la vuelta tiene que ser de 45 s o menos por cabecera**, y ninguna línea actual lo logra en mediana; la más rápida, la C, da 92,2 s. Las fuentes oficiales son consistentes con esto: el EsIA da 25 formaciones y 90 s, o sea un ciclo de 37,5 min, y con los 18 min de viaje que informa el Ministerio eso deja justo 45 s de vuelta por cabecera. Y los 100 s *"de requerirse"* del mismo Ministerio corresponden a una vuelta como la de la A.

No cambia la decisión D7, que recorre de 90 a 189 s porque son los valores de diseño y el plan de servicio no existe. Pero **el extremo de 90 s supone una maniobra en cabecera más rápida que cualquiera de la red actual**, o una flota mayor que la declarada, y eso hay que decirlo al informar los resultados de ese extremo.

## 6. Ventana de verificación de la oferta (D4)

La oferta se ajusta con 2025-07-01 a 2025-12-31 y se verifica contra 2026-03-01 a 2026-05-31, que no se usa para ajustar. Mismos filtros en las dos (día hábil, sin días parciales, sin la línea en días con cancelaciones gremiales). Cuando el modelo corra, los despachos simulados se comparan contra la columna de verificación; la biblioteca ya lo hace contra la de ajuste.

| Línea | Lado | Días (ajuste / verif.) | Despachos por día, ajuste | Verificación | Intervalo en pico, ajuste (s) | Verificación (s) |
|---|---|---|---:|---:|---:|---:|
| A | A | 113 / 56 | 289,7 | 295,0 | 191,8 | 189,0 |
| A | D | 113 / 56 | 294,6 | 299,8 | 198,6 | 197,5 |
| B | A | 70 / 32 | 238,9 | 248,3 | 245,3 | 235,8 |
| B | D | 70 / 32 | 243,5 | 253,0 | 253,0 | 243,0 |
| C | A | 100 / 57 | 284,0 | 281,7 | 194,1 | 196,7 |
| C | D | 100 / 57 | 286,6 | 284,1 | 195,1 | 197,1 |
| D | A | 116 / 58 | 258,0 | 264,9 | 217,0 | 212,3 |
| D | D | 116 / 58 | 263,4 | 269,3 | 218,4 | 214,3 |
| E | A | 118 / 56 | 181,0 | 183,8 | 315,9 | 312,2 |
| E | D | 118 / 56 | 184,6 | 187,7 | 324,2 | 318,9 |
| H | A | 108 / 56 | 278,8 | 279,9 | 206,3 | 206,1 |
| H | D | 108 / 56 | 282,7 | 283,7 | 206,7 | 206,1 |

El intervalo en hora pico difiere entre ventanas a lo sumo 4,0 % (mediana 1,4 %).

## 7. Lo que este paso no resuelve

- **Los intervalos consecutivos no son independientes**: un despacho atrasado acorta el siguiente. Muestrear intervalos independientes pierde esa correlación. Se ve en la verificación del modelo.
- **La configuración de apertura es la típica**, no la de cada día.
- **La Línea D en septiembre de 2024** (el mes de la demanda de SBASE) despachaba unos 280 s en pico contra unos 218 s de la ventana de ajuste. D4 prevé una sensibilidad del escenario base con esa oferta; requiere leer los despachos de 2024, que tienen otro esquema.
- **Las formaciones que se retiran al final del servicio** (horas 0 y 1, con recorrido parcial) quedan fuera: el modelo corta a las 24 h.
