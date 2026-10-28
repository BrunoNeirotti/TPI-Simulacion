# Simulador de control

Un programa en Java, independiente de AnyLogic, con la misma lógica que el modelo de la red:
los mismos datos, las mismas rutas, la misma llegada de pasajeros y la misma salida de trenes.
Sirve para dos cosas:

- **Verificar el modelo de AnyLogic.** Si dos programas escritos por separado dan el mismo
  resultado con los mismos datos, es muy improbable que compartan un error. El informe compara
  los dos en la tabla «AnyLogic contra el simulador de control».
- **Correr muchas variantes.** Simula un día en menos de un segundo; por eso se usó para las cien
  réplicas de cada frecuencia de la Línea F y para las pruebas de sensibilidad de los supuestos.

El modelo principal del trabajo es el de AnyLogic; este programa queda como respaldo.

## Qué hay

| Archivo | Qué es |
|---|---|
| `subte/` | La lógica compartida: red, rutas, demanda, oferta de trenes, andenes y carga a bordo. Son las mismas clases que el modelo de AnyLogic lleva adentro. |
| `SimuladorReferencia.java` | El simulador: avanza de un suceso al siguiente, corre las réplicas y escribe los resultados. |
| `correr.sh` | Compila y corre la red actual y la Línea F a cada intervalo, cien réplicas cada una. |

## Cómo correrlo

Hace falta el Java que trae AnyLogic 8.9 (o cualquier JDK 17) y Git Bash. Desde esta carpeta:

```
./correr.sh
```

Lee los datos de `../RedSubte_mapa/datos`, los mismos que el modelo de AnyLogic, y deja en
`salida/` una tabla por escenario: `<escenario>_resumen.csv` (una fila por réplica: viaje medio,
espera media, transbordos), `<escenario>_carga.csv` (pasajeros por tramo y hora) y otras dos con
el detalle por hora y por estación. Tarda unos quince minutos.
