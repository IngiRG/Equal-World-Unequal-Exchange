# Empirical data contract

The model ingests a long country-sector table. Required labor fields are:

| field | meaning |
|---|---|
| iso3 | ISO 3166-1 alpha-3 country code |
| sector | harmonized sector identifier |
| nominal_wage | nominal labor compensation per hour |
| ppp | PPP conversion factor, local currency units per international dollar |
| effective_labor | retained productivity/effective-labor coefficient |
| hours | labor hours represented by the observation |

The production-price layer additionally requires a square country-sector technical-coefficient matrix **A**, direct labor/unit coefficients, and explicitly documented non-labor value-added/normal-return terms.

All monetary units, base years, deflators, sector concordances, treatment of taxes/subsidies, and rest-of-world handling must be recorded in a release manifest.

## Missing data

Missing observations must not be silently imputed. Every imputation rule belongs in metadata and sensitivity analysis.

## Empirical versus normative inputs

Source observations and counterfactual choices must remain separate. In particular, `effective_labor`, normal-return assumptions, and any ecological allocation rule must be labelled as conditioning/specification choices rather than raw facts.
