# Data sources and provenance

## World Bank PPP

Baseline indicator: **PA.NUS.PPP — PPP conversion factor, GDP (LCU per international $)**, retrieved through the World Bank Indicators API by `scripts/fetch_world_bank_ppp.py`.

## MRIO

The repository is source-agnostic at model level. A first production release may use WIOD for a manageable country-sector implementation; EXIOBASE is a natural later extension for material, energy and ecological layers.

Do not commit large third-party raw archives unless their licenses permit redistribution. Store source URL, release/vintage, retrieval date, checksums and transformation scripts.

## Labor and productivity

A production release must document how compensation, hours, employment, sector output and effective-labor coefficients are harmonized. Measured productivity can itself embody historical hierarchy; the baseline static EWA therefore reports it as a retained conditioning variable, not as a claim that observed productivity differences are historically innocent.
