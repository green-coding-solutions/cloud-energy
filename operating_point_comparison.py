# An unsolved problem is how to split the energy best in a virtualized system
# Here we want to compare three scenarios.

# We assume we have a Hetzner CX11 default machine
# https://www.hetzner.com/cloud
# 1 vCPU
# 2 GB RAM
# 2 GB disk space
#
# Hetzner claims that all their Intel CPUs are Intel Xeon Gold.
# By looking at cat /proc/cpuinfo we can see that the CPU says it is running 2.1 GHz
# We can also confirm this assumption by running NOOP loops to see if the advertised speed is accurate.
#
# Since only two CPUs according to Wikipedia have 2.1 GHz ....


# Setup 1 - Using reduced values
-  CPUChips: 1
-  HW_CPUFreq: 2100
-  CPUCores: 1
-  TDP: 125
-  HW_MemAmountGB: 2



# Setup 2 - Using full values and splitting via coefficient


# Setup 3 - Using operating point movement - Shiftingto 50% load


=> Then move correct code to cloud server. Use vHost Ratio here
==> Compare with code when I estimate my local machine where I can read from the power plug, and assume I am 100% on one core for 4 tenants



