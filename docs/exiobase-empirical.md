# EXIOBASE empirical EWA

## Baseline year

The production baseline is **2020**, because EXIOBASE 3.9 documentation recommends 2020 as the latest core economic year for most analysis; 2021–2022 are now-casts. The pipeline pins Zenodo record 15689391 / EXIOBASE 3.9.6.

## Inputs

1. EXIOBASE industry-by-industry MRIO: technical coefficients, output, factor inputs and employment/hours.
2. World Bank `PA.NUS.PPP`: PPP conversion factor.
3. World Bank `SL.GDP.PCAP.EM.KD`: GDP per person employed, used as the first country-level productivity conditioning measure.

The World Bank itself cautions that modeled/imputed productivity observations carry uncertainty and should not be used uncritically for country rankings. EWA therefore treats this as a baseline specification requiring robustness analysis.

## Currency/PPP treatment

PPP is a **baseline EWA transformation**, not merely a robustness variable.

EXIOBASE monetary compensation is in common-currency EUR. World Bank PPP is LCU per international dollar, so units must first be reconciled. The pipeline retrieves World Bank official exchange rates (LCU/USD) and the ECB annual USD/EUR reference rate:

`XR_i^{LCU/EUR} = XR_i^{LCU/USD} × XR^{USD/EUR}`.

Then, cell by cell:

`w_i^{LCU} = (C_i^{EUR}/L_i) × XR_i^{LCU/EUR}`

`w_i^R = w_i^{LCU} / PPP_i`.

EWA is constructed in international-dollar purchasing-power space. After the Equal World real wage is found,

`w_i^{LCU*}=w_i^{R*}×PPP_i`

and

`w_i^{EUR*}=w_i^{LCU*}/XR_i^{LCU/EUR}`.

The last conversion puts the counterfactual labor cost back into EXIOBASE's monetary unit before solving production prices. Thus two otherwise equivalent countries can have different Equal World nominal wages because their PPP price levels differ.

## Effective labor

Country productivity is normalized to a global hours-weighted mean of one:

`e_c = productivity_c / weighted_world_productivity`.

This is a conditioning choice, not a claim that observed productivity differences are historically innocent.

## Wage counterfactual

Observed EXIOBASE compensation per hour is `wA_cs`. The conserved global compensation pool identifies

`u* = sum(compensation_cs) / sum(e_c * hours_cs)`

and

`w*_cs = u* e_c`.

Thus equal claims are defined at the country productivity level while sector technology/hours remain observed.

## Price system

Technology `A` is fixed. Actual labor value-added coefficients are compensation/output. Baseline non-labor value added is the residual unit value added after labor compensation and is held fixed. Counterfactual labor coefficients substitute Equal World compensation.

`pA = (I-A)^-1 (laborVA_A + nonlaborVA)`

`p* = (I-A)^-1 (laborVA_* + nonlaborVA)`.

This is a **baseline static production-price specification**, not the final word on normal profit. Alternative normal-return rules belong in robustness variants.

## Interpretation

These are empirical calculations conditional on the chosen data and counterfactual specification. They estimate a static hierarchy gap. They do not by themselves establish a historical causal effect of imperialism.
