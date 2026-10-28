package subte;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Los pasajeros a bordo de una formacion, agrupados por estacion de bajada.
 *
 * Bajar en una estacion es O(1): se entrega la lista de esa estacion. La
 * capacidad es la de la formacion (coches por 179 pasajeros, supuesto de la
 * especificacion, seccion 15).
 */
public final class Carga<T> {

    public final int capacidad;
    private final List<List<T>> porBajada;
    private int aBordo;
    private int maximo;

    public Carga(int estaciones, int capacidad) {
        this.capacidad = capacidad;
        this.porBajada = new ArrayList<>(estaciones);
        for (int i = 0; i < estaciones; i++) {
            porBajada.add(new ArrayList<>());
        }
    }

    public int lugares() {
        return capacidad - aBordo;
    }

    public int aBordo() {
        return aBordo;
    }

    public int maximo() {
        return maximo;
    }

    public void subir(T pasajero, int indiceBaja) {
        if (aBordo >= capacidad) {
            throw new IllegalStateException("formacion llena");
        }
        porBajada.get(indiceBaja).add(pasajero);
        aBordo++;
        maximo = Math.max(maximo, aBordo);
    }

    /** Los que bajan en la estacion i; quedan fuera de la formacion. */
    public List<T> bajar(int indice) {
        List<T> l = porBajada.get(indice);
        if (l.isEmpty()) {
            return Collections.emptyList();
        }
        List<T> bajan = new ArrayList<>(l);
        l.clear();
        aBordo -= bajan.size();
        return bajan;
    }

    /** Para reciclar la formacion (D11): tiene que llegar vacia a la cabecera final. */
    public void reiniciar() {
        for (List<T> l : porBajada) {
            l.clear();
        }
        aBordo = 0;
        maximo = 0;
    }
}
