"""Script automatizado para ejecutar casos de prueba del Water Sort Puzzle Solver."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from watersort.game import WaterSortGame
from watersort.search import SearchAlgorithms
from watersort.heuristics import available_heuristics


def run_single_test(
    algorithm: str,
    heuristic: str | None,
    tubes: int,
    colors: int,
    seed: int,
    scramble: int,
    timeout_seconds: int = 30
) -> Dict:
    """Ejecuta un único caso de prueba con timeout."""
    
    import signal
    
    class TimeoutException(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutException("Test excedió el tiempo límite")
    
    game = WaterSortGame(tubes, colors, seed=seed)
    initial_state = game.generate_initial_state(scramble_moves=scramble)
    algorithms = SearchAlgorithms(game)
    heuristics_dict = available_heuristics(game)
    
    # Configurar timeout (solo en sistemas Unix-like)
    # En Windows, simplemente ejecutamos sin timeout
    use_timeout = hasattr(signal, 'SIGALRM')
    
    try:
        if use_timeout:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        # Ejecutar algoritmo correspondiente
        if algorithm == "bfs":
            result = algorithms.bfs(initial_state)
        elif algorithm == "dfs":
            result = algorithms.dfs(initial_state, depth_limit=100)
        elif algorithm == "astar":
            if heuristic is None:
                heuristic = "entropy"
            heur_func = heuristics_dict[heuristic]
            result = algorithms.a_star(initial_state, heur_func)
        elif algorithm == "ida":
            if heuristic is None:
                heuristic = "entropy"
            heur_func = heuristics_dict[heuristic]
            result = algorithms.ida_star(initial_state, heur_func, max_depth=200)
        else:
            raise ValueError(f"Algoritmo desconocido: {algorithm}")
        
        if use_timeout:
            signal.alarm(0)  # Cancelar alarma
        
        return {
            "algorithm": algorithm,
            "heuristic": heuristic if heuristic else "N/A",
            "tubes": tubes,
            "colors": colors,
            "seed": seed,
            "scramble": scramble,
            "success": result.success,
            "moves": result.depth,
            "explored_nodes": result.explored_nodes,
            "expanded_nodes": result.expanded_nodes,
            "max_frontier": result.max_frontier_size,
            "time_seconds": round(result.time_seconds, 4)
        }
    
    except (TimeoutException, KeyboardInterrupt):
        if use_timeout:
            signal.alarm(0)
        raise
    except Exception as e:
        if use_timeout:
            signal.alarm(0)
        raise


def run_all_test_cases() -> List[Dict]:
    """Ejecuta todos los casos de prueba definidos."""
    
    all_results = []
      # Definir casos de prueba
    # RESTRICCIONES: 5 <= tubos <= 12, 3 <= colores <= tubos-2
    test_cases = [
        # Caso 1: Configuración mínima (5 tubos, 3 colores) - BASELINE
        # Prueba todos los algoritmos y heurísticas en el caso más simple
        {
            "name": "Configuración Mínima",
            "configs": [
                ("bfs", None, 5, 3, 42, 30),
                ("dfs", None, 5, 3, 42, 30),
                ("astar", "entropy", 5, 3, 42, 30),
                ("astar", "completion", 5, 3, 42, 30),
                ("astar", "blocking", 5, 3, 42, 30),
                ("ida", "entropy", 5, 3, 42, 30),
                ("ida", "completion", 5, 3, 42, 30),
                ("ida", "blocking", 5, 3, 42, 30),
            ]
        },
        
        # Caso 2: Configuración estándar (8 tubos, 6 colores) - REFERENCIA
        # Configuración típica para comparar todos los algoritmos
        {
            "name": "Configuración Estándar",
            "configs": [
                ("bfs", None, 8, 6, 100, 60),
                ("dfs", None, 8, 6, 100, 60),
                ("astar", "entropy", 8, 6, 100, 60),
                ("astar", "completion", 8, 6, 100, 60),
                ("astar", "blocking", 8, 6, 100, 60),
                ("ida", "entropy", 8, 6, 100, 60),
                ("ida", "completion", 8, 6, 100, 60),
                ("ida", "blocking", 8, 6, 100, 60),
            ]
        },
        
        # Caso 3: Escalabilidad Progresiva con A* (mismo algoritmo, complejidad creciente)
        # Evalúa cómo escala el rendimiento al aumentar tubos y colores
        {
            "name": "Escalabilidad A* con Blocking",
            "configs": [
                ("astar", "blocking", 5, 3, 500, 30),    # Mínimo: 5T, 3C
                ("astar", "blocking", 6, 4, 500, 40),    # +1T, +1C
                ("astar", "blocking", 7, 5, 500, 50),    # +1T, +1C
                ("astar", "blocking", 8, 6, 500, 60),    # +1T, +1C
                ("astar", "blocking", 9, 7, 500, 70),    # +1T, +1C
                ("astar", "blocking", 10, 8, 500, 80),   # +1T, +1C
                ("astar", "blocking", 11, 9, 500, 90),   # +1T, +1C
                ("astar", "blocking", 12, 10, 500, 100), # Máximo: 12T, 10C
            ]
        },
        
        # Caso 4: Escalabilidad Progresiva con IDA* (comparar memoria vs A*)
        {
            "name": "Escalabilidad IDA* con Entropy",
            "configs": [
                ("ida", "entropy", 5, 3, 500, 30),
                ("ida", "entropy", 7, 5, 500, 50),
                ("ida", "entropy", 9, 7, 500, 70),
                ("ida", "entropy", 11, 9, 500, 90),
            ]
        },
        
        # Caso 5: Comparación de Heurísticas en Puzzle Medio (9 tubos, 7 colores)
        # Mismo puzzle, diferentes heurísticas para A* e IDA*
        {
            "name": "Comparación Heurísticas (Puzzle Medio)",
            "configs": [
                ("astar", "entropy", 9, 7, 999, 80),
                ("astar", "completion", 9, 7, 999, 80),
                ("astar", "blocking", 9, 7, 999, 80),
                ("ida", "entropy", 9, 7, 999, 80),
                ("ida", "completion", 9, 7, 999, 80),
                ("ida", "blocking", 9, 7, 999, 80),
            ]        },
        
        # Caso 6: Comparación de Heurísticas en Puzzle Complejo (11 tubos, 9 colores)
        # Solo A* para evitar que IDA* completion tarde demasiado
        {
            "name": "Comparación Heurísticas (Puzzle Difícil)",
            "configs": [
                ("astar", "entropy", 11, 9, 777, 100),
                ("astar", "completion", 11, 9, 777, 100),
                ("astar", "blocking", 11, 9, 777, 100),
                ("ida", "entropy", 11, 9, 777, 100),
                ("ida", "entropy", 11, 9, 777, 100),
                ("ida", "completion", 11, 9, 777, 100),
                ("ida", "blocking", 11, 9, 777, 100),
            ]
        },
        
        # Caso 7: Robustez con Distintas Semillas (7 tubos, 5 colores)
        # Mismo algoritmo/configuración, 5 semillas diferentes
        {
            "name": "Robustez: A* Blocking (7T/5C)",
            "configs": [
                ("astar", "blocking", 7, 5, 42, 60),
                ("astar", "blocking", 7, 5, 123, 60),
                ("astar", "blocking", 7, 5, 256, 60),
                ("astar", "blocking", 7, 5, 789, 60),
                ("astar", "blocking", 7, 5, 999, 60),
            ]
        },
        
        # Caso 8: Robustez con Distintas Semillas para IDA*
        {
            "name": "Robustez: IDA* Entropy (8T/6C)",
            "configs": [
                ("ida", "entropy", 8, 6, 42, 60),
                ("ida", "entropy", 8, 6, 100, 60),
                ("ida", "entropy", 8, 6, 333, 60),
                ("ida", "entropy", 8, 6, 666, 60),
                ("ida", "entropy", 8, 6, 999, 60),
            ]
        },
        
        # Caso 9: Casos Extremos
        {
            "name": "Casos Extremos",
            "configs": [
                # Configuración máxima
                ("astar", "blocking", 12, 10, 1234, 120),
                ("ida", "blocking", 12, 10, 1234, 120),
                
                # Pocos tubos, máximo colores permitido
                ("astar", "entropy", 6, 4, 321, 50),   # 6-2=4 colores máximo
                ("ida", "entropy", 6, 4, 321, 50),
                
                # Muchos tubos, pocos colores (muchos vacíos)
                ("astar", "blocking", 10, 3, 555, 40),
                ("ida", "blocking", 10, 3, 555, 40),
            ]
        },
    ]
      # Ejecutar cada caso
    for idx, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"[{idx}/{len(test_cases)}] {test_case['name']}")
        print(f"{'='*70}")
        
        for config_idx, (algo, heur, tubes, colors, seed, scramble) in enumerate(test_case['configs'], 1):
            heur_str = f" ({heur})" if heur else ""
            print(f"  [{config_idx}/{len(test_case['configs'])}] {algo.upper()}{heur_str} - {tubes}T/{colors}C/seed={seed}...", end=" ", flush=True)
            
            try:
                result = run_single_test(algo, heur, tubes, colors, seed, scramble)
                result["test_case"] = test_case["name"]
                all_results.append(result)
                
                status = "✅" if result["success"] else "❌"
                print(f"{status} ({result['moves']} movs, {result['explored_nodes']} nodos, {result['time_seconds']}s)")
                
            except KeyboardInterrupt:
                print("⏭️  CANCELADO (tardando demasiado, continuando...)")
                all_results.append({
                    "test_case": test_case["name"],
                    "algorithm": algo,
                    "heuristic": heur if heur else "N/A",
                    "tubes": tubes,
                    "colors": colors,
                    "seed": seed,
                    "scramble": scramble,
                    "success": False,
                    "moves": 0,
                    "explored_nodes": 0,
                    "expanded_nodes": 0,
                    "max_frontier": 0,
                    "time_seconds": 0,
                    "error": "Timeout o cancelado manualmente"
                })
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)[:50]}")
                all_results.append({
                    "test_case": test_case["name"],
                    "algorithm": algo,
                    "heuristic": heur if heur else "N/A",
                    "tubes": tubes,
                    "colors": colors,
                    "seed": seed,
                    "scramble": scramble,
                    "success": False,
                    "moves": 0,
                    "explored_nodes": 0,
                    "expanded_nodes": 0,
                    "max_frontier": 0,
                    "time_seconds": 0,
                    "error": str(e)
                })
    
    return all_results


def save_results_csv(results: List[Dict], output_path: Path):
    """Guarda resultados en formato CSV."""
    
    if not results:
        print("⚠️  No hay resultados para guardar")
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'test_case', 'algorithm', 'heuristic', 'tubes', 'colors', 
            'seed', 'scramble', 'success', 'moves', 'explored_nodes',
            'expanded_nodes', 'max_frontier', 'time_seconds'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✅ CSV guardado: {output_path}")


def save_results_json(results: List[Dict], output_path: Path):
    """Guarda resultados en formato JSON."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON guardado: {output_path}")


def generate_markdown_report(results: List[Dict], output_path: Path):
    """Genera reporte en formato Markdown."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Resultados de Casos de Prueba - Water Sort Puzzle Solver\n\n")
        f.write(f"**Fecha de ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total de casos ejecutados:** {len(results)}\n")
        
        successful = sum(1 for r in results if r['success'])
        f.write(f"**Casos exitosos:** {successful}/{len(results)}\n\n")
        
        # Agrupar por test_case
        by_test_case = {}
        for r in results:
            test_name = r.get('test_case', 'Sin categoría')
            if test_name not in by_test_case:
                by_test_case[test_name] = []
            by_test_case[test_name].append(r)
        
        # Generar tablas por cada caso de prueba
        for test_name, test_results in by_test_case.items():
            f.write(f"## {test_name}\n\n")
            
            # Tabla de resultados
            f.write("| Algoritmo | Heurística | Tubos | Colores | Semilla | Éxito | Movs | Nodos Expl. | Nodos Exp. | Frontera | Tiempo (s) |\n")
            f.write("|-----------|------------|-------|---------|---------|-------|------|-------------|------------|----------|------------|\n")
            
            for r in test_results:
                algo = r['algorithm'].upper()
                heur = r['heuristic']
                success_icon = "✅" if r['success'] else "❌"
                moves = r['moves'] if r['success'] else "—"
                
                f.write(f"| {algo} | {heur} | {r['tubes']} | {r['colors']} | {r['seed']} | "
                       f"{success_icon} | {moves} | {r['explored_nodes']} | {r['expanded_nodes']} | "
                       f"{r['max_frontier']} | {r['time_seconds']} |\n")
            
            f.write("\n")
        
        # Análisis comparativo
        f.write("## Análisis Comparativo\n\n")
        
        # Mejor por eficiencia (menos nodos)
        successful_results = [r for r in results if r['success']]
        if successful_results:
            best_efficiency = min(successful_results, key=lambda x: x['explored_nodes'])
            f.write(f"### 🏆 Más Eficiente (menos nodos explorados)\n\n")
            f.write(f"- **Algoritmo:** {best_efficiency['algorithm'].upper()}\n")
            if best_efficiency['heuristic'] != "N/A":
                f.write(f"- **Heurística:** {best_efficiency['heuristic']}\n")
            f.write(f"- **Configuración:** {best_efficiency['tubes']} tubos, {best_efficiency['colors']} colores\n")
            f.write(f"- **Nodos explorados:** {best_efficiency['explored_nodes']}\n")
            f.write(f"- **Tiempo:** {best_efficiency['time_seconds']}s\n\n")
            
            # Más rápido
            fastest = min(successful_results, key=lambda x: x['time_seconds'])
            f.write(f"### ⚡ Más Rápido\n\n")
            f.write(f"- **Algoritmo:** {fastest['algorithm'].upper()}\n")
            if fastest['heuristic'] != "N/A":
                f.write(f"- **Heurística:** {fastest['heuristic']}\n")
            f.write(f"- **Configuración:** {fastest['tubes']} tubos, {fastest['colors']} colores\n")
            f.write(f"- **Tiempo:** {fastest['time_seconds']}s\n")
            f.write(f"- **Nodos explorados:** {fastest['explored_nodes']}\n\n")
            
            # Solución más corta
            shortest_solution = min(successful_results, key=lambda x: x['moves'])
            f.write(f"### 🎯 Solución Más Corta\n\n")
            f.write(f"- **Algoritmo:** {shortest_solution['algorithm'].upper()}\n")
            if shortest_solution['heuristic'] != "N/A":
                f.write(f"- **Heurística:** {shortest_solution['heuristic']}\n")
            f.write(f"- **Configuración:** {shortest_solution['tubes']} tubos, {shortest_solution['colors']} colores\n")
            f.write(f"- **Movimientos:** {shortest_solution['moves']}\n")
            f.write(f"- **Nodos explorados:** {shortest_solution['explored_nodes']}\n\n")
    
    print(f"✅ Reporte Markdown guardado: {output_path}")


def main():
    """Función principal."""
    
    print("="*70)
    print("  SCRIPT DE CASOS DE PRUEBA - WATER SORT PUZZLE SOLVER")
    print("="*70)
    
    # Crear directorio de resultados
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Directorio de resultados: {output_dir.absolute()}\n")
    
    # Ejecutar casos de prueba
    results = run_all_test_cases()
    
    # Guardar resultados
    print(f"\n{'='*70}")
    print("Guardando resultados...")
    print(f"{'='*70}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_path = output_dir / f"results_{timestamp}.csv"
    save_results_csv(results, csv_path)
    
    json_path = output_dir / f"results_{timestamp}.json"
    save_results_json(results, json_path)
    
    report_path = output_dir / f"report_{timestamp}.md"
    generate_markdown_report(results, report_path)
    
    # Resumen final
    print(f"\n{'='*70}")
    print("📊 RESUMEN FINAL")
    print(f"{'='*70}")
    print(f"Total de casos ejecutados: {len(results)}")
    successful = sum(1 for r in results if r['success'])
    print(f"Casos exitosos: {successful}/{len(results)}")
    print(f"Tasa de éxito: {successful/len(results)*100:.1f}%")
    
    if successful > 0:
        avg_time = sum(r['time_seconds'] for r in results if r['success']) / successful
        avg_nodes = sum(r['explored_nodes'] for r in results if r['success']) / successful
        print(f"Tiempo promedio: {avg_time:.4f}s")
        print(f"Nodos promedio: {avg_nodes:.0f}")
    
    print(f"\n✅ Todos los resultados guardados en: {output_dir.absolute()}")
    print("="*70)


if __name__ == "__main__":
    main()
