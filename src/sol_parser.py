from __future__ import annotations
from pathlib import Path
from typing import Optional
import re

COST_PATTERNS = [
    r"\bcost\b\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)",
    r"\btotal\s+cost\b\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)",
    r"\bobjective\b\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)",
]

def parse_sol_cost(sol_path: Path) -> Optional[float]:
    if not sol_path.exists():
        return None
    text = sol_path.read_text(encoding="utf-8", errors="ignore").lower()
    found = []
    for pat in COST_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            try:
                found.append(float(m.group(1)))
            except Exception:
                pass
    if found:
        return found[-1]

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) == 1:
        try:
            return float(lines[0])
        except Exception:
            return None
    return None
