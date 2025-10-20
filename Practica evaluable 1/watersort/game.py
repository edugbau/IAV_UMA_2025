from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

State = Tuple[Tuple[str, ...], ...]


@dataclass(frozen=True)
class Move:
    """Represents pouring the top stack from ``src`` tube into ``dst`` tube."""

    src: int
    dst: int

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.src}->{self.dst}"


class WaterSortGame:
    """State space representation of the Water Sort Puzzle."""

    DEFAULT_COLORS = (
        "R",
        "G",
        "B",
        "Y",
        "P",
        "C",
        "M",
        "O",
        "W",
        "K",
        "L",
        "N",
    )

    def __init__(self, num_tubes: int, num_colors: int, capacity: int = 4, seed: int | None = None) -> None:
        if not (5 <= num_tubes <= 12):
            raise ValueError("num_tubes must be between 5 and 12")
        if not (3 <= num_colors <= num_tubes - 2):
            raise ValueError("num_colors must be at least 3 and at most num_tubes-2")
        if num_colors > len(self.DEFAULT_COLORS):
            raise ValueError("num_colors exceeds available predefined colors")
        self.num_tubes = num_tubes
        self.num_colors = num_colors
        self.capacity = capacity
        self.random = random.Random(seed)
        self.colors = self.DEFAULT_COLORS[:num_colors]

    def generate_solved_state(self) -> State:
        tubes: List[Tuple[str, ...]] = [tuple(color for _ in range(self.capacity)) for color in self.colors]
        tubes.extend(() for _ in range(self.num_tubes - self.num_colors))
        return tuple(tubes)

    def generate_initial_state(self, scramble_moves: int = 60, max_attempts: int = 10) -> State:
        """Generate a random but solvable configuration using the provided seed."""

        attempts = max(max_attempts * 5, max(20, scramble_moves))
        last_candidate = self.generate_solved_state()
        for _ in range(attempts):
            candidate = self._generate_random_state()
            if not self.is_goal_state(candidate):
                return candidate
            last_candidate = candidate

        if self.is_goal_state(last_candidate):
            tubes = [list(tube) for tube in last_candidate]
            filled = [idx for idx, tube in enumerate(tubes) if tube]
            empties = [idx for idx, tube in enumerate(tubes) if not tube]
            if len(filled) >= 2 and empties:
                empty_idx = empties[0]
                donor_one, donor_two = filled[:2]
                tubes[empty_idx].append(tubes[donor_one].pop())
                if tubes[donor_two]:
                    tubes[empty_idx].append(tubes[donor_two].pop())
            return tuple(tuple(tube) for tube in tubes)

        return last_candidate

    def _generate_random_state(self) -> State:
        units: List[str] = []
        for color in self.colors:
            units.extend([color] * self.capacity)
        self.random.shuffle(units)

        tubes: List[List[str]] = [[] for _ in range(self.num_tubes)]
        fill_indices = self.random.sample(range(self.num_tubes), self.num_colors)

        for color in units:
            candidates = [idx for idx in fill_indices if len(tubes[idx]) < self.capacity]
            if not candidates:
                raise RuntimeError("Unable to distribute colors across tubes")
            chosen = self.random.choice(candidates)
            tubes[chosen].append(color)

        return tuple(tuple(tube) for tube in tubes)

    def _scramble_state(self, state: State, scramble_moves: int) -> State:
        current = state
        previous: Move | None = None
        for _ in range(scramble_moves):
            moves = self.get_valid_moves(current)
            if previous:
                moves = [m for m in moves if not (m.src == previous.dst and m.dst == previous.src)]
            if not moves:
                break
            move = self.random.choice(moves)
            current, _ = self.apply_move(current, move)
            previous = move
        return current

    def _is_solvable(self, state: State, node_limit: int) -> bool:
        frontier = deque([state])
        visited = {state}
        nodes = 0
        while frontier and nodes <= node_limit:
            current = frontier.popleft()
            if self.is_goal_state(current):
                return True
            nodes += 1
            for move in self.get_valid_moves(current):
                next_state, _ = self.apply_move(current, move)
                if next_state in visited:
                    continue
                visited.add(next_state)
                frontier.append(next_state)
        return False

    def is_goal_state(self, state: State) -> bool:
        for tube in state:
            if not tube:
                continue
            if len(tube) != self.capacity:
                return False
            if len(set(tube)) != 1:
                return False
        return True

    def is_valid_state(self, state: State) -> bool:
        if len(state) != self.num_tubes:
            return False
        for tube in state:
            if len(tube) > self.capacity:
                return False
        return True

    def get_valid_moves(self, state: State) -> List[Move]:
        moves: List[Move] = []
        for src_idx, src in enumerate(state):
            if not src:
                continue
            top_color = src[-1]
            run_length = 1
            for i in range(len(src) - 2, -1, -1):
                if src[i] == top_color:
                    run_length += 1
                else:
                    break
            for dst_idx, dst in enumerate(state):
                if src_idx == dst_idx:
                    continue
                if len(dst) == self.capacity:
                    continue
                if dst and dst[-1] != top_color:
                    continue
                if not dst and run_length == len(src):
                    # If destination empty and pour empties tube, avoid redundant backtracking
                    pass
                moves.append(Move(src_idx, dst_idx))
        return moves

    def apply_move(self, state: State, move: Move) -> Tuple[State, int]:
        if not (0 <= move.src < len(state) and 0 <= move.dst < len(state)):
            raise ValueError("Move indices out of range")
        if move.src == move.dst:
            raise ValueError("Source and destination tubes must differ")

        tubes = [list(tube) for tube in state]
        src = tubes[move.src]
        dst = tubes[move.dst]
        if not src:
            raise ValueError("Cannot pour from an empty tube")
        if len(dst) >= self.capacity:
            raise ValueError("Destination tube is full")
        if dst and dst[-1] != src[-1]:
            raise ValueError("Destination top color must match the poured color")

        top_color = src[-1]
        poured = 0
        while src and src[-1] == top_color and len(dst) < self.capacity:
            dst.append(src.pop())
            poured += 1
        new_state: State = tuple(tuple(tube) for tube in tubes)
        return new_state, poured

    @staticmethod
    def as_tuple(state: Sequence[Sequence[str]]) -> State:
        return tuple(tuple(tube) for tube in state)

    @staticmethod
    def visualize_state(state: State) -> str:
        """Return a human-friendly multiline representation."""

        max_height = max((len(tube) for tube in state), default=0)
        rows = []
        for level in range(max_height - 1, -1, -1):
            row = []
            for tube in state:
                row.append(tube[level] if level < len(tube) else " ")
            rows.append(" | ".join(row))
        rows.append("--" * len(state))
        rows.append("   ".join(str(i) for i in range(len(state))))
        return "\n".join(rows)

    @staticmethod
    def flatten_colors(state: State) -> Iterable[str]:
        for tube in state:
            for color in tube:
                yield color
