"""PPP/MER transformations for the baseline EWA wage construction."""
from __future__ import annotations
import pandas as pd

def common_currency_to_real(comp_common, hours, exchange_lcu_per_common, ppp_lcu_per_intl):
    """Convert common-currency compensation to local nominal and PPP-real wages.

    If EXIOBASE compensation C is in common currency (EUR), and xr is LCU/EUR:
      local compensation = C * xr
      nominal local wage  = C*xr/L
      real wage (intl$)   = nominal local wage / PPP
    """
    if (hours<=0).any() or (exchange_lcu_per_common<=0).any() or (ppp_lcu_per_intl<=0).any():
        raise ValueError("hours, exchange rates and PPP must be positive")
    local_comp=comp_common*exchange_lcu_per_common
    nominal_local=local_comp/hours
    real=nominal_local/ppp_lcu_per_intl
    return pd.DataFrame({"local_compensation":local_comp,"nominal_local_wage":nominal_local,"real_wage_intl":real})

def equal_world_real_wages(real_wage, hours, effective_labor):
    """Equalize remuneration/effective labor in PPP-real space, conserving real pool."""
    real_pool=float((real_wage*hours).sum())
    effective_hours=float((effective_labor*hours).sum())
    ustar=real_pool/effective_hours
    return ustar, ustar*effective_labor

def real_wage_to_common(equal_real_wage, ppp_lcu_per_intl, exchange_lcu_per_common):
    """Convert Equal World PPP-real wage back to the MRIO common currency."""
    equal_nominal_local=equal_real_wage*ppp_lcu_per_intl
    equal_common=equal_nominal_local/exchange_lcu_per_common
    return pd.DataFrame({"equal_nominal_local_wage":equal_nominal_local,"equal_common_wage":equal_common})
