# Seguimiento de Fly-in

Última actualización: 19 de octubre de 2026, al terminar la sesión. El alumno ha pedido parar por cansancio y continuar mañana.

## Cómo trabajar con el alumno

El objetivo es aprender a diseñar y construir software y defender las decisiones, además de completar el subject. Actuar como profesor y mentor: el alumno implementa; el asistente guía, lee sus archivos y revisa. No programar por él salvo petición expresa.

- Explicar responsabilidad, entradas y resultado antes de proponer una función.
- Una pieza pequeña cada vez. Dar pistas progresivas, ejemplos concretos y tablas. No entregar una arquitectura cerrada ni una implementación completa por adelantado.
- Si pregunta «cómo lo ves», revisar lo que está intentando en ese momento; no tratar un fragmento inacabado como si afirmase haber terminado todo.
- Si pide que no se le dé la solución, respetarlo. Puede pedir expresamente código, un arreglo puntual o que se haga una prueba.
- Distinguir errores objetivos de alternativas de diseño. No cambiar de dirección sin explicar el motivo.
- El alumno usa main.py como herramienta temporal de comprobación. No exigir aún un main definitivo.
- Docstrings, estilo y comprobación global de tipos se completarán después por preferencia del alumno.
- No menospreciar soluciones correctas por diferencias pequeñas de eficiencia no medidas. Aprender comparando alternativas, sin presentar la propia como automáticamente superior.
- Al explicar bucles, separar buscar alternativas, registrar un plan y ejecutar turnos. Esa confusión fue un bloqueo importante y ya se resolvió con ejemplos.
- El alumno está aprendiendo Pygame desde cero. También necesita apoyo puntual con desempaquetado, comprehensions, identidad e igualdad. No interpretar esto como desconocimiento general del proyecto.

## Fuente, objetivo y estado general

Subject: fly_in.pdf, versión 1.6. Consultarlo cuando haga falta verificar reglas. Se extrajo una copia de texto temporal en /tmp/fly_in_subject_review.txt; puede desaparecer.

La planificación y el núcleo de simulación están implementados y comprobados en los casos descritos abajo. El Challenger genera un plan de 25 drones que termina en el turno 43, por debajo del récord de referencia de 45. No afirmar óptimo global ni entrega completa: falta el renderer, integración final, salida reglamentaria y verificaciones globales.

El alumno quiere aprender Pygame para reutilizarlo en otros proyectos y conseguir un resultado elegante para portfolio. Dirección visual acordada: interfaz sobria de control de tráfico aéreo, mapa legible, rutas finas, hubs claros, drones sencillos con movimiento fluido, panel de turno/progreso y controles cuidados. No temática de anime ni estética recargada. La práctica de círculos no es el diseño final.

## Arquitectura acordada

Flujo: parsear mapa → Graph → Planner → itinerarios → crear Drone por itinerario → Simulation por turnos → presentación.

- Graph: mapa fijo, sin ocupaciones de ejecución.
- Pathfinder: busca un itinerario individual consultando reservas; no registra recursos durante la búsqueda.
- Reservations: cantidades compartidas de ocupación, anónimas. Los itinerarios individuales indican qué hará cada dron.
- Planner: coordina búsqueda, aceptación y registro, dron a dron.
- Drone: ID e itinerario individual ya terminado; consultas de ubicación y entrega.
- Simulation: interpreta los itinerarios por turnos, sin buscar rutas ni resolver conflictos nuevos.
- PygameRenderer: presentación gráfica; se acordó que cree y gestione su propia ventana.
- main: conectará las piezas. Ahora sigue siendo una herramienta temporal que imprime itinerarios.

Planner devuelve una lista de itinerarios. Posición 0 → D1, posición 1 → D2, etc. IDs consecutivos desde 1 y orden estable. No crear una clase que represente toda la flota como si fuera Drone. Los drones son idénticos para planificar; el ID identifica su plan, no modifica la búsqueda.

## Graph, Hub y Connection

- Hub contiene propiedades del mapa. zone y type usan Literal; color es str | None. Capacidad: max_drones. Coste: get_entry_cost().
- HubModel valida zone en mode="before" para mantener los errores con línea. Esto lo hizo el asistente por petición expresa en la sesión anterior.
- Connection referencia los mismos objetos Hub del grafo, es bidireccional y su capacidad es compartida entre ambos sentidos.
- get_other_hub(hub) devuelve el extremo opuesto o lanza ValueError si no pertenece a esa conexión.
- El coste de un movimiento depende del hub destino.
- Graph recibe MapModel validado; construye hubs: dict[str, Hub], connections: list[Connection] y adjacency: dict[Hub, list[Connection]]. Cada conexión aparece en ambos extremos.
- start_hub y end_hub siguen anotados Hub | None. El parser garantiza que existen, pero todavía no se ha afinado toda la cuestión de tipos.
- get_connection(hub_a, hub_b) devuelve Connection | None; supone hubs del grafo.
- Hub no define __eq__; actualmente == entre hubs coincide con identidad. Usar is para comprobar que es el mismo objeto del grafo es válido. Para None, is None / is not None; para valores numéricos y texto, == / !=.

## Convención temporal: no cambiarla

- Estado (hub, t): posición AL TERMINAR el turno t. Turno 0: situación inicial.
- hubs[t]: ocupación al terminar t.
- connections[t]: uso DURANTE el turno t, entre estados t-1 y t.
- departure_turn en can_move es el turno del estado de partida, no el primer turno de movimiento.
- Desde (A, 3), movimiento normal: conexión durante 4 y llegada al terminar 4.
- Desde (A, 3), hacia restricted: conexión durante 4 y 5, tránsito al terminar 4 y llegada obligatoria al terminar 5.
- Se comprueba/reserva conexión con range(departure_turn + 1, arrival_turn + 1).
- Salir libera el hub origen para ese mismo turno. Esperar requiere capacidad en el hub al terminar el siguiente turno.
- start y end no tienen límite de capacidad. Drones aún no planificados pueden esperar en start.

El alumno se bloqueó porque interpretaba (A, 3) como comienzo del turno 3. Se resolvió recordando que es una foto al FINAL del 3; el siguiente viaje comienza durante el 4. Esta precisión es esencial si vuelve la duda.

## Pathfinder y Reservations

Se movió pathfinder/pathfinder.py a planner/pathfinder.py y se eliminó la carpeta antigua por petición expresa. Imports actualizados.

### Pathfinder

- Constructor recibe Graph.
- find_route_dijkstra() conserva el Dijkstra estático: evita blocked, suma coste de entrada y devuelve list[Hub] o []. Se reutiliza como comprobación de conectividad.
- find_itinerary(reservations) devuelve list[tuple[Hub, int]]. Estados (Hub, turno), movimientos y espera; reconstrucción siguiendo parents, incluyendo initial_state y reverse().
- Heap: (turno, prioridad, counter, estado). Prioridad 0 para destino priority y 1 para los demás; turno manda, prioridad desempata y counter evita comparar objetos Hub.
- Entrada inicial: (0, 1, counter, initial_state). Al extraer se ignoran los tres primeros valores y se desempaqueta el estado.
- Los movimientos pasan por adjacency, descartan blocked y consultan can_move.
- La espera se genera fuera del for de conexiones, dentro del while, si can_reserve_hub lo permite. No se añade solo cuando falla una conexión: es una alternativa independiente.
- visited guarda estados completos; (A, 2) y (A, 3) son distintos.
- Se conserva el primer padre de cada estado: movimientos descartan next_state ya presente en parents; esperas solo se insertan si wait_state no está en parents. Antes se sobrescribían padres, borrando preferencias y generando recorridos alternativos innecesarios.
- Una prueba con dos ramales de igual duración, normal y priority, ahora conserva el ramal priority. Esta es una preferencia local en el orden de exploración; no se ha demostrado maximización global de uso de zonas priority ni debe afirmarse tal cosa.
- No hay max_turn arbitrario. Precondición: comprobar una vez que existe camino estático. Con reservas finitas y espera ilimitada en start, existe llegada en tiempo finito. La búsqueda explora por tiempo creciente. No llamar directamente a find_itinerary sobre un grafo sin camino: podría esperar indefinidamente.

### Reservations

Estructuras:

```python
self.hubs: dict[int, dict[Hub, int]] = {}
self.connections: dict[int, dict[Connection, int]] = {}
```

- get_hub_reservations / get_connection_reservations: cantidades o cero, sin mutar.
- reserve_hub / reserve_connection: incrementan el contador del recurso en el turno.
- can_reserve_hub: start/end siempre permiten; resto compara cantidad con max_drones. No valida blocked.
- can_reserve_connection: compara cantidad con max_link_capacity.
- can_move(connection, destination, departure_turn): comprueba destino al llegar y conexión durante todos los turnos del trayecto. No muta ni valida conectividad; lo garantiza el llamador.
- reserve_itinerary(itinerary, graph): primero reserva todos los pares (hub, turno). Después recorre estados consecutivos por índice; si el hub no cambia, es espera y no reserva conexión. Si cambia, obtiene graph.get_connection y reserva los turnos entre anterior+1 y llegada incluidos.
- Si no existe conexión, lanza ValueError con nombres de ambos hubs. El contrato es recibir un itinerario válido; no es una operación transaccional para entradas arbitrarias.

## Planner

planner/planner.py:

- Constructor recibe solo Graph y crea su Pathfinder y una Reservations compartida.
- plan_itineraries(nb_drones) -> list[list[tuple[Hub, int]]].
- Primero llama al Dijkstra estático una sola vez; si no hay camino devuelve [].
- Para cada dron: busca itinerario con las reservas actuales, lo registra con reserve_itinerary y lo añade al resultado.
- No recibe Drone ni les asigna itinerarios: main los creará después con enumerate(itineraries, start=1).
- Uso actual: una instancia nueva de Planner por planificación. Si más adelante se quiere reutilizar para planificar otra flota desde cero, sus reservas actuales no se reinician; revisar ese contrato entonces.
- Planificación secuencial: no garantiza óptimo global. No replantear ni optimizar sin una necesidad medida.

## Drone y Simulation

Se sustituyó el antiguo Drone de ruta/índice por esta implementación, por decisión del alumno.

### Drone: simulation/drone.py

- Constructor: drone_id e itinerary. Guarda self.id, self.itinerary y desempaqueta el último estado en self.end_hub / self.end_turn.
- Se supone itinerario válido, no vacío e inmutable durante la ejecución.
- is_delivered(turn): turn >= end_turn.
- get_hub_at_turn(turn): si entregado devuelve end_hub; busca hub cuyo state_turn coincide; si no, None (tránsito, para turnos válidos desde 0).
- get_connection_at_turn(turn, graph): recorre estados consecutivos y, si previous_turn < turn < current_turn, devuelve la conexión entre ambos hubs. En los extremos está en hub, no en conexión. Si no hay tránsito devuelve None.
- El alumno propuso una alternativa correcta: si get_hub devuelve None, consultar hubs de turnos anterior/siguiente. Funciona con costes 1/2, pero recorre varias veces el itinerario. Se eligió recorrer parejas una vez. No presentar su propuesta como mala; la eficiencia real no se ha medido y ambos enfoques son O(n).

### Simulation: simulation/simulation.py

- Constructor recibe Graph y list[Drone], guarda ambos y turn = 0.
- is_finished usa all(drone.is_delivered(self.turn) for drone in self.drones).
- step() -> list[tuple[Drone, Hub | Connection]]. Si terminada devuelve [] sin incrementar turno. Si no, incrementa turno y prepara lista movements.
- Recorre drones: descarta solo los entregados en self.turn - 1, para incluir la llegada a end en el turno actual.
- Consulta hub actual. Si es hub y el mismo que en turno anterior, espera y no añade movimiento. Si cambió, añade (drone, hub).
- Si no hay hub, consulta conexión y añade (drone, connection). La consulta de conexión ya está dentro del else para evitar trabajo innecesario.
- Devuelve movements fuera del for.
- Lista de movimientos no es la flota: omitir un dron que espera no lo elimina de self.drones ni pierde su posición.
- Núcleo de Simulation completo para avanzar por pasos. El bucle while not is_finished: step se conectará con la presentación; no añadir métodos innecesarios ahora.
- Todavía queda resolver los posibles None en tipos de forma coherente con el contrato; no afirmar que mypy global está aprobado.

## Reglas del subject verificadas

- VII.1–VII.3: no prohíbe entrar y volver de un callejón; exige evitar bloqueos mutuos, conflictos y respetar capacidades. No confundir callejón con zona blocked.
- priority cuesta 1 turno y debe preferirse en la búsqueda; no reducir artificialmente su coste temporal.
- VII.5: salida paso a paso, una línea por turno; movimientos D<ID>-<zona> o D<ID>-<conexión> durante tránsito restricted. Drones que esperan se omiten de la línea. Los entregados dejan de seguirse tras mostrar su llegada.
- Se acordó mantener salida textual reglamentaria además de la ventana gráfica. El renderer gráfico sí debe mostrar posiciones completas cuando corresponda, no solo la lista de movimientos.
- Turnos de simulación y fotogramas de pantalla son distintos. La animación fluida interpolará posiciones entre estados sin alterar los turnos del plan.

## Pruebas realizadas esta sesión

Sin añadir tests al proyecto; el asistente hizo comprobaciones temporales autorizadas.

- /tmp/check_fly_in_plans.py reconstruye ocupaciones directamente desde itinerarios, sin reutilizar can_move para validar. Comprueba número de drones, inicio y destino, tiempos crecientes, conexiones existentes, bloqueados, duración 1/2, esperas completas, capacidad de hubs y capacidad de conexiones compartida entre sentidos. Compara además reservas almacenadas con las reconstruidas.
- Resultados: easy linear 4 turnos, easy basic_capacity 4; medium dead_end 8, circular 15, priority 7; hard maze 13, capacity 16, ultimate 26; Challenger 43 con 25 drones. Cero conflictos detectados en esos nueve mapas.
- maps/easy/02_simple_fork.txt se rechaza por conexiones antes de definir hubs. EL ALUMNO LO MODIFICÓ A PROPÓSITO PARA PROBAR EL PARSER. No repararlo como supuesto fallo ni considerarlo regresión.
- Caso específico de empate normal/priority comprobado tras proteger parents: elige priority.
- Drone probado con [(start,0),(start,1),(A,3),(goal,4)], A restricted: espera, tránsito, llegada y consultas posteriores correctas.
- Simulation probada con dos drones que combinan espera, tránsito, llegadas y entrega; al terminar step devuelve [] y no avanza turnos.
- Ejecución de Simulation sobre el Challenger: 43 turnos, 475 movimientos; coincidieron con eventos reconstruidos independientemente de los itinerarios.
- Estos resultados no sustituyen la verificación de la salida final y de la futura animación.
- tests.py sigue siendo ejercicios antiguos de BFS/DFS con errores; no confundirlo con batería fiable.
- Usar .venv/bin/python. Dependencias ya instaladas por el alumno, incluido pygame==2.6.1, añadido por él a requirements.txt. Instalar todo: python -m pip install -r requirements.txt, con -r.

## Aprendizaje de Pygame realizado

pygame_practice.py es solo un ejercicio temporal, no la arquitectura de producción.

El alumno ya abrió una ventana y practicó:

- pygame.init y display.set_mode((1000,700)). Devuelve pygame.Surface, la superficie de la ventana.
- while running y pygame.event.get; pygame.QUIT es pulsar el botón de cerrar de la ventana, no escribir x en la terminal. pygame.quit al salir.
- screen.fill con RGB; componentes rojo/verde/azul de 0 a 255 forman UN color mezclado.
- display.flip muestra lo dibujado; limpiar fondo → dibujar → flip.
- pygame.time.Clock creado una vez antes del bucle; clock.tick(60) al final. Espera lo que falta para limitar aproximadamente a 60 FPS, considerando el trabajo ya hecho. No son 60 turnos de simulación.
- draw.circle (superficie, color, centro, radio); draw.line (superficie, color, extremos, grosor). Conexiones primero para que hubs cubran sus extremos.
- pygame.font.Font(None,24), font.render crea superficie del texto, screen.blit coloca esa superficie. blit no crea una fuente.
- No introducir muchas APIs nuevas juntas: se agobió al ver demasiados nombres. Usar pocas, explicar su finalidad y reutilizarlas.

## Renderer actual y punto EXACTO para retomar

Archivos: renderer/__init__.py y renderer/pygame_renderer.py.

PygameRenderer recibe SOLO Graph. Hubo una propuesta inicial de pasar screen desde fuera, pero el alumno señaló que la clase debía crear la ventana. Se acordó y se implementó así: NO volver a cambiar esa decisión por inercia.

Constructor actual:

```python
self.graph = graph
pygame.init()
self.screen = pygame.display.set_mode((1000, 700))
```

Método _calculate_positions(self) -> None, aún incompleto y todavía no llamado desde el constructor:

```python
hubs = list(self.graph.hubs.values())
min_x = min(hub.x for hub in hubs)
max_x = max(hub.x for hub in hubs)
min_y = min(hub.y for hub in hubs)
max_y = max(hub.y for hub in hubs)
map_width = max_x - min_x
map_height = max_y - min_y
```

No hay aún almacenamiento de posiciones transformadas, escala, márgenes, dibujo real ni bucle de eventos en el renderer definitivo.

### Qué entendió y dónde se cansó

- .values() obtiene objetos Hub del diccionario por nombre; list los recoge sin copiar los hubs.
- min/max sobre hub.x / hub.y dan extremos.
- max_x - min_x es ancho, NO punto medio.
- Coordenadas del mapa no son píxeles: x=1 es una unidad abstracta. Ejemplo entendido: map x=0,1,2,3 puede dibujarse en pantalla x=100,350,600,850.
- Se amplía/desplaza el mapa para no dibujar todos los hubs pegados en una esquina.
- Se propuso continuar con screen_width, screen_height = self.screen.get_size() y margin = 60. ESTAS LÍNEAS TODAVÍA NO ESTÁN EN EL ARCHIVO.
- Se explicó que la ventana sigue siendo 1000x700 y que un mapa grande se reduce con escala. Con márgenes de 60, ancho útil 880 y alto útil 580.
- Su última duda fue «un mapa grande no cabrá»: se explicó escala, y que encajar coordenadas no garantiza legibilidad en mapas densos; zoom/desplazamiento se podrán añadir después.
- Paró aquí por cansancio. No dar por dominada todavía la fórmula de escala ni introducir toda la transformación de golpe.

### Primer paso de la próxima sesión

1. Leer este seguimiento y revisar renderer/pygame_renderer.py sin modificarlo automáticamente.
2. Recordar brevemente: tamaño del mapa en unidades frente a tamaño de ventana en píxeles.
3. Obtener tamaño de pantalla y definir márgenes; calcular espacio útil con un ejemplo numérico.
4. Calcular escala paso a paso conservando proporción entre ejes. Tratar ancho/alto cero (mapas lineales) sin división por cero. Todavía NO se ha implementado ni explicado a fondo.
5. Después calcular desplazamiento para centrar y guardar posiciones de los hubs. Decidir y explicar orientación del eje y de pantalla respecto al mapa.
6. Luego draw_connections y draw_hubs, seguidos de texto, drones, controles y animación, introduciendo una pieza a la vez.

No saltar a una interfaz entera ni escribir automáticamente el renderer. Falta conectar main con creación de Drone, Simulation y presentación; main aún imprime itinerarios. Makefile, README, docstrings, estilo y tipos globales siguen pendientes.
