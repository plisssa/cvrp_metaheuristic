# CVRP Metaheuristic Project (Tabu Search)

Проект решает задачу маршрутизации транспорта с ограничениями грузоподъёмности (**CVRP**) с помощью **метаэвристики Tabu Search** (поиск с запретами) и конструктивной инициализации **Clarke–Wright Savings**.

## Структура проекта

* `src/cvrp_parser.py` — парсер CVRPLIB `.vrp` + извлечение best-known из `.sol` (если есть рядом)
* `src/sol_parser.py` — извлечение стоимости из `.sol`
* `src/constructive.py` — начальное решение (Clarke–Wright Savings)
* `src/tabu_solver.py` — Tabu Search (relocate + swap + 2-opt)
* `src/tune_params.py` — подбор параметров (grid search)
* `src/run_experiments.py` — эксперименты на наборах E/F/M/P + поддержка multi-start и adaptive-time
* `src/analyze_results.py` — сводный анализ: статистика, диапазоны отклонения, топ худших/лучших
* `src/make_report_plots.py` — генерация **графиков для отчёта/презентации** (png + csv)
* `src/prepare_data.py` — распаковка `data/raw/*.7z` в `data/instances/`

## Данные (для вычислительных экспериментов на тестовых задачах)

Архивы `E.7z`, `F.7z`, `M.7z`, `P.7z` лежат в `data/raw/`.
Источник: http://vrp.atd-lab.inf.puc-rio.br/index.php/en/

### Авто-распаковка

```bash
pip install -r requirements.txt
python -m src.prepare_data
```

Если распаковка не работает — распакуйте вручную так, чтобы получилось:

```
data/instances/E/*.vrp + *.sol
data/instances/F/*.vrp + *.sol
data/instances/M/*.vrp + *.sol
data/instances/P/*.vrp + *.sol
```

> Важно: для корректного расчёта отклонений от best-known файлы `.sol` должны лежать рядом с соответствующими `.vrp`.

## Подбор параметров

Подбор параметров делается grid search на подмножестве задач:

```bash
python -m src.tune_params --limit 10
```

Результат сохраняется в `results/tuning.csv`.

## Финальный запуск экспериментов (рекомендуемый)

Это режим, который дал лучшие финальные результаты (все задачи ≤ 10%):

* multi-start включается для сложных задач (по умолчанию набор **M** или `n>=150`)
* adaptive-time увеличивает лимит времени для крупных задач (с ограничением сверху)

```bash
python -m src.run_experiments --sets E F M P --out results --restarts 10 --adaptive-time --max-time 35
```

Результаты сохраняются в:

* `results/summary.csv` — все инстансы (стоимость, время, best_known, dev%, и т.д.)
* `results/by_set.csv` — агрегаты по наборам E/F/M/P
* `results/plots_quality_vs_n.png` — качество vs размерность
* `results/plots_time_vs_n.png` — скорость vs размерность

## Критерии остановки

Используются комбинированные критерии остановки:

* `max_iters`
* `no_improve`
* `time_limit` (сек)

В режиме `--adaptive-time` для сложных задач лимит времени масштабируется с размерностью (с верхней границей `--max-time`).

## Отклонение от оптимума / best-known

Отклонение считается по формуле:
[
dev% = \frac{cost - bestKnown}{bestKnown}\cdot 100%
]

Источник best-known:

1. если в `.vrp` в `COMMENT` есть best/optimal value — он извлекается автоматически;
2. иначе берётся стоимость из соседнего файла `.sol` (если он есть).

## Анализ результатов (диапазоны оценок)

После `run_experiments`:

```bash
python -m src.analyze_results --summary results/summary.csv --out results/report.csv
```

Скрипт выводит:

* общую статистику по отклонению и времени,
* распределение по диапазонам (<=10%, <=15%, …),
* топ-10 лучших/худших инстансов.

## Графики

После финального прогона можно сгенерировать полный набор графиков и файлов:

```bash
python -m src.make_report_plots --summary results/summary.csv --out-dir results/figures --title-prefix "CVRP Tabu Search (multi-start, restarts=10)"
```

Будут созданы:

* `results/figures/01_quality_vs_n.png` — качество vs размерность (с порогом 10%)
* `results/figures/02_time_vs_n.png` — время vs размерность
* `results/figures/03_box_dev_by_set.png` — boxplot качества по наборам
* `results/figures/04_box_time_by_set.png` — boxplot времени по наборам
* `results/figures/05_bar_mean_dev_by_set.png` — среднее отклонение по наборам
* `results/figures/06_bar_mean_time_by_set.png` — среднее время по наборам
* `results/figures/07_tradeoff_time_vs_dev.png` — компромисс качество/время

И вспомогательные файлы:

* `results/figures/by_set_for_report.csv`
* `results/figures/worst_10.csv`
* `results/figures/best_10.csv`
# cvrp_metaheuristic
