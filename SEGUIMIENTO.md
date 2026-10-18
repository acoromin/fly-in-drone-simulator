# Seguimiento de Fly-in

Última actualización: 18 de octubre de 2026, al terminar la sesión de madrugada.

## Cómo trabajar con el alumno

El objetivo es aprender a diseñar y construir software y poder defender cada decisión, además de completar el subject. El alumno estaba bloqueado por cambios de dirección y explicaciones que daban demasiados pasos por entendidos. Ha recuperado comprensión y confianza trabajando con objetivos pequeños.

- Actuar como profesor y mentor, no entregar una arquitectura cerrada ni programar el proyecto por el alumno.
- Marcar el siguiente paso técnico, explicar su necesidad, responsabilidad, entradas y resultado.
- Razonar con un ejemplo concreto, preferiblemente tablas que relacionen datos con preguntas que responden.
- Proponer una función cada vez. El alumno la implementa; leer su archivo, revisar, explicar errores y comprobar casos relevantes antes de avanzar.
- Dar pistas progresivas si se bloquea. Escribir código únicamente cuando lo pida expresamente.
- No mantener código solo por el esfuerzo invertido ni cambiar decisiones sin justificación.
- No confundir recomendaciones de diseño con errores objetivos. Explicar las alternativas sin dar bandazos.
- El alumno utiliza main.py como herramienta temporal de comprobación; no exigir aún un main definitivo.
- Las docstrings se completarán al final por preferencia del alumno. Estilo y comprobación global de tipos siguen pendientes.

## Fuente y objetivo

El subject está en fly_in.pdf, versión 1.6. Leerlo cuando haga falta verificar reglas.

Se desea un proyecto bien estructurado y eficiente. El objetivo adicional es resolver el Challenger en menos de 45 turnos (44 o menos). No se ha demostrado ni prometido alcanzar ese resultado con la estrategia inicial.

## Trabajo realizado

### Hub y Connection

- Hub describe propiedades del mapa; no almacena ocupación de una ejecución.
- Se corrigieron color a str | None, max_drone a max_drones y get_zone_cost() a get_entry_cost(). Pathfinder utiliza el nuevo nombre.
- Se añadieron Literal para type y zone en Hub. HubModel.zone utiliza el mismo Literal; su validación personalizada pasó a mode="before" para mantener el error con número de línea. Este cambio lo hizo el asistente por petición expresa.
- Connection referencia los mismos objetos Hub del grafo; no guarda copias ni impone una dirección por usar source/target.
- Su capacidad es compartida entre ambos sentidos.
- get_other_hub(hub) devuelve el extremo opuesto; lanza ValueError si el argumento no pertenece a la conexión. El alumno entiende por qué.
- El coste depende del hub de destino, no de un supuesto tipo restricted de la conexión.

### Graph

- Recibe MapModel validado, pero ya no lo conserva como atributo.
- El constructor inicializa sus atributos y llama a _generate_graph(map_model). Al terminar, está listo para consultar.
- _generate_graph pasa map_model a _create_hubs y _create_connections, y construye la adyacencia.
- hubs: dict[str, Hub] permite buscar por nombre.
- connections: list[Connection] permite recorrer todas las conexiones.
- adjacency: dict[Hub, list[Connection]] permite explorar solo las conexiones de un hub. Cada conexión aparece en las listas de ambos extremos.
- start_hub y end_hub permiten acceso directo. Siguen anotados como Hub | None; no dar por resueltos todos los detalles futuros de tipos.
- get_connection(hub_a, hub_b) recorre adjacency[hub_a] y compara connection.get_other_hub(hub_a) con hub_b. Devuelve Connection o None. Su contrato supone hubs pertenecientes al grafo.
- Se ejecutó el mapa lineal desde main y se verificó la adyacencia en ambos sentidos.

### Pathfinder actual

- pathfinder/pathfinder.py contiene Dijkstra estático, que devuelve list[Hub].
- Evita hubs bloqueados y suma get_entry_cost() del destino; no contempla reservas ni esperas ni preferencia entre empates por zonas priority.
- Usa heap con contador de desempate, distancias, visitados y padres.
- No reimplementarlo como si el alumno no lo conociera: lo escribió para aprender y recuerda el algoritmo.
- tests.py contiene ejercicios de BFS y DFS con errores pendientes. No confundirlos con pruebas automatizadas fiables ni desviarse a repararlos ahora.

### Reinicio de planificación y simulación

- Por petición expresa se eliminaron la antigua implementación de Simulation y el antiguo Planner/Reservations. Se retiraron sus imports. Se conservó simulation/drone.py.
- Drone conserva una implementación antigua basada en ruta e índice; aún no se ha adaptado a itinerarios temporales ni a tránsito.
- No recuperar por inercia el antiguo sistema de propuestas/resolución de conflictos.
- Se eligió como dirección inicial planificar por adelantado y ejecutar después. El mapa y las capacidades son conocidos y fijos.
- Planificar drones uno por uno: buscar un itinerario completo compatible, registrarlo y reservar sus recursos antes de buscar el siguiente.
- Durante la búsqueda solo se consultan reservas. Las alternativas descartadas no deben dejar reservas compartidas.
- Este enfoque no garantiza óptimo global. Las primeras decisiones condicionan las siguientes; mejorar rendimiento requerirá medir y justificar cambios. Permutar IDs de drones idénticos no aporta por sí solo diversidad útil.

### Reservations reconstruida por el alumno

Archivos: planner/__init__.py (vacío) y planner/reservations.py.

Estructuras actuales:

```python
self.hubs: dict[int, dict[Hub, int]] = {}
self.connections: dict[int, dict[Connection, int]] = {}
```

Métodos implementados y revisados:

- get_hub_reservations(hub, turn): cantidad o cero si falta turno/hub; no modifica datos.
- reserve_hub(hub, turn): crea el diccionario del turno si falta y asigna cantidad actual + 1.
- can_reserve_hub(hub, turn): inicio/final siempre permiten capacidad; para los demás compara reservas < max_drones. No comprueba blocked: eso se descarta durante la búsqueda.
- Los tres equivalentes para Connection, comparando con max_link_capacity.
- can_move(connection, destination, departure_turn): calcula llegada, comprueba capacidad del destino al llegar y capacidad de conexión en todos los turnos del desplazamiento. No modifica reservas ni valida conectividad o zonas bloqueadas; quien lo llama debe garantizar esas condiciones.

Se explicaron claves ausentes, KeyError, cortocircuito de or y la diferencia entre asignar con = y sumar con +=. El alumno ya lo comprendió; no interpretar esos tropiezos como falta de comprensión del proyecto completo.

Comprobaciones realizadas:

- El alumno ejecutó reservas de hubs y obtuvo 1, 2, 1, 2.
- El asistente comprobó conexión con capacidad dos: 0/1 reservas permiten otra; 2 no; independencia entre turnos.
- El asistente comprobó can_move hacia restricted: rechaza conexión llena en cualquiera de sus dos turnos, rechaza destino lleno al llegar, permite si todo está libre y no modifica reservas. No se añadieron archivos de tests.
- El entorno .venv ya tiene instaladas las dependencias por el alumno. Usar .venv/bin/python; no afirmar que faltan sin comprobarlo.

## Convención temporal acordada

- Estado en turno t: posición AL TERMINAR el turno t. Turno 0: situación inicial.
- hubs[t]: ocupación al terminar t.
- connections[t]: uso DURANTE el turno t, entre estados t-1 y t.
- departure_turn en can_move significa turno del estado de partida, no primer turno de movimiento. Conviene recordar esta precisión al explicar.
- Llegada = departure_turn + coste de entrada del destino.
- Conexión: comprobar range(departure_turn + 1, arrival_turn + 1).
- Normal desde estado 3: usa conexión en 4, llega al terminar 4.
- Restricted desde estado 3: usa conexión en 4 y 5, está en tránsito al terminar 4 y llega obligatoriamente al terminar 5. Esta es la contabilización de intervalos adoptada.
- Una salida libera capacidad del hub de origen para ese mismo turno; no se reserva ese origen en el estado final si el dron salió.
- Esperar también requiere reservar el hub para el siguiente estado. Si no hay capacidad para esperar, esa alternativa de búsqueda es inválida y hay que explorar otra, posiblemente retrasando un movimiento anterior.
- Los drones pendientes de planificar permanecen inicialmente en start, sin límite de capacidad.
- Todo itinerario aceptado debe cubrir la ocupación de todos sus estados, incluidas esperas, y garantizar llegada tras tránsito. No hay una fase previa con drones ya moviéndose: primero se construye el plan y después se ejecuta.

## Representación de itinerarios: propuesta comprendida, aún no implementada

Un itinerario individual: lista ordenada de pares (Hub, turno). Cada par representa estar en ese hub al terminar ese turno.

Ejemplo con A restringida:

```text
[(start, 0), (start, 1), (A, 3), (goal, 4)]
```

- Espera en start durante turno 1.
- Viaja hacia A durante turnos 2 y 3.
- Viaja a goal durante turno 4.
- El tránsito se deduce de pares consecutivos, costes y conexión recuperable desde Graph; no aparece como estado separado en la lista.

El alumno propuso lista de N itinerarios para la flota. Se aceptó como opción sencilla: índice 0 corresponde a D1, índice 1 a D2, etc., manteniendo IDs consecutivos y orden estable.

Separación que ayudó mucho al alumno:

| Información | Pregunta |
|---|---|
| Itinerario de un dron | ¿Qué hará D3 y cuándo? |
| Reservas compartidas | ¿Cuánta capacidad queda en A al terminar el turno 5? |

No se ha implementado aún la construcción del plan, el registro de un itinerario completo ni su ejecución.

## Punto exacto para retomar mañana

El alumno preguntó si antes de construir itinerarios había que adaptar Pathfinder. Sí: falta una búsqueda que produzca un itinerario individual compatible con reservas.

Se introdujo la idea de pasar de estados Hub a estados (Hub, turno), con acciones avanzar y esperar. También se mencionó que hace falta acotar el horizonte temporal para evitar infinitas esperas si no se encuentra solución.

PERO: el alumno dijo expresamente que NO seguía bien esa explicación, por cansancio a las 2:30. No darla por comprendida ni pedir que implemente ya un algoritmo completo.

### Primer paso de la próxima sesión

1. Leer este archivo y comprobar los archivos actuales sin modificar código.
2. Retomar con un ejemplo pequeño donde A esté ocupada en un turno y libre en el siguiente.
3. Explicar por qué llegar al mismo hub en tiempos distintos son alternativas distintas, comparándolo con su Dijkstra estático conocido.
4. Acordar el contrato del nuevo método: entradas, salida, uso solo de consulta de Reservations y límite temporal. Todavía no se ha fijado una firma definitiva ni elegido formalmente entre Dijkstra temporal y A*.
5. Proponer una primera tarea pequeña al alumno, revisar su intento y avanzar progresivamente.

No saltar directamente a Planner, Simulation, optimizaciones del Challenger ni entregar toda la búsqueda implementada. El flujo deseado sigue siendo: búsqueda de un itinerario → aceptación y registro de reservas → siguiente dron → ejecución posterior del plan.
