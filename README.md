# Overview

This repository containes the needed data to train a Linear Model for the [SPECPower
data set](https://www.spec.org/power_ssj2008/).

The model is built as an OLS model with dynamic variables designed to work 
in different cloud environments where some information may not be available.

Its use is the estimation of the current power draw of the whole machine in 
Watts.

Currently the model supports following variables:
- CPU Utilization `[float [0-100]]`
    + The utilization of all your assigned cores cumulative and normalized to 0-100
- CPU Chips `[integer [1,)]`
    + The CPU chips installed on the mainboard. Most machines have either 1 or 2.
    + If you do not know this value rather leave it off.
- RAM `[integer (0,]]`
    * in Gigabytes
- TDP `[integer (0,]]`
    + In Watts
    + The thermal design power of the CPU in your system. This value you typically find only on the data sheet online.
- vHost Ratio `[float (0,1])`
    + The vHost ratio on the system you are on. If you are on a bare metal machine this is 1
    + If you are a guest and have e.g. 24 of the 96 Threads than the ratio would be 0.25

Only the CPU Utilization parameter is mandatory. All other paramters are optional
vHost ratio is assumed to be 1 if not given.

You are free to supply only the utilization or as many additional parameters that
the model supports. The model will then be retrained on the new configuration on the spot.

Typically the model gets more accurate the more parameters you can supply.

# Background

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

# Discovery of the parameters

At least utilization is needed as an input parameter.

You need some small script that streams the CPU utilization as pure float numbers
line by line.

The solution we are using is a modified version of our [CPU Utilization reporter
from the Green Metrics Tool](https://github.com/green-coding-berlin/green-metrics-tool/tree/dev/tools/metric_providers/cpu/utilization/procfs/system).

This one is tailored to read from the procfs. You might need something different in your case ...

## Hyperthreading

HT can be easily checked if the core-id is similar to the processor id.

Last Core-ID should be processor_id+1
If Last core ID is > processor_id+2  then HT is enabled

Alternatively looking at `lscpu` might reveal some infos.

## SVM / VT-X / VT-D / AMD-V ...
The presence of virtualization can be checked by looking at:

`/dev/kvm`

If that directory is present this is a strong indicator, that virtualization is enabled.

One can also install cpu-checker and then run 
`sudo apt install kvm-ok -y && sudo kvm-ok`

This will tell with more checks if virtualization is on. even on AMD machines.

However in a vHost this might not work at all, as the directory is generally hidden.

Here it must be checked if a virtualization is already running through:
`sudo apt install virt-what -y && sudo virt-what`

Also `lscpu` might provide some insights by having these lines:

```
Virtualization features:
  Hypervisor vendor:     KVM
  Virtualization type:   full
```  

## Hardware prefetchers

There are actually many to disable:
The above mentioned processors support 4 types of h/w prefetchers for prefetching data. There are 2 prefetchers associated with L1-data cache (also known as DCU DCU prefetcher, DCU IP prefetcher) and 2 prefetchers associated with L2 cache (L2 hardware prefetcher, L2 adjacent cache line prefetcher).

There is a Model Specific Register (MSR) on every core with address of 0x1A4 that can be used to control these 4 prefetchers. Bits 0-3 in this register can be used to either enable or disable these prefetchers. Other bits of this MSR are reserved.

However it seems that for some processors this setting is only available in the BIOS
as it is not necessary disclosed info by Intel how to disable it.
For servers it seems quite standard to do be an available feature apparently ...

https://stackoverflow.com/questions/54753423/correctly-disable-hardware-prefetching-with-msr-in-skylake
https://stackoverflow.com/questions/55967873/how-can-i-verify-that-my-hardware-prefetcher-is-disabled
https://stackoverflow.com/questions/784041/how-do-i-programmatically-disable-hardware-prefetching
https://stackoverflow.com/questions/19435788/unable-to-disable-hardware-prefetcher-in-core-i7
https://stackoverflow.com/questions/784041/how-do-i-programmatically-disable-hardware-prefetching


## Other variables
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

# Model Details / EDA

- Model uses SPECPower raw data
    + Current copy is stored in `./data/raw`
    + We only process the html data. It contains the same info as the text
    + Look into `./scripts/create_data_csv.py`
    + Unprocessed version is then in `./data/spec_data.csv`
- CPU microarchitecture and TDP data is coming from
    + David Mytton [Cloud carbon coefficients](https://github.com/cloud-carbon-footprint/cloud-carbon-coefficients) (only AMD Epyc info)
    + Wikipedia (very! thorough source)
- Data is cleaned. Look into `./scripts/data_cleaning.py`
    + Cleaned and enriched version is then in `./data/spec_data_cleaned.csv`

The EDA is currently only on Kaggle, where you can see how we selected the subset of the 
available variables and their interaction in our [Kaggle notebook](https://www.kaggle.com/code/arne3000/spec-power-eda-pass-2)

In order to create some columns we inspected the `SUT_BIOS` and `SUT_Notes` fields
and created some feature columns dervied from them. Here is a quick summary:

- *BIOS_P_States_Enabled*
    + P-states are a power feature. P-State = 1 is the base frequency
    + Setting P-states to off will set P-State to max non-turbo (aka 1) (https://www.thomas-krenn.com/en/wiki/Disable_CPU_Power_Saving_Management_in_BIOS)
    + All P-States greater than 1 are power efficient states: https://www.thomas-krenn.com/en/wiki/Processor_P-states_and_C-states

- *BIOS_Memory_Setting_Changed*
    + When we found infos like "DDR Frequency set to 1066 MHz" we considered this memory tuning

- *BIOS_HT_Enabled*
    + We found Hyperthreading mostly not mentioned, but when than turned on. Which should be the default anyway.
    
- *BIOS_VT_Enabled*
    + Virtualization was sometimes disabled, which is also very often the default
    + However we believe it is almost always on in cloud environments, as it is for instance a prerequiste for KVM (EC2 hypervisor)
    + Includes SVM from AMD
   
- *BIOS_Turbo_Boost_Enabled*
    + Turbo Boost was very often turned off, which is a clear sign of tuning
    + Turbo Boost is almost always on by default
   
- *BIOS_C_States_Enabled*
    + C-States are a power saving feature. If they are fixed to a certain state this could well be considered tuning, as this is non default and very untypical for the cloud
   
- *BIOS_Prefetchers_Enabled*
    + Prefetchers like DCU Prefetcher, Adjacent Cache Line Prefetch, MLC Spatial Prefetcher etc. are almost always on by default
    + Most systems however have these disabled.
    + We do not know the typical state in the cloud here.

## Unclear data in SUT_BIOS / SUT_Notes

Some info we thought might be related to energy, but we could not make sense of them.
If you can, please share and create and create a Pull Request:

- The cores were mostly fixed to a JVM instance: *Each JVM instance was affinitized two logical processors on a single socket.*
    + We do not know if this optimizing for the benchmark or a SPECPower requirement.
    + Therefore not processed further

- We found however settings with TurboBoost on and then the *Maximum Processor State: 100%.* was set. 
    + We are not exactly sure what that means, but it could indicate that TurboBoost although enabled could never be executed ...

- We found settings like *SATA Controller = Disabled*
    + This setting was mostly set cause the machines were running on PCIe / M2 disks

- *Set "Uncore Frequency Override = Power balanced" in BIOS.* or *Power Option: Power Saver* or *"Power Mode: Balanced"*
    + Unsure what does translates to really since "power balanced" has no defined meaning and changes for every vendor.
    + Balanced might for instance include TurboBoost On for one vendor and Off for another

- *DEMT -enabled.*
    + Dynamic energy management
    + Ignored cause we do not know how this really affects energy consumption

- *Memory Data Scrambling: Disable* / *Set "Memory Patrol Scrub = Disabled"*
    + Ignored cause we do not know how this really affects energy consumption

- *EIST* is sometimes enabled and sometimes not. Although it can be a power saving feature it alone says nothing about power itself.
    + We believe this column holds no information on its own

- ASPM Support - Power saving for PCIe
    + Ignored cause we do not know how this really affects energy consumption

-  'USB Front Port Disabled.',
    + Ignored cause we do not know how this really affects energy consumption
    + Also we believe this is cloud standard

- *CPU Power Management set to DAPC*
    + Dell only feature for energy. Did not look into further

- *EfficiencyModeEn = Enabled*
    + Too few entries with feature

- *SGX enabled / disabled* 
    + is also very curious ... unclear what the cloud setting is

# Results

We have first compared the model against a machine from SPECPower that we 
did not include in the model training: [Hewlett Packard Enterprise Synergy 480 Gen10 Plus Compute Module](https://www.spec.org/power_ssj2008/results/res2022q1/power_ssj2008-20211207-01142.html)

This machine is comprised of 10 identical nodes, therefore the power values
have to be divided by 10 to get the approximate value that would have resulted 
if only one node was tested individually.

An individual node has the following characteristics as model parameters:
- --cpu-freq 2300 
- --tdp 270 
- --ram 256 
- --cpu-cores 80 
- --cpu-chips 2

![hp_synergy_480_Gen10_Plus.png](/img/hp_synergy_480_Gen10_Plus.png)


This is the comparison chart:

Secondly we have bought a machine from the SPECPower dataset: [FUJITSU Server PRIMERGY RX1330 M3](https://www.spec.org/power_ssj2008/results/res2017q2/power_ssj2008-20170315-00744.html)

The machine has the following characteristics as model parameters:
- --cpu-freq 3500
- --tdp 24 
- --ram 16
- --cpu-cores 4
- --cpu-chips 1

This is the comparison chart for the SPEC data vs our modelling:
![fujitsu_TX1330_SPEC.png](/img/fujitsu_TX1330_SPEC.png)


This is the comparison chart where we compare the standard BIOS setup against the *tuning* settings from SPECPower:
![fujitsu_TX1330_measured.png](/img/fujitsu_TX1330_measured.png)

## Summary
TODO

# Installation

Tested on python-3.10 but should work on older versions.

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

# Use
You must call the python file `linear_model.py` or `xgboost_model.py`. 
This file is designed to accept streaming inputs.

A typical call with a streaming binary that reports CPU Utilization could look like
so: 
```
$ ./static-binary | python3 linear_model.py --tdp 240 
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

# Demo reporter

If you want to use the demo reporter to read the CPU utilization there is a C reporter
in the `demo-reporter` directory.

Compile it with `gcc cpu-utilization.c`

Then run it with `./a.out`

Or feed it directly to the model with: `./a.out | python3 model.py --tdp ....`


# TODO

- vhost operating point
- validation of EC2 machines and the data from Teads. 
- Performance optimizations for inline processing to get below 2% of utilization for 100ms intervals


## Credits

A similar model has been developed in academia from [Interact DC](https://interactdc.com/) and the 
paper can be downloaded on [their official resources site](https://interactdc.com/static/images/documents/Elsevier_Journal.pdf).

Our model was initially developed idependently but we have taken some inspiration 
from the paper to tune the model afterwards.

A big thank you to [Rich Kenny](https://twitter.com/bigkatrich) from Interact DC to providing some insights to
parameters and possible pitfalls during our model development.