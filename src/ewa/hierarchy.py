"""Fixed-quantity trade revaluation."""
from __future__ import annotations
import numpy as np

def trade_revaluation(export_quantities, actual_prices, equal_prices) -> dict:
    q=np.asarray(export_quantities,dtype=float)
    pa=np.asarray(actual_prices,dtype=float)
    pe=np.asarray(equal_prices,dtype=float)
    if not (q.shape == pa.shape == pe.shape):
        raise ValueError("q, actual_prices and equal_prices must have equal shapes.")
    actual=float(q @ pa)
    equal=float(q @ pe)
    return {"actual_value":actual,"equal_world_value":equal,
            "hierarchy_gap":equal-actual,
            "hierarchy_ratio": (equal/actual if actual else None)}
