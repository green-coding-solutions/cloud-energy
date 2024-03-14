
import argparse
import logging
import platform
import sys
import time
import warnings

from auto_detect import CPUInfo, get_cpu_info
from models.models import Models

# -- Logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def set_silent():
    # sadly some libs have future warnings we need to suppress for
    # silent mode to work in bash scripts
    warnings.simplefilter(action='ignore', category=FutureWarning)
    logger.setLevel(logging.WARNING)

# -- CPU Info detector


def get_cpu(args: argparse.Namespace):
    # default values (None)
    defaults = CPUInfo()

    if args.autoinput:
        # set the defaults to be the auto detected values
        defaults = get_cpu_info(logger)

    return CPUInfo(
        chips=args.cpu_chips or defaults.chips,
        freq=args.cpu_freq or defaults.freq,
        threads=args.cpu_threads or defaults.threads,
        cores=args.cpu_cores or defaults.cores,
        make=args.cpu_make or defaults.make,
        tdp=args.tdp or defaults.tdp,
        mem=args.ram or defaults.mem
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # which model to run
    parser.add_argument('--model', type=Models, choices=list(Models))

    # allowed cpu info values
    parser.add_argument('--cpu-chips', type=float, help='Number of CPU Chips')
    parser.add_argument('--cpu-threads', type=float,
                        help='Number of CPU Threads')
    parser.add_argument('--cpu-cores', type=int, help='Number of CPU cores')
    parser.add_argument('--architecture', type=str,
                        help='The architecture of the CPU. lowercase. ex.: haswell')
    parser.add_argument('--cpu-make', type=str,
                        help='The make of the CPU (intel or amd)')
    parser.add_argument('--cpu-freq',
                        type=float,
                        help='CPU frequency. (Not used. Only for compatibility with XGBoost model)'
                        )
    parser.add_argument('--tdp', type=float, help='TDP in Watts of the CPU')
    parser.add_argument('--ram', type=float,
                        help='Amount of GB of RAM for the bare metal system')

    # model parameters
    parser.add_argument('--vhost-ratio',
                        type=float,
                        help='Virtualization ratio of the system. Input numbers between (0,1].',
                        default=1.0
                        )

    # tool info
    parser.add_argument('--energy',
                        action='store_true',
                        help='Switches to energy mode. The output will be in Joules instead of Watts. \
        This is achieved by multiplying the interval between inputs with the estimated wattage'
                        )
    parser.add_argument('--silent',
                        action='store_true',
                        help='Will suppress all debug output. Typically used in production.'
                        )
    parser.add_argument('--auto', action='store_true',
                        help='Force auto detect.')
    parser.add_argument('--autoinput', action='store_true',
                        help='Will get the CPU utilization through psutil.')
    parser.add_argument('--interval', type=float,
                        help='Interval in seconds if autoinput is used.', default=1.0)

    args = parser.parse_args()

    # handle silent
    if args.silent:
        set_silent()

    cpu_info = get_cpu(args)
    vhost_ratio = args.vhost_ratio or 1.0
    logger.info('vHost ratio is set to %s', vhost_ratio)
    logger.info(
        'Matching the training data to the supplied arguments: %s', cpu_info.__dict__)

    if args.model == Models.OLS:
        from models.ols import OLSModel
        model = OLSModel(cpu_info, args)
    elif args.model == Models.XGB:
        from models.xgb import XGBModel
        model = XGBModel(cpu_info, args)
    else:
        raise ValueError('Model not implemented')

    logger.info('Model is ready to predict')

    if platform.system() == 'Darwin' and args.autoinput and args.interval < 0.5:
        print('''
                Under MacOS the internal values are updated every 0.5 seconds by the kernel if you use the host_statistics call.
                There is another way to get the cpu utilization by using the host_processor_info call.
                Psutils uses host_statistics so intervals under 0.5 are not sensible. We have opened a discussion here:
                https://github.com/giampaolo/psutil/issues/2368
                If you want a higher resolution you can use the cpu_utilization_mac.c file in the demo-reporter folder.
            ''')
        sys.exit(1)

    input_source = sys.stdin
    if args.autoinput:
        logger.info('Using autoinput.')
        import psutil

        def cpu_utilization():
            while True:
                cpu_util = psutil.cpu_percent(args.interval)
                yield str(cpu_util)

        input_source = cpu_utilization()

    unit_str = 'J' if args.energy else 'W'
    last_measurement = time.time_ns()

    for line in input_source:
        utilization = float(line.strip())
        logger.info('Utilization: %s', utilization)

        if utilization < 0 or utilization > 100:
            raise ValueError(
                "Utilization can not be over 100%. If you have multiple CPU cores please divide by cpu count.")
        current_time = time.time_ns()
        value = model.predict(utilization, vhost_ratio)

        if args.energy:
            # convert Watts to Joules
            interval = (current_time - last_measurement) / 1_000_000_000
            last_measurement = current_time
            value *= interval

        logger.info('Usage: %s %s', value, unit_str)
