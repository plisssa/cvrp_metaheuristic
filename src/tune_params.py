from __future__ import annotations
import argparse
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from tqdm import tqdm

from .cvrp_parser import parse_vrplib, list_instances
from .tabu_solver import solve_cvrp_tabu, TabuParams

def deviation_pct(cost: float, best: int | None) -> float | None:
    if best is None:
        return None
    return (cost - best) / best * 100.0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=str, default="data/instances")
    p.add_argument("--sets", nargs="+", default=["E", "F", "M", "P"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--out", type=str, default="results/tuning.csv")
    args = p.parse_args()

    inst_paths = list_instances(Path(args.root), args.sets)
    if not inst_paths:
        raise SystemExit("Не найдено .vrp. Сначала распакуйте: python -m src.prepare_data")

    inst_paths = inst_paths[: args.limit]

    grid = []
    for tenure in [10, 20, 30, 45]:
        for ns in [250, 500, 900]:
            for max_iters in [3000, 6000]:
                grid.append(TabuParams(max_iters=max_iters, no_improve=max_iters//5, time_limit=10.0, tabu_tenure=tenure, neighbor_samples=ns))

    rows = []
    for params in tqdm(grid, desc="grid"):
        devs = []
        times = []
        for path in inst_paths:
            inst = parse_vrplib(path)
            res = solve_cvrp_tabu(inst.coords, inst.demands, inst.capacity, inst.depot, params=params, seed=0, dist_matrix=inst.dist_matrix)
            d = deviation_pct(res.best_cost, inst.best_known)
            if d is not None:
                devs.append(d)
            times.append(res.runtime)
        row = asdict(params)
        row["mean_dev_pct"] = sum(devs)/len(devs) if devs else None
        row["mean_time_s"] = sum(times)/len(times) if times else None
        rows.append(row)

    df = pd.DataFrame(rows).sort_values(["mean_dev_pct", "mean_time_s"], na_position="last")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Сохранено: {out}")
    print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
