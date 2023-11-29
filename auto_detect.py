# pylint: disable=redefined-outer-name,invalid-name

import subprocess
import re

def print_custom(*args, silent=False):
    if not silent:
        print(*args)

def get_cpu_info(silent=False):

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
            print_custom('Found Threads:', data['threads'], silent=silent)
        else:
            print_custom('Could not find Threads. Setting to None', silent=silent)

        match = re.search(r'Socket\(s\):\s*(\d+)', cpuinfo)
        if match:
            data['chips'] = int(match.group(1))
            print_custom('Found Sockets:', data['chips'], silent=silent)
        else:
            print_custom('Could not find Chips/Sockets. Setting to None', silent=silent)

        if data['threads']:
            match = re.search(r'Thread\(s\) per core:\s*(\d+)', cpuinfo)
            if match:
                threads_per_core = int(match.group(1))
                data['cores'] = (data['threads'] // threads_per_core) // data['chips']
                print_custom('Derived cores: ', data['cores'], silent=silent)
            else:
                print_custom('Could not derive Cores. Setting to None', silent=silent)

        match = re.search(r'(max )?MHz:\s*(\d+)', cpuinfo)
        if match:
            data['freq'] = int(match.group(2))
            print_custom('Found Frequency:', data['freq'], silent=silent)
        else:
            print_custom('Could not find Frequency. Setting to None', silent=silent)

        # we currently do not match for architecture, as this info is provided nowhere

        # we also currently do not matc for make, as this info can result in ARM which is currently not supported and
        # would rather lead to confusion
    #pylint: disable=broad-except
    except Exception as err:
        print_custom('Exception', err, silent=silent)
        print_custom('Could not check for CPU info. Setting all values to None.', silent=silent)


    try:
        meminfo = subprocess.check_output(['cat', '/proc/meminfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.search(r'MemTotal:\s*(\d+) kB', meminfo)
        if match:
            data['mem'] = round(int(match.group(1)) / 1024 / 1024)
            print_custom('Found Memory:', data['mem'], silent=silent)
        else:
            print_custom('Could not find Memory. Setting to None', silent=silent)
    #pylint: disable=broad-except
    except Exception as err:
        print_custom('Exception', err, silent=silent)
        print_custom('/proc/meminfo not accesible on system. Could not check for Memory info. Setting all values to None.', silent=silent)

    return data

if __name__ == "__main__":
    get_cpu_info()
