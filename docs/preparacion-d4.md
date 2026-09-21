# Preparación de D4: períodos de ajuste y validación

> **Decidida el 21/09/2026: opción A**, con los dos agregados de la recomendación. Ver
> `decisiones.md`. Lo que sigue es el documento con que se decidió.

Documento de trabajo del 21/09/2026. **No decide D4**: ordena qué depende del período
elegido, mide las ventanas candidatas y deja opciones con sus consecuencias para que el
grupo elija. Cuando se elija, se registra en `decisiones.md` y se aplica en
`FILTRO_FECHAS` de `src/12_ajuste_intervalos.py`.

---

## 1. Qué cambió desde que se abrió D4

D4 se planteó cuando el modelo iba a ajustarse con molinetes y despachos de un período y
validarse con otro. Tres decisiones posteriores cambiaron la pregunta:

- **D2** (27/08/2026): la demanda del modelo es la matriz de SBASE, un **día hábil de
  septiembre de 2024**. El nivel y la distribución espacial de la demanda no dependen
  del período que se elija.
- **D9** (27/08/2026): la carga por tramo de SBASE en hora pico mañana pasó a ser
  **calibración** y la de hora pico tarde, **validación**. Las dos son del mismo día de
  septiembre de 2024.
- **D3** (16/09/2026): la calibración a fondo es solo del corredor A, C, D y H.

O sea que **la validación principal del modelo ya tiene fecha fija**, septiembre de 2024,
y no la elige D4. Lo que D4 todavía decide es otra cosa.

## 2. Qué depende del período y qué no

| Insumo o contraste | Fuente | ¿Depende de D4? |
|---|---|---|
| Nivel y reparto espacial de la demanda | Matriz SBASE, sept. 2024 | No |
| Perfil horario fuera de las horas pico | Viajes y etapas, 16/10/2024 (paso 5) | No |
| Calibración (hora pico mañana) y validación (hora pico tarde) de la carga | Perfiles SBASE, sept. 2024 | No |
| **Intervalos entre despachos** (D17) | Despachos 2025, paso 12 | **Sí**: `FILTRO_FECHAS` |
| **Apertura y última salida** (D16) | Despachos 2025, paso 12 | **Sí**, el mismo filtro |
| **Forma de cada hora en bloques de 15 min** | Molinetes 2025, días hábiles típicos (paso 3) | **Sí**, pero solo como forma dentro de la hora |
| Verificación del proceso de despachos (el simulado contra uno observado que no se usó para ajustar) | Despachos de otro período | **Sí**: es la única validación que necesita una ventana aparte |

**D4 pasó a ser, sobre todo, una decisión sobre la oferta**: con qué período se
representa el servicio de las líneas actuales, y con qué período separado se verifica
que el modelo lo reproduce.

## 3. Lo que se midió

Medición del 21/09/2026 sobre los despachos de 2024, 2025 y 2026, con los filtros del
paso 12: viajes de recorrido completo, fuera de la apertura, hora pico (7, 8, 17 y 18 h),
sin intervalos de más de 5 veces la mediana (D18). 2025 y 2026 se leyeron con
`lib_despachos`; **2026 se lee bien**, con la corrección de la columna `Km` (punto 7).
**2024 no lo lee `lib_despachos`**: tiene otro esquema (fecha `dd/mm/aa`, tipo de día
`H`/`S`/`D`/`F`, encabezado en Latin-1). Se bajó del mismo servidor
(`formaciones-despachadas-2024.csv`, 495.719 filas) y se leyó aparte, sin guardarlo en
`data/raw/`.

### 3.1 Los días que quedan

Restricciones ya impuestas: días hábiles del calendario del operador, sin días
parciales, sin marzo de 2025, sin el 10/04/2025 y sin los 25 días atípicos de molinetes
(estos dos últimos solo existen para 2025). Falta decidir **cómo excluir los días con
cancelaciones gremiales**, y pesa mucho:

| Año | Días con alguna cancelación gremial en la red | Días típicos si se excluye el día de toda la red | Días típicos si se excluye solo la línea afectada |
|---|---:|---:|---:|
| 2024 | 52 | 192 | 241 |
| 2025 | 97 | 123 | 213 |
| 2026 (ene–jun) | 62 | 56 | 117 |

Con el criterio de toda la red, noviembre de 2025 queda con 4 días, diciembre de 2025 con
ninguno y marzo y abril de 2026 con 6 cada uno. **Ese criterio no deja ventanas
utilizables**. El de línea afectada saca el día solo de la línea donde hubo
cancelación, que es donde la oferta estuvo alterada.

### 3.2 Intervalo en hora pico por ventana

Media / mediana en segundos, con el criterio gremial por línea:

| Ventana | Días | A | B | C | D | E | H |
|---|---:|---|---|---|---|---|---|
| 2024 sept. (mes de la demanda SBASE) | 21 | 196 / 185 | 247 / 236 | 196 / 186 | **282 / 277** | 314 / 291 | 207 / 205 |
| 2024 abr.–dic. | 181 | 194 / 185 | 249 / 240 | 198 / 188 | 288 / 279 | 318 / 295 | 208 / 205 |
| 2025 ene.–feb. | 42 | **224 / 218** | **291 / 284** | **220 / 210** | 275 / 274 | **386 / 376** | **281 / 292** |
| 2025 abr.–jun. | 56 | 196 / 186 | 249 / 240 | 194 / 185 | 244 / 238 | 329 / 307 | 208 / 205 |
| 2025 jul.–dic. | 115 | 195 / 184 | 249 / 237 | 195 / 186 | **218 / 207** | 320 / 302 | 206 / 205 |
| **2025 completo (lo que usa hoy el paso 12)** | 213 | 201 / 191 | 260 / 249 | 200 / 189 | 234 / 230 | 334 / 314 | 219 / 206 |
| 2026 mar.–may. | 59 | 193 / 182 | 239 / 222 | 197 / 186 | 213 / 203 | 316 / 299 | 206 / 204 |
| 2026 jun. | 21 | 192 / 179 | **220 / 202** | 200 / 187 | 209 / 200 | 303 / 286 | 207 / 205 |

Y la demanda de molinetes en días hábiles típicos de 2025 (`demanda_diaria.csv`):
**502.140** pasajeros por día en enero y **569.936** en febrero, contra entre 759.279 y
809.055 de abril a noviembre.

### 3.3 Qué muestran los números

1. **Enero y febrero son otro régimen.** En las dos fuentes: intervalos de 13 a 36 % más
   largos que en julio–diciembre en A, B, C, E y H (la H pasa de 206 a 281 s de media;
   la D no se compara porque cambió de régimen en el año) y entre 28 y 36 % menos
   demanda. Es el horario de
   verano, en 2024, 2025 y 2026. **El paso 12 hoy ajusta con todo 2025 y los mezcla**:
   por eso la columna "2025 completo" queda por encima de cualquier ventana sin verano
   en todas las líneas.
2. **La Línea D cambió de oferta en 2025.** Pasó de unos 280 s en 2024 a 244 s en
   abril–junio de 2025 y a 218 s desde julio. Está en el corredor calibrado (D3). En el
   mes de la demanda y de los perfiles de carga de SBASE (septiembre de 2024) la D
   despachaba un 29 % más espaciado que desde julio de 2025.
3. **La B vuelve a cambiar en junio de 2026** (de 239 a 220 s de media).
4. **El resto de las líneas es estable** de abril de 2024 en adelante fuera del verano:
   A, C y H varían menos de 2 % entre ventanas; la E, alrededor de 5 %.

La restricción 6 de `decisiones.md` ("estacionalidad comparable entre ambas ventanas")
queda medida: **ninguna ventana puede incluir enero o febrero**, y **ninguna partición
puede cortar en el medio del cambio de la D**.

## 4. Opciones

En todas, la carga se sigue calibrando con la hora pico mañana y validando con la hora
pico tarde de SBASE (D9), y el criterio gremial es por línea (sección 3.1).

### A. Oferta vigente: ajustar con 2025 jul.–dic., verificar con 2026 mar.–may.

- **Ajuste**: 115 días, el régimen actual y estable de las seis líneas, sin verano.
- **Verificación de la oferta**: 59 días de 2026 del mismo régimen, que no se usaron para
  ajustar. Se deja afuera junio de 2026 por el cambio de la B.
- **A favor**: el escenario base representa la red de hoy, que es contra la que se va a
  comparar la Línea F. Las dos ventanas son comparables (sección 3.2).
- **En contra**: la oferta es de 2025 y la demanda de septiembre de 2024. Para la D el
  desfase es grande (218 s contra 282 s). El flujo por tramo en pasajeros por hora casi
  no depende de la frecuencia mientras no haya saturación, pero la espera, la ocupación
  por formación y los que quedan en el andén sí.

### B. Oferta coherente con la demanda: ajustar con 2024 abr.–dic.

- **Ajuste**: 181 días de 2024 sin verano (o solo septiembre, 21 días); verificación con
  una parte separada del mismo año, o con 2025 abr.–jun.
- **A favor**: oferta y demanda del mismo momento, así que la calibración y la
  validación de la carga contra SBASE son coherentes en la D.
- **En contra**: el escenario base deja de ser la red actual (la D de 2024 ya no existe).
  Hay que extender `lib_despachos` al esquema de 2024. La restricción 1 ("posterior a
  diciembre de 2024") nació por los molinetes y no afecta a los despachos, pero habría
  que decirlo explícitamente.

### C. Dejar 2025 completo (como está hoy)

- **Ajuste**: 213 días, sin ventana de verificación separada.
- **En contra**: mezcla el horario de verano con el resto y dos regímenes de la D; no
  representa ningún día típico real. **No cumple la restricción 6.**

### D. Partir 2025: ajustar con abr.–sep., validar con oct.–dic.

- Es la partición que se tenía en mente al abrir D4.
- **En contra**: la D cambia en el medio (244 s antes de julio, 218 s después), así que
  la ventana de validación no es comparable con la de ajuste en una línea del corredor.
  Solo sirve si se corta en julio, y entonces es la opción A sin 2026.

## 5. Recomendación

**Recomendación: opción A**, con dos agregados:

1. **Análisis de sensibilidad de la oferta de la D**: correr el escenario base también
   con la D de septiembre de 2024, que es el mes de la demanda. Así el desfase entre
   oferta y demanda de la D queda medido en vez de supuesto, y responde la objeción
   principal de la opción A sin renunciar a representar la red actual.
2. **Sacar enero y febrero también de la forma de los bloques de 15 min** (molinetes,
   paso 3). Hoy entran todos los días hábiles típicos de 2025. El efecto probablemente
   sea chico porque es solo forma, pero conviene medirlo al aplicar.

Aplicarla es cambiar `FILTRO_FECHAS` en el paso 12 a julio–diciembre de 2025, pasar el
criterio gremial a línea afectada y volver a correr el paso 12 y `compilar.sh`. La
verificación con 2026 mar.–may. es la misma medición del paso 12 sobre esas fechas,
contra lo que simula el modelo.

## 6. Lo que queda afuera

- **Los días atípicos de 2024 y 2026** no se pueden detectar con molinetes (no hay 2026
  y 2024 no se procesó); se confía en el calendario del operador y en el filtro de días
  parciales. En 2025 ese calendario ya había reconocido 17 de los 25 atípicos.
- **2024 no se incorporó al repositorio.** Si se elige la opción B o la sensibilidad de
  la D, hay que bajarlo a `data/raw/` y extender `lib_despachos` a su esquema.
