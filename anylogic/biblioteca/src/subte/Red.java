package subte;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * La topologia: nodos, recorridos por linea y sentido, y transbordos.
 *
 * Sale de grafo_nodos.csv y grafo_aristas.csv. Un nodo es un par
 * linea-estacion; un complejo es la estacion fisica (guia, seccion 3.1). El
 * grafo es dirigido por Alberti y Pasco, que se sirven en un solo sentido.
 */
public final class Red {

    public static final class Nodo {
        public final String id;
        public final String linea;
        public final String nombre;
        public final double lat;
        public final double lon;

        Nodo(String id, String linea, String nombre, double lat, double lon) {
            this.id = id;
            this.linea = linea;
            this.nombre = nombre;
            this.lat = lat;
            this.lon = lon;
        }
    }

    private final Map<String, Nodo> nodos = new LinkedHashMap<>();
    private final Map<String, Recorrido> recorridos = new TreeMap<>();
    private final Map<String, Double> transbordo = new HashMap<>();

    public static Red leer(Path carpeta) {
        Red red = new Red();

        Csv n = Csv.leer(carpeta.resolve("grafo_nodos.csv"));
        int cId = n.col("nodo_id"), cLinea = n.col("linea"), cNombre = n.col("nombre");
        int cLat = n.col("lat"), cLon = n.col("lon");
        for (String[] f : n.filas()) {
            String linea = f[cLinea].replace("Linea", "");
            red.nodos.put(f[cId], new Nodo(f[cId], linea, f[cNombre], Csv.num(f[cLat]), Csv.num(f[cLon])));
        }

        Csv a = Csv.leer(carpeta.resolve("grafo_aristas.csv"));
        int cTipo = a.col("tipo"), cDe = a.col("de_nodo"), cA = a.col("a_nodo");
        int cLin = a.col("linea"), cSen = a.col("direction_id"), cOrd = a.col("orden"), cT = a.col("t_s");
        // tramos agrupados por linea y sentido, ordenados por `orden`
        Map<String, TreeMap<Double, String[]>> tramos = new TreeMap<>();
        for (String[] f : a.filas()) {
            if (f[cTipo].equals("transbordo")) {
                red.transbordo.put(f[cDe] + ">" + f[cA], Csv.num(f[cT]));
            } else {
                String clave = f[cLin].replace("Linea", "") + "/" + (int) Csv.num(f[cSen]);
                tramos.computeIfAbsent(clave, k -> new TreeMap<>())
                        .put(Csv.num(f[cOrd]), new String[] {f[cDe], f[cA], f[cT]});
            }
        }
        for (Map.Entry<String, TreeMap<Double, String[]>> e : tramos.entrySet()) {
            List<String[]> lista = new ArrayList<>(e.getValue().values());
            String[] seq = new String[lista.size() + 1];
            double[] t = new double[lista.size()];
            seq[0] = lista.get(0)[0];
            for (int i = 0; i < lista.size(); i++) {
                String[] tr = lista.get(i);
                if (!tr[0].equals(seq[i])) {
                    throw new IllegalStateException("tramos no encadenados en " + e.getKey() + ": " + tr[0]);
                }
                seq[i + 1] = tr[1];
                t[i] = Csv.num(tr[2]);
            }
            String[] partes = e.getKey().split("/");
            red.recorridos.put(e.getKey(), new Recorrido(partes[0], Integer.parseInt(partes[1]), seq, t));
        }
        return red;
    }

    public Nodo nodo(String id) {
        Nodo x = nodos.get(id);
        if (x == null) {
            throw new IllegalArgumentException("nodo desconocido: " + id);
        }
        return x;
    }

    public Collection<Nodo> nodos() {
        return nodos.values();
    }

    public Collection<Recorrido> recorridos() {
        return recorridos.values();
    }

    public Recorrido recorrido(String linea, int sentido) {
        Recorrido r = recorridos.get(linea + "/" + sentido);
        if (r == null) {
            throw new IllegalArgumentException("no hay recorrido " + linea + "/" + sentido);
        }
        return r;
    }

    /** Tiempo de caminata del transbordo de un nodo a otro, o NaN si no existe. */
    public double transbordo(String de, String a) {
        Double t = transbordo.get(de + ">" + a);
        return t == null ? Double.NaN : t;
    }

    public int cantidadTransbordos() {
        return transbordo.size();
    }
}
