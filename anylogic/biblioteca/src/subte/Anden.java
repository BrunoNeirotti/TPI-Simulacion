package subte;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

/**
 * Los pasajeros que esperan en un anden: un nodo y un sentido.
 *
 * Cola en orden de llegada. Todas las formaciones de un recorrido paran en
 * todas las estaciones, asi que cualquiera que llegue sirve a todos los que
 * esperan. Si no entran todos, los demas siguen esperando la proxima (D12).
 *
 * Es generico para no depender de la clase de agente de AnyLogic: en el modelo
 * es {@code Anden<Pasajero>}.
 */
public final class Anden<T> {

    public final Recorrido recorrido;
    public final int indice;
    private final ArrayDeque<T> cola = new ArrayDeque<>();
    private int maximo;
    private long quedaronAbajo;   // pasajeros-vez que no entraron en una formacion

    public Anden(Recorrido recorrido, int indice) {
        this.recorrido = recorrido;
        this.indice = indice;
    }

    public void llega(T pasajero) {
        cola.addLast(pasajero);
        maximo = Math.max(maximo, cola.size());
    }

    /** Sube hasta {@code lugares} pasajeros, en orden de llegada. */
    public List<T> subir(int lugares) {
        int n = Math.min(Math.max(lugares, 0), cola.size());
        List<T> suben = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            suben.add(cola.pollFirst());
        }
        quedaronAbajo += cola.size();
        return suben;
    }

    public int esperando() {
        return cola.size();
    }

    public int maximo() {
        return maximo;
    }

    public long quedaronAbajo() {
        return quedaronAbajo;
    }

    public String nodo() {
        return recorrido.nodos[indice];
    }

    /** Vacia la cola y los contadores, para reiniciar entre replicaciones. */
    public void reiniciar() {
        cola.clear();
        maximo = 0;
        quedaronAbajo = 0;
    }
}
