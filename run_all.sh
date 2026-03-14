#!/usr/bin/env bash
set -e
python -m src.prepare_data
python -m src.tune_params --limit 10
python -m src.run_experiments --sets E F M P --out results --restarts 5 --adaptive-time
python -m src.analyze_results --summary results/summary.csv --out results/report.csv
