package subte;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.TreeMap;

/**
 * La oferta de las lineas actuales: despachos por cabecera (D14), apertura (D16)
 * e intervalos con distribucion empirica (D17). Sale del paso 12
 * (src/12_ajuste_intervalos.py).
 *
 * El dataset de despachos llama A y D a las cabeceras; aca se traducen al
 * recorrido del grafo con cabeceras_despacho.csv. No suponer que A es la
 * cabecera 1: en la E es al reves.
 */
public final class Oferta {

    /** Una cabecera: el lado del dataset y el recorrido por el que despacha. */
    public static final class Cabecera {
        public final String linea;
        public final String lado;           // "A" o "D"
        public final Recorrido recorrido;
        public final double apertura;       // s desde medianoche
        public final double ultimaSalida;   // s desde medianoche

        Cabecera(String linea, String lado, Recorrido recorrido, double apertura, double ultimaSalida) {
            this.linea = linea;
            this.lado = lado;
            this.recorrido = recorrido;
            this.apertura = apertura;
            this.ultimaSalida = ultimaSalida;
        }

        @Override
        public String toString() {
            return linea + "/" + lado;
        }
    }

    /** Una formacion que arranca en la apertura desde una estacion (D16). */
    public static final class Arranque {
        public final Cabecera cabecera;
        public final int indice;            // estacion de arranque en el recorrido (0 = cabecera)
        public final double hora;

        Arranque(Cabecera cabecera, int indice, double hora) {
            this.cabecera = cabecera;
            this.indice = indice;
            this.hora = hora;
        }
    }

    public static final int PUNTOS = 501;

    private final Map<String, Cabecera> cabeceras = new TreeMap<>();
    private final List<Arranque> arranques = new ArrayList<>();
    private final Map<String, double[]> cuantiles = new HashMap<>();

    public static Oferta leer(Path carpeta, Red red) {
        Oferta o = new Oferta();

        Csv c = Csv.leer(carpeta.resolve("cabeceras_despacho.csv"));
        int cL = c.col("linea"), cC = c.col("cabecera"), cS = c.col("direction_id");
        int cNod = c.col("nodo_cabecera"), cAp = c.col("apertura_s"), cUl = c.col("ultima_salida_s");
        for (String[] f : c.filas()) {
            Recorrido r = red.recorrido(f[cL], (int) Csv.num(f[cS]));
            if (!r.nodos[0].equals(f[cNod])) {
                throw new IllegalStateException("la cabecera " + f[cL] + "/" + f[cC]
                        + " no es el inicio de " + r);
            }
            o.cabeceras.put(f[cL] + "/" + f[cC],
                    new Cabecera(f[cL], f[cC], r, Csv.num(f[cAp]), Csv.num(f[cUl])));
        }

        Csv a = Csv.leer(carpeta.resolve("apertura_formaciones.csv"));
        int aL = a.col("linea"), aC = a.col("cabecera"), aN = a.col("nodo_inicio"), aH = a.col("hora_s");
        for (String[] f : a.filas()) {
            Cabecera cab = o.cabecera(f[aL], f[aC]);
            int i = cab.recorrido.indice(f[aN]);
            if (i < 0) {
                throw new IllegalStateException(f[aN] + " no esta en " + cab.recorrido);
            }
            o.arranques.add(new Arranque(cab, i, Csv.num(f[aH])));
        }

        Csv e = Csv.leer(carpeta.resolve("intervalos_empiricos.csv"));
        int eL = e.col("linea"), eC = e.col("cabecera"), eH = e.col("hora"), eP = e.col("p"), eI = e.col("intervalo_s");
        Map<String, List<double[]>> tmp = new HashMap<>();
        for (String[] f : e.filas()) {
            String k = f[eL] + "/" + f[eC] + "/" + (int) Csv.num(f[eH]);
            tmp.computeIfAbsent(k, x -> new ArrayList<>()).add(new double[] {Csv.num(f[eP]), Csv.num(f[eI])});
        }
        for (Map.Entry<String, List<double[]>> en : tmp.entrySet()) {
            List<double[]> l = en.getValue();
            l.sort((x, y) -> Double.compare(x[0], y[0]));
            if (l.size() != PUNTOS) {
                throw new IllegalStateException(en.getKey() + ": " + l.size() + " cuantiles, se esperaban " + PUNTOS);
            }
            double[] q = new double[PUNTOS];
            for (int i = 0; i < PUNTOS; i++) {
                q[i] = l.get(i)[1];
            }
            o.cuantiles.put(en.getKey(), q);
        }
        return o;
    }

    public Cabecera cabecera(String linea, String lado) {
        Cabecera c = cabeceras.get(linea + "/" + lado);
        if (c == null) {
            throw new IllegalArgumentException("no hay cabecera " + linea + "/" + lado);
        }
        return c;
    }

    public List<Cabecera> cabeceras() {
        return new ArrayList<>(cabeceras.values());
    }

    public List<Arranque> arranques() {
        return Collections.unmodifiableList(arranques);
    }

    /**
     * Si alguna formacion de la apertura arranca en la cabecera misma. Cuando no
     * (pasa en la variante de la D de septiembre de 2024), los despachos regulares
     * se programan desde la hora de apertura, sin formacion en la cabecera.
     */
    public boolean arrancaEnCabecera(Cabecera c) {
        for (Arranque a : arranques) {
            if (a.cabecera == c && a.indice == 0) {
                return true;
            }
        }
        return false;
    }

    /**
     * Intervalo hasta el proximo despacho, muestreado de la empirica de la hora
     * de t por transformada inversa, interpolando entre cuantiles (Law, cap. 6).
     */
    public double intervalo(Cabecera c, double t, double u) {
        int hora = Math.max(5, Math.min(23, (int) (t / 3600)));
        double[] q = cuantiles.get(c.linea + "/" + c.lado + "/" + hora);
        if (q == null) {
            throw new IllegalStateException("sin tabla para " + c + " a las " + hora + " h");
        }
        double x = u * (PUNTOS - 1);
        int i = Math.min((int) x, PUNTOS - 2);
        return q[i] + (x - i) * (q[i + 1] - q[i]);
    }

    /** Proximo despacho desde la cabecera despues de t, o infinito si ya cerro. */
    public double proximaSalida(Cabecera c, double t, Random rng) {
        double s = t + intervalo(c, t, rng.nextDouble());
        return s <= c.ultimaSalida ? s : Double.POSITIVE_INFINITY;
    }
}
