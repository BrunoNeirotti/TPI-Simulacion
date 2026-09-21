import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Random;

import subte.Anden;
import subte.Carga;
import subte.Datos;
import subte.Demanda;
import subte.Oferta;
import subte.Recorrido;
import subte.Ruta;

/**
 * Simulador de referencia del modelo base, en Java plano, sin AnyLogic.
 *
 * Reproduce paso por paso la logica de anylogic/modelo/GUIA_CONSTRUCCION.md con la
 * misma biblioteca: los mismos eventos (llegada de pasajero, apertura, despacho),
 * el mismo orden dentro de la detencion (bajan al llegar, suben al partir), las
 * mismas reglas (D12 a D17). Sirve para dos cosas:
 *
 *   1. Verificar la logica antes de armarla en la interfaz, y tener los valores
 *      esperados de los indicadores.
 *   2. Verificacion cruzada: el modelo de AnyLogic tiene que dar lo mismo, dentro
 *      del error de muestreo, con los mismos insumos.
 *
 * No reemplaza al modelo de AnyLogic, que es el entregable del TPI.
 *
 * Uso: java -cp subte.jar;referencia/build SimuladorReferencia
 *        [--datos ../../data/processed] [--salida DIR] [--replicas 10]
 *        [--semilla 1] [--solo C] [--oferta DIR] [--prefijo referencia]
 */
public final class SimuladorReferencia {

    // ------------------------------------------------------------------------
    // Motor de eventos
    // ------------------------------------------------------------------------

    private static final class Evento implements Comparable<Evento> {
        final double t;
        final long orden;
        final Runnable accion;

        Evento(double t, long orden, Runnable accion) {
            this.t = t;
            this.orden = orden;
            this.accion = accion;
        }

        @Override
        public int compareTo(Evento o) {
            int c = Double.compare(t, o.t);
            return c != 0 ? c : Long.compare(orden, o.orden);
        }
    }

    private final PriorityQueue<Evento> cola = new PriorityQueue<>();
    private long secuencia;
    private double ahora;

    private void programar(double t, Runnable accion) {
        cola.add(new Evento(t, secuencia++, accion));
    }

    // ------------------------------------------------------------------------
    // Entidades
    // ------------------------------------------------------------------------

    private static final class Pasajero {
        Ruta ruta;
        int etapa;
        double tIngreso;
        double tLlegoAnden;
        double tEspera;
        int ascensos;

        Ruta.Etapa etapaActual() {
            return ruta.etapas[etapa];
        }
    }

    private static final class Formacion {
        Recorrido recorrido;
        int indice;
        boolean recienSale;
        Carga<Pasajero> carga;
    }

    // ------------------------------------------------------------------------
    // Estado de una replicacion
    // ------------------------------------------------------------------------

    private final Datos datos;
    private final String soloLinea;
    private final Random rng;
    private final Map<String, Anden<Pasajero>> andenes;

    long ingresados, arribados, descartados, caminando, aBordo;
    long vivos, maxVivos, formacionesVivas, maxFormaciones;
    double sumaViaje, sumaEspera;
    long sumaAscensos;
    // por hora de ingreso: viajes que terminaron, suma de espera, de viaje y de ascensos
    final long[] arribadosHora = new long[24];
    final double[] esperaHora = new double[24];
    final double[] viajeHora = new double[24];
    final long[] ascensosHora = new long[24];
    // carga por tramo: pasajeros a bordo al partir, y formaciones, por (anden, hora)
    final Map<String, double[]> cargaSaliente = new HashMap<>();
    final Map<String, double[]> trenesSalientes = new HashMap<>();
    final Map<String, Integer> maxOcupacion = new HashMap<>();

    SimuladorReferencia(Datos datos, String soloLinea, long semilla) {
        this.datos = datos;
        this.soloLinea = soloLinea;
        this.rng = new Random(semilla);
        this.andenes = datos.crearAndenes();
    }

    private boolean correEnEstaCorrida(Ruta r) {
        if (soloLinea.isEmpty()) {
            return true;
        }
        return r.etapas.length == 1 && r.etapas[0].recorrido.linea.equals(soloLinea);
    }

    // ------------------------------------------------------------------------
    // Eventos del modelo (los mismos de la guia, seccion 4)
    // ------------------------------------------------------------------------

    void correr() {
        double inicio = 5 * 3600;
        double t0 = datos.demanda.proximaLlegadaRed(inicio, rng);
        if (t0 < Demanda.FIN_S) {
            programar(t0, this::llegadaPasajero);
        }
        for (Oferta.Arranque a : datos.oferta.arranques()) {
            if (soloLinea.isEmpty() || a.cabecera.linea.equals(soloLinea)) {
                programar(a.hora, () -> arranque(a));
            }
        }
        // cabeceras sin formacion propia en la apertura: los despachos regulares
        // arrancan igual a la hora de apertura
        for (Oferta.Cabecera c : datos.oferta.cabeceras()) {
            if ((soloLinea.isEmpty() || c.linea.equals(soloLinea)) && !datos.oferta.arrancaEnCabecera(c)) {
                programar(c.apertura, () -> programarDespacho(c));
            }
        }
        while (!cola.isEmpty()) {
            Evento e = cola.poll();
            if (e.t > Demanda.FIN_S) {
                break;
            }
            ahora = e.t;
            e.accion.run();
        }
    }

    private void llegadaPasajero() {
        String o = datos.demanda.sortearOrigen(ahora, rng);
        String d = datos.demanda.sortearDestino(o, (int) (ahora / 3600), rng);
        Ruta r = datos.ruta(o, d);
        if (correEnEstaCorrida(r)) {
            Pasajero p = new Pasajero();
            p.ruta = r;
            p.tIngreso = ahora;
            ingresados++;
            vivos++;
            maxVivos = Math.max(maxVivos, vivos);
            llegaAnden(p);
        } else {
            descartados++;
        }
        double prox = datos.demanda.proximaLlegadaRed(ahora, rng);
        if (prox < Demanda.FIN_S) {
            programar(prox, this::llegadaPasajero);
        }
    }

    private void arranque(Oferta.Arranque a) {
        lanzarFormacion(a.cabecera, a.indice);
        if (a.indice == 0) {
            programarDespacho(a.cabecera);
        }
    }

    private void programarDespacho(Oferta.Cabecera c) {
        double s = datos.oferta.proximaSalida(c, ahora, rng);
        if (s < Double.POSITIVE_INFINITY) {
            programar(s, () -> {
                lanzarFormacion(c, 0);
                programarDespacho(c);
            });
        }
    }

    private void lanzarFormacion(Oferta.Cabecera c, int desde) {
        Formacion f = new Formacion();
        f.recorrido = c.recorrido;
        f.indice = desde;
        f.recienSale = true;
        f.carga = new Carga<>(c.recorrido.largo(), Datos.capacidad(c.linea));
        formacionesVivas++;
        maxFormaciones = Math.max(maxFormaciones, formacionesVivas);
        llegaEstacion(f);
    }

    // ------------------------------------------------------------------------
    // Pasajero (guia, seccion 5)
    // ------------------------------------------------------------------------

    private void llegaAnden(Pasajero p) {
        p.tLlegoAnden = ahora;
        andenes.get(Datos.claveAnden(p.etapaActual())).llega(p);
    }

    private void baja(Pasajero p) {
        aBordo--;
        if (p.etapa < p.ruta.etapas.length - 1) {
            p.etapa++;
            double caminata = p.etapaActual().caminataPrevia;
            caminando++;
            programar(ahora + caminata, () -> {
                caminando--;
                llegaAnden(p);
            });
        } else {
            arribados++;
            vivos--;
            int h = (int) (p.tIngreso / 3600);
            double viaje = ahora - p.tIngreso;
            sumaViaje += viaje;
            sumaEspera += p.tEspera;
            sumaAscensos += p.ascensos;
            arribadosHora[h]++;
            viajeHora[h] += viaje;
            esperaHora[h] += p.tEspera;
            ascensosHora[h] += p.ascensos;
        }
    }

    // ------------------------------------------------------------------------
    // Formacion (guia, seccion 6)
    // ------------------------------------------------------------------------

    private void llegaEstacion(Formacion f) {
        // bajan los que llegaron a su estacion
        for (Pasajero p : f.carga.bajar(f.indice)) {
            baja(p);
        }
        boolean ultima = f.indice == f.recorrido.largo() - 1;
        double detencion = (f.recienSale || ultima) ? 0 : f.recorrido.detencion;
        programar(ahora + detencion, () -> parte(f));
    }

    private void parte(Formacion f) {
        f.recienSale = false;
        if (f.indice == f.recorrido.largo() - 1) {
            if (f.carga.aBordo() != 0) {
                throw new IllegalStateException("formacion llega a la cabecera con pasajeros");
            }
            formacionesVivas--;
            return;
        }
        // suben los que esperan, al partir; los que no entran siguen esperando (D12)
        Anden<Pasajero> anden = andenes.get(Datos.claveAnden(f.recorrido, f.indice));
        for (Pasajero p : anden.subir(f.carga.lugares())) {
            f.carga.subir(p, p.etapaActual().baja);
            p.tEspera += ahora - p.tLlegoAnden;
            p.ascensos++;
            aBordo++;
        }
        registrarCarga(f);
        double viaje = f.recorrido.tramo[f.indice];
        programar(ahora + viaje, () -> {
            f.indice++;
            llegaEstacion(f);
        });
    }

    private void registrarCarga(Formacion f) {
        String k = Datos.claveAnden(f.recorrido, f.indice);
        int h = (int) (ahora / 3600);
        cargaSaliente.computeIfAbsent(k, x -> new double[24])[h] += f.carga.aBordo();
        trenesSalientes.computeIfAbsent(k, x -> new double[24])[h] += 1;
        maxOcupacion.merge(k, f.carga.aBordo(), Math::max);
    }

    long enAndenes() {
        long s = 0;
        for (Anden<Pasajero> a : andenes.values()) {
            s += a.esperando();
        }
        return s;
    }

    // ------------------------------------------------------------------------
    // Programa
    // ------------------------------------------------------------------------

    public static void main(String[] args) throws IOException {
        Map<String, String> op = new HashMap<>(Map.of(
                "--datos", "../../data/processed", "--salida", "", "--replicas", "10",
                "--semilla", "1", "--solo", "", "--oferta", "", "--prefijo", "referencia"));
        for (int i = 0; i + 1 < args.length; i += 2) {
            op.put(args[i], args[i + 1]);
        }
        Path carpetaDatos = Path.of(op.get("--datos"));
        Datos datos = op.get("--oferta").isEmpty() ? Datos.leer(carpetaDatos)
                : Datos.leer(carpetaDatos, Path.of(op.get("--oferta")));
        String prefijo = op.get("--prefijo");
        int replicas = Integer.parseInt(op.get("--replicas"));
        long semilla = Long.parseLong(op.get("--semilla"));
        String solo = op.get("--solo");

        List<String> resumen = new ArrayList<>();
        resumen.add("replica,semilla,ingresados,arribados,en_andenes,a_bordo,caminando,descartados,"
                + "conservacion,viaje_medio_s,espera_media_s,ascensos_por_viaje,ascensos_por_viaje_hpm,"
                + "ascensos_por_viaje_hpt,max_vivos,max_formaciones,quedaron_abajo,segundos_de_computo");
        Map<String, double[]> cargaSum = new HashMap<>(), carga2 = new HashMap<>(), trenesSum = new HashMap<>();
        Map<String, Integer> maxOcup = new HashMap<>();
        Map<String, Long> maxAnden = new HashMap<>(), abajo = new HashMap<>();
        double[] esperaH = new double[24], viajeH = new double[24], ascH = new double[24], arrH = new double[24];

        for (int r = 0; r < replicas; r++) {
            long s = semilla + r;
            long t0 = System.nanoTime();
            SimuladorReferencia sim = new SimuladorReferencia(datos, solo, s);
            sim.correr();
            double seg = (System.nanoTime() - t0) / 1e9;
            long enAnd = sim.enAndenes();
            boolean ok = sim.ingresados == sim.arribados + enAnd + sim.aBordo + sim.caminando;
            long quedaron = 0;
            for (Map.Entry<String, Anden<Pasajero>> e : sim.andenes.entrySet()) {
                quedaron += e.getValue().quedaronAbajo();
                maxAnden.merge(e.getKey(), (long) e.getValue().maximo(), Math::max);
                abajo.merge(e.getKey(), e.getValue().quedaronAbajo(), Long::sum);
            }
            resumen.add(String.format(Locale.ROOT, "%d,%d,%d,%d,%d,%d,%d,%d,%s,%.1f,%.1f,%.4f,%.4f,%.4f,%d,%d,%d,%.1f",
                    r + 1, s, sim.ingresados, sim.arribados, enAnd, sim.aBordo, sim.caminando, sim.descartados,
                    ok ? "OK" : "FALLA", sim.sumaViaje / sim.arribados, sim.sumaEspera / sim.arribados,
                    (double) sim.sumaAscensos / sim.arribados,
                    (double) sim.ascensosHora[8] / sim.arribadosHora[8],
                    (double) sim.ascensosHora[17] / sim.arribadosHora[17],
                    sim.maxVivos, sim.maxFormaciones, quedaron, seg));
            System.out.println(resumen.get(resumen.size() - 1));
            for (Map.Entry<String, double[]> e : sim.cargaSaliente.entrySet()) {
                double[] a = cargaSum.computeIfAbsent(e.getKey(), x -> new double[24]);
                double[] b = carga2.computeIfAbsent(e.getKey(), x -> new double[24]);
                double[] tr = trenesSum.computeIfAbsent(e.getKey(), x -> new double[24]);
                double[] trS = sim.trenesSalientes.get(e.getKey());
                for (int h = 0; h < 24; h++) {
                    a[h] += e.getValue()[h];
                    b[h] += e.getValue()[h] * e.getValue()[h];
                    tr[h] += trS[h];
                }
            }
            sim.maxOcupacion.forEach((k, v) -> maxOcup.merge(k, v, Math::max));
            for (int h = 0; h < 24; h++) {
                esperaH[h] += sim.esperaHora[h];
                viajeH[h] += sim.viajeHora[h];
                ascH[h] += sim.ascensosHora[h];
                arrH[h] += sim.arribadosHora[h];
            }
        }

        if (op.get("--salida").isEmpty()) {
            return;
        }
        Path salida = Path.of(op.get("--salida"));
        Files.createDirectories(salida);
        Files.write(salida.resolve(prefijo + "_resumen.csv"), resumen, StandardCharsets.UTF_8);

        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(salida.resolve(prefijo + "_carga.csv")))) {
            w.println("linea,direction_id,orden,nodo,hora,pasajeros_hora_media,pasajeros_hora_desvio,"
                    + "formaciones_hora_media,capacidad,max_a_bordo,max_anden,quedaron_abajo_por_replica");
            for (Recorrido rec : datos.red.recorridos()) {
                for (int i = 0; i < rec.largo() - 1; i++) {
                    String k = Datos.claveAnden(rec, i);
                    double[] a = cargaSum.get(k), b = carga2.get(k), tr = trenesSum.get(k);
                    if (a == null) {
                        continue;
                    }
                    for (int h = 5; h < 24; h++) {
                        double m = a[h] / replicas;
                        double v = replicas > 1 ? (b[h] - replicas * m * m) / (replicas - 1) : 0;
                        w.println(String.format(Locale.ROOT, "%s,%d,%d,%s,%d,%.2f,%.2f,%.2f,%d,%d,%d,%.1f",
                                rec.linea, rec.sentido, i, rec.nodos[i], h, m, Math.sqrt(Math.max(v, 0)),
                                tr[h] / replicas, Datos.capacidad(rec.linea), maxOcup.getOrDefault(k, 0),
                                maxAnden.getOrDefault(k, 0L), abajo.getOrDefault(k, 0L) / (double) replicas));
                    }
                }
            }
        }
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(salida.resolve(prefijo + "_hora.csv")))) {
            w.println("hora_ingreso,viajes_por_replica,viaje_medio_s,espera_media_s,ascensos_por_viaje");
            for (int h = 5; h < 24; h++) {
                if (arrH[h] == 0) {
                    continue;
                }
                w.println(String.format(Locale.ROOT, "%d,%.1f,%.1f,%.1f,%.4f", h, arrH[h] / replicas,
                        viajeH[h] / arrH[h], esperaH[h] / arrH[h], ascH[h] / arrH[h]));
            }
        }
        System.out.println("Salidas en " + salida.toAbsolutePath());
    }
}
