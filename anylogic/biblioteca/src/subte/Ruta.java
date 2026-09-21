package subte;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * El camino precalculado de un par de complejos, partido en etapas a bordo.
 *
 * Sale de la columna `camino` de caminos_minimos.csv (asignacion todo-o-nada,
 * D9). Cada tramo de nodos consecutivos de una misma linea es una etapa; entre
 * etapas hay una caminata de transbordo con el tiempo del GTFS. El pasajero
 * espera en el anden de `sube` una formacion del recorrido de la etapa y baja en
 * `baja`.
 */
public final class Ruta {

    public static final class Etapa {
        public final Recorrido recorrido;
        public final int sube;              // indice en el recorrido
        public final int baja;
        public final double caminataPrevia; // segundos de transbordo antes de esta etapa

        Etapa(Recorrido recorrido, int sube, int baja, double caminataPrevia) {
            this.recorrido = recorrido;
            this.sube = sube;
            this.baja = baja;
            this.caminataPrevia = caminataPrevia;
        }

        public String nodoSube() {
            return recorrido.nodos[sube];
        }

        public String nodoBaja() {
            return recorrido.nodos[baja];
        }

        public double tiempoABordo() {
            return recorrido.tiempoEntre(sube, baja);
        }
    }

    public final String origen;     // complejo
    public final String destino;    // complejo
    public final Etapa[] etapas;
    public final double tiempoTabla;     // tiempo_s de caminos_minimos.csv
    public final int transbordosTabla;   // n_transbordos de caminos_minimos.csv
    public final int caminatas;          // aristas de transbordo recorridas

    private Ruta(String origen, String destino, Etapa[] etapas, double tiempoTabla,
                 int transbordosTabla, int caminatas) {
        this.origen = origen;
        this.destino = destino;
        this.etapas = etapas;
        this.tiempoTabla = tiempoTabla;
        this.transbordosTabla = transbordosTabla;
        this.caminatas = caminatas;
    }

    /** Tiempo sin esperas: a bordo mas caminatas. Tiene que coincidir con tiempo_s. */
    public double tiempoSinEsperas() {
        double t = 0;
        for (Etapa e : etapas) {
            t += e.caminataPrevia + e.tiempoABordo();
        }
        return t;
    }

    public static String clave(String origen, String destino) {
        return origen + ">" + destino;
    }

    public static Map<String, Ruta> leer(Path carpeta, Red red) {
        Csv c = Csv.leer(carpeta.resolve("caminos_minimos.csv"));
        int cO = c.col("comp_origen"), cD = c.col("comp_destino"), cT = c.col("tiempo_s");
        int cN = c.col("n_transbordos"), cCam = c.col("camino");
        Map<String, Ruta> rutas = new HashMap<>();
        for (String[] f : c.filas()) {
            String[] camino = f[cCam].trim().split(" ");
            rutas.put(clave(f[cO], f[cD]), armar(f[cO], f[cD], camino, Csv.num(f[cT]),
                    (int) Csv.num(f[cN]), red));
        }
        return rutas;
    }

    static Ruta armar(String origen, String destino, String[] camino, double tiempo,
                      int transbordos, Red red) {
        // grupos de nodos consecutivos de la misma linea
        List<List<String>> grupos = new ArrayList<>();
        for (String nodo : camino) {
            String linea = red.nodo(nodo).linea;
            if (grupos.isEmpty() || !red.nodo(last(grupos)).linea.equals(linea)) {
                grupos.add(new ArrayList<>());
            }
            grupos.get(grupos.size() - 1).add(nodo);
        }
        List<Etapa> etapas = new ArrayList<>();
        double caminata = 0;
        int caminatas = 0;
        for (int g = 0; g < grupos.size(); g++) {
            List<String> grupo = grupos.get(g);
            if (g > 0) {
                String de = last(grupos.subList(0, g));
                double t = red.transbordo(de, grupo.get(0));
                if (Double.isNaN(t)) {
                    throw new IllegalStateException("sin transbordo " + de + " -> " + grupo.get(0)
                            + " en " + origen + ">" + destino);
                }
                caminata += t;
                caminatas++;
            }
            if (grupo.size() == 1) {
                continue; // se pasa caminando por un nodo sin subir a esa linea
            }
            // Un grupo de la misma linea puede cambiar de sentido: el grafo del
            // paso 6 no distingue sentido en los nodos, y para llegar a Alberti o
            // salir de Pasco (servidas en un solo sentido) el camino sigue de largo
            // y vuelve. Se parte en dos etapas que comparten el nodo de la vuelta,
            // donde el pasajero baja y espera una formacion en sentido contrario.
            for (List<String> tramo : partirPorSentido(red, grupo)) {
                Recorrido r = recorridoQueSirve(red, tramo);
                etapas.add(new Etapa(r, r.indice(tramo.get(0)), r.indice(tramo.get(tramo.size() - 1)), caminata));
                caminata = 0;
            }
        }
        if (etapas.isEmpty()) {
            throw new IllegalStateException("ruta sin etapas: " + origen + ">" + destino);
        }
        return new Ruta(origen, destino, etapas.toArray(new Etapa[0]), tiempo, transbordos, caminatas);
    }

    /** Cambios de sentido dentro de una misma linea (etapas sin caminata entre ellas). */
    public int cambiosDeSentido() {
        int n = 0;
        for (int i = 1; i < etapas.length; i++) {
            if (etapas[i].caminataPrevia == 0 && etapas[i].recorrido.linea.equals(etapas[i - 1].recorrido.linea)) {
                n++;
            }
        }
        return n;
    }

    private static List<List<String>> partirPorSentido(Red red, List<String> grupo) {
        List<List<String>> tramos = new ArrayList<>();
        List<String> actual = new ArrayList<>(List.of(grupo.get(0), grupo.get(1)));
        Recorrido r = recorridoQueSirve(red, actual);
        for (int k = 2; k < grupo.size(); k++) {
            String previo = grupo.get(k - 1), nodo = grupo.get(k);
            if (r.indice(nodo) == r.indice(previo) + 1) {
                actual.add(nodo);
            } else {
                tramos.add(actual);
                actual = new ArrayList<>(List.of(previo, nodo));
                r = recorridoQueSirve(red, actual);
            }
        }
        tramos.add(actual);
        return tramos;
    }

    private static Recorrido recorridoQueSirve(Red red, List<String> grupo) {
        String linea = red.nodo(grupo.get(0)).linea;
        for (int sentido = 0; sentido <= 1; sentido++) {
            Recorrido r = red.recorrido(linea, sentido);
            int i0 = r.indice(grupo.get(0));
            if (i0 < 0) {
                continue;
            }
            boolean ok = true;
            for (int k = 1; k < grupo.size() && ok; k++) {
                ok = r.indice(grupo.get(k)) == i0 + k;
            }
            if (ok) {
                return r;
            }
        }
        throw new IllegalStateException("ningun recorrido de la " + linea + " sirve " + grupo);
    }

    private static String last(List<List<String>> grupos) {
        List<String> g = grupos.get(grupos.size() - 1);
        return g.get(g.size() - 1);
    }
}
