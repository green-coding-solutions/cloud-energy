# Overview

This repository containes the needed data to train a Linear Model for the [SPECPower
data set](https://www.spec.org/power_ssj2008/).

The model is built as an OLS model with dynamic variables designed to work 
in different cloud environments where some information may not be available.

Its use is the estimation of the current power draw of the whole machine in 
Watts.

Currently the model supports following variables:
- CPU Utilization `[float 0-100]`
    + The utilization of all your assigned cores cumulative and normalized to 0-100
- CPU Chips `[integer (1,)]`
    + The CPU chips installed on the mainboard. Most machines have either 1 or 2.
    + If you do not know this value rather leave it off.
- RAM `[integer (0,]]`
- TDP `[integer (0,]]`
    + The thermal design power of the CPU in your system. This value you typically find only on the data sheet online.
- vHost Ratio `[float (0,1])`
    + The vHost ratio on the system you are on. If you are on a bare metal machine this is 1
    + If you are a guest and have e.g. 24 of the 96 Threads than the ratio would be 0.25

Only the CPU Utilization parameter is mandatory. All other paramters are optional
vHost ratio is assumed to be 1 if not given.

You are free to supply only the utilization or as many additional parameters that
the model supports. The model will then be retrained on the new configuration on the spot.

Typically the model gets more accurate the more parameters you can supply.

## Background

Typically in the cloud, especially when virtualized, it is not posssible to 
access any energy metrics either from the [ILO](https://en.wikipedia.org/wiki/HP_Integrated_Lights-Out) / [IDRAC](https://en.wikipedia.org/wiki/Dell_DRAC) 
controllers or from [RAPL](https://en.wikipedia.org/wiki/Perf_(Linux)#RAPL).

Therfore power draw must be estimated.

Many approaches like this have been made so far:
- https://www.cloudcarbonfootprint.org/
- https://greenpixie.com/
- https://medium.com/teads-engineering/evaluating-the-carbon-footprint-of-a-software-platform-hosted-in-the-cloud-e716e14e060c#3bf5

Cloud Carbon Footprint and Teads operate on Billing data and are too coarse 
for a fast paced development that pushes changing code on a daily basis.

Teads could theoretically solve this, but is strictily limited to AWS EC2. Also
it provides no interface out of the box to inline monitor the emissions.

Therefore we created a model out of the SPECPower dataset that also can be used
in real-time.

### Discovery of the parameters

At least utilization is needed as an input parameter.

You need some small script that streams the CPU utilization as pure float numbers
line by line.

The solution we are using is a modified version of our [CPU Utilization reporter
from the Green Metrics Tool](https://github.com/green-coding-berlin/green-metrics-tool/tree/dev/tools/metric_providers/cpu/utilization/procfs/system).

This one is tailored to read from the procfs. You might need something different in your case ...

Other variables to be discovered like CPU Make etc. can be found in these locations typically:

- `/proc/stat`
- `/proc/memory`
- `/proc/cpuinfo`
- `/sys/devices/virtual/dmi`
- `dmidecode`
- `lspci`
- `lshw`
- `/var/log/dmesg`

Informations like the vHost-Ratio you can sometimes see in `/proc/stat`, but this
info is usually given in the machine selector of your cloud provider.

If you cannot find out specific parameters the best thing is: Write an email to your cloud provider and ask :)

### Model Details

- Model uses SPECPower raw data
    + Current copy is stored in `./data/raw`
    + We only process the html data. It contains the same info as the text
    + Look into `./scripts/create_data_csv.py`
    + Unprocessed version is then in `./data/spec_data.csv`
- CPU microarchitecture and TDP data is coming from
    + David Mytton [Cloud carbon coefficients](https://github.com/cloud-carbon-footprint/cloud-carbon-coefficients) (only AMD Epyc info)
    + Wikipedia (very! through source)
- Data is cleaned. Look into `./scripts/data_cleaning.py`
    + Cleaned and enriched version is then in `./data/spec_data_cleaned.csv`

The EDA is currently only on Kaggle, where you can see how we selected the subset of the 
available variables and their interaction in our [Kaggle notebook](https://www.kaggle.com/arne3000/specpower-eda)

## Installation
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Use
You must call the python file `model.py`. This file is designed to accept 
streaming inputs.

A typical call with a streaming binary that reports CPU Utilization could look like
so: 
```
$ ./static-binary | python3 model.py --tdp 240 
191.939294374113
169.99632303510703
191.939294374113
191.939294374113
191.939294374113
191.939294374113
194.37740205685841
191.939294374113
169.99632303510703
191.939294374113
....
```

The model currently is not performance optimized and should not be called more 
often than with a 500 ms interval to stay below a 2% CPU utilization on a single
core.

Calling it with 100ms intervals will incur around a 7-8% utilization in our testings
on an Intel Skylake processor in the cloud.




