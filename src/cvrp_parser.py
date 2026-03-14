from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
import math

from .sol_parser import parse_sol_cost

@dataclass
class CVRPInstance:
    name: str
    dimension: int
    capacity: int
    depot: int
    coords: List[Tuple[float, float]]
    demands: List[int]
    best_known: Optional[int] = None
    edge_weight_type: str = "EUC_2D"
    dist_matrix: Optional[List[List[float]]] = None

COMMENT_BEST_PATTERNS = [
    r"(?:optimal|optimum|best known|best)\s*[:=]?\s*(\d+)",
    r"\b(\d+)\b\s*(?:is\s*)?(?:optimal|optimum|best)\b",
]

def _parse_explicit_matrix(nums: List[float], n: int, fmt: str) -> List[List[float]]:
    fmt = fmt.upper()
    dist = [[0.0]*n for _ in range(n)]
    k = 0

    def get():
        nonlocal k
        v = nums[k]
        k += 1
        return v

    if fmt == "FULL_MATRIX":
        for i in range(n):
            for j in range(n):
                dist[i][j] = get()
        return dist

    if fmt == "LOWER_ROW":
        for i in range(n):
            for j in range(i):
                dist[i][j] = get()
                dist[j][i] = dist[i][j]
        return dist

    if fmt == "LOWER_DIAG_ROW":
        for i in range(n):
            for j in range(i+1):
                dist[i][j] = get()
                dist[j][i] = dist[i][j]
        return dist

    if fmt == "UPPER_ROW":
        for i in range(n):
            for j in range(i+1, n):
                dist[i][j] = get()
                dist[j][i] = dist[i][j]
        return dist

    if fmt == "UPPER_DIAG_ROW":
        for i in range(n):
            for j in range(i, n):
                dist[i][j] = get()
                dist[j][i] = dist[i][j]
        return dist

    raise ValueError(f"Unsupported EDGE_WEIGHT_FORMAT: {fmt}")

def parse_vrplib(path: Path) -> CVRPInstance:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    header: Dict[str, str] = {}
    coords: Dict[int, Tuple[float, float]] = {}
    dem: Dict[int, int] = {}
    depot = 1

    section: Optional[str] = None
    edge_nums: List[float] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.upper() == "EOF":
            continue

        if section is None and ":" in line:
            k, v = [x.strip() for x in line.split(":", 1)]
            header[k.upper()] = v
            continue

        u = line.upper()
        if u.endswith("SECTION"):
            section = u
            continue

        if section == "NODE_COORD_SECTION":
            parts = re.split(r"\s+", line)
            if len(parts) >= 3:
                idx = int(parts[0])
                coords[idx] = (float(parts[1]), float(parts[2]))
            continue

        if section == "DEMAND_SECTION":
            parts = re.split(r"\s+", line)
            if len(parts) >= 2:
                idx = int(parts[0])
                dem[idx] = int(float(parts[1]))
            continue

        if section == "DEPOT_SECTION":
            if line.startswith("-1"):
                section = None
                continue
            depot = int(line)
            continue

        if section == "EDGE_WEIGHT_SECTION":
            parts = re.split(r"\s+", line)
            for p in parts:
                if p:
                    edge_nums.append(float(p))
            continue

    name = header.get("NAME", path.stem)
    dim = int(header.get("DIMENSION", str(len(coords) or 0)))
    cap = int(float(header.get("CAPACITY", "0")))
    ewt = header.get("EDGE_WEIGHT_TYPE", "EUC_2D").upper()
    ewf = header.get("EDGE_WEIGHT_FORMAT", "FULL_MATRIX").upper()

    coords_list = [(0.0, 0.0)] * dim
    demands_list = [0] * dim
    for i in range(1, dim + 1):
        if i in coords:
            coords_list[i - 1] = coords[i]
        if i in dem:
            demands_list[i - 1] = dem[i]
    demands_list[depot - 1] = 0

    best = None
    comment = header.get("COMMENT", "")
    for pat in COMMENT_BEST_PATTERNS:
        m = re.search(pat, comment, flags=re.IGNORECASE)
        if m:
            try:
                best = int(m.group(1))
                break
            except Exception:
                pass

    if best is None:
        sol_cost = parse_sol_cost(path.with_suffix('.sol'))
        if sol_cost is not None:
            best = int(round(sol_cost))

    dist_matrix = None
    if ewt == "EXPLICIT":
        if dim <= 0:
            raise ValueError("DIMENSION is required for EXPLICIT instances.")
        dist_matrix = _parse_explicit_matrix(edge_nums, dim, ewf)

    return CVRPInstance(
        name=name,
        dimension=dim,
        capacity=cap,
        depot=depot - 1,
        coords=coords_list,
        demands=demands_list,
        best_known=best,
        edge_weight_type=ewt,
        dist_matrix=dist_matrix,
    )

def list_instances(root: Path, sets: List[str]) -> List[Path]:
    out: List[Path] = []
    for s in sets:
        folder = root / s
        if folder.exists():
            out += sorted(folder.rglob("*.vrp"))
    return out
