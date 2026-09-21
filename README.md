# Equal World / Unequal Exchange — Empirical EWA

Reproducible computational companion for **Equal World Analysis (EWA)**.\n\n## Interactive Atlas\n\nThe public GitHub Pages application is the **Equal World Atlas**. The repository homepage you are reading is documentation, not the application. After a successful empirical EXIOBASE build, the Atlas automatically prefers `site/data/real/` and falls back to the synthetic demonstration dataset only when empirical output is absent.\n

This repository contains:

- a Python reference implementation of the counterfactual wage and price-of-production system;
- validation tests for conservation and price-system identities;
- a World Bank PPP data retriever;
- a transparent demo dataset used to exercise the complete pipeline;
- static JSON result generation;
- an interactive GitHub Pages world map with country-level, step-by-step calculations;
- GitHub Actions for tests/data refresh and Pages deployment.

> **Research status:** the bundled country figures are a **demonstration dataset, not empirical estimates of unequal exchange**. The model and website are designed so a harmonized MRIO/labor dataset can replace the demo inputs without changing the audit trail.

## Core static EWA pipeline

For country-sector observations, the baseline implementation computes:

1. real remuneration: `w_real = w_nominal / PPP`;
2. effective-labor remuneration: `u = w_real / e`, where `e` is the effective-labor/productivity coefficient;
3. aggregate-conserving benchmark: `u* = Σ(w_real L) / Σ(e L)`;
4. equal-world real wage: `w* = u* e`;
5. counterfactual unit value-added vector `v*`;
6. counterfactual production prices `p* = (I-A)^{-1}v*`;
7. fixed-quantity trade revaluation and hierarchy gaps.

The empirical specification is documented in [docs/model-specification.md](docs/model-specification.md).

## Local run

```bash
python -m pip install -r requirements.txt
python scripts/build_results.py
python -m pytest
python -m http.server 8000 --directory site
```

Open http://localhost:8000.

## Data

`scripts/fetch_world_bank_ppp.py` retrieves World Bank indicator `PA.NUS.PPP` through the World Bank Indicators API. The API requires no key.

A production empirical release should pin the MRIO source/vintage and provide a harmonized `country × sector` table matching [docs/data-contract.md](docs/data-contract.md). Large raw MRIO archives should not be committed to Git; store checksums and provenance instead.

## Reproducibility

Every site build writes `site/data/manifest.json` with model version, timestamp, source labels, and assumptions. Published chapter results should additionally be tagged as immutable Git releases.

## License

Code: MIT. Data retain their original source licenses; see [docs/data-sources.md](docs/data-sources.md).


## Real empirical EXIOBASE pipeline

The repository now includes a pinned real-data pipeline using EXIOBASE 3.9.6 plus World Bank PPP and labor-productivity indicators.

Run:

```bash
python scripts/fetch_world_bank.py --year 2020
python scripts/fetch_exiobase.py --year 2020 --format ixi
python scripts/build_exiobase_results.py --year 2020 --archive data/raw/exiobase/IOT_2020_ixi.zip
```

Or run the **Build empirical EXIOBASE EWA** workflow manually in GitHub Actions. See `docs/exiobase-empirical.md` and `docs/empirical-release-checklist.md`.

The pipeline fails rather than silently guessing when EXIOBASE account labels, country mappings, or required observations are ambiguous.
