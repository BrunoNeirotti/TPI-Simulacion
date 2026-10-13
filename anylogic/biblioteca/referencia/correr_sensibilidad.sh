#!/usr/bin/env bash
# Pregunta 5 del informe: sensibilidad a la desagregacion temporal (D2) y a la regla del
# pasajero que no aborda. Mismas 10 replicaciones y semillas que correr_informe.sh.
# Necesita haber corrido antes src/22_sensibilidad_d2.py y correr_informe.sh (los controles).
# Uso, desde anylogic/biblioteca:   ./referencia/correr_sensibilidad.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
CP="subte.jar;referencia/build"
P=../../data/processed
O=$P/escenario_f/informe
mkdir -p "$O" referencia/build
"$JDK/bin/javac" --release 17 -encoding UTF-8 -cp subte.jar -d referencia/build referencia/SimuladorReferencia.java
(cd ../.. && python src/22_sensibilidad_d2.py >/dev/null)
COMUN="--replicas 10 --semilla 1 --separacion aplicar --detencion endogena --salida $O"

corre() {  # prefijo, datos, oferta, [regla]
  "$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia --datos "$2" --oferta "$3" $COMUN --regla "${4:-espera}" --prefijo "$1" >/dev/null
  echo "listo $1"
}

for V in red plano; do
  corre base_d2$V $P/variantes/d2_$V $P
  corre f100_d2$V $P/escenario_f/I100_d2_$V $P/escenario_f/oferta_I100
done
for R in ilimitada abandona2; do
  corre base_$R $P $P $R
  corre f100_$R $P/escenario_f/I100 $P/escenario_f/oferta_I100 $R
done
