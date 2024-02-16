# pylint: disable=redefined-outer-name,invalid-name

import subprocess
import re
import logging
import math

def get_cpu_info(logger):

    data = {
        'freq' : None,
        'threads': None,
        'cores': None,
        'tdp': None,
        'mem': None,
        'make': None,
        'chips': None
    }

    try:
        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/name'
        with open(file_path, 'r', encoding='UTF-8') as file:
            domain_name = file.read().strip()
            if domain_name != 'package-0':
                raise RuntimeError(f"Domain /sys/class/powercap/intel-rapl/intel-rapl:0/name was not package-0, but {domain_name}")

        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_name'
        with open(file_path, 'r', encoding='UTF-8') as file:
            constraint_name = file.read().strip()
            if constraint_name != 'long_term':
                raise RuntimeError(f"Constraint /sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_name was not long_term, but {constraint_name}")

        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_max_power_uw'
        with open(file_path, 'r', encoding='UTF-8') as file:
            tdp = file.read()
            data['tdp'] = int(tdp) / 1_000_000

        logger.info('Found TDP: %d W', data['tdp'])
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not read RAPL powercapping info from /sys/class/powercap/intel-rapl')

    try:
        file_paths = {
            1: '/sys/class/powercap/intel-rapl/intel-rapl:0/name',
            2: '/sys/class/powercap/intel-rapl/intel-rapl:1/name',
            3: '/sys/class/powercap/intel-rapl/intel-rapl:2/name',
            4: '/sys/class/powercap/intel-rapl/intel-rapl:3/name',
            5: '/sys/class/powercap/intel-rapl/intel-rapl:4/name',
            6: '/sys/class/powercap/intel-rapl/intel-rapl:5/name',
        }
        for chips, file_path in file_paths.items():
            with open(file_path, 'r', encoding='UTF-8') as file:
                domain_name = file.read().strip()
                if domain_name != f"package-{chips-1}":
                    raise RuntimeError(f"Domain {file_path} was not package-{chips-1}, but {domain_name}")
                logger.info('Found Sockets: %d', chips)
                data['chips'] = chips
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not find (additional) chips info under file path. Most likely reached final chip. continuing ...')


    try:
        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')
        match = re.search(r'On-line CPU\(s\) list:\s*(0-)?(\d+)', cpuinfo)
        if match:
            data['threads'] = int(match.group(2))+1 # +1 because 0 indexed
            logger.info('Found Threads: %d', data['threads'])
        else:
            logger.info('Could not find Threads. Using default None')

        # this will overwrite info we have from RAPL socket discovery, as we
        # deem lscpu more relieable
        match = re.search(r'Socket\(s\):\s*(\d+)', cpuinfo)
        if match:
            data['chips'] = int(match.group(1))
            logger.info('Found Sockets: %d (will take precedence if not 0)', data['chips'])
        else:
            logger.info('Could not find Chips/Sockets via lscpu')

        if data['threads'] and data['chips']:
            match = re.search(r'Thread\(s\) per core:\s*(\d+)', cpuinfo)
            if match:
                threads_per_core = int(match.group(1))
                data['cores'] = (data['threads'] // threads_per_core) // data['chips']
                logger.info('Derived cores: %d ', data['cores'])
            else:
                logger.info('Could not derive Cores. Using default None')

        match = re.search(r'Model name:.*@\s*([\d.]+)\s*GHz', cpuinfo)
        if match:
            data['freq'] = int(float(match.group(1))*1000)
            logger.info('Found Frequency: %s', data['freq'])
        else:
            logger.info('Could not find Frequency. Using default None')

        match = re.search(r'Model name:.*Intel\(R\)', cpuinfo)
        if match:
            data['make'] = 'intel'
            logger.info('Found Make: %s', data['make'])

        match = re.search(r'Model name:.*AMD ', cpuinfo)
        if match:
            data['make'] = 'amd'
            logger.info('Found Make: %s', data['make'])


        # we currently do not match for architecture, as this info is provided nowhere

        # we also currently do not matc for make, as this info can result in ARM which is currently not supported and
        # would rather lead to confusion
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not check for CPU info.')


    """ This code is problematic, as the CPU freq is changing rapidly sometimes and making the resulting XGBoost
    values fluctuate a lot.
    """


    # if not data['freq']:
    #     try:
    #         cpuinfo_proc = subprocess.check_output(['cat', '/proc/cpuinfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
    #         match = re.findall(r'cpu MHz\s*:\s*([\d.]+)', cpuinfo_proc)
    #         if match:
    #             data['freq'] = round(max(map(float, match)))
    #             logger.info('Found assumend Frequency: %d', data['freq'])
    #         else:
    #             logger.info('Could not find Frequency. Using default None')
    #     #pylint: disable=broad-except
    #     except Exception as err:
    #         logger.info('Exception: %s', err)
    #         logger.info('/proc/cpuinfo not accesible on system. Could not check for Base Frequency info. Setting value to None.')



    try:
        meminfo = subprocess.check_output(['cat', '/proc/meminfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.search(r'MemTotal:\s*(\d+) kB', meminfo)
        if match:
            data['mem'] = math.ceil(int(match.group(1)) / 1024 / 1024)
            logger.info('Found Memory: %d GB', data['mem'])
        else:
            logger.info('Could not find Memory. Using default None')
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('/proc/meminfo not accesible on system. Could not check for Memory info. Setting all values to None.')

    return data

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    print(get_cpu_info(logger))
