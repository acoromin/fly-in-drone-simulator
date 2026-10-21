*This project has been created as part of the 42 curriculum by acoromin.*

# Fly-In

## Description

Fly-In is a Python drone simulation. It reads a network of hubs from a text
file, plans routes from start to goal, and animates the resulting movements
with Pygame while printing each turn to the terminal.

The objective is to deliver every drone in as few turns as possible while
respecting hub capacities, shared connection capacities, and zone types:

| Zone | Behavior |
| --- | --- |
| `normal` | Takes one turn to enter. |
| `priority` | Takes one turn to enter; preferred when search priorities tie. |
| `restricted` | Takes two turns to enter, occupying the connection for both. |
| `blocked` | Cannot be entered. |

## Instructions

Requires Python 3.13 or later, [uv](https://docs.astral.sh/uv/), Make, and a
graphical desktop for the Pygame window. Run commands from the project root.

```sh
make install
make run MAP=maps/easy/01_linear_path.txt
```

Installation creates `.venv` and installs the runtime and development
dependencies from `uv.lock`. No manual environment activation is needed.
Running `make run` without `MAP` uses `maps/my_map.txt`.

To run directly through uv:

```sh
PYGAME_HIDE_SUPPORT_PROMPT=1 uv run --locked python fly_in.py maps/easy/01_linear_path.txt
```

The window starts in manual mode. Press **Space** to advance or **A** to run
automatically. Each completed turn prints its movements to the terminal.

| Command | Purpose |
| --- | --- |
| `make install` | Install dependencies using the lockfile. |
| `make run MAP=path/to/map.txt` | Run a map. |
| `make debug MAP=path/to/map.txt` | Start the program in Python's `pdb` debugger. |
| `make lint` | Run Flake8 and mypy with the required flags. |
| `make lint-strict` | Run Flake8 and mypy in strict mode. |
| `make clean` | Remove the virtual environment and local Python/tool caches. |

Input and graphics errors are reported to standard error. Exit codes are
`0` for a normal exit, `1` for a handled error, and `130` for Ctrl+C.

## Controls and visual representation

| Control | Action |
| --- | --- |
| **Space** | Advance one turn when no animation is in progress. |
| **A** | Toggle automatic advancement. |
| **R** | Reset to turn zero and return to manual mode. |
| **Esc** or close window | Exit the program. |
| Hover over a hub | Reveal its name when it does not fit inside the hub. |

To return to manual stepping, toggle **A** off and use **Space**. An animation
already in progress finishes before automatic advancement stops.

The renderer scales and centers the network using the map coordinates.
Animated drones show travel between hubs, including the intermediate turn
on a connection toward a restricted zone. Overlapping drones have a count
label, and the status panel shows the current turn and delivered drones.

Hub colors come from the map; unrecognized colors use a default color.
Colored rings distinguish blocked, priority, and restricted zones. These
visual cues help identify bottlenecks and follow simultaneous movements.

## Algorithm explanation

### Parsing and graph construction

Lark reads the map grammar, and Pydantic validates the resulting data.
The validated hubs and bidirectional connections form an adjacency list.
Parsing, graph construction, planning, simulation, and rendering are kept
in separate packages.

### Planning with time and reservations

1. A static Dijkstra search checks that a route exists, excluding blocked
   hubs and accounting for entry costs.
2. Drones are planned sequentially. Each search explores states of the form
   `(hub, turn)`, meaning that the drone is at that hub after that turn.
3. A state can lead to a neighboring hub or a one-turn wait. Moves must fit
   both the destination capacity and the connection capacity for every
   turn spent travelling.
4. A heap processes earlier turns first, then fewer movements. Entering a
   priority zone is a further queue tie-breaker. Waiting does not count as
   a movement, which discourages unnecessary trips when waiting works.
5. The chosen itinerary is reserved before planning the next drone.

For example, entering a restricted hub from turn 2 reaches it at turn 4.
The connection must have space during both turns 3 and 4, and the
destination must have space at turn 4. Connection capacity is shared by
both travel directions. Start and goal have unlimited hub occupancy.

This approach finds the earliest feasible arrival for each drone under
existing reservations. Earlier itineraries are not reconsidered, so it
does not guarantee the best total completion time for every possible map.
The priority-zone tie-breaker is local to the search queue; it does not
maximize the number of priority zones along a complete route.

All itineraries are computed before rendering starts. The simulation then
plays them turn by turn, without recalculating paths on every frame.
Search time and memory grow with the number of explored `(hub, turn)`
states; congested maps can require more waiting states.

## Example input and output

The map `maps/easy/01_linear_path.txt` contains:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Run it with `make run MAP=maps/easy/01_linear_path.txt` and advance four turns:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line represents one turn, with space-separated movements. `D1-goal`
means drone 1 reaches `goal`. A drone still travelling toward a restricted
hub is printed with the connection endpoints, such as `D1-loop_B-exit_point`.
Waiting drones and drones delivered on previous turns are omitted.

Maps may specify `zone`, `color`, and `max_drones` on hubs, and
`max_link_capacity` on connections. Both capacities default to one.
Comments begin with `#`. More examples are available in the
[maps directory](maps/README.md).

## Resources

- [Python heapq documentation](https://docs.python.org/3/library/heapq.html):
  priority queues used by the searches.
- [Lark documentation](https://lark-parser.readthedocs.io/en/stable/):
  grammar definitions and parsing.
- [Pydantic documentation](https://docs.pydantic.dev/latest/):
  data models and validation.
- [Pygame documentation](https://www.pygame.org/docs/):
  drawing, events, and animation.
- [uv project guide](https://docs.astral.sh/uv/guides/projects/):
  dependency management, virtual environments, and lockfiles.

### AI usage

AI was used for explanations of Python concepts, discussion of pathfinding
and capacity rules, and reviews of parsing, planning, and rendering behavior.
It also assisted with implementation changes to the entry point, error
handling, movement output, and Makefile, and with learning the uv workflow.
The English docstrings and this README were drafted with AI assistance.
