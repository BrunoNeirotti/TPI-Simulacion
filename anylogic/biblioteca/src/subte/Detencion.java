package subte;

import java.util.Map;

/**
 * Detencion endogena en estacion (D13, parametros decididos el 06/10/2026).
 *
 * <pre>
 *   detencion = max(piso, apertura + (tBaja * bajan + tSube * suben) / canales)
 * </pre>
 *
 * El piso es el dato oficial (24 s lineas actuales, 30 s Linea F) y vive en
 * {@code Recorrido.detencion}. Los tiempos por pasajero son las medianas del TCQSM,
 * 2a ed., parte 5, Exhibit 5-15: 1,85 s por pasajero que baja y 2,1 s por pasajero
 * que sube, por canal de puerta. Los canales de una formacion son
 * coches x puertas por lado x canales por puerta (puertas de doble flujo).
 *
 * {@code apertura} es el tiempo de apertura y cierre de puertas: el TCQSM dice que
 * el flujo de pasajeros es solo el 38 a 64 % de la detencion, pero no se decidio un
 * valor, asi que queda en 0 (el piso oficial lo cubre) y se recorre en sensibilidad.
 */
public final class Detencion {

    /** Puertas por lado y por coche, por linea (supuesto declarado, decisiones.md D13). */
    public static final Map<String, Integer> PUERTAS = Map.of(
            "A", 4, "B", 3, "C", 4, "D", 4, "E", 4, "H", 4, "F", 4);

    public final double tBaja;
    public final double tSube;
    public final double apertura;
    public final int canalesPorPuerta;

    public Detencion(double tBaja, double tSube, double apertura, int canalesPorPuerta) {
        this.tBaja = tBaja;
        this.tSube = tSube;
        this.apertura = apertura;
        this.canalesPorPuerta = canalesPorPuerta;
    }

    /** Valores decididos el 06/10/2026. */
    public static Detencion porDefecto() {
        return new Detencion(1.85, 2.10, 0.0, 2);
    }

    public int canales(String linea, int coches) {
        return coches * PUERTAS.get(linea) * canalesPorPuerta;
    }

    /**
     * Duracion de la detencion de una formacion de {@code coches} coches.
     *
     * @param piso minimo oficial de la linea, en segundos
     */
    public double segundos(double piso, String linea, int coches, int bajan, int suben) {
        double flujo = (tBaja * bajan + tSube * suben) / canales(linea, coches);
        return Math.max(piso, apertura + flujo);
    }
}
