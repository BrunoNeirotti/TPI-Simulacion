package subte;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.TreeMap;

/**
 * La demanda del modelo: llegadas de Poisson no homogeneo por complejo de origen.
 *
 * La tasa es constante dentro de cada bloque de 15 min: viajes de la hora
 * (demanda_modelo_od_hora.csv) por la fraccion del bloque
 * (demanda_modelo_intrahorario.csv), dividido 900 s. Con tasa constante por
 * tramos, muestrear exponenciales y reiniciar en cada borde de bloque es exacto,
 * porque la exponencial no tiene memoria.
 *
 * Los 78 procesos se pueden correr por separado ({@link #proximaLlegada}) o
 * juntos ({@link #proximaLlegadaRed} y {@link #sortearOrigen}): la
 * superposicion de procesos de Poisson independientes es un Poisson con la suma
 * de las tasas, y el origen de cada llegada se sortea en proporcion a la tasa
 * de cada complejo en ese bloque. Las dos formas son equivalentes; la segunda
 * necesita un solo temporizador en AnyLogic.
 *
 * `viajes` tiene decimales y no se redondea (guia, seccion 2.4).
 */
public final class Demanda {

    public static final int BLOQUE_S = 900;
    public static final int BLOQUES = 96;
    public static final double FIN_S = 24 * 3600.0;

    private static final class Origen {
        final double[] viajesHora = new double[24];
        final double[][] fraccion = new double[24][4];
        final String[][] destinos = new String[24][];
        final double[][] acumulada = new double[24][];
    }

    private final Map<String, Origen> origenes = new TreeMap<>();
    private String[] nombres;
    private double[] tasaRed;          // por bloque, suma de las tasas
    private double[][] acumOrigen;     // por bloque, acumulada de tasas por origen

    public static Demanda leer(Path carpeta) {
        Demanda d = new Demanda();

        Csv od = Csv.leer(carpeta.resolve("demanda_modelo_od_hora.csv"));
        int cO = od.col("comp_origen"), cD = od.col("comp_destino"), cH = od.col("hora"), cV = od.col("viajes");
        Map<String, Map<Integer, List<Object[]>>> tmp = new TreeMap<>();
        for (String[] f : od.filas()) {
            int h = (int) Csv.num(f[cH]);
            double v = Csv.num(f[cV]);
            Origen o = d.origenes.computeIfAbsent(f[cO], k -> new Origen());
            o.viajesHora[h] += v;
            tmp.computeIfAbsent(f[cO], k -> new HashMap<>())
                    .computeIfAbsent(h, k -> new ArrayList<>()).add(new Object[] {f[cD], v});
        }
        for (Map.Entry<String, Map<Integer, List<Object[]>>> e : tmp.entrySet()) {
            Origen o = d.origenes.get(e.getKey());
            for (Map.Entry<Integer, List<Object[]>> eh : e.getValue().entrySet()) {
                List<Object[]> lista = eh.getValue();
                String[] dest = new String[lista.size()];
                double[] acum = new double[lista.size()];
                double s = 0;
                for (int i = 0; i < lista.size(); i++) {
                    dest[i] = (String) lista.get(i)[0];
                    s += (Double) lista.get(i)[1];
                    acum[i] = s;
                }
                for (int i = 0; i < acum.length; i++) {
                    acum[i] /= s;
                }
                o.destinos[eh.getKey()] = dest;
                o.acumulada[eh.getKey()] = acum;
            }
        }

        Csv in = Csv.leer(carpeta.resolve("demanda_modelo_intrahorario.csv"));
        int cC = in.col("complejo"), cHr = in.col("hora"), cF = in.col("franja"), cS = in.col("share");
        for (String[] f : in.filas()) {
            Origen o = d.origenes.get(f[cC]);
            if (o == null) {
                continue; // complejo sin demanda de origen
            }
            int h = (int) Csv.num(f[cHr]);
            int q = Integer.parseInt(f[cF].substring(3, 5)) / 15;
            o.fraccion[h][q] = Csv.num(f[cS]);
        }
        // Normalizar por hora: en las horas 0 a 4 el share no suma 1 (guia 2.5).
        // Si una hora con viajes no tiene perfil, se reparte uniforme.
        for (Origen o : d.origenes.values()) {
            for (int h = 0; h < 24; h++) {
                double s = Arrays.stream(o.fraccion[h]).sum();
                for (int q = 0; q < 4; q++) {
                    o.fraccion[h][q] = s > 0 ? o.fraccion[h][q] / s : 0.25;
                }
            }
        }
        d.armarRed();
        return d;
    }

    private void armarRed() {
        nombres = origenes.keySet().toArray(new String[0]);
        tasaRed = new double[BLOQUES];
        acumOrigen = new double[BLOQUES][nombres.length];
        for (int b = 0; b < BLOQUES; b++) {
            double s = 0;
            for (int i = 0; i < nombres.length; i++) {
                s += tasa(origenes.get(nombres[i]), b);
                acumOrigen[b][i] = s;
            }
            tasaRed[b] = s;
        }
    }

    private static double tasa(Origen o, int bloque) {
        int h = bloque / 4, q = bloque % 4;
        return o.viajesHora[h] * o.fraccion[h][q] / BLOQUE_S;
    }

    private static double proxima(double t, Random rng, java.util.function.IntToDoubleFunction tasa) {
        while (t < FIN_S) {
            int b = (int) (t / BLOQUE_S);
            double fin = (b + 1) * (double) BLOQUE_S;
            double r = tasa.applyAsDouble(b);
            if (r > 0) {
                double dt = -Math.log(1.0 - rng.nextDouble()) / r;
                if (t + dt < fin) {
                    return t + dt;
                }
            }
            t = fin;
        }
        return Double.POSITIVE_INFINITY;
    }

    /** Proxima llegada desde un complejo, en segundos desde medianoche, o infinito. */
    public double proximaLlegada(String complejo, double t, Random rng) {
        Origen o = origenes.get(complejo);
        return proxima(t, rng, b -> tasa(o, b));
    }

    /** Proxima llegada en toda la red, o infinito. */
    public double proximaLlegadaRed(double t, Random rng) {
        return proxima(t, rng, b -> tasaRed[b]);
    }

    /** Origen de una llegada de la red ocurrida en el instante t. */
    public String sortearOrigen(double t, Random rng) {
        int b = Math.min((int) (t / BLOQUE_S), BLOQUES - 1);
        double[] acum = acumOrigen[b];
        double u = rng.nextDouble() * acum[acum.length - 1];
        return nombres[buscar(acum, u)];
    }

    /** Destino de un viaje que sale del complejo en la hora dada. */
    public String sortearDestino(String complejo, int hora, Random rng) {
        Origen o = origenes.get(complejo);
        double[] acum = o.acumulada[hora];
        if (acum == null) {
            throw new IllegalStateException(complejo + " no tiene destinos a las " + hora + " h");
        }
        return o.destinos[hora][buscar(acum, rng.nextDouble() * acum[acum.length - 1])];
    }

    /**
     * Primer indice con acumulada estrictamente mayor que u: el intervalo del
     * elemento i es [acum[i-1], acum[i]). Si u cae justo en un borde repetido
     * (elementos de peso cero), avanza hasta el primero con peso.
     */
    static int buscar(double[] acum, double u) {
        int i = Arrays.binarySearch(acum, u);
        if (i >= 0) {
            while (i < acum.length - 1 && acum[i] <= u) {
                i++;
            }
        } else {
            i = -i - 1;
        }
        return Math.min(i, acum.length - 1);
    }

    public String[] complejosDeOrigen() {
        return nombres.clone();
    }

    public double viajesDelDia() {
        double s = 0;
        for (Origen o : origenes.values()) {
            for (double v : o.viajesHora) {
                s += v;
            }
        }
        return s;
    }

    public double viajesDeLaHora(int hora) {
        double s = 0;
        for (Origen o : origenes.values()) {
            s += o.viajesHora[hora];
        }
        return s;
    }

    /** Viajes esperados en la red en un bloque de 15 min. */
    public double esperadosEnBloque(int bloque) {
        return tasaRed[bloque] * BLOQUE_S;
    }
}
