# 2021 Hickel comparison mode

The site exposes a scenario selector so the same 2021 EXIOBASE production system can be viewed under different counterfactuals.

## Hickel et al. reference result

Hickel, Hanbury Lemos & Barbour (2024) use EXIOBASE to estimate embodied labor flows through 2021. Their 2021 result is 826 billion net South-to-North embodied labor hours. They value that labor at Northern wages for the same skill levels and report €16.9 trillion in constant 2005 EUR. Their North approximates the IMF advanced-economy grouping.

## Scenario A — EWA

Equivalent effective-labor claims receive the same remuneration and the global compensation pool is conserved. Current productivity is retained as a conditioning variable.

## Scenario B — Hickel-style Northern wage

Southern labor is valued at the hours-weighted Northern wage. When high/medium/low skill satellite data are available, matching is performed by skill. If the source adapter cannot supply skill classes, the website must say **all-skill approximation** and must not call the result a replication.

## North/South selector

The default North list is versioned in `config/regions_hickel_2021.json`. The UI also permits:
- North only
- South only
- World
- North vs South comparison

This grouping is an analytical classification, not an EWA assumption.

## Important comparability caveat

EXIOBASE 3.9's 2021 table is now-cast rather than a core supply/use-table year; its maintainers recommend caution, particularly around the pandemic. We nevertheless expose 2021 because the Hickel paper's headline comparison is for 2021. The release manifest labels the year as now-cast.

A genuine numerical replication of Hickel's €16.9T additionally requires matching their constant-2005-EUR deflation, MER valuation, skill classes, sector treatment, and embodied-labor MRIO calculation. The code must report deviations from those specifications rather than silently claiming equivalence.
