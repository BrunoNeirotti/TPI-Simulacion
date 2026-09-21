#!/usr/bin/env bash
# Compila la biblioteca con el JDK 17 que trae AnyLogic 8.9, arma subte.jar y
# corre la prueba contra los CSV reales de data/processed.
#
# Uso, desde esta carpeta:   ./compilar.sh
# Si AnyLogic esta en otro lado:   JDK="/ruta/al/jre" ./compilar.sh
set -euo pipefail
cd "$(dirname "$0")"

JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
JAVAC="$JDK/bin/javac"
JAR="$JDK/bin/jar"
JAVA="$JDK/bin/java"
SEP=";"   # separador de classpath en Windows

rm -rf build
mkdir -p build prueba/build
"$JAVAC" --release 17 -encoding UTF-8 -Xlint:all -d build src/subte/*.java
"$JAR" --create --file subte.jar -C build .
"$JAVAC" --release 17 -encoding UTF-8 -cp build -d prueba/build prueba/PruebaBiblioteca.java
"$JAVA" -cp "build${SEP}prueba/build" PruebaBiblioteca ../../data/processed
