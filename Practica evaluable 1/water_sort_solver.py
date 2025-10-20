from __future__ import annotations

import argparse
from typing import Iterable, List, Sequence

from watersort.game import Move, State, WaterSortGame
from watersort.heuristics import available_heuristics
from watersort.search import SearchAlgorithms, SearchResult


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Water Sort Puzzle solver")
    parser.add_argument("algorithm", choices=["bfs", "dfs", "astar", "ida"], help="Search algorithm to execute")
    parser.add_argument("--tubes", type=int, default=8, help="Number of tubes (5-12)")
    parser.add_argument("--colors", type=int, default=6, help="Number of colors (>=3)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible puzzles")
    parser.add_argument("--scramble", type=int, default=60, help="Number of scrambling moves to create the puzzle")
    parser.add_argument("--depth-limit", type=int, default=None, help="Depth limit for DFS")
    parser.add_argument("--heuristic", choices=["entropy", "completion", "blocking"], default="entropy", help="Heuristic to use with informed search")
    parser.add_argument("--ida-max-depth", type=int, default=200, help="Maximum depth explored by IDA*")
    parser.add_argument("--show-states", action="store_true", help="Print each intermediate state of the solution")
    parser.add_argument("--no-scramble", action="store_true", help="Start from solved configuration (debug)")
    return parser.parse_args()


def build_state_sequence(initial_state: State, moves: Sequence[Move], game: WaterSortGame) -> List[State]:
    sequence = [initial_state]
    current = initial_state
    for move in moves:
        current, _ = game.apply_move(current, move)
        sequence.append(current)
    return sequence


def display_solution(sequence: Iterable[State], header: str | None = None) -> None:
    if header:
        print(header)
    for step, state in enumerate(sequence):
        print(f"Step {step}")
        print(WaterSortGame.visualize_state(state))
        print()


def main() -> None:
    args = parse_args()
    game = WaterSortGame(num_tubes=args.tubes, num_colors=args.colors, seed=args.seed)
    initial_state = game.generate_solved_state() if args.no_scramble else game.generate_initial_state(scramble_moves=args.scramble)

    print("Initial state:")
    print(WaterSortGame.visualize_state(initial_state))
    print()

    algorithms = SearchAlgorithms(game)
    heuristics = available_heuristics(game)

    if args.algorithm == "bfs":
        result = algorithms.bfs(initial_state)
    elif args.algorithm == "dfs":
        result = algorithms.dfs(initial_state, depth_limit=args.depth_limit)
    elif args.algorithm == "astar":
        heuristic_fn = heuristics[args.heuristic]
        result = algorithms.a_star(initial_state, heuristic_fn)
    else:
        heuristic_fn = heuristics[args.heuristic]
        result = algorithms.ida_star(initial_state, heuristic_fn, max_depth=args.ida_max_depth)

    print(format_result(result))

    if result.success:
        sequence = build_state_sequence(initial_state, result.moves, game)
        if args.show_states:
            display_solution(sequence, header="Solution path:")
    else:
        print("No solution found with the selected configuration.")


def format_result(result: SearchResult) -> str:
    status = "Success" if result.success else "Failure"
    lines = [f"Result: {status}"]
    lines.append(f"Depth: {result.depth}")
    lines.append(f"Moves: {[str(move) for move in result.moves]}")
    lines.append(f"Nodes explored: {result.explored_nodes}")
    lines.append(f"Nodes expanded: {result.expanded_nodes}")
    lines.append(f"Max frontier size: {result.max_frontier_size}")
    lines.append(f"Time: {result.time_seconds:.4f}s")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
