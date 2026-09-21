import numpy as np
from ewa.prices import production_prices, price_residual

def test_price_identity():
    A=np.array([[.2,.1],[.1,.25]])
    v=np.array([.6,.55])
    p=production_prices(A,v)
    assert np.max(np.abs(price_residual(A,p,v))) < 1e-12
