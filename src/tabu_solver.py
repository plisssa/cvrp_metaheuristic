from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import random, time

from .utils import solution_cost, feasible_route, build_distance_matrix
from .constructive import clarke_wright_savings

@dataclass
class TabuParams:
    max_iters: int = 6000
    no_improve: int = 1200
    time_limit: float = 12.0
    tabu_tenure: int = 30
    neighbor_samples: int = 600
    w_2opt: float = 0.15

@dataclass
class TabuResult:
    best_routes: List[List[int]]
    best_cost: float
    iters: int
    runtime: float

def _random_2opt_indices(m: int) -> Optional[Tuple[int, int]]:
    if m < 4:
        return None
    i = random.randint(0, m - 3)
    j = random.randint(i + 2, m - 1)
    return i, j

def _apply_2opt(route: List[int], i: int, j: int) -> List[int]:
    return route[:i] + list(reversed(route[i:j+1])) + route[j+1:]

def solve_cvrp_tabu(
    coords: List[Tuple[float, float]],
    demands: List[int],
    capacity: int,
    depot: int,
    params: TabuParams,
    seed: int = 0,
    dist_matrix: Optional[List[List[float]]] = None,
) -> TabuResult:
    random.seed(seed)
    dist = dist_matrix if dist_matrix is not None else build_distance_matrix(coords)

    routes = clarke_wright_savings(dist, demands, capacity, depot)
    cur_cost = solution_cost(routes, dist, depot)
    best_routes = [r[:] for r in routes]
    best_cost = cur_cost

    tabu: Dict[Tuple[int, int], int] = {}
    start = time.time()
    last_improve = 0
    it = 0

    def remove_expired(it_now: int):
        dead = [k for k, v in tabu.items() if v <= it_now]
        for k in dead:
            del tabu[k]

    def pick_move():
        if random.random() < params.w_2opt:
            rid = random.randrange(len(routes))
            ij = _random_2opt_indices(len(routes[rid]))
            if ij is None:
                return None
            i, j = ij
            return ("2opt", rid, i, j)

        if len(routes) >= 2 and random.random() < 0.5:
            r1 = random.randrange(len(routes))
            r2 = random.randrange(len(routes))
            if r1 == r2 or (not routes[r1]) or (not routes[r2]):
                return None
            i = random.randrange(len(routes[r1]))
            j = random.randrange(len(routes[r2]))
            return ("swap", r1, i, r2, j)

        rf = random.randrange(len(routes))
        if not routes[rf]:
            return None
        i = random.randrange(len(routes[rf]))
        rt = random.randrange(len(routes))
        pos = random.randint(0, len(routes[rt]))
        return ("reloc", rf, i, rt, pos)

    def evaluate_move(move):
        typ = move[0]
        new_routes = [r[:] for r in routes]

        if typ == "2opt":
            _, rid, i, j = move
            new_routes[rid] = _apply_2opt(new_routes[rid], i, j)
            key = (rid, i * 1000 + j)

        elif typ == "swap":
            _, r1, i, r2, j = move
            a = new_routes[r1][i]
            b = new_routes[r2][j]
            new_routes[r1][i] = b
            new_routes[r2][j] = a
            if not feasible_route(new_routes[r1], demands, capacity):
                return None
            if not feasible_route(new_routes[r2], demands, capacity):
                return None
            key = (min(a, b), max(a, b))

        elif typ == "reloc":
            _, rf, i, rt, pos = move
            if rf == rt and (pos == i or pos == i + 1):
                return None
            cust = new_routes[rf].pop(i)
            if rt == rf and pos > i:
                pos -= 1
            new_routes[rt].insert(pos, cust)
            if not feasible_route(new_routes[rf], demands, capacity):
                return None
            if not feasible_route(new_routes[rt], demands, capacity):
                return None
            key = (cust, rt + 100000)
        else:
            return None

        new_routes = [r for r in new_routes if r]
        new_cost = solution_cost(new_routes, dist, depot)
        return new_cost, new_routes, key

    while it < params.max_iters:
        it += 1
        if time.time() - start > params.time_limit:
            break
        if it - last_improve > params.no_improve:
            break

        remove_expired(it)

        best_candidate = None
        best_key = None

        for _ in range(params.neighbor_samples):
            mv = pick_move()
            if mv is None:
                continue
            out = evaluate_move(mv)
            if out is None:
                continue
            cand_cost, cand_routes, key = out

            is_tabu = key in tabu
            aspiration = cand_cost < best_cost
            if is_tabu and not aspiration:
                continue

            if best_candidate is None or cand_cost < best_candidate[0]:
                best_candidate = (cand_cost, cand_routes)
                best_key = key

        if best_candidate is None:
            continue

        cur_cost, routes = best_candidate
        tabu[best_key] = it + params.tabu_tenure

        if cur_cost < best_cost:
            best_cost = cur_cost
            best_routes = [r[:] for r in routes]
            last_improve = it

    return TabuResult(best_routes=best_routes, best_cost=best_cost, iters=it, runtime=time.time() - start)
