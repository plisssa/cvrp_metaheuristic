from __future__ import annotations
from typing import List, Tuple, Optional
import math, random

def euclid(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])

def build_distance_matrix(coords: List[Tuple[float, float]]) -> List[List[float]]:
    n = len(coords)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = euclid(coords[i], coords[j])
            dist[i][j] = d
            dist[j][i] = d
    return dist

def route_cost(route: List[int], dist: List[List[float]], depot: int) -> float:
    if not route:
        return 0.0
    c = dist[depot][route[0]]
    for k in range(len(route) - 1):
        c += dist[route[k]][route[k + 1]]
    c += dist[route[-1]][depot]
    return c

def solution_cost(routes: List[List[int]], dist: List[List[float]], depot: int) -> float:
    return sum(route_cost(r, dist, depot) for r in routes)

def feasible_route(route: List[int], demands: List[int], cap: int) -> bool:
    return sum(demands[i] for i in route) <= cap

def seed_everything(seed: int) -> None:
    random.seed(seed)
