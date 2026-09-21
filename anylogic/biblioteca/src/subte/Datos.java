package subte;

import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

/**
 * Todos los insumos del modelo, leidos de una carpeta con los CSV de
 * data/processed. En AnyLogic se llama una vez en el arranque de Main.
 */
public final class Datos {

    /** Pasajeros por coche: la capacidad de la Linea F, 1.075 / 6 (especificacion, seccion 15). */
    public static final int PASAJEROS_POR_COCHE = 179;

    /** Coches por formacion, medianas medidas (reports/05_despachos.md, seccion 6). */
    public static final Map<String, Integer> COCHES = Map.of(
            "A", 5, "B", 6, "C", 5, "D", 6, "E", 5, "H", 6);

    public final Red red;
    public final Map<String, Ruta> rutas;
    public final Demanda demanda;
    public final Oferta oferta;

    private Datos(Red red, Map<String, Ruta> rutas, Demanda demanda, Oferta oferta) {
        this.red = red;
        this.rutas = rutas;
        this.demanda = demanda;
        this.oferta = oferta;
    }

    public static Datos leer(Path carpeta) {
        return leer(carpeta, carpeta);
    }

    /**
     * Con la oferta de otra carpeta: la red, las rutas y la demanda salen de
     * {@code carpeta}, y los tres archivos de oferta de {@code carpetaOferta}.
     * Es como se corren las variantes (p. ej. la D de septiembre de 2024, D4).
     */
    public static Datos leer(Path carpeta, Path carpetaOferta) {
        Red red = Red.leer(carpeta);
        return new Datos(red, Ruta.leer(carpeta, red), Demanda.leer(carpeta), Oferta.leer(carpetaOferta, red));
    }

    public static Datos leer(String carpeta) {
        return leer(Path.of(carpeta));
    }

    public Ruta ruta(String origen, String destino) {
        Ruta r = rutas.get(Ruta.clave(origen, destino));
        if (r == null) {
            throw new IllegalArgumentException("sin ruta " + origen + " -> " + destino);
        }
        return r;
    }

    public static int capacidad(String linea) {
        Integer c = COCHES.get(linea);
        if (c == null) {
            throw new IllegalArgumentException("sin coches para la linea " + linea);
        }
        return c * PASAJEROS_POR_COCHE;
    }

    /** Un anden por nodo y recorrido, con clave {@link #claveAnden}. */
    public <T> Map<String, Anden<T>> crearAndenes() {
        Map<String, Anden<T>> m = new HashMap<>();
        for (Recorrido r : red.recorridos()) {
            for (int i = 0; i < r.largo(); i++) {
                m.put(claveAnden(r, i), new Anden<>(r, i));
            }
        }
        return m;
    }

    public static String claveAnden(Recorrido r, int indice) {
        return r.clave() + "/" + indice;
    }

    /** El anden donde espera quien va a hacer esta etapa. */
    public static String claveAnden(Ruta.Etapa e) {
        return claveAnden(e.recorrido, e.sube);
    }
}
