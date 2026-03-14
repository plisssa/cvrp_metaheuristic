from __future__ import annotations
from typing import List, Tuple, Dict

def clarke_wright_savings(dist: List[List[float]], demands: List[int], cap: int, depot: int) -> List[List[int]]:
    n = len(dist)
    customers = [i for i in range(n) if i != depot]

    routes: Dict[int, List[int]] = {i: [i] for i in customers}
    route_load: Dict[int, int] = {i: demands[i] for i in customers}
    belongs: Dict[int, int] = {i: i for i in customers}

    savings: List[Tuple[float, int, int]] = []
    for i in customers:
        for j in customers:
            if i >= j:
                continue
            s = dist[i][depot] + dist[depot][j] - dist[i][j]
            savings.append((s, i, j))
    savings.sort(reverse=True, key=lambda x: x[0])

    def is_end(route: List[int], node: int) -> bool:
        return route[0] == node or route[-1] == node

    for _, i, j in savings:
        ri = belongs[i]
        rj = belongs[j]
        if ri == rj:
            continue

        route_i = routes[ri]
        route_j = routes[rj]
        if not is_end(route_i, i) or not is_end(route_j, j):
            continue
        if route_load[ri] + route_load[rj] > cap:
            continue

        if route_i[-1] != i:
            route_i = list(reversed(route_i))
        if route_j[0] != j:
            route_j = list(reversed(route_j))

        merged = route_i + route_j
        routes[ri] = merged
        route_load[ri] = route_load[ri] + route_load[rj]

        del routes[rj]
        del route_load[rj]

        for node in merged:
            belongs[node] = ri

    return list(routes.values())
