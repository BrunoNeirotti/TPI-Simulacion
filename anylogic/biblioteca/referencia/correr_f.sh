#!/usr/bin/env bash
# Escenario con Linea F (paso 8): barrido del intervalo entre trenes (D7) con el
# simulador de referencia, 10 replicaciones, detencion endogena (D13) y separacion
# por tramo literal (D15). Deja data/processed/escenario_f/ref_*.csv y el reporte 17.
# Uso, desde anylogic/biblioteca:   ./referencia/correr_f.sh [intervalos...]
set -euo pipefail
cd "$(dirname "$0")/.."
JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
CP="subte.jar;referencia/build"
P=../../data/processed
INT="${*:-90 100 120 150 189}"
(cd ../.. && python src/14_grafo_linea_f.py && python src/15_demanda_linea_f.py && python src/16_oferta_linea_f.py $INT && python src/21_escenarios_por_intervalo.py $INT)
mkdir -p referencia/build
"$JDK/bin/javac" --release 17 -encoding UTF-8 -cp subte.jar -d referencia/build referencia/SimuladorReferencia.java
COMUN="--replicas 10 --semilla 1 --separacion aplicar --detencion endogena --salida $P/escenario_f"
"$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia --datos $P $COMUN --prefijo ref_base >/dev/null
for I in $INT; do
  N=$(printf "%03d" "$I")
  "$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia --datos $P/escenario_f/I$N \
      --oferta $P/escenario_f/oferta_I$N $COMUN --prefijo ref_f_I$N >/dev/null
done
(cd ../.. && python src/17_barrido_linea_f.py $INT)
