# pylint: disable=redefined-outer-name,invalid-name

import subprocess
import re
import logging

def get_cpu_info(logger):

    data = {
        'freq' : None,
        'threads': None,
        'cores': None,
        #'tdp': None,
        'mem': None,
        #'make': None,
        'chips': None
    }

    try:
        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')
        match = re.search(r'On-line CPU\(s\) list:\s*(0-)?(\d+)', cpuinfo)
        if match:
            data['threads'] = int(match.group(2))+1 # +1 because 0 indexed
            logger.info('Found Threads: %d', data['threads'])
        else:
            logger.info('Could not find Threads. Setting to None')

        match = re.search(r'Socket\(s\):\s*(\d+)', cpuinfo)
        if match:
            data['chips'] = int(match.group(1))
            logger.info('Found Sockets: %d', data['chips'])
        else:
            logger.info('Could not find Chips/Sockets. Setting to None')

        if data['threads']:
            match = re.search(r'Thread\(s\) per core:\s*(\d+)', cpuinfo)
            if match:
                threads_per_core = int(match.group(1))
                data['cores'] = (data['threads'] // threads_per_core) // data['chips']
                logger.info('Derived cores: %d ', data['cores'])
            else:
                logger.info('Could not derive Cores. Setting to None')

        # we currently do not match for architecture, as this info is provided nowhere

        # we also currently do not matc for make, as this info can result in ARM which is currently not supported and
        # would rather lead to confusion
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not check for CPU info. Setting all values to None.')



    try:
        cpuinfo_proc = subprocess.check_output(['cat', '/proc/cpuinfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.findall(r'cpu MHz\s*:\s*([\d.]+)', cpuinfo_proc)
        if match:
            data['freq'] = round(max(map(float, match)))
            logger.info('Found assumend Frequency: %d', data['freq'])
        else:
            logger.info('Could not find Frequency. Setting to None')
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('/proc/cpuinfo not accesible on system. Could not check for Base Frequency info. Setting value to None.')


    try:
        meminfo = subprocess.check_output(['cat', '/proc/meminfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.search(r'MemTotal:\s*(\d+) kB', meminfo)
        if match:
            data['mem'] = round(int(match.group(1)) / 1024 / 1024)
            logger.info('Found Memory: %d', data['mem'])
        else:
            logger.info('Could not find Memory. Setting to None')
    #pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('/proc/meminfo not accesible on system. Could not check for Memory info. Setting all values to None.')

    return data

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    get_cpu_info(logger)
