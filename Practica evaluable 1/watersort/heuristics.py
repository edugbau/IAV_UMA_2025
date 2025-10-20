from __future__ import annotations

from collections import Counter, defaultdict
from typing import Callable, Dict, Iterable

from .game import State, WaterSortGame

Heuristic = Callable[[State], int]


def build_entropy_heuristic(game: WaterSortGame) -> Heuristic:
    """Penalise dispersion of colors across multiple tubes."""

    def heuristic(state: State) -> int:
        color_distribution: Dict[str, list[int]] = defaultdict(list)
        for tube in state:
            counts = Counter(tube)
            for color, amount in counts.items():
                color_distribution[color].append(amount)
        penalty = 0
        for color, amounts in color_distribution.items():
            if len(amounts) <= 1:
                continue
            total_units = sum(amounts)
            max_in_single_tube = max(amounts)
            units_outside = total_units - max_in_single_tube
            penalty += (len(amounts) - 1) * units_outside
        return penalty

    return heuristic


def build_completion_heuristic(game: WaterSortGame) -> Heuristic:
    """Reward tubes that are already complete and penalise unfinished tubes."""

    def heuristic(state: State) -> int:
        tubes_incomplete = 0
        colors_positioned = 0
        for tube in state:
            if not tube:
                continue
            if len(tube) == game.capacity and len(set(tube)) == 1:
                continue
            tubes_incomplete += 1
            base_color = tube[0]
            streak = 1
            for color in tube[1:]:
                if color == base_color:
                    streak += 1
                else:
                    break
            colors_positioned += streak
        return (tubes_incomplete * game.capacity) - colors_positioned

    return heuristic


def build_blocking_heuristic(game: WaterSortGame) -> Heuristic:
    """Optional heuristic that penalises mixed tubes and blocked units."""

    def heuristic(state: State) -> int:
        total_mixed = 0
        blocked_units = 0
        for tube in state:
            if not tube:
                continue
            if len(set(tube)) > 1:
                total_mixed += len(tube)
            for idx, color in enumerate(tube[:-1]):
                above = tube[idx + 1 :]
                if any(upper != color for upper in above):
                    blocked_units += 1
        return total_mixed + (2 * blocked_units)

    return heuristic


def available_heuristics(game: WaterSortGame) -> Dict[str, Heuristic]:
    return {
        "entropy": build_entropy_heuristic(game),
        "completion": build_completion_heuristic(game),
        "blocking": build_blocking_heuristic(game),
    }
