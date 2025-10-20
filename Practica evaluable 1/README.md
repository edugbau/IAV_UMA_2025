# Water Sort Puzzle Solver

Solver implementation for the Water Sort Puzzle developed as part of the "Inteligencia Artificial para Juegos" coursework. The project models the puzzle as a state-space search problem and includes several uninformed and informed search algorithms along with configurable heuristics.

## Features

- Puzzle model with immutable state representation and move validation.
- Random, reproducible puzzle generator that filters for solvable instances.
- Search algorithms: Breadth-First Search (BFS), Depth-First Search (DFS), A*, Iterative Deepening A* (IDA*).
- Heuristics inspired by the assignment brief: entropy, tube completion, and blocking penalties.
- Command-line interface for running experiments, printing solutions, and collecting search metrics.
- Interactive Tkinter GUI with manual play, solver playback, and visual analytics.
- Dedicated analysis mode that charts nodes explored versus runtime for recorded solver runs.

## Requirements

- Python 3.11+
- `pypdf` (only required if you plan to parse the assignment PDF programmatically)

## Setup

```powershell
# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The solver does not have runtime dependencies beyond the Python standard library.

## Usage

Generate and solve a puzzle directly from the command line:

```powershell
python water_sort_solver.py bfs --tubes 6 --colors 3 --seed 42 --show-states
```

Options:

- `algorithm`: `bfs`, `dfs`, `astar`, or `ida`
- `--tubes`: number of tubes (5–12)
- `--colors`: number of colors (3–num_tubes-2)
- `--seed`: random seed for reproducible puzzles
- `--scramble`: controls the node-limit when validating solvability
- `--heuristic`: `entropy`, `completion`, or `blocking` (used for A* and IDA*)
- `--depth-limit`: optional limit for DFS
- `--show-states`: print each intermediate board state

Example A* run:

```powershell
python water_sort_solver.py astar --tubes 7 --colors 4 --seed 99 --heuristic completion --show-states
```

### Interactive GUI

To experiment visually with the puzzle, launch the graphical interface:

```powershell
python water_sort_gui.py
```

Features available in the GUI:

- Configure tubes, colors, seed, search algorithm, heuristic, and scramble difficulty.
- Generate solvable puzzles and play manually by clicking source and destination tubes.
- Compute solutions with BFS, DFS, A*, or IDA*, then step through or auto-play the solver.
- Undo or reset states at any time and monitor metrics (nodes explored, runtime, move count).
- Switch to the "Modo Análisis" tab to plot nodes vs. time for recent solver executions and compare algorithms quickly.

## Project Structure

- `water_sort_solver.py`: CLI entrypoint and user interface.
- `water_sort_gui.py`: Tkinter application for interactive play and solver visualization.
- `watersort/game.py`: Puzzle domain model, move generation, and puzzle generator.
- `watersort/search.py`: Search algorithms and performance instrumentation.
- `watersort/heuristics.py`: Heuristic factory functions.

## Extending

- Add new heuristics by expanding `watersort/heuristics.py` and registering them in `available_heuristics`.
- Implement additional search strategies (e.g., beam search) inside `watersort/search.py`.
- Extend the graphical experience inside `water_sort_gui.py` (new UI widgets, themes, or alternative animations).

## License

Distributed for educational use within the "Inteligencia Artificial para Juegos" course.
