# Data sources and provenance

## World Bank PPP

Baseline indicator: **PA.NUS.PPP — PPP conversion factor, GDP (LCU per international $)**, retrieved through the World Bank Indicators API by `scripts/fetch_world_bank_ppp.py`.

## WIOD 2016

The first production MRIO target is the **World Input-Output Database (WIOD) 2016 Release**, DOI `10.34894/PJ2M1C`. It covers 43 individually modelled countries plus Rest of World, 56 ISIC Rev. 4 sectors, and 2000–2014. WIOTs are in millions of current US dollars; matching Socio-Economic Accounts contain industry-level employment, capital stocks, gross output and value added. WIOD is distributed under CC BY 4.0.

Canonical project page: `https://www.rug.nl/ggdc/valuechain/wiod/wiod-2016-release`

The repository intentionally does not pretend WIOD supplies every EWA input directly. Labor hours/compensation and the exact productivity/effective-labor construction must be audited against the SEA variables and supplemented where necessary.

## Later ecological extension

EXIOBASE is a natural later MRIO extension for material, energy and ecological layers. It should be introduced as a separate release/model variant rather than silently mixed with the WIOD baseline.

## Storage policy

Do not commit large third-party raw archives unless their licenses and repository size make redistribution appropriate. Store source URL/DOI, release/vintage, retrieval date, checksums, concordances and transformation scripts. Immutable chapter results should be Git-tagged.

## Labor and productivity

A production release must document how compensation, hours, employment, sector output and effective-labor coefficients are harmonized. Measured productivity can itself embody historical hierarchy; the baseline static EWA therefore reports it as a retained conditioning variable, not as a claim that observed productivity differences are historically innocent.
