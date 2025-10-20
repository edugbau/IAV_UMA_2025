from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional, Sequence

from watersort.game import Move, State, WaterSortGame
from watersort.heuristics import available_heuristics
from watersort.search import SearchAlgorithms

CANVAS_BG = "#0f1327"
CONTROL_BG = "#151a33"
TEXT_LIGHT = "#f4f6fb"
TEXT_MUTED = "#8f9bb3"
TUBE_SHADOW = "#050714"
TUBE_BODY = "#1f2a44"
SELECTION_ACCENT = "#ffd166"

COLOR_PALETTE: Dict[str, str] = {
    "R": "#ff6b6b",
    "G": "#3ddc84",
    "B": "#3498db",
    "Y": "#f4d35e",
    "P": "#a56eff",
    "C": "#1abc9c",
    "M": "#ff7eb9",
    "O": "#f39c12",
    "W": "#ecf0f1",
    "K": "#2d3436",
    "L": "#7bed9f",
    "N": "#ff9ff3",
}

ALGORITHM_COLORS: Dict[str, str] = {
    "bfs": "#ff7f50",
    "dfs": "#f4d35e",
    "astar": "#3ddc84",
    "ida": "#3498db",
}


class WaterSortApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Water Sort Puzzle Studio")
        self.geometry("1180x720")
        self.configure(bg=CONTROL_BG)
        self.minsize(960, 600)

        self.game: Optional[WaterSortGame] = None
        self.current_state: Optional[State] = None
        self.state_history: List[State] = []
        self.solution_states: List[State] = []
        self.solution_index = 0
        self.selected_tube: Optional[int] = None
        self.move_counter = 0
        self.auto_job: Optional[str] = None
        self.analytics_data: list[dict[str, object]] = []

        self.tubes_var = tk.IntVar(value=8)
        self.colors_var = tk.IntVar(value=6)
        self.seed_var = tk.StringVar(value="")
        self.algorithm_var = tk.StringVar(value="astar")
        self.heuristic_var = tk.StringVar(value="entropy")
        self.scramble_var = tk.DoubleVar(value=60.0)
        self.speed_var = tk.DoubleVar(value=350.0)

        self.feedback_var = tk.StringVar(value="Genera un puzzle para comenzar.")
        self.stats_var = tk.StringVar(value="")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=CONTROL_BG)
        style.configure("TLabel", background=CONTROL_BG, foreground=TEXT_LIGHT)
        style.configure("TButton", padding=6)
        style.configure("Card.TFrame", background=CANVAS_BG)
        style.configure("Accent.TButton", background=SELECTION_ACCENT)

        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        controls = ttk.Frame(main_frame)
        controls.pack(side=tk.LEFT, fill=tk.Y)

        self._build_controls(controls)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        puzzle_tab = ttk.Frame(self.notebook, style="Card.TFrame")
        analysis_tab = ttk.Frame(self.notebook, style="Card.TFrame")
        puzzle_tab.pack_propagate(False)
        analysis_tab.pack_propagate(False)
        self.notebook.add(puzzle_tab, text="Modo Juego")
        self.notebook.add(analysis_tab, text="Modo Análisis")

        self.canvas = tk.Canvas(
            puzzle_tab,
            bg=CANVAS_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.canvas.configure(width=880, height=520)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", lambda _event: self._redraw_state())

        self.analysis_canvas = tk.Canvas(
            analysis_tab,
            bg=CANVAS_BG,
            highlightthickness=0,
            height=360,
        )
        self.analysis_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 4))
        self.analysis_canvas.configure(width=880, height=360)
        self.analysis_canvas.bind("<Configure>", lambda _event: self._update_analysis_panel())

        summary_frame = ttk.Frame(analysis_tab)
        summary_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        self.analysis_summary = ttk.Label(summary_frame, text="Genera soluciones para comparar el rendimiento.", foreground=TEXT_MUTED, wraplength=520)
        self.analysis_summary.pack(anchor=tk.W)
        self._update_analysis_panel()

    def _build_controls(self, parent: ttk.Frame) -> None:
        header = ttk.Label(parent, text="Controles", font=("Segoe UI", 14, "bold"))
        header.pack(anchor=tk.W, pady=(4, 10))

        grid = ttk.Frame(parent)
        grid.pack(fill=tk.X)

        ttk.Label(grid, text="Tubos").grid(row=0, column=0, sticky=tk.W, pady=2)
        tubes_spin = ttk.Spinbox(grid, from_=5, to=12, textvariable=self.tubes_var, width=6, command=self._sync_color_limit)
        tubes_spin.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(grid, text="Colores").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.colors_spin = ttk.Spinbox(grid, from_=3, to=10, textvariable=self.colors_var, width=6, command=self._sync_color_limit)
        self.colors_spin.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(grid, text="Semilla").grid(row=2, column=0, sticky=tk.W, pady=2)
        seed_entry = ttk.Entry(grid, textvariable=self.seed_var, width=12)
        seed_entry.grid(row=2, column=1, sticky=tk.W)

        ttk.Label(grid, text="Algoritmo").grid(row=3, column=0, sticky=tk.W, pady=(6, 2))
        algorithm_combo = ttk.Combobox(
            grid,
            textvariable=self.algorithm_var,
            values=["bfs", "dfs", "astar", "ida"],
            state="readonly",
            width=10,
        )
        algorithm_combo.grid(row=3, column=1, sticky=tk.W)
        algorithm_combo.bind("<<ComboboxSelected>>", lambda _event: self._toggle_heuristic())

        ttk.Label(grid, text="Heurística").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.heuristic_combo = ttk.Combobox(
            grid,
            textvariable=self.heuristic_var,
            values=[],
            state="readonly",
            width=10,
        )
        self.heuristic_combo.grid(row=4, column=1, sticky=tk.W)

        ttk.Label(grid, text="Dificultad").grid(row=5, column=0, sticky=tk.W, pady=(10, 2))
        scramble_scale = ttk.Scale(grid, from_=20, to=160, variable=self.scramble_var, orient=tk.HORIZONTAL, command=lambda _v: None)
        scramble_scale.grid(row=5, column=1, sticky="we")
        grid.columnconfigure(1, weight=1)

        ttk.Label(grid, text="Velocidad animación (ms)").grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(10, 4))
        speed_scale = ttk.Scale(grid, from_=80, to=800, variable=self.speed_var, orient=tk.HORIZONTAL, command=lambda _v: None)
        speed_scale.grid(row=7, column=0, columnspan=2, sticky="we")

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=14)

        ttk.Button(button_frame, text="Generar puzzle", command=self._generate_puzzle).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Calcular solución", command=self._compute_solution).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Paso siguiente", command=self._step_solution).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Reproducir solución", command=self._auto_solution).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Detener animación", command=self._cancel_auto).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Deshacer", command=self._undo_move).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Restablecer", command=self._reset_puzzle).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Modo análisis", command=self._switch_to_analysis).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Limpiar análisis", command=self._clear_analysis).pack(fill=tk.X, pady=2)

        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Label(info_frame, text="Estado", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, textvariable=self.feedback_var, wraplength=240, foreground=TEXT_MUTED).pack(anchor=tk.W, pady=4)

        ttk.Label(info_frame, text="Detalle", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(info_frame, textvariable=self.stats_var, wraplength=240).pack(anchor=tk.W, pady=4)

        self._toggle_heuristic()
        self._sync_color_limit()

    def _sync_color_limit(self) -> None:
        max_colors = max(3, self.tubes_var.get() - 2)
        if hasattr(self, "colors_spin"):
            self.colors_spin.configure(to=max_colors)
        if self.colors_var.get() > max_colors:
            self.colors_var.set(max_colors)

    def _switch_to_analysis(self) -> None:
        if hasattr(self, "notebook"):
            tabs = self.notebook.tabs()
            if len(tabs) > 1:
                self.notebook.select(tabs[1])

    def _clear_analysis(self) -> None:
        self.analytics_data.clear()
        if hasattr(self, "analysis_summary"):
            self.analysis_summary.configure(text="Sin datos de rendimiento. Calcula una solución para generar métricas.")
        self._update_analysis_panel()

    def _update_analysis_panel(self) -> None:
        if not hasattr(self, "analysis_canvas"):
            return
        canvas = self.analysis_canvas
        canvas.delete("all")
        width = canvas.winfo_width() or canvas.winfo_reqwidth()
        height = canvas.winfo_height() or canvas.winfo_reqheight()
        margin = 60
        axis_color = TEXT_MUTED
        text_color = TEXT_LIGHT

        if not self.analytics_data:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Sin datos disponibles. Calcula soluciones para visualizar el rendimiento.",
                fill=TEXT_MUTED,
                font=("Segoe UI", 14, "bold"),
                width=width - 80,
            )
            return

        max_nodes = max(entry["nodes"] for entry in self.analytics_data) or 1
        max_time = max(entry["time"] for entry in self.analytics_data) or 1e-6
        plot_left = margin
        plot_right = width - margin
        plot_bottom = height - margin
        plot_top = margin

        canvas.create_line(plot_left, plot_top, plot_left, plot_bottom, fill=axis_color, width=2)
        canvas.create_line(plot_left, plot_bottom, plot_right, plot_bottom, fill=axis_color, width=2)
        canvas.create_text(plot_left - 30, plot_top, text="Tiempo (s)", angle=90, fill=text_color, font=("Segoe UI", 11, "bold"))
        canvas.create_text(plot_right, plot_bottom + 30, text="Nodos explorados", fill=text_color, font=("Segoe UI", 11, "bold"))

        tick_count = 4
        for i in range(tick_count + 1):
            node_value = (max_nodes / tick_count) * i
            x = plot_left + (node_value / max_nodes) * (plot_right - plot_left)
            canvas.create_line(x, plot_bottom, x, plot_bottom + 6, fill=axis_color)
            canvas.create_text(x, plot_bottom + 18, text=f"{int(node_value)}", fill=axis_color, font=("Segoe UI", 9))

            time_value = (max_time / tick_count) * i
            y = plot_bottom - (time_value / max_time) * (plot_bottom - plot_top)
            canvas.create_line(plot_left - 6, y, plot_left, y, fill=axis_color)
            canvas.create_text(plot_left - 12, y, text=f"{time_value:.2f}", fill=axis_color, font=("Segoe UI", 9), anchor=tk.E)

        grouped: Dict[str, List[dict]] = {}
        for entry in self.analytics_data:
            grouped.setdefault(entry["algorithm"], []).append(entry)

        legend_x = plot_right - 160
        legend_y = plot_top
        legend_spacing = 18

        for idx, (algorithm, entries) in enumerate(sorted(grouped.items())):
            color = ALGORITHM_COLORS.get(algorithm, SELECTION_ACCENT)
            legend_label = f"{algorithm.upper()}"
            canvas.create_rectangle(
                legend_x,
                legend_y + idx * legend_spacing - 6,
                legend_x + 14,
                legend_y + idx * legend_spacing + 8,
                fill=color,
                outline="",
            )
            canvas.create_text(
                legend_x + 20,
                legend_y + idx * legend_spacing + 1,
                text=legend_label,
                fill=text_color,
                font=("Segoe UI", 10, "bold"),
                anchor=tk.W,
            )

            sorted_entries = sorted(entries, key=lambda item: item["nodes"])
            previous_point: Optional[tuple[float, float]] = None
            for entry in sorted_entries:
                x = plot_left + (entry["nodes"] / max_nodes) * (plot_right - plot_left)
                y = plot_bottom - (entry["time"] / max_time) * (plot_bottom - plot_top)
                radius = 6
                canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline="")
                canvas.create_text(x + 8, y - 10, text=f"{entry['time']:.3f}s", fill=text_color, font=("Segoe UI", 9), anchor=tk.W)
                if previous_point is not None:
                    canvas.create_line(previous_point[0], previous_point[1], x, y, fill=color, width=2)
                previous_point = (x, y)

        latest = self.analytics_data[-3:][::-1]
        summary_lines = [
            f"{item['algorithm'].upper()} • Nodos: {item['nodes']} • Tiempo: {item['time']:.3f}s • Movs: {item['moves']}" + (f" • Heurística: {item['heuristic']}" if item['heuristic'] else "")
            for item in latest
        ]
        summary_text = "\n".join(summary_lines) if summary_lines else "Sin datos recientes."
        if hasattr(self, "analysis_summary"):
            self.analysis_summary.configure(text=summary_text)

    def _toggle_heuristic(self) -> None:
        if not self.game:
            # Use a temporary game for option listing
            temp_game = WaterSortGame(self.tubes_var.get(), self.colors_var.get())
            heuristics = list(available_heuristics(temp_game).keys())
        else:
            heuristics = list(available_heuristics(self.game).keys())
        self.heuristic_combo.configure(values=heuristics)
        if self.heuristic_var.get() not in heuristics:
            self.heuristic_var.set(heuristics[0])
        if self.algorithm_var.get() in {"astar", "ida"}:
            self.heuristic_combo.state(["!disabled", "readonly"])
        else:
            self.heuristic_combo.state(["disabled"])

    def _generate_puzzle(self) -> None:
        self._cancel_auto()
        try:
            tubes = self.tubes_var.get()
            colors = self.colors_var.get()
            if colors > tubes - 2:
                raise ValueError("La cantidad de colores debe ser al menos dos menos que los tubos.")
            seed_value: Optional[int] = None
            seed_text = self.seed_var.get().strip()
            if seed_text:
                seed_value = int(seed_text)
            self.game = WaterSortGame(tubes, colors, seed=seed_value)
            state = self.game.generate_initial_state(scramble_moves=int(self.scramble_var.get()))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            return

        self.current_state = state
        self.state_history = [state]
        self.solution_states = []
        self.solution_index = 0
        self.selected_tube = None
        self.move_counter = 0
        self.stats_var.set("")
        self.feedback_var.set("Puzzle listo. Haz clic en un tubo para seleccionar el origen.")
        self._toggle_heuristic()
        self._redraw_state()

    def _compute_solution(self) -> None:
        if not self.game or self.current_state is None:
            messagebox.showinfo("Información", "Primero genera un puzzle.")
            return
        self._cancel_auto()
        algorithms = SearchAlgorithms(self.game)
        algorithm = self.algorithm_var.get()
        heuristics = available_heuristics(self.game)
        try:
            if algorithm == "bfs":
                result = algorithms.bfs(self.current_state)
            elif algorithm == "dfs":
                result = algorithms.dfs(self.current_state)
            elif algorithm == "astar":
                result = algorithms.a_star(self.current_state, heuristics[self.heuristic_var.get()])
            else:
                result = algorithms.ida_star(self.current_state, heuristics[self.heuristic_var.get()])
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            return

        if not result.success:
            self.stats_var.set("No se encontró solución con la configuración actual.")
            return

        self.solution_states = self._build_sequence(self.current_state, result.moves)
        self.solution_index = 0
        info = (
            f"Algoritmo: {algorithm.upper()}\n"
            f"Movimientos: {len(result.moves)}\n"
            f"Nodos explorados: {result.explored_nodes}\n"
            f"Tiempo: {result.time_seconds:.3f}s"
        )
        self.stats_var.set(info)
        self.feedback_var.set("Solución calculada. Usa 'Paso siguiente' o 'Reproducir solución'.")
        heuristic_name = self.heuristic_var.get() if algorithm in {"astar", "ida"} else ""
        self.analytics_data.append(
            {
                "algorithm": algorithm,
                "heuristic": heuristic_name,
                "nodes": result.explored_nodes,
                "time": result.time_seconds,
                "moves": len(result.moves),
                "tubes": self.tubes_var.get(),
                "colors": self.colors_var.get(),
                "seed": self.seed_var.get().strip() or "—",
            }
        )
        if len(self.analytics_data) > 60:
            self.analytics_data = self.analytics_data[-60:]
        self._update_analysis_panel()

    def _step_solution(self) -> None:
        if not self.solution_states:
            self._compute_solution()
            if not self.solution_states:
                return
        self._cancel_auto()
        if not self._advance_solution():
            self.feedback_var.set("La solución ya se reprodujo por completo.")

    def _auto_solution(self) -> None:
        if not self.solution_states:
            self._compute_solution()
            if not self.solution_states:
                return
        self._cancel_auto()
        self.feedback_var.set("Reproduciendo solución automática...")
        self._animate_step()

    def _animate_step(self) -> None:
        if self._advance_solution():
            delay = max(50, int(self.speed_var.get()))
            self.auto_job = self.after(delay, self._animate_step)
        else:
            self.auto_job = None
            if self.game and self.current_state and self.game.is_goal_state(self.current_state):
                self.feedback_var.set("¡Puzzle resuelto!")
            else:
                self.feedback_var.set("No quedan pasos en la solución.")

    def _advance_solution(self) -> bool:
        if not self.game or not self.current_state or not self.solution_states:
            return False
        if self.solution_index >= len(self.solution_states) - 1:
            return False
        self.solution_index += 1
        next_state = self.solution_states[self.solution_index]
        if next_state == self.current_state:
            return self._advance_solution()
        self.current_state = next_state
        self.state_history.append(next_state)
        self.move_counter = len(self.state_history) - 1
        self.selected_tube = None
        self._redraw_state()
        if self.game.is_goal_state(next_state):
            self.feedback_var.set("¡Puzzle resuelto!")
        else:
            self.feedback_var.set(f"Paso {self.solution_index}/{len(self.solution_states) - 1}")
        return True

    def _undo_move(self) -> None:
        if len(self.state_history) <= 1:
            self.feedback_var.set("No hay movimientos para deshacer.")
            return
        self._cancel_auto()
        self.state_history.pop()
        self.current_state = self.state_history[-1]
        self.move_counter = len(self.state_history) - 1
        self.selected_tube = None
        self.solution_states = []
        self.stats_var.set("")
        self.feedback_var.set("Movimiento deshecho.")
        self._redraw_state()

    def _reset_puzzle(self) -> None:
        if not self.state_history:
            return
        self._cancel_auto()
        self.current_state = self.state_history[0]
        self.state_history = [self.current_state]
        self.move_counter = 0
        self.selected_tube = None
        self.solution_states = []
        self.stats_var.set("")
        self.feedback_var.set("Puzzle restablecido al estado inicial.")
        self._redraw_state()

    def _cancel_auto(self) -> None:
        if self.auto_job is not None:
            self.after_cancel(self.auto_job)
            self.auto_job = None

    def _on_canvas_click(self, event: tk.Event) -> None:
        if not self.game or not self.current_state:
            return
        tube_index = self._tube_index_from_coord(event.x)
        if tube_index is None:
            return
        if self.selected_tube is None:
            if not self.current_state[tube_index]:
                self.feedback_var.set("Selecciona un tubo con contenido para verter.")
                return
            self.selected_tube = tube_index
            self.feedback_var.set(f"Tubo {tube_index} seleccionado. Elige el destino.")
            self._redraw_state()
            return

        if tube_index == self.selected_tube:
            self.selected_tube = None
            self.feedback_var.set("Selección cancelada.")
            self._redraw_state()
            return

        move = Move(self.selected_tube, tube_index)
        valid_moves = self.game.get_valid_moves(self.current_state)
        if move not in valid_moves:
            self.feedback_var.set("Movimiento inválido según las reglas.")
            self.selected_tube = None
            self._redraw_state()
            return

        self._cancel_auto()
        new_state, poured = self.game.apply_move(self.current_state, move)
        if poured == 0:
            self.feedback_var.set("No se pudo realizar el vertido.")
            self.selected_tube = None
            self._redraw_state()
            return
        self.current_state = new_state
        self.state_history.append(new_state)
        self.move_counter = len(self.state_history) - 1
        self.selected_tube = None
        self.solution_states = []
        self.solution_index = 0
        self.stats_var.set("")
        if self.game.is_goal_state(new_state):
            self.feedback_var.set("¡Puzzle resuelto manualmente!")
        else:
            self.feedback_var.set(f"Movimiento {move.src}->{move.dst} aplicado. Total: {self.move_counter}")
        self._redraw_state()

    def _tube_index_from_coord(self, x: int) -> Optional[int]:
        if not self.current_state:
            return None
        tube_count = len(self.current_state)
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        margin = 48
        available = max(1, width - margin * 2)
        gap = 22
        tube_width = max(50, min(90, (available - gap * (tube_count - 1)) / tube_count))
        for idx in range(tube_count):
            left = margin + idx * (tube_width + gap)
            right = left + tube_width
            if left <= x <= right:
                return idx
        return None

    def _redraw_state(self) -> None:
        self.canvas.delete("all")
        if not self.current_state:
            self._draw_placeholder()
            return
        tube_count = len(self.current_state)
        width = self.canvas.winfo_width() or self.canvas.winfo_reqwidth()
        height = self.canvas.winfo_height() or self.canvas.winfo_reqheight()
        margin_x = 48
        margin_y = 60
        available_width = max(1, width - margin_x * 2)
        available_height = max(1, height - margin_y * 2)
        gap = 22
        tube_width = max(58, min(110, (available_width - gap * (tube_count - 1)) / tube_count))
        tube_height = min(available_height, 420)
        base_y = height - margin_y
        lip_height = 14
        padding = 12

        for idx, tube in enumerate(self.current_state):
            left = margin_x + idx * (tube_width + gap)
            right = left + tube_width
            top = base_y - tube_height
            shadow_offset = 8
            self.canvas.create_rectangle(
                left + shadow_offset,
                top + shadow_offset,
                right + shadow_offset,
                base_y + shadow_offset,
                fill=TUBE_SHADOW,
                outline="",
            )
            outline_color = SELECTION_ACCENT if idx == self.selected_tube else TEXT_LIGHT
            outline_width = 3 if idx == self.selected_tube else 2
            self.canvas.create_rectangle(left, top, right, base_y, fill=TUBE_BODY, outline=outline_color, width=outline_width)
            self.canvas.create_rectangle(left, top - lip_height, right, top, fill=TUBE_BODY, outline=outline_color, width=outline_width)
            self.canvas.create_text((left + right) / 2, base_y + 24, text=str(idx), fill=TEXT_MUTED, font=("Segoe UI", 12, "bold"))

            segment_height = (tube_height - padding * 2) / self.game.capacity
            for level in range(self.game.capacity):
                slot_bottom = base_y - padding - level * segment_height
                slot_top = slot_bottom - segment_height + 4
                color_index = len(tube) - 1 - level
                if color_index < 0:
                    continue
                color_code = tube[color_index]
                fill_color = self._color_for(color_code)
                rect_left = left + 6
                rect_right = right - 6
                rect_top = slot_top
                rect_bottom = slot_bottom - 4
                if rect_top >= rect_bottom:
                    continue
                self.canvas.create_rectangle(
                    rect_left,
                    rect_top,
                    rect_right,
                    rect_bottom,
                    fill=fill_color,
                    outline="",
                )
                self.canvas.create_rectangle(
                    rect_left,
                    rect_top,
                    rect_right,
                    rect_top + 6,
                    fill=self._lighten(fill_color, 0.25),
                    outline="",
                )
                self.canvas.create_rectangle(
                    rect_left,
                    rect_top,
                    rect_right,
                    rect_bottom,
                    outline=self._lighten(fill_color, 0.6),
                    width=1,
                )

    def _draw_placeholder(self) -> None:
        self.canvas.create_text(
            self.canvas.winfo_width() / 2,
            self.canvas.winfo_height() / 2,
            text="Genera un puzzle para comenzar",
            fill=TEXT_MUTED,
            font=("Segoe UI", 20, "bold"),
        )

    def _color_for(self, code: str) -> str:
        if code in COLOR_PALETTE:
            return COLOR_PALETTE[code]
        seed = abs(hash(code))
        hue = (seed % 360) / 360
        return self._hsl_to_hex(hue, 0.65, 0.55)

    def _lighten(self, hex_color: str, amount: float) -> str:
        r, g, b = self._hex_to_rgb(hex_color)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _hex_to_rgb(self, hex_color: str) -> Sequence[int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in range(0, 6, 2))

    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1 / 3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1 / 3)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def _build_sequence(self, start: State, moves: Sequence[Move]) -> List[State]:
        sequence = [start]
        current = start
        for move in moves:
            current, _ = self.game.apply_move(current, move)
            sequence.append(current)
        return sequence

    def _on_close(self) -> None:
        self._cancel_auto()
        self.destroy()


def main() -> None:
    app = WaterSortApp()
    app.mainloop()


if __name__ == "__main__":
    main()
