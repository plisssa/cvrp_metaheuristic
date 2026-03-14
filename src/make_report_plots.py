from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)


def _save_fig(fig, path: Path) -> None:
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _safe_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        raise ValueError(f"В summary.csv нет столбца '{col}'")
    return df[col]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=str, default="results/summary.csv", help="Путь к summary.csv")
    p.add_argument("--out-dir", type=str, default="results/figures", help="Папка для графиков")
    p.add_argument("--title-prefix", type=str, default="CVRP Tabu Search", help="Префикс заголовков графиков")
    p.add_argument("--max-dev-line", type=float, default=10.0, help="Линия порога по отклонению (например 10%)")
    args = p.parse_args()

    summary_path = Path(args.summary)
    out_dir = Path(args.out_dir)
    _ensure_out_dir(out_dir)

    df = pd.read_csv(summary_path)

    # базовые проверки
    for col in ["set", "instance", "n", "runtime_s", "cost", "best_known", "dev_pct"]:
        if col not in df.columns:
            raise SystemExit(f"summary.csv не содержит '{col}'. Проверь, что ты запускала run_experiments (v3/v4).")

    # сортировки удобные для графиков
    df = df.sort_values(["set", "n", "instance"]).reset_index(drop=True)

    # Качество vs размерность
    fig = plt.figure()
    for s in sorted(df["set"].unique()):
        sub = df[df["set"] == s]
        plt.scatter(sub["n"], sub["dev_pct"], label=s)
    plt.axhline(args.max_dev_line, linewidth=1.5)  # порог 10%
    plt.xlabel("Размерность задачи, n")
    plt.ylabel("Отклонение от best known, %")
    plt.title(f"{args.title_prefix}: качество решения vs размерность (порог {args.max_dev_line:.0f}%)")
    plt.legend(title="Набор")
    _save_fig(fig, out_dir / "01_quality_vs_n.png")

    # Время vs размерность
    fig = plt.figure()
    for s in sorted(df["set"].unique()):
        sub = df[df["set"] == s]
        plt.scatter(sub["n"], sub["runtime_s"], label=s)
    plt.xlabel("Размерность задачи, n")
    plt.ylabel("Время работы, сек")
    plt.title(f"{args.title_prefix}: скорость получения решения vs размерность")
    plt.legend(title="Набор")
    _save_fig(fig, out_dir / "02_time_vs_n.png")

    # Boxplot отклонений по наборам
    fig = plt.figure()
    sets = sorted(df["set"].unique())
    data = [df[df["set"] == s]["dev_pct"].values for s in sets]
    plt.boxplot(data, labels=sets, showmeans=True)
    plt.axhline(args.max_dev_line, linewidth=1.5)
    plt.xlabel("Набор задач")
    plt.ylabel("Отклонение от best known, %")
    plt.title(f"{args.title_prefix}: распределение качества по наборам")
    _save_fig(fig, out_dir / "03_box_dev_by_set.png")

    # Boxplot времени по наборам
    fig = plt.figure()
    data = [df[df["set"] == s]["runtime_s"].values for s in sets]
    plt.boxplot(data, labels=sets, showmeans=True)
    plt.xlabel("Набор задач")
    plt.ylabel("Время работы, сек")
    plt.title(f"{args.title_prefix}: распределение времени по наборам")
    _save_fig(fig, out_dir / "04_box_time_by_set.png")

    # Средние значения по наборам (bar chart)
    by = df.groupby("set").agg(
        instances=("instance", "count"),
        n_mean=("n", "mean"),
        dev_mean=("dev_pct", "mean"),
        dev_median=("dev_pct", "median"),
        dev_max=("dev_pct", "max"),
        time_mean=("runtime_s", "mean"),
        time_max=("runtime_s", "max"),
    ).reset_index().sort_values("set")

    # сохраняем табличку для отчёта
    by.to_csv(out_dir / "by_set_for_report.csv", index=False)

    fig = plt.figure()
    plt.bar(by["set"], by["dev_mean"])
    plt.axhline(args.max_dev_line, linewidth=1.5)
    plt.xlabel("Набор задач")
    plt.ylabel("Среднее отклонение, %")
    plt.title(f"{args.title_prefix}: среднее отклонение по наборам")
    _save_fig(fig, out_dir / "05_bar_mean_dev_by_set.png")

    fig = plt.figure()
    plt.bar(by["set"], by["time_mean"])
    plt.xlabel("Набор задач")
    plt.ylabel("Среднее время, сек")
    plt.title(f"{args.title_prefix}: среднее время по наборам")
    _save_fig(fig, out_dir / "06_bar_mean_time_by_set.png")

    # Качество vs время (trade-off)
    fig = plt.figure()
    for s in sorted(df["set"].unique()):
        sub = df[df["set"] == s]
        plt.scatter(sub["runtime_s"], sub["dev_pct"], label=s)
    plt.axhline(args.max_dev_line, linewidth=1.5)
    plt.xlabel("Время работы, сек")
    plt.ylabel("Отклонение от best known, %")
    plt.title(f"{args.title_prefix}: компромисс качество/время")
    plt.legend(title="Набор")
    _save_fig(fig, out_dir / "07_tradeoff_time_vs_dev.png")

    # Топ худших/лучших (таблицы)
    worst = df.sort_values("dev_pct", ascending=False).head(10)
    best = df.sort_values("dev_pct", ascending=True).head(10)

    worst.to_csv(out_dir / "worst_10.csv", index=False)
    best.to_csv(out_dir / "best_10.csv", index=False)

    print(f"Графики сохранены в: {out_dir}")
    print(f"Таблицы: {out_dir/'by_set_for_report.csv'}, {out_dir/'worst_10.csv'}, {out_dir/'best_10.csv'}")


if __name__ == "__main__":
    main()
