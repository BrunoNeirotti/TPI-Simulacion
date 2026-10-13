# Impacto de la Línea F sobre la red de Subte de Buenos Aires

Modelo de simulación de eventos discretos de la red de Subte de la Ciudad de Buenos
Aires, calibrado con datos públicos, para comparar cómo funciona la red actual contra un
escenario futuro que incluya la Línea F.

Trabajo Práctico Integrador de la materia Simulación, UTN Facultad Regional Rosario.

Título del trabajo: *Evaluación mediante simulación del impacto de la Línea F sobre la
operación de la red de Subte de Buenos Aires*.

> **Rama `entrega`.** Esta rama publica lo necesario para **abrir y correr los modelos de
> AnyLogic** que se presentan (tabla de «Para ver el modelo funcionar», más abajo), los
> datos que leen, el código que los produce y la documentación de las fuentes. El informe
> final se agrega cuando el grupo lo cierre.

---

## Qué hay acá

La Línea F es una obra real que hoy está en licitación: 12 estaciones, 9,8 km, USD 1.350
millones y servicio previsto para 2031. Su objetivo declarado es descongestionar la Línea
C. Lo que hacemos es armar un modelo de la red actual, calibrarlo contra datos
observados, y después agregarle la Línea F para medir la diferencia.

Casi nada de lo que hace falta para eso estaba publicado en forma usable, así que buena
parte del repositorio es el registro de cómo se consiguió cada cosa y qué problemas tiene
cada fuente:

- Un pipeline de datos que va de los datasets crudos a los archivos que consume el
  modelo, con un reporte por paso.
- El modelo de la red en AnyLogic y un simulador de referencia en Java con la misma
  lógica, que lo verifica.
- El escenario con la Línea F y su resultado: con la F el viaje medio de la red baja un
  4 % y la carga máxima de la Línea C cae a la mitad.
- Un submodelo peatonal de la estación Constitución de la Línea F, construido sobre los
  planos oficiales, con sus tiempos de acceso al andén y de salida en hora pico.
- La documentación oficial del proyecto Línea F: el expediente de evaluación ambiental,
  el pliego de licitación y las respuestas a los pedidos por Ley 104. Los juntamos acá
  porque los portales de origen ya dieron de baja recursos sin avisar.
- Las fichas de análisis de esa documentación, con las tablas pasadas en limpio y las
  contradicciones marcadas.
- La propuesta en LaTeX.

Para empezar a leer conviene ir a
[`docs/contexto-del-proyecto.md`](docs/contexto-del-proyecto.md), que junta el estado, las
fuentes con sus problemas, las cifras oficiales con su procedencia y el plan de trabajo.
Si lo que se busca es entender qué consume el modelo, el archivo es
[`docs/guia-del-modelo.md`](docs/guia-del-modelo.md); cómo está armado, en
[`anylogic/modelo/GUIA_CONSTRUCCION.md`](anylogic/modelo/GUIA_CONSTRUCCION.md).

---

## Para ver el modelo funcionar

Hace falta AnyLogic 8.9 Personal Learning Edition. Se abren estos dos `.alp` y se corren
con el botón de ejecutar; no hay que instalar ni construir nada más.

| Modelo | Archivo | Qué se ve |
|---|---|---|
| Red de Subte, con o sin la Línea F | `anylogic/modelo/RedSubte_mapa/RedSubte.alp` | Mapa de la red con trenes, estaciones, carga por tramo, comparación con la red actual y ficha por estación al hacer clic. El parámetro `escenario` de `Main` elige la red actual (0) o la Línea F con su intervalo entre trenes (1 a 5: 90, 100, 120, 150 y 189 s; por defecto 2) |
| Estación Constitución de la F | `anylogic/peatonal/ConstitucionF_3D/ConstitucionF_3D.alp` | Hora pico de la mañana en 3D: andén, entrepiso, vestíbulo, trenes, vínculo con la C; botones de cámara y de niveles arriba de la ventana |

**Cómo está hecho el modelo de la red.** Es un modelo de la *Process Modeling Library*
con dos tipos de agente, `Pasajero` y `Formacion`, servidos desde poblaciones
declaradas y recicladas (`Enter`/`Exit`): un agente por pasajero, horizonte de día
completo. La topología, las rutas, la demanda y la oferta no se dibujan, porque con 90
estaciones y 6.006 pares origen-destino no entran en un diagrama: viven en los CSV de
`data/processed/` y en once clases Java que forman parte del propio proyecto de AnyLogic
(árbol *Java classes*). Lo demás son elementos del modelo: parámetros, variables,
funciones, salidas, eventos, los dos diagramas de proceso, los experimentos
(`Simulation`, `Replicas20` y `VariacionEscenario`, que recorre los cinco intervalos de
la F) y, en `RedSubte_mapa`, el mapa como figuras y controles del lienzo. El `.alp` es
autocontenido: no depende de ningún jar ni programa externo.

El submodelo peatonal usa la *Pedestrian Library* sobre los planos oficiales de la
estación: paredes, escaleras mecánicas y fijas, andenes y los flujos de entrada, salida
y combinación con la Línea C.

---

## Estructura

```
src/          Pipeline de datos. Un script numerado por paso, más las librerías
              de lectura de cada dataset (lib_*.py).
reports/      Resultado de cada paso, con sus verificaciones.
docs/         Propuesta en LaTeX, contexto del proyecto, fichas de análisis y
              documentación oficial.
anylogic/     Modelos de AnyLogic: modelo de la red, biblioteca Java (la misma que va
              dentro del modelo) y simulador de referencia, submodelo peatonal de
              Constitución y plantillas de las pruebas de límites.
data/         No se versiona entero. Ver "Datos" más abajo.
```

Los documentos de `docs/` que conviene conocer:

| Archivo | Qué es |
|---|---|
| `contexto-del-proyecto.md` | Estado, fuentes, cifras y plan |
| `guia-del-modelo.md` | Qué consume el modelo, qué es fijo y qué es variable |
| `diseno-modelo-base.md` | El diseño del modelo de la red antes de construirlo |
| `preparacion-de-datos.md` | Qué se hizo en cada paso del pipeline y con qué criterio |
| `expediente-eia-linea-f.md` | Extracción del expediente ambiental, con cita por documento y página |
| `pliego-licitacion-linea-f.md` | Análisis del pliego de licitación |
| `pruebas-anylogic-topes.md` | Las pruebas de límites de AnyLogic y qué salió de cada una |
| `respuestas-oficiales/` | Los informes oficiales que recibimos, con su ficha de análisis |
| `definitivo-main.tex` | La propuesta |
| `especificacion-modelo.md`, `.tex` | La especificación del modelo entregada en la materia |
| `glosario.md` | Los términos del trabajo y las traducciones elegidas |
| `figuras/` | Figuras de la propuesta y el diagrama conceptual del modelo |
| `historico/` | Versiones ya superadas; no son documentos vigentes |

---

## Reproducir el pipeline

Hace falta Python 3.12 con `pandas`, `numpy`, `networkx` y `matplotlib`.

```bash
pip install pandas numpy networkx matplotlib scipy
```

Los scripts se corren en orden y desde la raíz del repositorio. Cada uno deja sus salidas
en `data/processed/` y su reporte en `reports/`.

```bash
python src/01_tabla_maestra_estaciones.py    # 90 estaciones cruzadas entre 4 fuentes
python src/03_grafo_red.py                   # 90 nodos, 166 tramos, 28 transbordos
python src/04_demanda_molinetes.py           # demanda por estación y bloque de 15 min
python src/05_despachos.py                   # intervalos reales entre despachos
python src/06_matriz_od.py                   # matriz origen-destino
python src/07_caminos_minimos.py             # caminos mínimos con penalización
python src/09_sbase_od_carga.py              # matriz y perfiles de carga de SBASE
python src/10_calibracion_penalizacion.py    # calibración de la penalización
python src/11_demanda_modelo.py              # matriz de demanda del modelo
python src/12_ajuste_intervalos.py           # oferta: intervalos entre despachos y apertura
```

El paso 13 corre el simulador de referencia (Java, ver `anylogic/biblioteca/LEEME.md`)
y genera `reports/13_verificacion_referencia.md`:

```bash
cd anylogic/biblioteca && ./compilar.sh && ./referencia/correr.sh
```

Los runners del simulador de referencia para el escenario con la Línea F están en
`anylogic/biblioteca/referencia/` (`correr_f.sh`, `correr_informe.sh`,
`correr_sensibilidad.sh`); los insumos de ese escenario ya están construidos en
`data/processed/escenario_f/` (una carpeta por intervalo entre trenes).

`src/02_figuras_propuesta.py` genera las figuras de la propuesta y no depende del resto.
`src/08_generar_pruebas_anylogic.py` genera los modelos de prueba de `anylogic/pruebas/`.

En `src/03_grafo_red.py` hay un interruptor, `REPARAR_LINEA_E`, que controla si se
corrige el sentido 1 de la Línea E en el GTFS. Está en `True`, y el efecto de apagarlo
está medido en `reports/07_caminos_minimos.md`.

### Lo que el modelo consume

Al final del pipeline, AnyLogic necesita estos archivos:

| Archivo | Contenido |
|---|---|
| `data/processed/grafo_nodos.csv` | Los 90 nodos de la red |
| `data/processed/grafo_aristas.csv` | 166 aristas de tramo y 28 de transbordo, con sus tiempos |
| `data/processed/caminos_minimos.csv` | La ruta de cada uno de los 6.006 pares |
| `data/processed/demanda_modelo_od_hora.csv` | 827.289 viajes del día hábil, en 71.686 celdas |
| `data/processed/demanda_modelo_intrahorario.csv` | Reparto en bloques de 15 minutos |
| `data/processed/intervalos_empiricos.csv` | Distribución empírica de los intervalos entre despachos, por línea, cabecera y hora (501 cuantiles por celda) |
| `data/processed/cabeceras_despacho.csv` | Qué cabecera es cada lado (A/D) del dataset de despachos, y su sentido en el grafo |
| `data/processed/apertura_formaciones.csv` | Desde qué estaciones arrancan las formaciones a las 5:30 |
| `data/processed/escenario_f/I<nnn>/`, `oferta_I<nnn>/` | Lo mismo para la red con la Línea F a 90, 100, 120, 150 y 189 s entre trenes |
| `data/processed/escenario_f/mapa_esquematico.csv`, `mapa_tramos.csv`, `informe/` | Trazado del mapa y la carga de referencia por tramo para la comparación sin la F → con la F |

El detalle de cada columna está en [`docs/guia-del-modelo.md`](docs/guia-del-modelo.md).

---

## Datos

`data/raw/` no se versiona: son 2,2 GB y todo se puede volver a bajar de
[data.buenosaires.gob.ar](https://data.buenosaires.gob.ar). Qué archivos hacen falta y
qué aporta cada uno está en la sección 4 de
[`docs/contexto-del-proyecto.md`](docs/contexto-del-proyecto.md), junto con los problemas
de formato de cada uno, que en varios casos el publicador no documenta.

De `data/processed/` se versiona lo que los modelos leen. Con eso alcanza para correrlos
y verificar los resultados sin tener que rearmar los datasets crudos.

Tres advertencias que conviene leer antes de tocar cualquier dataset:

- Los datasets se leen con las librerías del repositorio y no parseando a mano.
  `lib_molinetes.py`, `lib_despachos.py` y `lib_sbase.py` resuelven entre las tres una
  docena de problemas de formato que no están documentados: codificaciones mezcladas,
  tres formatos de fecha en un mismo archivo, filas vacías, valores centinela, y dos
  planillas oficiales que numeran las estaciones distinto.
- Conviene desconfiar de los recursos "agregados" del portal. Ya encontramos dos
  congelados: `viajes_anual.csv`, sin actualizar desde 2020, y "Formaciones despachadas -
  Total", con contenido hasta 2021 y tres años faltantes. Los recursos por año sí se
  mantienen.
- Hay un cambio en los molinetes a partir de diciembre de 2024, por la apertura a medios
  de pago distintos de SUBE. Lo medimos y resultó menor de lo que temíamos, pero
  condiciona qué períodos se pueden usar.

---

## Documentación oficial

El expediente de evaluación ambiental (98 documentos) y el pliego de licitación están en
`docs/Documentos-EX-2026-20211143/` y `docs/Documentos-BA-Obras/`.

Para cualquier cifra de la Línea F conviene ir a las fichas de análisis y no a los PDF
sueltos ni a los diarios. Las fichas ya tienen las tablas pasadas en limpio y las
contradicciones marcadas. Por ejemplo, que las tres longitudes que circulan (9,8, 10,9 y
8,6 km) no se contradicen porque son magnitudes distintas, o que la cifra anunciada de
270.000 a 300.000 pasajeros diarios no aparece en ninguna pieza del expediente y no cierra
con el perfil de carga que el propio expediente publica.

Queda afuera un solo archivo de BA Obras,
`AnexosActualizacion+Documentacion+Tecnica+8ta+Tanda.zip` (138 MB), porque pasa el límite
por archivo de GitHub. Se baja del portal
[Buenos Aires Obras](https://buenosairesobras.dguiaf-gcba.gov.ar), proceso
`10241-0094-LPU25`.

---

## Fuentes

- GTFS de Subte, Buenos Aires Data. Topología, tiempos de tramo y de transbordo.
- Viajes Molinetes, Buenos Aires Data. Ingresos por estación y bloque de 15 minutos.
- Trenes despachados, Buenos Aires Data. Oferta real y causas de servicios no prestados.
- Viajes y etapas en transporte público del AMBA. La única fuente de destinos abierta.
- Matriz origen-destino y perfiles de carga de SBASE, obtenidos por Ley 104.
- Expediente EX-2026-20211143-GCABA-APRA, de la evaluación de impacto ambiental, y pliego
  del proceso 10241-0094-LPU25, de la licitación.
