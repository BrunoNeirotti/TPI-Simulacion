#!/usr/bin/env bash
# Compila y corre el simulador de referencia (10 replicaciones del dia habil),
# deja las salidas en data/processed/referencia_*.csv y genera el reporte
# reports/13_verificacion_referencia.md.
#
# Uso, desde anylogic/biblioteca:   ./referencia/correr.sh
# Requiere subte.jar armado (./compilar.sh).
set -euo pipefail
cd "$(dirname "$0")/.."

JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
SEP=";"   # separador de classpath en Windows

mkdir -p referencia/build
"$JDK/bin/javac" --release 17 -encoding UTF-8 -Xlint:all -cp subte.jar -d referencia/build \
    referencia/SimuladorReferencia.java
"$JDK/bin/java" -Xmx4g -cp "subte.jar${SEP}referencia/build" SimuladorReferencia \
    --datos ../../data/processed --salida ../../data/processed --replicas 10 --semilla 1 "$@"
(cd ../.. && python src/13_verificacion_referencia.py)
