#!/usr/bin/env bash
# Compila el simulador de control y corre la red actual y la red con la Linea F a cada
# intervalo entre trenes, 100 replicas cada una, con los mismos datos que lee el modelo de
# AnyLogic (../RedSubte_mapa/datos). Deja una tabla por escenario en salida/.
#
# Uso, con Git Bash desde esta carpeta:   ./correr.sh
# Si AnyLogic esta en otro lado:          JDK="/ruta/al/jre" ./correr.sh
set -euo pipefail
cd "$(dirname "$0")"

JDK="${JDK:-/c/Program Files/AnyLogic 8.9 Personal Learning Edition/jre}"
D=../RedSubte_mapa/datos
mkdir -p build salida
"$JDK/bin/javac" --release 17 -encoding UTF-8 -d build subte/*.java SimuladorReferencia.java

COMUN="--replicas 100 --semilla 1 --separacion aplicar --detencion endogena --salida salida"
"$JDK/bin/java" -Xmx4g -cp build SimuladorReferencia --datos "$D" $COMUN --prefijo base > /dev/null
echo "listo: red actual"
for I in 090 100 120 150 189; do
    "$JDK/bin/java" -Xmx4g -cp build SimuladorReferencia --datos "$D/escenario_f/I$I" \
        --oferta "$D/escenario_f/oferta_I$I" $COMUN --prefijo "f$I" > /dev/null
    echo "listo: Linea F cada $((10#$I)) s"
done
