"""Validation identities used in CI and empirical releases."""
def remuneration_conservation(df, tolerance=1e-9):
    actual=float((df["real_wage"]*df["hours"]).sum())
    equal=float((df["equal_real_wage"]*df["hours"]).sum())
    scale=max(1.0,abs(actual))
    return abs(actual-equal) <= tolerance*scale, actual, equal
