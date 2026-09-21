"""Counterfactual price-of-production calculations."""
from __future__ import annotations
import numpy as np

def production_prices(A: np.ndarray, value_added: np.ndarray) -> np.ndarray:
    """Solve p = A p + v, i.e. p = (I-A)^(-1)v.

    A is the input coefficient matrix under the repository's column/row
    convention documented in docs/model-specification.md. The baseline is a
    transparent Leontief/Sraffian unit-cost system. Richer capital-return
    specifications should enter value_added explicitly rather than being hidden.
    """
    A = np.asarray(A, dtype=float)
    v = np.asarray(value_added, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("A must be square.")
    if v.shape != (A.shape[0],):
        raise ValueError("value_added must have one entry per sector.")
    spectral_radius = max(abs(np.linalg.eigvals(A)))
    if spectral_radius >= 1:
        raise ValueError("Productive system is not viable: spectral radius >= 1.")
    return np.linalg.solve(np.eye(A.shape[0]) - A, v)

def price_residual(A: np.ndarray, p: np.ndarray, v: np.ndarray) -> np.ndarray:
    return np.asarray(p) - np.asarray(A) @ np.asarray(p) - np.asarray(v)
