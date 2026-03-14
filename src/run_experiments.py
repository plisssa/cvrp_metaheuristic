from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

from .cvrp_parser import parse_vrplib, list_instances
from .tabu_solver import solve_cvrp_tabu, TabuParams

def deviation_pct(cost: float, best: int | None) -> float | None:
    if best is None:
        return None
    return (cost - best) / best * 100.0

def pick_time_limit(n: int, base: float, adaptive: bool, per_node: float, max_time: float) -> float:
    if not adaptive:
        return base
    return min(max_time, max(base, per_node * n))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=str, default='data/instances')
    p.add_argument('--sets', nargs='+', default=['E', 'F', 'M', 'P'])
    p.add_argument('--out', type=str, default='results')

    p.add_argument('--max-iters', type=int, default=6000)
    p.add_argument('--no-improve', type=int, default=1200)
    p.add_argument('--time-limit', type=float, default=10.0)
    p.add_argument('--tabu-tenure', type=int, default=30)
    p.add_argument('--neighbor-samples', type=int, default=900)
    p.add_argument('--w-2opt', type=float, default=0.15)

    p.add_argument('--restarts', type=int, default=1, help='Сколько перезапусков (разных seed) делать для каждой задачи')
    p.add_argument('--hard-n-threshold', type=int, default=150, help='Перезапуски/усиление применять для n >= threshold')
    p.add_argument('--hard-sets', nargs='*', default=['M'], help='Наборы, где включать усиление независимо от n')

    p.add_argument('--adaptive-time', action='store_true', help='Включить time_limit = max(base, per_node*n) с ограничением max_time')
    p.add_argument('--time-per-node', type=float, default=0.12, help='Секунд на вершину при adaptive-time (например 0.12)')
    p.add_argument('--max-time', type=float, default=25.0, help='Максимальный time_limit при adaptive-time')

    p.add_argument('--seed', type=int, default=0, help='Базовый seed. Для перезапусков будет seed+i')

    args = p.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = list_instances(root, args.sets)
    if not paths:
        raise SystemExit('Не найдено .vrp. Сначала распакуйте: python -m src.prepare_data')

    base_params = TabuParams(
        max_iters=args.max_iters,
        no_improve=args.no_improve,
        time_limit=args.time_limit,
        tabu_tenure=args.tabu_tenure,
        neighbor_samples=args.neighbor_samples,
        w_2opt=args.w_2opt,
    )

    rows = []
    for path in tqdm(paths, desc='instances'):
        inst = parse_vrplib(path)

        try:
            set_name = path.relative_to(root).parts[0]
        except Exception:
            set_name = '?'

        is_hard = (inst.dimension >= args.hard_n_threshold) or (set_name in set(args.hard_sets))
        restarts = args.restarts if is_hard else 1

        tl = pick_time_limit(inst.dimension, args.time_limit, args.adaptive_time and is_hard, args.time_per_node, args.max_time)
        params = TabuParams(
            max_iters=base_params.max_iters,
            no_improve=base_params.no_improve,
            time_limit=tl,
            tabu_tenure=base_params.tabu_tenure,
            neighbor_samples=base_params.neighbor_samples,
            w_2opt=base_params.w_2opt,
        )

        best_cost = float('inf')
        best_runtime = None
        best_iters = None
        best_seed = None
        best_routes = None
        total_runtime = 0.0

        for i in range(restarts):
            sd = args.seed + i
            res = solve_cvrp_tabu(
                inst.coords, inst.demands, inst.capacity, inst.depot,
                params=params, seed=sd, dist_matrix=inst.dist_matrix
            )
            total_runtime += res.runtime
            if res.best_cost < best_cost:
                best_cost = res.best_cost
                best_runtime = res.runtime
                best_iters = res.iters
                best_seed = sd
                best_routes = res.best_routes

        rows.append({
            'set': set_name,
            'instance': inst.name,
            'n': inst.dimension,
            'capacity': inst.capacity,
            'best_known': inst.best_known,
            'cost': best_cost,
            'dev_pct': deviation_pct(best_cost, inst.best_known),
            'runtime_s': float(best_runtime if best_runtime is not None else total_runtime),
            'runtime_total_s': float(total_runtime),
            'iters': int(best_iters if best_iters is not None else 0),
            'routes': int(len(best_routes) if best_routes is not None else 0),
            'restarts_used': int(restarts),
            'best_seed': int(best_seed if best_seed is not None else args.seed),
            'time_limit_used': float(tl),
            'path': str(path),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / 'summary.csv', index=False)

    agg = df.groupby('set').agg(
        instances=('instance','count'),
        n_mean=('n','mean'),
        time_mean=('runtime_s','mean'),
        time_total_mean=('runtime_total_s','mean'),
        dev_mean=('dev_pct','mean'),
        dev_median=('dev_pct','median'),
        dev_max=('dev_pct','max'),
    ).reset_index()
    agg.to_csv(out_dir / 'by_set.csv', index=False)

    if df['dev_pct'].notna().any():
        fig = plt.figure()
        for s in sorted(df['set'].unique()):
            sub = df[df['set'] == s]
            plt.scatter(sub['n'], sub['dev_pct'], label=s)
        plt.xlabel('Размерность (n)')
        plt.ylabel('Отклонение от best known, %')
        plt.title('Качество решения vs размерность')
        plt.legend()
        fig.savefig(out_dir / 'plots_quality_vs_n.png', dpi=200, bbox_inches='tight')
        plt.close(fig)

    fig = plt.figure()
    for s in sorted(df['set'].unique()):
        sub = df[df['set'] == s]
        plt.scatter(sub['n'], sub['runtime_s'], label=s)
    plt.xlabel('Размерность (n)')
    plt.ylabel('Время, сек')
    plt.title('Скорость vs размерность')
    plt.legend()
    fig.savefig(out_dir / 'plots_time_vs_n.png', dpi=200, bbox_inches='tight')
    plt.close(fig)

    print(f"Сохранено: {out_dir/'summary.csv'} и {out_dir/'by_set.csv'}")

    if df['dev_pct'].notna().any():
        max_dev = float(df['dev_pct'].max())
        print(f"Худшее отклонение: {max_dev:.2f}%")
        if max_dev <= 10:
            print('Диапазон для оценки 8-10 (<=10%).')
        elif max_dev <= 15:
            print('Диапазон для оценки 6-7 (<=15%).')
        elif max_dev <= 20:
            print('Диапазон для оценки <=5 (<=20%).')
        elif max_dev <= 25:
            print('Диапазон для оценки <=4 (<=25%).')
        else:
            print('Отклонение >25% — увеличьте время/итерации и повторите.')

if __name__ == '__main__':
    main()

