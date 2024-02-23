# pylint: disable=redefined-outer-name,invalid-name

import sys
import os
import time
import logging
import platform
import pandas as pd
import numpy as np
import warnings
from xgboost import XGBRegressor

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

def train_model(cpu_chips, Z):

    df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/data/spec_data_cleaned.csv")

    X = df.copy()
    X = pd.get_dummies(X, columns=['CPUMake', 'Architecture'])

    if cpu_chips:
        logger.info('Training data will be restricted to the following amount of chips: %d', cpu_chips)

        X = X[X.CPUChips == cpu_chips] # Fit a model for every amount of CPUChips

    if X.empty:
        raise RuntimeError(f"The training data does not contain any servers with a chips amount ({cpu_chips}). Please select a different amount.")

    y = X.power

    X = X[Z.columns] # only select the supplied columns from the command line

    logger.info('Model will be trained on the following columns and restrictions: \n%s', Z)

#    params = {
#      'max_depth': 10,
#      'learning_rate': 0.3037182109676833,
#      'n_estimators': 792,
#      'min_child_weight': 1,
#      'random_state': 762
#    }
    params = {} # we see no strong improvements with hyperparamters tuned by optune

    model = XGBRegressor(**params)
    model.fit(X,y)

    return model

def infer_predictions(model, Z):

    predictions = {}

    for i in range(0,110,5):
        Z['utilization'] = i
        predictions[float(i)] = model.predict(Z)[0]
    return predictions

def interpolate_helper(predictions, lower, upper, step=501):

    diff = int(upper-lower)
    diff_value = predictions[upper] - predictions[lower]

    for i in np.linspace(0, diff, step):
        predictions[round(lower+i, 2)] = predictions[lower]+((diff_value/diff)*i)

    return predictions

def interpolate_predictions(predictions):
    predictions = interpolate_helper(predictions, 0.0, 5.0, 501)
    predictions = interpolate_helper(predictions, 5.0, 15.0, 1001)
    predictions = interpolate_helper(predictions, 15.0, 25.0, 1001)
    predictions = interpolate_helper(predictions, 25.0, 35.0, 1001)
    predictions = interpolate_helper(predictions, 35.0, 45.0, 1001)
    predictions = interpolate_helper(predictions, 45.0, 55.0, 1001)
    predictions = interpolate_helper(predictions, 55.0, 65.0, 1001)
    predictions = interpolate_helper(predictions, 65.0, 75.0, 1001)
    predictions = interpolate_helper(predictions, 75.0, 85.0, 1001)
    predictions = interpolate_helper(predictions, 85.0, 95.0, 1001)
    # Question: between 95 and 100 is no difference. How do we extrapolate?
    predictions = interpolate_helper(predictions, 95.0, 100.0, 501)

    return predictions

def set_silent():
    # sadly some libs have future warnings we need to suppress for
    # silent mode to work in bash scripts
    warnings.simplefilter(action='ignore', category=FutureWarning)
    logger.setLevel(logging.WARNING)

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--cpu-chips', type=int, help='Number of CPU chips')
    parser.add_argument('--cpu-freq', type=int, help='CPU frequency')
    parser.add_argument('--cpu-threads', type=int, help='Number of CPU threads')
    parser.add_argument('--cpu-cores', type=int, help='Number of CPU cores')
    parser.add_argument('--release-year', type=int, help='Release year of the CPU')
    parser.add_argument('--tdp', type=int, help='TDP of the CPU')
    parser.add_argument('--ram', type=int, help='Amount of DRAM for the bare metal system')
    parser.add_argument('--architecture', type=str, help='The architecture of the CPU. lowercase. ex.: haswell')
    parser.add_argument('--cpu-make', type=str, help='The make of the CPU (intel or amd)')
    parser.add_argument('--auto', action='store_true', help='Force auto detect. Will overwrite supplied arguments')

    parser.add_argument('--vhost-ratio',
        type=float,
        help='Virtualization ratio of the system. Input numbers between (0,1].'

    )
    parser.add_argument('--silent',
        action='store_true',
        help='Will suppress all debug output. Typically used in production.'
    )

    parser.add_argument('--energy',
        action='store_true',
        help='Switches to energy mode. The output will be in Joules instead of Watts. \
        This is achieved by multiplying the interval between inputs with the estimated wattage'
    )

    parser.add_argument('--autoinput', action='store_true', help='Will get the CPU utilization through psutil.')
    parser.add_argument('--interval', type=float, help='Interval in seconds if autoinput is used.', default=1.0)

    args = parser.parse_args()

    if args.silent:
        set_silent()

    args_dict = args.__dict__.copy()
    del args_dict['silent']
    del args_dict['auto']
    del args_dict['energy']

    # did the user supply any of the auto detectable arguments?
    if not any(args_dict.values()) or args.auto:
        logger.info('No arguments where supplied, or auto mode was forced. Running auto detect on the sytem.')

        import auto_detect

        data = auto_detect.get_cpu_info(logger)

        logger.info('The following data was auto detected: %s', data)

        # only overwrite not already supplied values
        args.cpu_freq = args.cpu_freq or data['freq']
        args.cpu_threads = args.cpu_threads or data['threads']
        args.cpu_cores = args.cpu_cores or data['cores']
        args.tdp = args.tdp or data['tdp']
        args.ram = args.ram or data['mem']
        args.cpu_make = args.cpu_make or data['make']
        args.cpu_chips = args.cpu_chips or data['chips']

    # set default. We do this here and not in argparse, so we can check if anything was supplied at all
    if not args.vhost_ratio:
        args.vhost_ratio = 1.0

    if platform.system() == 'Darwin' and args.autoinput and args.interval < 0.5:
        print('''
                Under MacOS the internal values are updated every 0.5 seconds by the kernel if you use the host_statistics call.
                There is another way to get the cpu utilization by using the host_processor_info call.
                Psutils uses host_statistics so intervals under 0.5 are not sensible. We have opened a discussion here:
                https://github.com/giampaolo/psutil/issues/2368
                If you want a higher resolution you can use the cpu_utilization_mac.c file in the demo-reporter folder.
              ''')
        sys.exit(1)

    Z = pd.DataFrame.from_dict({
        'HW_CPUFreq' : [args.cpu_freq],
        'CPUThreads': [args.cpu_threads],
        'CPUCores': [args.cpu_cores],
        'TDP': [args.tdp],
        'Hardware_Availability_Year': [args.release_year],
        'HW_MemAmountGB': [args.ram],
        'Architecture': [args.architecture],
        'CPUMake': [args.cpu_make],
        'utilization': [0.0]
    })

    Z = pd.get_dummies(Z, columns=['CPUMake', 'Architecture'])

    Z = Z.dropna(axis=1)


    logger.info('vHost ratio is set to %s', args.vhost_ratio)

    trained_model = train_model(args.cpu_chips, Z)

    logger.info('Infering all predictions to dictionary')

    inferred_predictions = infer_predictions(trained_model, Z)
    interpolated_predictions = interpolate_predictions(inferred_predictions)

    input_source = sys.stdin
    if args.autoinput:
        import psutil
        def cpu_utilization():
            while True:
                cpu_util = psutil.cpu_percent(args.interval)
                yield str(cpu_util)

        input_source = cpu_utilization()


    for line in input_source:
        utilization = float(line.strip())
        if utilization < 0 or utilization > 100:
            raise ValueError("Utilization can not be over 100%. If you have multiple CPU cores please divide by cpu count.")

        if args.energy:
            current_time = time.time_ns()
            print(interpolated_predictions[utilization] * args.vhost_ratio * \
                (time.time_ns() - current_time) / 1_000_000_000, flush=True)
            current_time = time.time_ns()
        else:
            print(interpolated_predictions[utilization] * args.vhost_ratio, flush=True)
