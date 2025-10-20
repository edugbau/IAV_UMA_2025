from __future__ import annotations

import heapq
import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .game import Move, State, WaterSortGame


@dataclass
class SearchResult:
    success: bool
    moves: List[Move]
    explored_nodes: int
    expanded_nodes: int
    max_frontier_size: int
    depth: int
    time_seconds: float

    def require_success(self) -> None:
        if not self.success:
            raise RuntimeError("Search did not find a solution")


class SearchAlgorithms:
    def __init__(self, game: WaterSortGame) -> None:
        self.game = game

    def bfs(self, initial_state: State) -> SearchResult:
        start = time.perf_counter()
        if self.game.is_goal_state(initial_state):
            elapsed = time.perf_counter() - start
            return SearchResult(True, [], 1, 0, 1, 0, elapsed)

        frontier = deque([initial_state])
        parents: Dict[State, Optional[State]] = {initial_state: None}
        moves_taken: Dict[State, Optional[Move]] = {initial_state: None}
        visited = {initial_state}
        visited_history = {initial_state}
        expanded = 0
        max_frontier = 1

        while frontier:
            current = frontier.popleft()
            expanded += 1
            if self.game.is_goal_state(current):
                elapsed = time.perf_counter() - start
                path = self._reconstruct_moves(current, parents, moves_taken)
                return SearchResult(True, path, len(visited_history), expanded, max_frontier, len(path), elapsed)

            for move in self.game.get_valid_moves(current):
                next_state, _ = self.game.apply_move(current, move)
                if next_state in visited:
                    continue
                visited.add(next_state)
                visited_history.add(next_state)
                parents[next_state] = current
                moves_taken[next_state] = move
                frontier.append(next_state)
            max_frontier = max(max_frontier, len(frontier))

        elapsed = time.perf_counter() - start
        return SearchResult(False, [], len(visited_history), expanded, max_frontier, 0, elapsed)

    def dfs(self, initial_state: State, depth_limit: Optional[int] = None) -> SearchResult:
        start = time.perf_counter()
        visited = {initial_state}
        visited_history = {initial_state}
        parents: Dict[State, Optional[State]] = {initial_state: None}
        moves_taken: Dict[State, Optional[Move]] = {initial_state: None}
        expanded = 0
        max_frontier = 1
        success_state: Optional[State] = None

        def search(state: State, depth: int) -> bool:
            nonlocal expanded, max_frontier, success_state
            if self.game.is_goal_state(state):
                success_state = state
                return True
            if depth_limit is not None and depth >= depth_limit:
                return False
            expanded += 1
            for move in self.game.get_valid_moves(state):
                next_state, _ = self.game.apply_move(state, move)
                if next_state in visited:
                    continue
                visited.add(next_state)
                parents[next_state] = state
                moves_taken[next_state] = move
                max_frontier = max(max_frontier, len(visited))
                visited_history.add(next_state)
                if search(next_state, depth + 1):
                    return True
                visited.remove(next_state)
            return False

        found = search(initial_state, 0)
        elapsed = time.perf_counter() - start
        if found and success_state is not None:
            path = self._reconstruct_moves(success_state, parents, moves_taken)
            return SearchResult(True, path, len(visited_history), expanded, max_frontier, len(path), elapsed)
        return SearchResult(False, [], len(visited_history), expanded, max_frontier, 0, elapsed)

    def a_star(self, initial_state: State, heuristic) -> SearchResult:
        start = time.perf_counter()
        open_heap: List[Tuple[int, int, State]] = []
        g_cost: Dict[State, int] = {initial_state: 0}
        parents: Dict[State, Optional[State]] = {initial_state: None}
        moves_taken: Dict[State, Optional[Move]] = {initial_state: None}
        expanded = 0
        entry_counter = 0

        initial_h = heuristic(initial_state)
        heapq.heappush(open_heap, (initial_h, entry_counter, initial_state))
        visited = set()
        max_frontier = 1

        while open_heap:
            f_score, _, current = heapq.heappop(open_heap)
            if current in visited:
                continue
            visited.add(current)

            if self.game.is_goal_state(current):
                elapsed = time.perf_counter() - start
                path = self._reconstruct_moves(current, parents, moves_taken)
                return SearchResult(True, path, len(visited), expanded, max_frontier, len(path), elapsed)

            expanded += 1
            current_g = g_cost[current]

            for move in self.game.get_valid_moves(current):
                next_state, _ = self.game.apply_move(current, move)
                tentative_g = current_g + 1
                if tentative_g >= g_cost.get(next_state, math.inf):
                    continue
                g_cost[next_state] = tentative_g
                parents[next_state] = current
                moves_taken[next_state] = move
                entry_counter += 1
                f_value = tentative_g + heuristic(next_state)
                heapq.heappush(open_heap, (f_value, entry_counter, next_state))
            max_frontier = max(max_frontier, len(open_heap))

        elapsed = time.perf_counter() - start
        return SearchResult(False, [], len(visited), expanded, max_frontier, 0, elapsed)

    def ida_star(self, initial_state: State, heuristic, max_depth: int = 200) -> SearchResult:
        start = time.perf_counter()
        expanded = 0
        max_frontier = 1
        global_visited: set[State] = {initial_state}

        def search(
            state: State,
            g: int,
            threshold: int,
            visited: set[State],
            path: List[Move],
        ) -> Tuple[bool, int]:
            nonlocal expanded, max_frontier
            f = g + heuristic(state)
            if f > threshold:
                return False, f
            if self.game.is_goal_state(state):
                return True, g
            if g >= max_depth:
                return False, math.inf
            expanded += 1
            min_threshold = math.inf
            for move in self.game.get_valid_moves(state):
                next_state, _ = self.game.apply_move(state, move)
                if next_state in visited:
                    continue
                visited.add(next_state)
                global_visited.add(next_state)
                max_frontier = max(max_frontier, len(visited))
                path.append(move)
                found, temp_threshold = search(next_state, g + 1, threshold, visited, path)
                if found:
                    return True, temp_threshold
                path.pop()
                min_threshold = min(min_threshold, temp_threshold)
                visited.remove(next_state)
            return False, min_threshold

        threshold = heuristic(initial_state)
        path: List[Move] = []
        while True:
            visited = {initial_state}
            found, temp_threshold = search(initial_state, 0, threshold, visited, path)
            if found:
                elapsed = time.perf_counter() - start
                return SearchResult(True, list(path), len(global_visited), expanded, max_frontier, len(path), elapsed)
            if temp_threshold == math.inf:
                elapsed = time.perf_counter() - start
                return SearchResult(False, [], len(global_visited), expanded, max_frontier, 0, elapsed)
            threshold = temp_threshold

    @staticmethod
    def _reconstruct_moves(goal_state: State, parents: Dict[State, Optional[State]], moves_taken: Dict[State, Optional[Move]]) -> List[Move]:
        path: List[Move] = []
        current = goal_state
        while True:
            move = moves_taken[current]
            if move is None:
                break
            path.append(move)
            parent = parents[current]
            if parent is None:
                break
            current = parent
        path.reverse()
        return path
