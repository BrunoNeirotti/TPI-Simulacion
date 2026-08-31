# Paso 4: Intervalos entre despachos

Generado por `src/05_despachos.py` sobre `data/raw/formaciones-despachadas-2025.csv`, leído con `src/lib_despachos.py`. Salidas: `intervalos_despacho.csv` y `despachos_diario.csv` en `data/processed/`.

## 1. El recurso agregado del portal no sirve

Teníamos anotado usar el recurso **"Formaciones despachadas - Total" (CSV, 2015 a la actualidad, archivo único)** y que *"su historia desde 2015 es homogénea"*. **Las dos cosas son falsas.** Verificado sobre la copia local y contra la API del portal el 18/08/2026:

| Afirmación | Qué se verificó |
|---|---|
| "2015 a la actualidad" | El contenido **termina el 22/10/2021**. El metadato del recurso dice `last_modified = 2019-06-04`. |
| "archivo único" | El dataset publica además **un recurso por año**, incluidos 2025 y 2026. |
| "historia homogénea desde 2015" | Faltan **2016, 2017 y 2018 enteros**, y de 2015 hay 6 días. |

Es el mismo patrón que `viajes_anual.csv`: un recurso agregado que quedó congelado mientras el dataset siguió publicando por año. **Este paso usa los recursos anuales**, descargados el 18/08/2026 de `cdn.buenosaires.gob.ar/datosabiertos/datasets/sbase/subte-trenes-despachados/`.

El esquema anual además es mejor: nombres legibles, causas en texto y una columna **`Tipo Día` con el valor `Feriado`**, que es el calendario operativo del propio operador. Ver la sección 5.

Lectura: formaciones-despachadas-2025.csv en Latin-1, 495,719 filas crudas, 24,696 vacias descartadas, 471,023 utiles, 0 con fecha invalida. Formatos de fecha -> d/m/aaaa: 75,535, dd/mm/aa: 395,488.

## 2. Cobertura, y el mes que falta

- Días con registros: **335 de 365**.
- Servicios de cabecera programados: **869.691**, de los cuales **849.613 prestados** y 20.078 no prestados. Seis líneas; el Premetro queda fuera de alcance.
- **Faltan 30 días**: 30 días de 03.

> **Marzo de 2025 no está.** Faltan 30 de sus 31 días; solo sobrevive el 08/03. **Es un faltante del publicador, no un mes sin servicio**: los molinetes registran demanda normal en todo marzo, así que los trenes circularon y lo que falta es el registro de oferta. **Marzo queda fuera de cualquier ventana de ajuste o validación**, y deja sin verificar los cuatro días atípicos que el paso 3 detectó en ese mes.

- Pares (línea, día) con datos parciales, por debajo del 60 % de la mediana de su tipo de día: **0**. Quedan excluidos de los intervalos.

### 2.1 Un día con registros y cero servicios prestados

**2025-04-10**: 3.122 servicios programados, **ninguno prestado**, en las seis líneas. Causa registrada: *Huelga / Paro General* en 3.122 de ellos.

> **Esto corrige al paso 3.** Ese paso encontró el 10/04/2025 en molinetes con 66 pasajeros y 31 de 90 estaciones con dato, y lo clasificó como **hueco de datos del publicador**. No lo es: fue un **paro general, un día sin servicio**. Las dos fuentes son independientes y coinciden. El tratamiento no cambia (el día se excluye de todos los perfiles por no ser representativo) pero la caracterización sí, y ahora está verificada en lugar de supuesta. Ver `reports/04_demanda.md`, sección 2.1.

## 3. Intervalos entre despachos en día hábil típico

Se miden **en cabecera**: es el intervalo con que la línea despacha, no el que ve un pasajero en una estación intermedia, que puede degradarse por acumulación. Esa degradación es una salida del modelo, no una entrada.

Base: 663.709 intervalos de días hábiles completos, excluyendo los despachos con causa registrada (sección 4).

### 3.1 Por línea

| Línea | Cabeceras | Pico (7-9 y 17-19) | Valle (11-15) | Trenes/h en pico |
|---|---|---:|---:|---:|
| A | San Pedrito ↔ Plaza De Mayo | 3,17 min | 3,82 min | 18,9 |
| B | Juan Manuel De Rosas ↔ Leandro N. Alem | 4,13 min | 4,38 min | 14,5 |
| C | Constitucion ↔ Retiro | 3,15 min | 4,28 min | 19,0 |
| D | Congreso De Tucuman ↔ Catedral | 3,82 min | 4,27 min | 15,7 |
| E | Plaza De Los Virreyes ↔ Bolivar | 5,22 min | 5,88 min | 11,5 |
| H | Las Heras ↔ Hospitales | 3,43 min | 4,10 min | 17,5 |

La cifra de trenes por hora es por cabecera, es decir **por sentido**.

### 3.2 Perfil horario

Mediana del intervalo, en minutos:

| Hora | A | B | C | D | E | H |
|---|---:|---:|---:|---:|---:|---:|
| 05 | 4,42 | 4,50 | 4,35 | 4,95 | 3,64 | 4,55 |
| 06 | 4,65 | 5,51 | 3,47 | 5,90 | 6,87 | 3,88 |
| 07 | 3,42 | 4,42 | 3,12 | 4,00 | 5,28 | 3,43 |
| 08 | 3,08 | 4,10 | 3,12 | 3,67 | 5,22 | 3,43 |
| 09 | 3,05 | 4,02 | 3,13 | 3,68 | 5,10 | 3,43 |
| 10 | 3,32 | 4,23 | 3,97 | 4,00 | 5,12 | 3,45 |
| 11 | 3,83 | 4,47 | 4,37 | 4,27 | 5,87 | 4,12 |
| 12 | 3,90 | 4,45 | 4,38 | 4,35 | 5,93 | 4,17 |
| 13 | 3,90 | 4,48 | 4,40 | 4,30 | 6,12 | 4,13 |
| 14 | 3,55 | 4,15 | 3,92 | 4,20 | 5,68 | 3,88 |
| 15 | 3,07 | 4,02 | 3,20 | 3,87 | 5,25 | 3,45 |
| 16 | 3,03 | 3,97 | 3,18 | 3,78 | 5,17 | 3,45 |
| 17 | 3,12 | 3,95 | 3,17 | 3,67 | 5,19 | 3,43 |
| 18 | 3,12 | 4,00 | 3,20 | 3,82 | 5,17 | 3,43 |
| 19 | 3,08 | 4,08 | 3,17 | 4,02 | 5,15 | 3,48 |
| 20 | 3,52 | 4,67 | 4,40 | 4,23 | 6,72 | 4,90 |
| 21 | 4,82 | 4,82 | 4,97 | 5,85 | 7,28 | 4,90 |
| 22 | 5,45 | 5,77 | 4,95 | 6,00 | 7,25 | 4,90 |
| 23 | 5,65 | 6,42 | 5,33 | 6,18 | 7,22 | 4,95 |

### 3.3 Contraste con el diseño de la Línea F

El EsIA fija para la Línea F un headway de **1,5 min, 40 trenes por sentido y hora**. La línea más frecuente de la red actual en hora pico es la **C**, con una mediana de 3,15 min, es decir 19,0 trenes por hora y sentido.

> El diseño de la Línea F supone despachar **2,1 veces más seguido que lo que hoy logra la mejor línea de la red**. No es imposible (es una línea nueva, con señalamiento nuevo) pero **es un supuesto fuerte del escenario futuro y hay que tratarlo como variable de escenario, no como dato**. El documento ya declara 1,5 min como cota superior de frecuencia; este contraste le da la magnitud.

## 4. Servicio no prestado y sus causas

De 869.691 servicios de cabecera programados, **20.078 no se prestaron (2,31 %)**. El 100,0 % de ellos tiene causa registrada, así que la trazabilidad es prácticamente total.

> La distinción importa y es fácil de perder: si se filtran de entrada los servicios no prestados, **las causas que se ven son las de los servicios que sí se hicieron**, y un paro (que por definición cancela) desaparece del análisis. Acá se cuentan los no prestados.

| Causa | Servicios no prestados |
|---|---:|
| Coche descompuesto | 5.410 |
| Huelga / Paro General | 3.122 |
| Conflicto Gremial | 1.924 |
| Falta de coches | 1.733 |
| Obra de Modernización | 1.631 |
| Responsabilidad Siemens | 1.095 |
| Por Conductor | 870 |
| Incidente con pasajeros | 631 |
| Pasajero descompuesto en formacion | 599 |
| Intento de suicidio /Arrollamiento | 410 |
| Actitud / Desempeño de personal | 392 |
| Por Guarda | 358 |

Las causas gremiales concentran **5.060 servicios cancelados en 100 días**, es decir 25,2 % de todo el servicio no prestado del año. Los seis días de mayor incidencia:

| Fecha | Servicios cancelados | Tipo de día |
|---|---:|---|
| 2025-04-10 | 3.122 | Habil |
| 2025-08-04 | 379 | Habil |
| 2025-04-11 | 219 | Habil |
| 2025-10-07 | 89 | Habil |
| 2025-10-27 | 84 | Habil |
| 2025-08-20 | 68 | Habil |

**Estos días no pueden entrar en las ventanas de ajuste ni de validación**: la oferta está afectada y la demanda medida en molinetes también, por razones que el modelo no representa.

Aparte, 3.333 de los 845.615 intervalos entre despachos **sí prestados** (0,4 %) tienen una causa cargada (demoras y anomalías que no impidieron el viaje). También se excluyen del cálculo de intervalos típicos.

## 5. El calendario del operador valida el paso 3

La columna `Tipo Día` de este dataset es el **calendario operativo de SBASE**, y permite hacer la verificación externa que el paso 3 dejó abierta sobre sus 25 días hábiles atípicos.

- SBASE declara **13 feriados** en 2025, de los cuales **11 caen en día hábil**.
- El método del paso 3 detectó **11 de esos 11** (todos), sin conocer el calendario.

De los 14 días atípicos que **no** son feriado:

- **6 están declarados por SBASE como servicio de sábado** pese a caer en día hábil: 2025-04-17, 2025-05-02, 2025-08-15, 2025-11-21, 2025-12-24, 2025-12-31. Es decir que el operador ya reconoce que no son días normales, y explica la menor demanda por menor oferta.
- **4 caen en marzo**, que no tiene datos de despachos (2025-03-03, 2025-03-04, 2025-03-05, 2025-03-24), así que **no se pueden verificar con esta fuente**.
- **4 quedan sin explicación**: SBASE los declara hábiles con servicio normal (2025-08-01, 2025-12-26, 2025-12-29, 2025-12-30). Son días de menor demanda con oferta normal.

> **El criterio del paso 3 queda validado**: recall de 100 % sobre los feriados hábiles, y 6 detecciones más que el propio operador corrobora como días de servicio reducido. Sigue sin ser un clasificador de feriados (no lo pretende) pero como detector de días no representativos funciona.

## 6. Coches por formación

Insumo directo de la capacidad de formación del modelo:

| Línea | Mediana | Media | Mínimo | Máximo |
|---|---:|---:|---:|---:|
| A | 5 | 5,00 | 5 | 5 |
| B | 6 | 6,00 | 6 | 6 |
| C | 5 | 5,04 | 5 | 6 |
| D | 6 | 6,00 | 6 | 6 |
| E | 5 | 5,00 | 5 | 6 |
| H | 6 | 6,00 | 6 | 6 |

La capacidad por formación no sale de acá (depende del modelo de coche) pero la cantidad de coches sí, y varía dentro de una misma línea.

## 7. Qué queda de esto

- **Corregido en `docs/contexto-del-proyecto.md`, sección 4**: el recurso "Total" está congelado y la historia no es homogénea desde 2015 (sección 1).
- **Marzo de 2025 no existe en este dataset** (sección 2). Condiciona la elección de períodos: ninguna ventana de ajuste o validación puede tocar marzo.
- **El headway de 1,5 min de la Línea F es un supuesto fuerte** (sección 3.3), no un dato: exige despachar bastante más seguido que la mejor línea actual. Va como variable de escenario.
- **El pendiente de verificación del paso 3 se cierra** (sección 5).
- **Sigue faltando el contraste GTFS contra operación real**: los tiempos de marcha del GTFS son un perfil nominal único y este paso mide despachos, no tiempos de recorrido. El contraste completo necesita el modelo.
