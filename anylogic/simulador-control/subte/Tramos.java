package subte;

import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;

/**
 * Separacion minima por tramo (D15): una formacion no entra a un tramo hasta que la
 * anterior lo dejo. El tramo es el que une dos estaciones consecutivas de un recorrido
 * (una linea en un sentido); las formaciones de recorridos distintos no se afectan.
 *
 * **Linea F (D15, decidida el 06/10/2026 tras el paso 8):** el tramo no puede retener mas que
 * el intervalo minimo tecnico, {@link #INTERVALO_MINIMO_F_S}. Un tramo de la F que tarda mas
 * que eso (Constitucion-Cochabamba, ~100 s) admite dos formaciones a la vez: las separa la
 * senal, no el tramo entero. En las lineas actuales la regla sigue siendo la literal.
 *
 * Con {@code aplicar = false} no retiene a nadie pero cuenta cuantas veces la regla
 * habria actuado: es la verificacion de D15 mientras la detencion es fija.
 */
public final class Tramos {

    /** Intervalo minimo tecnico de la Linea F, el piso de D7 (s). */
    public static final double INTERVALO_MINIMO_F_S = 90.0;

    private final boolean aplicar;
    private final Map<String, double[]> libreDesde = new HashMap<>();

    /** Veces que una formacion tuvo que esperar a que el tramo se liberara. */
    public long retenciones;
    /** Segundos totales de espera por esa causa. */
    public double segundosRetenidos;
    /** Salidas de estacion consultadas. */
    public long salidas;
    /** Detalle por tramo y hora: {retenciones, segundos}, para diagnostico. */
    public final Map<String, double[]> detalle = new TreeMap<>();

    public Tramos(boolean aplicar) {
        this.aplicar = aplicar;
    }

    /**
     * Pide salir de la estacion {@code tramo} del recorrido a la hora {@code ahora} y
     * devuelve la hora a la que puede salir (igual a {@code ahora} si el tramo esta libre).
     */
    public double reservar(Recorrido r, int tramo, double ahora) {
        double[] libre = libreDesde.computeIfAbsent(r.clave(), k -> new double[r.largo()]);
        salidas++;
        double salida = Math.max(ahora, libre[tramo]);
        if (salida > ahora) {
            retenciones++;
            segundosRetenidos += salida - ahora;
            double[] d = detalle.computeIfAbsent(r.clave() + "#" + tramo + "@" + (int) (ahora / 3600), k -> new double[2]);
            d[0]++;
            d[1] += salida - ahora;
        }
        if (!aplicar) {
            salida = ahora;
        }
        double ocupa = r.linea.equals("F") ? Math.min(r.tramo[tramo], INTERVALO_MINIMO_F_S) : r.tramo[tramo];
        libre[tramo] = salida + ocupa;
        return salida;
    }

    public void reiniciar() {
        libreDesde.clear();
        retenciones = 0;
        segundosRetenidos = 0;
        salidas = 0;
        detalle.clear();
    }
}
