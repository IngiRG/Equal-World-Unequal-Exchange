# EWA empirical specification v0.1

This document is the executable specification for the baseline **static** Equal World Analysis. It deliberately separates observed quantities from counterfactual restrictions.

## 1. Estimand

For an actual world \(W^A\), construct a minimally transformed world \(W^*\) in which the specified international remuneration hierarchy is neutralized while named conditioning characteristics are retained. The hierarchy gap is always reported as a difference between the two states, never inferred from observed difference alone.

## 2. Labor transformation

For country-sector cell \(i\):

\[
w_i^R = \frac{w_i^N}{q_i}
\]

where \(w^N\) is nominal hourly compensation and \(q\) is the PPP conversion factor.

Let \(e_i>0\) be the retained effective-labor coefficient and \(L_i\) hours. Actual remuneration per effective labor unit is

\[
u_i^A = \frac{w_i^R}{e_i}.
\]

The Equal World imposes Equivalent Claim Neutrality:

\[
u_i^* = \bar u^* \quad \forall i.
\]

Aggregate Conservation requires

\[
\sum_i w_i^*L_i = \sum_i w_i^R L_i.
\]

Since \(w_i^*=\bar u^*e_i\), this identifies

\[
\boxed{\bar u^*=\frac{\sum_i w_i^R L_i}{\sum_i e_iL_i}}
\]

and

\[
\boxed{w_i^*=\bar u^*e_i}.
\]

This is **not** a Northern-wage benchmark. It conserves the observed global real remuneration pool while redistributing it according to the declared equivalence rule.

## 3. Production-price system

Let \(A\) be the technical input coefficient matrix and \(v^*\) the counterfactual direct value-added/unit-cost vector after labor and any explicitly specified normal non-labor returns have been constructed.

The transparent baseline solves

\[
p^* = Ap^*+v^*
\]

hence

\[
\boxed{p^*=(I-A)^{-1}v^*}.
\]

The actual empirical implementation must document exactly how \(v^*\) is assembled. A richer Sraffian specification with an explicit profit rate may replace this baseline, but must be a named model variant and must not be silently mixed into it.

## 4. Fixed-quantity trade revaluation

The static exercise holds quantities fixed. For export vector \(x_c\):

\[
V_c^A=x_c^\top p^A, \qquad V_c^*=x_c^\top p^*
\]

and

\[
\boxed{H_c=V_c^*-V_c^A}.
\]

Positive \(H_c\) means the fixed bundle commands more under the specified Equal World price system. It does not by itself establish historical imperialism.

## 5. Interpretation boundary

The baseline conditions on current technology, sector structure and supplied effective-labor coefficients. It therefore estimates a **static distributive hierarchy conditional on present productive structure**. It does not estimate the productive structure that would have existed absent colonialism or historical imperialism.

## 6. Required robustness variants

A publishable empirical release should at minimum compare:

- raw-hours/no-productivity adjustment;
- baseline effective-labor adjustment;
- alternative defensible productivity normalization;
- market-exchange-rate versus PPP real remuneration;
- alternative normal-return assumptions;
- alternative sector aggregation.

If plausible specifications reverse the sign of a hierarchy gap, the result should be reported as counterfactually underidentified rather than forced into a directional conclusion.
