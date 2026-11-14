#pylint: disable=invalid-name
"""
Linear regression (statsmodels OLS) to analyse which machine parameters influence the power draw and by how much.

This is a research script and not part of the runtime (see xgb.py for that).

- Numeric parameters are z-score normalized, so their coefficients are standardized betas: watts per
  standard deviation of the parameter. Their sizes can be compared directly.
- Categorical parameters are dummy coded against their most frequent level. Levels with fewer than
  --min-machines machines are merged into 'other' so that single machines do not get their own coefficient.
- Every machine has 11 rows (utilization 0..100). The rows are not independent, so the standard errors are
  clustered by machine (Result_ID). Without this the p-values would be much too optimistic.
- The influence of every parameter is reported as a joint Wald test (all dummies / interaction terms together),
  as the drop in R² when the parameter is removed, and as VIF to show multicollinearity.

Examples:
    python3 ols_parameter_analysis.py
    python3 ols_parameter_analysis.py --interactions --log-transform
    python3 ols_parameter_analysis.py --params TDP CPUThreads CPUMake --full-summary
"""

import os
import argparse
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

DATA_PATH = f"{os.path.dirname(os.path.abspath(__file__))}/spec-power-data/data/spec_data_cleaned.csv"

# Same parameters that xgb.py accepts on the CLI
NUMERIC_PARAMS = ['HW_CPUFreq', 'CPUThreads', 'CPUCores', 'TDP', 'HW_MemAmountGB', 'Hardware_Availability_Year']
CATEGORICAL_PARAMS = ['CPUMake', 'CPUChips', 'Turbo', 'FormFactor', 'Vendor', 'PowerProfile']
# Strongly right-skewed size parameters that can be log transformed with --log-transform
LOG_CANDIDATES = ['CPUThreads', 'CPUCores', 'HW_MemAmountGB']


def load_data(params, min_machines, log_transform):
    df = pd.read_csv(DATA_PATH)
    df = df[['Result_ID', 'utilization', 'power'] + params].dropna().copy()

    numeric = [p for p in params if p in NUMERIC_PARAMS]
    categorical = [p for p in params if p in CATEGORICAL_PARAMS]

    for p in numeric:
        if log_transform and p in LOG_CANDIDATES:
            df[p] = np.log2(df[p])

    references = {}
    for p in categorical:
        df[p] = df[p].astype(str)
        machines_per_level = df.groupby(p)['Result_ID'].nunique()
        rare = machines_per_level[machines_per_level < min_machines].index
        if len(rare) > 0:
            df.loc[df[p].isin(rare), p] = 'other'
        # If even the merged group is too small its coefficient would only describe a handful of machines
        machines_per_level = df.groupby(p)['Result_ID'].nunique()
        too_small = machines_per_level[machines_per_level < min_machines]
        if not too_small.empty:
            print(f"Dropping {too_small.sum()} machine(s) with {p} in {list(rare)}: "
                  f"fewer than {min_machines} machines even after merging")
            df = df[~df[p].isin(too_small.index)]
        references[p] = df.groupby(p)['Result_ID'].nunique().idxmax()

    # Normalize after dropping so that the z-scores refer to the data that is actually fitted.
    # Utilization is normalized too, so that main effects are at average load when --interactions is used.
    for p in numeric + ['utilization']:
        df[p] = (df[p] - df[p].mean()) / df[p].std()

    return df, numeric, categorical, references


def term(p, numeric, references):
    if p in numeric:
        return p
    return f"C({p}, Treatment(reference='{references[p]}'))"


def build_formula(params, numeric, references, interactions):
    terms = ['utilization']
    for p in params:
        t = term(p, numeric, references)
        terms.append(t)
        if interactions:
            terms.append(f"utilization:{t}")
    return 'power ~ ' + ' + '.join(terms)


def fit(formula, df):
    return smf.ols(formula, data=df).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(df['Result_ID'])[0]})


def joint_wald_p(model, t):
    """p-value of the joint test that all columns of a term (dummies and utilization interactions) are zero"""
    names = model.model.exog_names
    cols = [i for i, n in enumerate(names)
            if any(n == base or n.startswith(f"{base}[") for base in (t, f"utilization:{t}"))]
    R = np.zeros((len(cols), len(names)))
    for row, col in enumerate(cols):
        R[row, col] = 1
    return float(model.wald_test(R, scalar=True).pvalue)


def drop_one_r2(df, params, numeric, references, interactions, full_r2):
    delta_r2 = []
    for p in params:
        reduced = build_formula([q for q in params if q != p], numeric, references, interactions)
        delta_r2.append(full_r2 - smf.ols(reduced, data=df).fit().rsquared)
    return pd.DataFrame({'delta_R2': delta_r2}, index=pd.Index(params, name='parameter'))


def vif_table(model):
    exog = model.model.exog
    names = model.model.exog_names
    with warnings.catch_warnings(): # perfect collinearity produces inf and a divide warning
        warnings.simplefilter('ignore')
        vifs = [variance_inflation_factor(exog, i) for i in range(exog.shape[1])]
    return pd.Series(vifs, index=names, name='VIF').drop('Intercept').sort_values(ascending=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--params', nargs='+', default=NUMERIC_PARAMS + CATEGORICAL_PARAMS,
        choices=NUMERIC_PARAMS + CATEGORICAL_PARAMS, help='Parameters to put in the model (default: all)')
    parser.add_argument('--interactions', action='store_true',
        help='Add utilization x parameter terms. Shows if a parameter changes the slope and not only the idle power')
    parser.add_argument('--log-transform', action='store_true',
        help=f"log2 transform {', '.join(LOG_CANDIDATES)} before normalization")
    parser.add_argument('--min-machines', type=int, default=10,
        help='Categorical levels with fewer machines are merged into "other" (default: 10)')
    parser.add_argument('--full-summary', action='store_true', help='Also print the full statsmodels summary')
    args = parser.parse_args()

    df, numeric, _, references = load_data(args.params, args.min_machines, args.log_transform)
    formula = build_formula(args.params, numeric, references, args.interactions)
    model = fit(formula, df)

    pd.set_option('display.width', 200)
    pd.set_option('display.max_rows', 200)

    print(f"Machines: {df['Result_ID'].nunique()}, rows: {len(df)}")
    print(f"Formula: {formula}")
    print('Reference levels: ' + ', '.join(f"{k}={v}" for k, v in references.items()))
    print(f"R²: {model.rsquared:.4f}  adj. R²: {model.rsquared_adj:.4f}  "
          f"RMSE: {np.sqrt(model.mse_resid):.1f} W  mean power: {df['power'].mean():.1f} W")

    if args.full_summary:
        print(model.summary())

    print('\n=== Coefficients [W per std. dev. for numeric, W vs. reference level for categorical] ===')
    print('    (standard errors clustered by machine)')
    coefs = pd.DataFrame({'coef_W': model.params, 'std_err': model.bse, 'p_value': model.pvalues})
    coefs = coefs[coefs.index != 'Intercept']
    coefs = coefs.reindex(coefs['coef_W'].abs().sort_values(ascending=False).index)
    print(coefs.to_string(float_format=lambda x: f"{x:.4g}"))

    print('\n=== Influence per parameter ===')
    print('    Wald test over all terms of a parameter (incl. dummies and interactions), '
          'delta_R2 = loss in R² when the parameter is removed')
    influence = drop_one_r2(df, args.params, numeric, references, args.interactions, model.rsquared)
    influence['wald_p_value'] = [joint_wald_p(model, term(p, numeric, references)) for p in influence.index]
    influence['kind'] = ['numeric' if p in numeric else 'categorical' for p in influence.index]
    print(influence.sort_values('delta_R2', ascending=False).to_string(float_format=lambda x: f"{x:.4g}"))

    print('\n=== Multicollinearity (VIF > 10 is problematic, > 5 worth a look) ===')
    print(vif_table(model).to_string(float_format=lambda x: f"{x:.2f}"))


if __name__ == '__main__':
    main()
