package subte;

import java.util.HashMap;
import java.util.Map;

/**
 * Una linea en un sentido: la secuencia de nodos y el tiempo de cada tramo.
 *
 * El indice 0 es la cabecera de salida. {@code tramo[i]} es el tiempo de marcha
 * de {@code nodos[i]} a {@code nodos[i + 1]}, sin detencion.
 */
public final class Recorrido {

    public final String linea;      // "A" ... "H"
    public final int sentido;       // direction_id del GTFS
    public final String[] nodos;
    public final double[] tramo;    // segundos
    private final Map<String, Integer> indice = new HashMap<>();

    /** Detencion por parada intermedia (D13: fija primero, 24 s; 30 s en la F). */
    public double detencion = 24.0;

    Recorrido(String linea, int sentido, String[] nodos, double[] tramo) {
        this.linea = linea;
        this.sentido = sentido;
        this.nodos = nodos;
        this.tramo = tramo;
        for (int i = 0; i < nodos.length; i++) {
            indice.put(nodos[i], i);
        }
    }

    public int largo() {
        return nodos.length;
    }

    /** Indice del nodo en este recorrido, o -1 si no lo sirve. */
    public int indice(String nodo) {
        Integer i = indice.get(nodo);
        return i == null ? -1 : i;
    }

    /**
     * Tiempo a bordo de i a j (i menor que j): marcha mas una detencion por cada
     * parada intermedia. Quien sube no espera la detencion de su estacion ni
     * quien baja la de la suya (guia del modelo, seccion 7, punto 1).
     */
    public double tiempoEntre(int i, int j) {
        double t = 0;
        for (int k = i; k < j; k++) {
            t += tramo[k];
        }
        return t + detencion * (j - i - 1);
    }

    /** Tiempo de punta a punta, con detenciones intermedias. */
    public double tiempoTotal() {
        return tiempoEntre(0, nodos.length - 1);
    }

    public String clave() {
        return linea + "/" + sentido;
    }

    @Override
    public String toString() {
        return "Linea " + linea + " sentido " + sentido + " (" + nodos[0] + " -> " + nodos[nodos.length - 1] + ")";
    }
}
