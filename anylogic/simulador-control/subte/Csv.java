package subte;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Lectura minima de los CSV de data/processed.
 *
 * Los archivos que genera el pipeline no tienen comillas ni BOM (verificado el
 * 21/09/2026), asi que alcanza con separar por coma. Si algun dia aparece una
 * coma dentro de un campo, esto falla de forma ruidosa: la fila queda con mas
 * columnas que el encabezado.
 */
public final class Csv {

    private final String[] encabezado;
    private final Map<String, Integer> columna = new HashMap<>();
    private final List<String[]> filas = new ArrayList<>();

    private Csv(String[] encabezado) {
        this.encabezado = encabezado;
        for (int i = 0; i < encabezado.length; i++) {
            columna.put(encabezado[i], i);
        }
    }

    public static Csv leer(Path ruta) {
        try (BufferedReader r = Files.newBufferedReader(ruta, StandardCharsets.UTF_8)) {
            String linea = r.readLine();
            if (linea == null) {
                throw new IllegalStateException("archivo vacio: " + ruta);
            }
            Csv csv = new Csv(linea.split(",", -1));
            int n = 1;
            while ((linea = r.readLine()) != null) {
                n++;
                if (linea.isEmpty()) {
                    continue;
                }
                String[] campos = linea.split(",", -1);
                if (campos.length != csv.encabezado.length) {
                    throw new IllegalStateException(ruta.getFileName() + ", fila " + n
                            + ": " + campos.length + " campos, se esperaban " + csv.encabezado.length);
                }
                csv.filas.add(campos);
            }
            return csv;
        } catch (IOException e) {
            throw new UncheckedIOException("no se pudo leer " + ruta, e);
        }
    }

    public List<String[]> filas() {
        return filas;
    }

    public int col(String nombre) {
        Integer i = columna.get(nombre);
        if (i == null) {
            throw new IllegalArgumentException("no existe la columna " + nombre);
        }
        return i;
    }

    public static double num(String s) {
        return s.isEmpty() ? Double.NaN : Double.parseDouble(s);
    }
}
