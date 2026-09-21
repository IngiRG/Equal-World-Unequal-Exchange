"""Labor-side Equal World transformations."""
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED = {"nominal_wage", "ppp", "effective_labor", "hours"}

def equal_world_wages(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Construct aggregate-conserving Equal World wages.

    PPP is local-currency-units per international dollar. Hence real wage is
    nominal_wage / ppp. effective_labor is an explicitly supplied conditioning
    coefficient, not interpreted here as morally deserved productivity.
    """
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if (df[list(REQUIRED)] <= 0).any().any():
        raise ValueError("Wages, PPP, effective labor and hours must be positive.")

    out = df.copy()
    out["real_wage"] = out["nominal_wage"] / out["ppp"]
    out["actual_effective_remuneration"] = out["real_wage"] / out["effective_labor"]
    actual_pool = float((out["real_wage"] * out["hours"]).sum())
    effective_hours = float((out["effective_labor"] * out["hours"]).sum())
    benchmark = actual_pool / effective_hours
    out["equal_effective_remuneration"] = benchmark
    out["equal_real_wage"] = benchmark * out["effective_labor"]
    out["equal_nominal_wage"] = out["equal_real_wage"] * out["ppp"]
    out["real_wage_gap"] = out["equal_real_wage"] - out["real_wage"]
    return out, benchmark
