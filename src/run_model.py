     
import argparse
import logging
import platform
import sys
import time
import warnings

from src.auto_detect import CPUInfo, get_cpu_info
from src.models.interpolate import infer_predictions
from src.models.models import Models

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
    base = CPUInfo()
    
    if args.autoinput:
        base = get_cpu_info(logger)

    return CPUInfo(
        chips=args.cpu_chips or base.chips,
        freq=args.cpu_freq or base.freq,
        threads=args.cpu_threads or base.cpu_threads,
        cores=args.cpu_cores or base.cores,
        make=args.cpu_make or base.make,
        tdp=args.tdp or base.tdp,
        mem=args.ram or base.mem
    )

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    # which model to run
    parser.add_argument('--model', type=Models, choices=list(Models))
    
    # allowed cpu info values
    parser.add_argument('--cpu-chips', type=float, help='Number of CPU Chips')
    parser.add_argument('--cpu-threads', type=float, help='Number of CPU Threads')
    parser.add_argument('--cpu-freq',
        type=float,
        help='CPU frequency. (Not used. Only for compatibility with XGBoost model)'
    )
    parser.add_argument('--tdp', type=float, help='TDP in Watts of the CPU')
    parser.add_argument('--ram', type=float, help='Amount of GB of RAM for the bare metal system')
    
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
    parser.add_argument('--auto', action='store_true', help='Force auto detect.')
    parser.add_argument('--autoinput', action='store_true', help='Will get the CPU utilization through psutil.')
    parser.add_argument('--interval', type=float, help='Interval in seconds if autoinput is used.', default=1.0)
    
    args = parser.parse_args()
    
    # handle silent
    if args.silent:
        set_silent()
    
    cpu_info = get_cpu(args)
    
    if not args.vhost_ratio:
        args.vhost_ratio = 1.0
        
    logger.info('vHost ratio is set to %s', args.vhost_ratio)
    logger.info('Matching the training data to the supplied arguments: %s', cpu_info.__dict__)
    
    if args.model == Models.OLS:
        from src.models.ols import OLSModel
        model = OLSModel(cpu_info)
    elif args.model == Models.XGB:
        from src.models.xgb import XGBModel
        model = XGBModel(cpu_info)
    else:
        raise ValueError('Model not implemented')
    
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
        import psutil
        def cpu_utilization():
            while True:
                cpu_util = psutil.cpu_percent(args.interval)
                yield str(cpu_util)

        input_source = cpu_utilization()
        
        
    # inferred_predictions = infer_predictions(trained_model, Z)
    # interpolated_predictions = interpolate_predictions(inferred_predictions)

    for line in input_source:
        utilization = float(line.strip())
        
        if utilization < 0 or utilization > 100:
            raise ValueError("Utilization can not be over 100%. If you have multiple CPU cores please divide by cpu count.")
        
        model.predict(utilization)