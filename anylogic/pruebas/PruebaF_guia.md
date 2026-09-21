# Prueba F: `Event` + `Enter` desde una población, 20 h

Armada el 21/09/2026. Ver `docs/diseno-modelo-base.md`, sección 7.1.

## Qué responde

Una sola corrida contesta dos preguntas que las pruebas A a E dejaron abiertas:

1. **¿Un `Event` de `Main` que inyecta pasajeros hace perder la exención de 5 h de PML?**
   La prueba A usó `Source`; el modelo real no puede, así que necesita un temporizador.
2. **¿Inyectar por `Enter` desde una población cuenta contra el tope de 50.000
   creaciones?** La prueba E lo dejó como "lo más probable es que no, sin verificar".

Para separar las dos, el evento inyecta **un pasajero por segundo durante 20 h**: 72.000
inyecciones, más que el tope, reciclando una población de 1.000.

| Valor final de `inyectados` | Qué significa |
|---|---|
| **~72.000** | Las dos bien: el `Event` conserva la exención y `Enter` no cuenta como creación |
| ~18.000 (se cortó a las 5 h) | El `Event` hace perder la exención: hay que usar un agente reloj con `Delay` |
| ~50.000 (se cortó antes de las 20 h) | `Enter` cuenta como creación: el pool no resuelve el tope y hay que pasar al plan B |

## Cómo armarla (unos 10 minutos)

1. **Modelo nuevo**: `File → New → Model`, nombre `PruebaF_EventEnter`, unidades de
   tiempo del modelo: **segundos**.
2. **Tipo de agente `Pax`**: desde la paleta *Agent*, arrastrar **Agent** a `Main` →
   *Population of agents* → *I want to create a new agent type* → nombre del tipo `Pax`,
   nombre de la población `paxs` → sin animación → **cantidad inicial 1000**.
3. **Flowchart en `Main`** (paleta *Process Modeling Library*), conectados en este orden:
   - **`Enter`**, nombre `enter`. *Agent type*: `Pax`.
   - **`Delay`**, nombre `delay`. *Delay time*: `300` segundos. *Maximum capacity*:
     **tildado** (capacidad infinita, si no la cola absorbe todo; ver `src/08`).
   - **`Exit`**, nombre `exit`. En *On enter*:
     ```java
     libres.add(agent);
     ```
4. **Variable** en `Main` (paleta *Agent*): nombre `inyectados`, tipo `int`, valor
   inicial `0`.
5. **Colección** en `Main` (paleta *Agent → Collection*): nombre `libres`, *Collection
   class* `LinkedList`, *Element class* `Pax`.
6. **Arranque de `Main`**: en las propiedades de `Main`, *Agent actions → On startup*:
   ```java
   for (Pax p : paxs) libres.add(p);
   ```
7. **Evento** en `Main` (paleta *Agent → Event*): nombre `inyectar`.
   - *Trigger type*: `Timeout`. *Mode*: `Cyclic`.
   - *First occurrence time*: `0`. *Recurrence time*: `1` segundo.
   - *Action*:
     ```java
     Pax p = libres.poll();
     if (p != null) {
         enter.take(p);
         inyectados++;
     }
     ```
8. **Experimento** `Simulation`: *Model time → Stop*: `Stop at specified time`,
   *Stop time*: `72000` (20 h). Modo de ejecución: **virtual time** (lo más rápido
   posible).
9. Correr y anotar:
   - el valor final de `inyectados` (clic en la variable durante la corrida, o
     `traceln(inyectados)` en *On destroy* de `Main`);
   - la hora del modelo en la que terminó;
   - cualquier mensaje de error o aviso de límite de la edición.

Con ~300 pasajeros en el `Delay` a la vez y 1.000 en la población, nunca se queda sin
agentes libres, así que el total esperado es 72.000 (o 72.001 por el evento de tiempo
cero).

## Variante F2: evento dinámico (agregada el 21/09/2026)

El modelo real no usa un `Event` cíclico sino **eventos dinámicos** (*Dynamic Event*),
que se reprograman solos con un tiempo distinto cada vez (llegadas de pasajeros,
despachos). Conviene probar también ese mecanismo. Son cinco minutos más sobre el mismo
modelo:

1. **Borrar el evento `inyectar`** (o ponerle *Mode*: `Occurs once` con tiempo muy
   grande, para desactivarlo).
2. Agregar un **Dynamic Event** (paleta *Agent → Dynamic Event*) en `Main`, nombre
   `Inyectar`. En *Action*:
   ```java
   Pax p = libres.poll();
   if (p != null) {
       enter.take(p);
       inyectados++;
   }
   create_Inyectar(1);   // se reprograma dentro de 1 segundo
   ```
3. En *On startup* de `Main`, agregar al final:
   ```java
   create_Inyectar(0);
   ```
4. Correr igual, 72.000 s, y anotar `inyectados`. La lectura de la tabla de arriba es la
   misma.

Si F pasa y F2 corta a las 5 h (o al revés), anotarlo tal cual: define qué mecanismo usa
el modelo.

## Resultado

*(completar al correrla)*

| Dato | F (`Event` cíclico) | F2 (evento dinámico) |
|---|---|---|
| `inyectados` al final | | |
| Hora del modelo al terminar | | |
| Mensajes | | |
| Conclusión | | |
