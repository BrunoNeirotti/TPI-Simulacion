#!/usr/bin/env bash
# Compila y corre el simulador de referencia (10 replicaciones del dia habil),
# deja las salidas en data/processed/referencia_*.csv y genera el reporte
# reports/13_verificacion_referencia.md.
#
# Corre dos veces con las mismas semillas: la oferta base y la variante de la
# sensibilidad de D4 (la Linea D con la oferta de septiembre de 2024, salidas
# referencia_d2024_*.csv).
#
# Uso, desde anylogic/biblioteca:   ./referencia/correr.sh
# Requiere subte.jar armado (./compilar.sh).
set -euo pipefail
cd "$(dirname "$0")/.."

JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
SEP=";"   # separador de classpath en Windows
CP="subte.jar${SEP}referencia/build"
DATOS=../../data/processed

mkdir -p referencia/build
"$JDK/bin/javac" --release 17 -encoding UTF-8 -Xlint:all -cp subte.jar -d referencia/build \
    referencia/SimuladorReferencia.java
"$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia \
    --datos "$DATOS" --salida "$DATOS" --replicas 10 --semilla 1 "$@"
"$JDK/bin/java" -Xmx4g -cp "$CP" SimuladorReferencia \
    --datos "$DATOS" --salida "$DATOS" --replicas 10 --semilla 1 \
    --oferta "$DATOS/variantes/oferta_d_2024_09" --prefijo referencia_d2024 "$@"
(cd ../.. && python src/13_verificacion_referencia.py)
