#!/usr/bin/env bash
# Corridas del informe final: red actual y red con la Linea F en el barrido de D7,
# 10 replicaciones cada una, y la sensibilidad de la detencion (D13).
# Salidas: data/processed/escenario_f/informe/<prefijo>_{resumen,carga,hora,ascensos}.csv
# Uso, desde anylogic/biblioteca:   ./referencia/correr_informe.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
CP="subte.jar;referencia/build"
P=../../data/processed
O=$P/escenario_f/informe
mkdir -p "$O" referencia/build
"$JDK/bin/javac" --release 17 -encoding UTF-8 -cp subte.jar -d referencia/build referencia/SimuladorReferencia.java
(cd ../.. && python src/16_oferta_linea_f.py 90 100 120 150 189 >/dev/null && python src/21_escenarios_por_intervalo.py 90 100 120 150 189 >/dev/null)
COMUN="--replicas 10 --semilla 1 --separacion aplicar --detencion endogena --salida $O"

corre() {  # prefijo, datos, [oferta], [escala]
  local pref=$1 datos=$2 oferta=${3:-} escala=${4:-1}
  if [ -n "$oferta" ]; then
    "$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia --datos "$datos" --oferta "$oferta" $COMUN --detencion-escala "$escala" --prefijo "$pref" >/dev/null
  else
    "$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia --datos "$datos" $COMUN --detencion-escala "$escala" --prefijo "$pref" >/dev/null
  fi
  echo "listo $pref"
}

corre base $P
for I in 090 100 120 150 189; do corre f$I $P/escenario_f/I$I $P/escenario_f/oferta_I$I; done
# sensibilidad de la detencion por pasajero (D13): sin termino (piso fijo), doble y triple
for K in 0 2 3; do
  corre base_det$K $P "" $K
  corre f100_det$K $P/escenario_f/I100 $P/escenario_f/oferta_I100 $K
done
