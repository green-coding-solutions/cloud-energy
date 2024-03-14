# pylint: disable=redefined-outer-name,invalid-name

import subprocess
import re
import logging
import math
import platform


class CPUInfo:
    def __init__(self, chips: int = None, cores: int = None, threads: int = None, freq: int = None, tdp: int = None, mem: int = None, make: str = None, architecture: str = None, release_year: str = None):
        # Chip count
        self.chips = chips
        # Core count
        self.cores = cores
        # Thread count
        self.threads = threads
        # Frequency in Mhz
        self.freq = freq
        # TDP in W
        self.tdp = tdp
        # Memory in GB
        self.mem = mem
        # make
        self.make = make
        # architecture
        self.architecture = architecture
        # release year
        self.release_year = release_year

    def __str__(self) -> str:
        return f'CPUInfo(chips={self.chips}, cores={self.cores}, threads={self.threads}, freq={self.freq}, tdp={self.tdp}, mem={self.mem}, make={self.make})'


def get_cpu_info_linux(logger):
    data = CPUInfo()

    try:
        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/name'
        with open(file_path, 'r', encoding='UTF-8') as file:
            domain_name = file.read().strip()
            if domain_name != 'package-0':
                raise RuntimeError(
                    f"Domain /sys/class/powercap/intel-rapl/intel-rapl:0/name was not package-0, but {domain_name}")

        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_name'
        with open(file_path, 'r', encoding='UTF-8') as file:
            constraint_name = file.read().strip()
            if constraint_name != 'long_term':
                raise RuntimeError(
                    f"Constraint /sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_name was not long_term, but {constraint_name}")

        file_path = '/sys/class/powercap/intel-rapl/intel-rapl:0/constraint_0_max_power_uw'
        with open(file_path, 'r', encoding='UTF-8') as file:
            tdp = file.read()
            data.tdp = int(tdp) / 1_000_000

        logger.info('Found TDP: %d W', data.tdp)
    # pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            'Could not read RAPL powercapping info from /sys/class/powercap/intel-rapl')

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
                    raise RuntimeError(
                        f"Domain {file_path} was not package-{chips-1}, but {domain_name}")
                logger.info('Found Sockets: %d', chips)
                data.chips = chips
    # pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            'Could not find (additional) chips info under file path. Most likely reached final chip. continuing ...')

    try:
        cpuinfo = subprocess.check_output('lscpu', encoding='UTF-8')
        match = re.search(r'On-line CPU\(s\) list:\s*(0-)?(\d+)', cpuinfo)
        if match:
            data.threads = int(match.group(2))+1  # +1 because 0 indexed
            logger.info('Found Threads: %d', data.threads)
        else:
            logger.info('Could not find Threads. Using default None')

        # this will overwrite info we have from RAPL socket discovery, as we
        # deem lscpu more relieable
        match = re.search(r'Socket\(s\):\s*(\d+)', cpuinfo)
        if match:
            data.chips = int(match.group(1))
            logger.info(
                'Found Sockets: %d (will take precedence if not 0)', data.chips)
        else:
            logger.info('Could not find Chips/Sockets via lscpu')

        if data.chips:
            match = re.search(r'Core\(s\) per socket:\s*(\d+)', cpuinfo)
            if match:
                cores_per_socket = int(match.group(1))
                data.cores = cores_per_socket * data.chips
                logger.info('Found cores: %d ', data.cores)
            else:
                logger.info('Could not find Cores. Using default None')

        match = re.search(r'Model name:.*@\s*([\d.]+)\s*GHz', cpuinfo)
        if match:
            data.freq = int(float(match.group(1))*1000)
            logger.info('Found Frequency: %s', data.freq)
        else:
            logger.info('Could not find Frequency. Using default None')

        match = re.search(r'Model name:.*Intel\(R\)', cpuinfo)
        if match:
            data.make = 'intel'
            logger.info('Found Make: %s', data.make)

        match = re.search(r'Model name:.*AMD ', cpuinfo)
        if match:
            data.make = 'amd'
            logger.info('Found Make: %s', data.make)

        # we currently do not match for architecture, as this info is provided nowhere

        # we also currently do not matc for make, as this info can result in ARM which is currently not supported and
        # would rather lead to confusion
    # pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info('Could not check for CPU info.')

    """ This code is problematic, as the CPU freq is changing rapidly sometimes and making the resulting XGBoost
    values fluctuate a lot.
    """

    # if not data.freq:
    #     try:
    #         cpuinfo_proc = subprocess.check_output(['cat', '/proc/cpuinfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
    #         match = re.findall(r'cpu MHz\s*:\s*([\d.]+)', cpuinfo_proc)
    #         if match:
    #             data.freq = round(max(map(float, match)))
    #             logger.info('Found assumend Frequency: %d', data.freq)
    #         else:
    #             logger.info('Could not find Frequency. Using default None')
    #     #pylint: disable=broad-except
    #     except Exception as err:
    #         logger.info('Exception: %s', err)
    #         logger.info('/proc/cpuinfo not accesible on system. Could not check for Base Frequency info. Setting value to None.')

    try:
        meminfo = subprocess.check_output(
            ['cat', '/proc/meminfo'], encoding='UTF-8', stderr=subprocess.DEVNULL)
        match = re.search(r'MemTotal:\s*(\d+) kB', meminfo)
        if match:
            data.mem = math.ceil(int(match.group(1)) / 1024 / 1024)
            logger.info('Found Memory: %d GB', data.mem)
        else:
            logger.info('Could not find Memory. Using default None')
    # pylint: disable=broad-except
    except Exception as err:
        logger.info('Exception: %s', err)
        logger.info(
            '/proc/meminfo not accesible on system. Could not check for Memory info. Defaulting to None.')

    return data


def get_cpu_make():
    processor_name = platform.processor().lower()
    if 'intel' in processor_name:
        return 'intel'
    elif 'amd' in processor_name:
        return 'amd'
    else:
        return 'unknown'


def get_cpu_info(logger):
    if platform.system() == 'Linux':
        return get_cpu_info_linux(logger)
    else:
        import psutil

        logger.info('Gathering CPU info')
        chips = 1  # TODO: find a way to get this info
        freq = int(psutil.cpu_freq().max)
        threads = psutil.cpu_count(logical=True)
        cores = psutil.cpu_count(logical=False)
        tdp = 0  # TODO: find a way to get this info
        mem = math.ceil(psutil.virtual_memory().total / 1024 / 1024 / 1024)
        make = get_cpu_make()

        # write summary to logger
        logger.info('CPU info for: %s', platform.processor())
        logger.info('Found # of chips: %d', chips)
        logger.info('Found # of cores: %d', cores)
        logger.info('Found # of threads: %d', threads)
        logger.info('Found frequency: %d Mhz', freq)
        logger.info('Found TDP: %d W', tdp)
        logger.info('Found memory: %d GB', mem)
        logger.info('Found make: %s', make)

        # return CPU info
        return CPUInfo(
            chips=chips,
            freq=freq,
            threads=threads,
            cores=cores,
            make=make,
            tdp=tdp,
            mem=mem
        )


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    print(get_cpu_info(logger))
