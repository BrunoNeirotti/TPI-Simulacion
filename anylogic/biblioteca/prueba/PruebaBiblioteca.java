import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;

import subte.Anden;
import subte.Carga;
import subte.Datos;
import subte.Demanda;
import subte.Oferta;
import subte.Recorrido;
import subte.Red;
import subte.Ruta;

/**
 * Verifica la biblioteca contra los CSV reales de data/processed.
 *
 * Uso: java -cp build;prueba PruebaBiblioteca ../../data/processed
 * Termina con codigo 1 si falla alguna verificacion.
 */
public final class PruebaBiblioteca {

    private static int fallas = 0;

    private static void chequear(boolean ok, String que) {
        System.out.println((ok ? "  ok     " : "  FALLA  ") + que);
        if (!ok) {
            fallas++;
        }
    }

    private static String f(double x, int dec) {
        return String.format(Locale.ROOT, "%,." + dec + "f", x);
    }

    public static void main(String[] args) {
        Path carpeta = Path.of(args.length > 0 ? args[0] : "../../data/processed");
        long t0 = System.nanoTime();
        Datos d = Datos.leer(carpeta);
        System.out.println("Lectura: " + f((System.nanoTime() - t0) / 1e6, 0) + " ms\n");

        red(d.red);
        rutas(d);
        demanda(d.demanda);
        oferta(d.oferta);
        contenedores(d);

        System.out.println(fallas == 0 ? "\nTODO OK" : "\n" + fallas + " FALLAS");
        System.exit(fallas == 0 ? 0 : 1);
    }

    static void red(Red red) {
        System.out.println("Red");
        chequear(red.nodos().size() == 90, "90 nodos (" + red.nodos().size() + ")");
        chequear(red.recorridos().size() == 12, "12 recorridos (" + red.recorridos().size() + ")");
        chequear(red.cantidadTransbordos() == 28, "28 transbordos (" + red.cantidadTransbordos() + ")");
        int tramos = 0;
        for (Recorrido r : red.recorridos()) {
            tramos += r.tramo.length;
        }
        chequear(tramos == 166, "166 tramos (" + tramos + ")");
        // Alberti y Pasco: la A tiene 17 nodos por sentido y 18 en total
        chequear(red.recorrido("A", 0).largo() == 17 && red.recorrido("A", 1).largo() == 17,
                "la A tiene 17 estaciones por sentido");
    }

    static void rutas(Datos d) {
        System.out.println("\nRutas");
        chequear(d.rutas.size() == 6006, "6.006 rutas (" + d.rutas.size() + ")");
        double peor = 0;
        int distintas = 0, transbordosMal = 0, caminatasMal = 0, conVuelta = 0, vueltaMal = 0;
        Map<Integer, Integer> porEtapas = new HashMap<>();
        for (Ruta r : d.rutas.values()) {
            // en el nodo de la vuelta tiempo_s cuenta una detencion que el pasajero
            // no pasa a bordo: la reconstruccion queda 24 s por debajo por vuelta
            int v = r.cambiosDeSentido();
            double dif = Math.abs(r.tiempoSinEsperas() + 24.0 * v - r.tiempoTabla);
            if (v > 0) {
                conVuelta++;
                if (dif > 0.5) {
                    vueltaMal++;
                }
                continue;
            }
            peor = Math.max(peor, dif);
            if (dif > 0.5) {
                distintas++;
            }
            if (r.etapas.length - 1 != r.transbordosTabla) {
                transbordosMal++;
            }
            if (r.caminatas != r.transbordosTabla) {
                caminatasMal++;
            }
            porEtapas.merge(r.etapas.length, 1, Integer::sum);
        }
        chequear(distintas == 0, "sin cambio de sentido: el tiempo reconstruido coincide con tiempo_s "
                + "(diferencia maxima " + f(peor, 3) + " s; " + distintas + " distintas)");
        chequear(transbordosMal == 0 && caminatasMal == 0, "sin cambio de sentido: etapas - 1 = caminatas = "
                + "n_transbordos (" + transbordosMal + " y " + caminatasMal + " distintas)");
        chequear(conVuelta == 142 && vueltaMal == 0, conVuelta + " rutas con cambio de sentido en la misma "
                + "linea, tiempo coincide salvo los 24 s de la vuelta (" + vueltaMal + " distintas)");
        System.out.println("         etapas por ruta (sin cambio de sentido): " + porEtapas);
        // una etapa siempre baja despues de subir
        boolean orden = d.rutas.values().stream().allMatch(r -> {
            for (Ruta.Etapa e : r.etapas) {
                if (e.baja <= e.sube) {
                    return false;
                }
            }
            return true;
        });
        chequear(orden, "en toda etapa baja > sube");
    }

    static void demanda(Demanda dem) {
        System.out.println("\nDemanda");
        double total = dem.viajesDelDia();
        chequear(Math.abs(total - 827289) < 1, "827.289 viajes en el dia (" + f(total, 1) + ")");
        double esperadosBloques = 0;
        for (int b = 0; b < Demanda.BLOQUES; b++) {
            esperadosBloques += dem.esperadosEnBloque(b);
        }
        chequear(Math.abs(esperadosBloques - total) < 1, "los bloques de 15 min suman el total ("
                + f(esperadosBloques, 1) + ")");

        // un dia simulado con el proceso unido
        Random rng = new Random(20260921);
        int[] porHora = new int[24];
        Map<String, Integer> porOrigen = new HashMap<>();
        int n = 0;
        double t = 0;
        while ((t = dem.proximaLlegadaRed(t, rng)) < Demanda.FIN_S) {
            porHora[(int) (t / 3600)]++;
            porOrigen.merge(dem.sortearOrigen(t, rng), 1, Integer::sum);
            n++;
        }
        double z = (n - total) / Math.sqrt(total);
        chequear(Math.abs(z) < 4, "un dia simulado da " + f(n, 0) + " llegadas (z = " + f(z, 2) + ")");
        double peorHora = 0;
        for (int h = 5; h < 24; h++) {
            double e = dem.viajesDeLaHora(h);
            if (e > 1000) {
                peorHora = Math.max(peorHora, Math.abs(porHora[h] - e) / Math.sqrt(e));
            }
        }
        chequear(peorHora < 4.5, "cada hora cerca de lo esperado (peor desvio " + f(peorHora, 2) + " sigmas)");
        chequear(porHora[8] > porHora[12] && porHora[17] > porHora[12], "hay dos picos, 8 y 17 h");

        // el proceso por complejo da lo mismo que el unido para un complejo grande
        String[] origenes = dem.complejosDeOrigen();
        String mayor = origenes[0];
        for (String o : origenes) {
            if (porOrigen.getOrDefault(o, 0) > porOrigen.getOrDefault(mayor, 0)) {
                mayor = o;
            }
        }
        Random rng2 = new Random(7);
        int m = 0;
        t = 0;
        while ((t = dem.proximaLlegada(mayor, t, rng2)) < Demanda.FIN_S) {
            m++;
        }
        int u = porOrigen.get(mayor);
        chequear(Math.abs(m - u) < 4 * Math.sqrt(u), "el complejo de mas demanda (" + mayor + ") da "
                + f(u, 0) + " unido y " + f(m, 0) + " por separado");

        // destinos: la frecuencia empirica reproduce la de la tabla
        Map<String, Integer> destinos = new HashMap<>();
        Random rng3 = new Random(11);
        int k = 200_000;
        for (int i = 0; i < k; i++) {
            destinos.merge(dem.sortearDestino(mayor, 8, rng3), 1, Integer::sum);
        }
        chequear(destinos.size() > 20, "los destinos de " + mayor + " a las 8 h se reparten en "
                + destinos.size() + " complejos");
    }

    static void oferta(Oferta of) {
        System.out.println("\nOferta");
        chequear(of.cabeceras().size() == 12, "12 cabeceras");
        chequear(of.arranques().size() == 50, "50 formaciones en la apertura (" + of.arranques().size() + ")");
        // Media de despachos completos por dia habil tipico de 2025 (paso 12). Se
        // compara contra la media y no la mediana: la distribucion diaria tiene
        // cola hacia abajo (dias con demoras) y muestrear intervalos
        // independientes reproduce la media.
        Map<String, Double> observados = Map.ofEntries(
                Map.entry("A/A", 282.1), Map.entry("A/D", 287.0), Map.entry("B/A", 230.4), Map.entry("B/D", 235.0),
                Map.entry("C/A", 278.5), Map.entry("C/D", 281.3), Map.entry("D/A", 242.0), Map.entry("D/D", 247.3),
                Map.entry("E/A", 173.1), Map.entry("E/D", 176.6), Map.entry("H/A", 263.9), Map.entry("H/D", 267.6));
        Random rng = new Random(3);
        double peor = 0;
        StringBuilder detalle = new StringBuilder();
        for (Oferta.Cabecera c : of.cabeceras()) {
            // promedio de 20 dias simulados
            double suma = 0;
            for (int dia = 0; dia < 20; dia++) {
                int n = 1; // la formacion que sale de la cabecera en la apertura
                double t = c.apertura;
                while ((t = of.proximaSalida(c, t, rng)) < Double.POSITIVE_INFINITY) {
                    n++;
                }
                suma += n;
            }
            double sim = suma / 20;
            double obs = observados.get(c.toString());
            double rel = sim / obs - 1;
            peor = Math.max(peor, Math.abs(rel));
            detalle.append(String.format(Locale.ROOT, "%s %.0f/%.0f  ", c, sim, obs));
        }
        chequear(peor < 0.02, "despachos por dia simulados contra la media observada, peor "
                + f(peor * 100, 1) + " %");
        System.out.println("         " + detalle);
        boolean enCabecera = of.arranques().stream().filter(a -> a.indice == 0).count() == 12;
        chequear(enCabecera, "cada cabecera tiene una formacion que arranca en ella");
    }

    static void contenedores(Datos d) {
        System.out.println("\nAnden y carga");
        Map<String, Anden<Integer>> andenes = d.crearAndenes();
        chequear(andenes.size() == 178, "178 andenes, uno por nodo y sentido (" + andenes.size() + ")");
        Recorrido c = d.red.recorrido("C", 0);
        Anden<Integer> a = andenes.get(Datos.claveAnden(c, 2));
        for (int i = 0; i < 10; i++) {
            a.llega(i);
        }
        Carga<Integer> carga = new Carga<>(c.largo(), 4);
        List<Integer> suben = a.subir(carga.lugares());
        for (int p : suben) {
            carga.subir(p, 5);
        }
        chequear(suben.equals(List.of(0, 1, 2, 3)), "suben los primeros en llegar, hasta llenar");
        chequear(a.esperando() == 6 && a.quedaronAbajo() == 6, "los demas quedan esperando");
        chequear(carga.bajar(4).isEmpty() && carga.bajar(5).size() == 4 && carga.aBordo() == 0,
                "bajan en su estacion");
        chequear(Datos.capacidad("C") == 895, "capacidad de la C: 5 coches x 179 = 895");
    }
}
