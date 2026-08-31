# Pliego de la licitación de la Línea F

Lo bajamos del portal Buenos Aires Obras (`buenosairesobras.dguiaf-gcba.gov.ar`), de la
ficha de vista previa de pliego ciudadano. Es descarga libre y no hizo falta ningún
trámite. Copia local en `docs/Documentos-BA-Obras/`.

No hay que confundirlo con BAC (Buenos Aires Compras): el proceso tiene numeración BAC,
`10241-0094-LPU25`, pero la ficha con los adjuntos está en BA Obras.
`mesadeayuda_bac@buenosaires.gob.ar` es soporte del portal, no una vía documental.

---

## 1. Datos del proceso

| Campo | Valor |
|---|---|
| Proceso | 10241-0094-LPU25, Licitación Pública Nacional e Internacional de Etapa Múltiple |
| Expedientes | EX-2025-43875108-GCABA-SSPO (técnico) y EX-2025-43793855-GCABA-DGTALMI (administrativo) |
| Obra | Ingeniería, construcción y equipamiento Línea F |
| Contratante | Ministerio de Movilidad e Infraestructura. Ministro: Pablo José Bereciartúa |
| Marco legal | Ley 6.246 arts. 22 y 24, Decretos 60/21, 204/22, 152/21 y 401/25 |
| Sistema | Ajuste alzado |
| Presupuesto oficial | USD 1.350.000.000, con anticipo financiero del 20 % |
| Fin de consultas | 04/09/2026 |
| Apertura de ofertas | 10/09/2026, 13:00 |

### 1.1 El presupuesto quedó confirmado

Era un dato que veníamos arrastrando de fuentes secundarias. Ahora hay dos fuentes
oficiales independientes que coinciden, las dos en `docs/Documentos-BA-Obras/`:

- La RESOL-2026-175-GCABA-MMIGC (`RS-2026-26334102-MMIGC`), en los considerandos: "Que
  el presupuesto oficial se ha establecido en la suma DÓLARES ESTADOUNIDENSES MIL
  TRESCIENTOS CINCUENTA MILLONES (U$D 1.350.000.000.-) con anticipo financiero del
  veinte por ciento (20%)".
- Las Cláusulas Particulares (`PLIEG-2026-30055586-SSPO`): "El Presupuesto Oficial de la
  Obra asciende a la suma de DÓLARES ESTADOUNIDENSES MIL TRESCIENTOS CINCUENTA MILLONES
  (U$D 1.350.000.000.-), con Anticipo Financiero del VEINTE POR CIENTO (20%)", con mes
  base el anterior a la presentación de ofertas.

### 1.2 Las dos postergaciones, con fechas

Salen de la RESOL-2026-175. Teníamos anotado que la licitación se había postergado dos
veces, pero sin las fechas:

| Hito | Fecha | Norma |
|---|---|---|
| Llamado original | apertura al 22/04/2026, 13:00 | Resolución 568/MIGC/25 |
| Primera postergación | 14/07/2026, 13:00 | Resolución 95/MMIGC/26 |
| Segunda postergación | 10/09/2026, 13:00 | RESOL-2026-175-GCABA-MMIGC, del 03/06/2026 |

---

## 2. Qué contiene y qué no

### 2.1 El Pliego de Especificaciones Técnicas no trae plan de servicio

Es el `PLIEG-2026-30055895-GCABA-SSPO`, Rev. 01, de 606 páginas. Lo revisamos completo
por búsqueda de términos. Es ingeniería constructiva: normativa, proyecto ejecutivo,
obradores, estudios de suelos, túneles, estructuras, electricidad, ventilación e
instalaciones. No contiene intervalo de servicio, ni flota, ni capacidad, ni demanda.

Lo único operativo que aporta es que confirma la velocidad objetivo de 90 km/h en vía
directa, y agrega un dato que el EsIA no da: una "aceleración sin compensar de 0,65
m/s²" como criterio de diseño geométrico de vía en desvíos.

O sea que los parámetros operativos siguen viniendo del EsIA. No hay una fuente mejor.

### 2.2 No existe estudio de demanda en toda la licitación

Extrajimos el índice maestro embebido en la *Planilla Integradora de Documentación
Técnica al 24/06/2026* (`IF-2026-29710867-GCABA-MMIGC`). El PDF es una carátula GEDO y
el listado viene como archivo embebido en `.xlsx` y `.pdf`. Son 1.866 documentos
técnicos catalogados.

Buscando sobre el índice completo, los únicos documentos cuya descripción menciona
demanda son los dos de medios de salida. No hay ningún estudio de demanda de transporte,
ni matriz origen-destino, ni plan de explotación en toda la documentación licitatoria.

---

## 3. Qué es el `LF-GL-GEN-GNR-IN-003`

Lo teníamos mal identificado. Habíamos anotado que era el *Análisis de Demanda Línea F*
de SBASE 2019, y es falso. Según el índice maestro y el propio documento:

> `LF-GL-GEN-GNR-IN-003` = "Demandas Etapa I - Medios de Salida - Evacuación Estaciones
> Brandsen a Pizzurno"

O sea que es el documento que ya teníamos descargado como ANEXO 2. El error vino de leer
mal la nota de fuente del EsIA, que dice "Tomado de LF-GL-GEN-GNR-IN-003 *que cita*
Análisis de Demanda Línea F. SBASE 2019": el IN-003 es el intermediario, no el estudio.

### 3.1 La cadena de procedencia de las tablas de carga

| Eslabón | Documento | ¿Público? |
|---|---|---|
| 1. Primario | Nota técnica "Análisis de Demanda Línea F", SBASE, 2019 | No. No está ni en la licitación ni en el expediente ambiental |
| 2. Intermedio | "Informe Strans Demanda de la Línea F", SBASE, entregado por el Ministerio de Infraestructura el 17/07/2025 | No |
| 3. Derivado | `LF-GL-GEN-GNR-IN-003` Demandas Etapa I (Brandsen a Pizzurno) y `LF-GL-GEN-GNR-IN-004` Demandas Etapa II (Junín a Pacífico) | Sí, los tenemos |
| 4. Reproducción | EsIA Cap. 3, Tablas 2 y 3 | Sí |

Verificamos que la tabla SBP de la página 3 del `IN-003` es idéntica a la Tabla 2 del
EsIA, valor por valor y con el mismo resaltado de la fila Constitución. Las dos fuentes
no se contradicen: el EsIA copió del pliego.

Con eso, lo único que faltaba pedirle a SBASE era un solo documento, la nota técnica de
2019 o el Informe Strans de 2025.

---

## 4. Un dato operativo nuevo: el factor de superpico

El `IN-003` y el `IN-004` desagregan la demanda por estación y por movimiento
(desembarcando, pasantes y embarcando) en las dos horas pico, y aplican un factor de
superpico de 1,1 para dimensionar.

Los tres parámetros que usan son consistentes con el EsIA y lo confirman de forma
independiente: intervalo de trenes de 1,5 min, 40 trenes por hora y ahora superpico 1,1.

Para el TPI importa porque el superpico es el reconocimiento oficial de que la demanda no
se distribuye uniformemente dentro de la hora pico. Nuestro perfil intrahorario sale de
los molinetes y era supuesto propio; ahora hay un valor oficial contra el cual medirlo.
La concentración intrahoraria que produzcan nuestros datos debería dar del orden de 1,1
sobre el promedio horario. Es un contraste barato y todavía no lo hicimos.

---

## 5. Salvedades sobre lo descargado

### 5.1 Los tres anexos son revisiones superadas

El índice maestro al 24/06/2026 lista la revisión 1 de los tres, con otros números GEDO:

| Documento | Lo que tenemos | Vigente según el índice |
|---|---|---|
| `LF-GL-GEN-GNR-IN-001` Informe Inicial | IF-2025-44182550, Rev. 0, 15/08/2025 | IF-2026-22974173, Rev. 1 |
| `LF-GL-GEN-GNR-IN-003` Demandas Etapa I | IF-2025-44089535, Rev. 0, 06/10/2025 | IF-2026-17933062, Rev. 1 |
| `LF-GL-GEN-GNR-IN-004` Demandas Etapa II | IF-2025-44089622, Rev. 0, 06/10/2025 | IF-2026-17931298, Rev. 1 |

No invalida lo que obtuvimos, porque la tabla SBP de la Rev. 0 coincide exactamente con
la que reproduce el EsIA de abril de 2026, pero antes de citar cifras del IN-003 conviene
bajar la Rev. 1 y verificar si cambiaron. El Pliego de Especificaciones Técnicas sí está
en su versión vigente, la Rev. 01: el índice lo daba como pendiente de carga al 24/06 y
se publicó después.

Existe además el `LF-GL-GEN-GNR-IN-005`, *Sistema de Ventilación Subte Línea F*, que no
bajamos porque no le sirve al modelo.

### 5.2 Había un archivo duplicado

`PE-RES-MIGC-MIGC-568-25-ANX-1.pdf` era byte por byte el mismo archivo que
`Anexosanexo2if202544089535gcabasspo.pdf`, con idéntico SHA-1 y 1.822.509 bytes. Era el
`IN-003` republicado como Anexo 1 de la Resolución 568/MIGC/25. Lo borramos, porque no
aportaba nada y ocupaba el doble.

### 5.3 El `IN-003` se contradice a sí mismo en dos estaciones

La sección de estimación por estación del `IN-003`, págs. 5 a 18, no siempre reproduce su
propia tabla SBP de la página 3. Comparando pasajeros que descienden en hora pico de la
tarde:

| Estación | Suma de la tabla SBP | Sección por estación | Diferencia |
|---|---:|---:|---:|
| Brandsen | 5.443 | 5.443 | - |
| Cochabamba | 3.603 | 3.603 | - |
| Chile | 920 | 920 | - |
| Congreso | 3.369 | 3.369 | - |
| Pizzurno | 4.816 | 4.816 | - |
| Constitución | 33.066 | 33.106 | +40 |
| Corrientes | 4.283 | 4.559 | +276 |

Diez de doce cierran exacto y dos no, y la diferencia no responde a ningún factor que
hayamos podido identificar. No nos afecta, porque usamos la tabla SBP, que es el eslabón
común con el EsIA y coincide con él, y no la sección de dimensionado de evacuación. Queda
anotado por si alguna vez se citan cifras de esa sección.

---

## 6. Confirmaciones cruzadas con el expediente ambiental

- Los planos `PLANO-2025-43987736` y `PLANO-2025-43989169`, que el EsIA cita como fuente
  de sus Figuras 3 y 5, son los PLANO 65 y PLANO 67 de este pliego.
- Los modelos 3D del pliego (ANEXOS 9 a 20) nombran las estaciones así: Brandsen,
  Constitución, Cochabamba, Chile, Congreso, Corrientes, Pizzurno, Junín, Pueyrredón,
  Parque Las Heras, Ecoparque y Pacífico. Es sistemáticamente el segundo nombre de cada
  par del EsIA, lo que confirma que nunca hubo contradicción.
- La partición Etapa I de Brandsen a Pizzurno y Etapa II de Junín a Pacífico, que usan el
  `IN-003` y el `IN-004`, coincide exactamente con los Tramos A y B del EsIA.

---

## 7. La respuesta oficial del 25/08/2026 remite a este mismo pliego

El Ministerio de Movilidad e Infraestructura contestó la Solicitud de Información Pública
N° 00868015/26 con el informe `IF-2026-38342377-GCABA-DGTALMMI`, del 25/08/2026, firmado
por Fernando Codino, Director General Técnico Administrativo y Legal, con referencia
`EX-2026-35501690-GCABA-DGAIGA`. Copia local en `docs/respuestas-oficiales/`.

El cuerpo es una sola idea: "toda documentación técnica relativa a 'Ingeniería,
construcción y equipamiento línea de Subterráneo F' se encuentra disponible" en la vista
previa de pliego ciudadano de BA Obras, que es el mismo portal del que sacamos todo lo
que este documento analiza. Después copia tres anexos "a modo ilustrativo".

### 7.1 Los tres anexos que cita ya los teníamos

| Anexo que cita la respuesta | Archivo local | Qué es |
|---|---|---|
| ANEXO 1, `IF-2025-44182550-GCABA-SSPO` | `Anexosanexo1if202544182550gcabasspo.pdf` | `LF-GL-GEN-GNR-IN-001`, Informe Inicial |
| ANEXO 2, `IF-2025-44089535-GCABA-SSPO` | `Anexosanexo2if202544089535gcabasspo.pdf` | `LF-GL-GEN-GNR-IN-003`, Demandas Etapa I |
| ANEXO 3, `IF-2025-44089622-GCABA-SSPO` | `Anexosanexo3if202544089622gcabasspo.pdf` | `LF-GL-GEN-GNR-IN-004`, Demandas Etapa II |

Coinciden uno a uno por número de IF, y los bajamos el 05/08/2026, veinte días antes de
la respuesta. Son además los Rev. 0 que la sección 5.1 identifica como revisiones
superadas: la respuesta remite a versiones vencidas de documentos que ya teníamos.

### 7.2 Por qué no contesta lo que se pidió

La respuesta leyó el pedido como si fuera documentación licitatoria, y no lo era. Los
ítems pedidos (matriz origen-destino de la red, perfiles de carga por tramo, estudio de
demanda de la Línea F, escenarios con y sin proyecto, parámetros operativos de las líneas
existentes) son información de operación, que está en SBASE y no en un pliego de obra.

La sección 2.2 de este documento ya lo demuestra, y es evidencia propia y verificable:
extrajimos el índice maestro de la Planilla Integradora, 1.866 documentos, y los únicos
cuya descripción menciona demanda son los dos de medios de salida. Remitir al pliego es
remitir a un corpus donde está verificado que lo pedido no está.

A eso se suma que los medios de salida no son lo que el trabajo necesita: el `IN-003` y
el `IN-004` dimensionan evacuación de andenes y escaleras, no demanda de viajes. Todo lo
que aportan al TPI es el factor de superpico de la sección 4.

En resumen, esta respuesta no cambió ninguna cifra ni ninguna decisión. El perfil de
carga de la Línea F sigue viniendo del EsIA, los parámetros operativos también, y el
escenario futuro siguió sin matriz O-D oficial hasta que contestó SBASE.

---

## 8. Lo que queda por hacer con este material

- Bajar la Rev. 1 del `IN-003` y del `IN-004` antes de citar cifras suyas.
- Contrastar el factor de superpico de 1,1 contra el perfil intrahorario de molinetes.
- Sin bajar y sin prioridad: los modelos 3D de estaciones (ANEXOS 9 a 20) y los planos de
  geotecnia, interferencias, trazado y detalle de Pizzurno.
