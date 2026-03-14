from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

def band(dev: float) -> str:
    if dev <= 10: return "8-10 (<=10%)"
    if dev <= 15: return "6-7 (<=15%)"
    if dev <= 20: return "<=5 (<=20%)"
    if dev <= 25: return "<=4 (<=25%)"
    return ">25% (fail)"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=str, default="results/summary.csv")
    p.add_argument("--out", type=str, default="results/report.csv")
    args = p.parse_args()

    df = pd.read_csv(args.summary)
    if "dev_pct" not in df.columns:
        raise SystemExit("summary.csv не содержит dev_pct, сначала запустить run_experiments новой версии.")

    df["band"] = df["dev_pct"].apply(lambda x: band(x) if pd.notna(x) else "no best_known")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    print("Общая статистика")
    print(df[["dev_pct","runtime_s","n"]].describe().to_string())

    print("\nРаспределение по диапазонам")
    print(df["band"].value_counts(dropna=False).to_string())

    print("\nПо наборам (E/F/M/P)")
    by = df.groupby("set").agg(
        instances=("instance","count"),
        dev_mean=("dev_pct","mean"),
        dev_median=("dev_pct","median"),
        dev_max=("dev_pct","max"),
        time_mean=("runtime_s","mean"),
        time_max=("runtime_s","max"),
        n_mean=("n","mean"),
    ).reset_index()
    print(by.to_string(index=False))

    worst = df.sort_values("dev_pct", ascending=False).head(10)
    print("\n10 худших по отклонению")
    print(worst[["set","instance","n","best_known","cost","dev_pct","runtime_s"]].to_string(index=False))

    best = df.sort_values("dev_pct", ascending=True).head(10)
    print("\n10 лучших по отклонению")
    print(best[["set","instance","n","best_known","cost","dev_pct","runtime_s"]].to_string(index=False))

    print(f"\nСохранено: {out}")

if __name__ == "__main__":
    main()
