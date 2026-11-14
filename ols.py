#pylint: disable=invalid-name

import os
import sys
import statsmodels.formula.api as smf
import pandas as pd
import numpy as np

NUMERIC_COLUMNS = {
    'cpu_cores': 'CPUCores',
    'cpu_freq': 'HW_CPUFreq',
    'release_year': 'Hardware_Availability_Year',
}

CATEGORICAL_COLUMNS = {
    'cpu_make': 'CPUMake',
    'turbo': 'Turbo',
    'form_factor': 'FormFactor',
    'vendor': 'Vendor',
    'power_profile': 'PowerProfile',
}

def load_data():
    data = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/spec-power-data/data/spec_data_cleaned.csv")
    data['Turbo'] = data['Turbo'].map({True: 'yes', False: 'no'})
    return data

def categorical_term(data, col):
    # Use the level with the most machines as reference instead of the alphabetically first one. This does not
    # change the predictions, but makes the coefficients in --dump-stats readable
    reference = data.groupby(col)['Result_ID'].nunique().idxmax()
    reference = reference.item() if hasattr(reference, 'item') else reference # numpy scalar -> python for repr
    return f"C({col}, Treatment(reference={reference!r}))"

def train_model(data, cpu_chips, ram, tdp, cpu_threads, *, params, log=False):

    terms = []

    if cpu_threads is not None:
        terms.append('CPUThreads')

    if cpu_chips is not None:
        terms.append(categorical_term(data, 'CPUChips'))

    if ram is not None:
        terms.append('HW_MemAmountGB')

    if tdp is not None:
        terms.append('TDP')

    for name, col in NUMERIC_COLUMNS.items():
        if params.get(name) is not None:
            terms.append(col)

    for name, col in CATEGORICAL_COLUMNS.items():
        if params.get(name) is not None:
            terms.append(categorical_term(data, col))

    # Every parameter interacts with utilization, so it can change the slope of the power curve and not only shift
    # it. With a single shared slope small machines get the slope of the big servers and go negative at idle.
    target = 'np.log(power)' if log else 'power'
    formula = f"{target} ~ utilization * ({' + '.join(terms)})" if terms else f"{target} ~ utilization"

    return smf.ols(formula=formula, data=data).fit()

def predict(fitted, X, log=False):
    prediction = fitted.predict(X).iloc[0]
    return np.exp(prediction) if log else prediction

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--cpu-chips', type=float, help='Number of CPUChips')
    parser.add_argument('--cpu-threads', type=float, help='Number of CPU Threads')
    parser.add_argument('--cpu-cores', type=float, help='Number of CPU cores')
    parser.add_argument('--cpu-freq', type=float, help='CPU frequency')
    parser.add_argument('--release-year', type=float, help='Release year of the CPU')
    parser.add_argument('--cpu-make', type=str, help='The make of the CPU (intel, amd, ampere or nvidia)')
    parser.add_argument('--turbo', type=str, choices=['yes', 'no'], help='Whether Turbo Boost is enabled on the CPU')
    parser.add_argument('--form-factor',
        type=str,
        choices=['1U', '2U', '3U', '4U', '5U', '6U', '8U', '10U', 'Tower', 'Blade'],
        help='The form factor of the server'
    )
    parser.add_argument('--vendor',
        type=str,
        choices=['hpe', 'lenovo', 'fujitsu', 'supermicro', 'dell', 'other'],
        help='The vendor of the server'
    )
    parser.add_argument('--power-profile',
        type=str,
        choices=['power-saver', 'balanced', 'performance'],
        help='Coarse power setting of the system. See the README for how power plans, governors and CPU caps map to it'
    )
    parser.add_argument('--tdp', type=float, help='TDP of the CPU')
    parser.add_argument('--ram', type=float, help='Amount of RAM for the bare metal system')
    parser.add_argument('--vhost-ratio',
        type=float,
        help='Virtualization ratio of the system. Input numbers between (0,1].',
        default=1.0
    )
    parser.add_argument('--silent',
        action='store_true',
        help='Will suppress all debug output. Typically used in production.'
    )
    parser.add_argument('--log',
        action='store_true',
        help='Fit log(power) instead of power. Predictions can then never be negative'
    )
    parser.add_argument('--dump-stats',
        action='store_true',
        help='Print the statsmodels summary of the trained model (coefficients, p-values, R², AIC, BIC, ...) and exit'
    )

    args = parser.parse_args()

    df = load_data()
    extra_params = {arg: getattr(args, arg) for arg in list(NUMERIC_COLUMNS) + list(CATEGORICAL_COLUMNS)}

    if args.cpu_chips is not None and args.cpu_chips not in set(df['CPUChips']):
        parser.error(f"--cpu-chips {args.cpu_chips:g} does not exist in the training data. "
                     f"Available: {', '.join(str(c) for c in sorted(df['CPUChips'].unique()))}")

    for arg, column in CATEGORICAL_COLUMNS.items():
        if extra_params[arg] is not None and extra_params[arg] not in set(df[column]):
            parser.error(f"--{arg.replace('_', '-')} {extra_params[arg]} does not exist in the training data. "
                         f"Available: {', '.join(sorted(df[column].unique()))}")

    model = train_model(df, args.cpu_chips, args.ram, args.tdp, args.cpu_threads, params=extra_params, log=args.log)

    if args.dump_stats:
        print(model.summary())
        sys.exit(0)
    my_data = pd.DataFrame({
        'utilization': [0.0],
        'CPUChips': [args.cpu_chips],
        'CPUThreads': [args.cpu_threads],
        'HW_MemAmountGB': [args.ram],
        'TDP' : [args.tdp],
        **{column: [extra_params[arg]] for arg, column in {**NUMERIC_COLUMNS, **CATEGORICAL_COLUMNS}.items()},
    })

    # Drop all arguments that were not supplied
    my_data.dropna(axis=1, inplace=True)

    if not args.silent:
        print('Sending following dataframe to model', my_data)
        print('vHost ratio is set to ', args.vhost_ratio)


    for line in sys.stdin:
        my_data['utilization'] = float(line.strip())
        print(predict(model, my_data, args.log) * args.vhost_ratio)
