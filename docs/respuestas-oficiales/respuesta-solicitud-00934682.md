# Respuesta a la Solicitud de Información Pública Ley 104 N° 00934682/26

Llegó el 16/09/2026 por correo de `legalesdgtalmi@buenosaires.gob.ar`, con **algo más de
tres semanas de demora** respecto al plazo habitual de las otras solicitudes (esta se
presentó el 26/08/2026, ver `RE-2026-38432270-GCABA-DGAIGA`). Es la solicitud dirigida a
**SBASE** que la sección 6, punto 4 del `CLAUDE.md` daba por **no presentada** ("CERRADO
el 27/08/2026: no se presenta"). Esa nota estaba desactualizada: la solicitud **sí se
presentó**, el mismo 26/08/2026, un día antes de que se registrara la decisión de no
insistir. Queda corregido acá.

Tres archivos, copiados en este mismo directorio:

| Archivo | Qué es |
|---|---|
| `RE-2026-38432270-GCABA-DGAIGA.pdf` | El formulario de la solicitud original (Contacto N° 00934682/26), a nombre de Bruno Neirotti |
| `IF-2026-41875173-GCABA-DGTALMMI.pdf` | La respuesta, firmada por Fernando Codino (mismo firmante que la negativa del 25/08/2026) |
| `IF-2019-20550252-GCABA-SBASE.pdf` | Nota de elevación de 2019, con el documento pedido **embebido como adjunto** (mismo patrón que la respuesta de la solicitud 00866317/26: hay que abrirlo con un lector que muestre `/EmbeddedFiles`, un visor común no lo revela) |

El adjunto embebido se extrajo a
`adjuntos-sbase/analisis-demanda-linea-f-2019.pdf`.

## Qué se pidió y qué contestaron

La solicitud tenía un ítem principal y dos subsidiarios (texto completo en el PDF del
formulario):

1. **Principal**: la nota técnica *"Análisis de Demanda Línea F"* (SBASE, 2019) o su
   derivado *"Informe Strans Demanda de la Línea F"*.
2. Subsidiario: matriz origen-destino de la red a nivel de estación.
3. Subsidiario: parámetros operativos de las líneas en servicio.

La respuesta:

- **Ítem 1: SÍ, adjuntaron el documento pedido.** Es *"Análisis de Demanda Línea F"*,
  Gerencia de Planeamiento de SBASE, **febrero de 2019**.
- **Ítems 2 y 3**: remiten a la respuesta ya recibida de la solicitud 00866317/26
  (`EX-2026-35399949-GCABA-DGAIGA`, ver `respuesta-ley104-00866317.md`). **No hay nada
  nuevo ahí**: esos dos ítems ya estaban cubiertos.

## Qué trae el documento de 2019 (`analisis-demanda-linea-f-2019.pdf`)

Es un informe de 10 páginas, hecho con el software VISUM, "a fin de realizar la
documentación licitatoria" (es decir, es material preparatorio del pliego, de 2019, no
un estudio independiente posterior).

1. **Cuadro de datos de entrada (intervalos e intervalo entre trenes supuestos para
   simular)**, para las líneas A, B, C, D, E, F y H. **Ojo: no son datos medidos, son el
   supuesto de entrada al simulador**, y el propio documento aclara que corresponden "a
   la red actual... con la mejora de frecuencia que está llevando a cabo SBASE", es decir
   una frecuencia **mejorada respecto a la de 2019**, no la real de ningún año.
   Comparado con lo medido en `reports/05_despachos.md` (día hábil, hora pico, 2025),
   la mejora supuesta **no se concretó**: todas las líneas circulan hoy más espaciadas
   que lo que este documento asumía como entrada:

   | Línea | Supuesto 2019 (este doc) | Medido 2025 (despachos) |
   |---|---:|---:|
   | A | 135 s (2,25 min) | 3,17 min |
   | B | 180 s (3,00 min) | 4,13 min |
   | C | 135 s (2,25 min) | 3,15 min |
   | D | 135 s (2,25 min) | 3,82 min |
   | E | 210 s (3,50 min) | 5,22 min |
   | H | 150 s (2,50 min) | 3,43 min |

   **No reemplaza los intervalos medidos que ya usa el pipeline.** Se deja registrado
   solo como antecedente de que la "mejora de frecuencia" de 2019 no se sostuvo.

2. **Intervalo simulado de la Línea F**: Servicio Largo (California–Palermo) a 200 s y
   Servicio Corto (Constitución–Palermo) a 200 s, que combinados dan **100 s en el tramo
   Constitución–Palermo** y **200 s en el tramo California–Constitución**. El **100 s**
   coincide con la cifra que el Ministerio dio en 2026 ("de requerirse", ver D7 en
   `decisiones.md`) — es una tercera fuente independiente, de 2019, que converge en el
   mismo número para el tramo troncal. **No cambia la decisión D7** (ya cerrada, rango
   90–189 s): es un dato más a favor del 100 s como punto de referencia dentro del rango
   ya definido, no una razón para reabrirlo.

3. **Tablas suben-bajan-pasan (SBP) por estación de la Línea F**, en HPM y HPT, ambos
   sentidos. Confirma con fuente primaria el número que ya se venía citando por vía
   indirecta (a través del EsIA): **32.640 ascensos en Constitución en la HPM**, sentido
   a Palermo. Antes se tenía ese número citado en el expediente ambiental; ahora está la
   nota técnica original que lo origina.

4. **Matrices origen-destino, estación por estación, para las siete estaciones de
   combinación de la Línea F** (Constitución, Entre Ríos–Rodolfo Walsh, Congreso,
   Corrientes, Córdoba, Las Heras, Plaza Italia), en HPM y HPT. Esto es dato nuevo que
   no estaba disponible por ninguna otra vía: reparte, para cada combinación, cuántos
   pasajeros de la Línea F siguen viaje en la otra línea versus cuántos entran o salen a
   la calle. Es el nivel de detalle que hace falta para el **escenario futuro** (paso 8),
   cuando haya que decidir cómo asignar los pasajeros de la Línea F a la red existente en
   los nodos de combinación.

## Aviso: el trazado de este estudio no es el vigente

**El estudio de 2019 modela 13 estaciones, con terminal sur en California.** El
trazado vigente (`docs/expediente-eia-linea-f.md`, EsIA doc 0010 y pliego) tiene
**12 estaciones, con terminal sur en Brandsen** — una menos, y con la cabecera sur en
otro punto. No es la misma traza.

Alineando por las tres combinaciones que coinciden por nombre y por línea (Constitución
con la C, Congreso con la A, Corrientes con la B), el resto de las combinaciones **no
calza de forma prolija**:

- Este estudio declara combinación con la **Línea D en dos estaciones** (Córdoba y
  Plaza Italia) y con la **Línea H en una** (Las Heras).
- El expediente vigente declara combinación con la **Línea D en dos estaciones
  distintas** (Pizzurno y Palermo) y **no resuelve con certeza** en qué estación
  combina con la H (ambigüedad ya declarada en `docs/expediente-eia-linea-f.md`,
  sección "La combinación con la Línea H no está resuelta en el expediente").

**No corresponde asumir una correspondencia estación por estación entre las siete
matrices de este documento y las doce estaciones vigentes sin verificarla
explícitamente primero** (por geometría, como ya se hizo para resolver la
combinación con la H). Usar estas matrices como contraste en el paso 8 requiere ese
paso previo de correspondencia; no se puede comparar nodo por nodo a ciegas por
nombre o por posición en la lista.

## Qué no cambia

- No reabre D3, D4, D6, D7, D9, D10 ni D11.
- No hay razón para reabrir el frente de pedidos de información: el ítem que faltaba
  llegó, tarde pero llegó, y el frente sigue cerrado, ahora con el dato en mano.

## Cómo se usan las matrices OD por estación de combinación (punto 4)

**Decidido el 16/09/2026, con el grupo: solo como contraste, nunca como insumo del
modelo.** El paso 8 asigna la demanda de la Línea F en los nodos de combinación con el
mismo método ya validado del paso 6; las matrices de SBASE 2019 se comparan después
contra ese resultado, nodo por nodo. Es la continuación de la postura que ya estaba
escrita desde el 05/08/2026 para el perfil de carga agregado, y evita tomar como dato
duro una fuente que el propio trabajo ya documentó como no conciliable en su nivel
agregado (ver más abajo) y calculada sobre una red base (frecuencias de las líneas
existentes) que no llegó a concretarse. Detalle completo, con las alternativas
descartadas, en `decisiones.md`.
