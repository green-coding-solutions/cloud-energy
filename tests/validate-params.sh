#!/bin/bash

# Run xgb.py with --dump and capture output
output=$(python3 ../xgb.py --cpu-chips=2 --cpu-freq=3300 --cpu-threads=48 --cpu-cores=24 --release-year=2019 --tdp=165 --ram=384 --cpu-make="intel" --vhost-ratio=0.04167 --dump-hashmap)
exit_code=$?
output_file="tmp/output.txt"
expected_file="tmp/expected_start.txt"

mkdir -p tmp

# Save output to a file
echo "$output" > "$output_file"
echo "Output saved to $output_file"

# Exit if xgb.py failed
if [ $exit_code -ne 0 ]; then
    echo "Error: xgb.py failed with exit code $exit_code"
    exit $exit_code
fi

# Expected start of the output (save to a file for diff)
cat > "$expected_file" << 'EOF'
#!/usr/bin/env bash
set -eu
declare -A cloud_energy_hashmap
cloud_energy_hashmap[0.00]=4.6573012525177
cloud_energy_hashmap[10.00]=7.195407474431991
cloud_energy_hashmap[20.00]=7.954035930175781
cloud_energy_hashmap[30.00]=9.223907816162109
cloud_energy_hashmap[40.00]=10.12022483642578
cloud_energy_hashmap[50.00]=10.488268295288085
cloud_energy_hashmap[60.00]=11.827818657531738
cloud_energy_hashmap[70.00]=14.060792996520995
cloud_energy_hashmap[80.00]=15.774451399841308
cloud_energy_hashmap[90.00]=15.580517022399901
cloud_energy_hashmap[100.00]=16.24188457397461
cloud_energy_hashmap[0.01]=4.659839358739614
cloud_energy_hashmap[0.02]=4.662377464961528
cloud_energy_hashmap[0.03]=4.664915571183443
cloud_energy_hashmap[0.04]=4.667453677405358
cloud_energy_hashmap[0.05]=4.669991783627271
cloud_energy_hashmap[0.06]=4.672529889849185
cloud_energy_hashmap[0.07]=4.6750679960711
cloud_energy_hashmap[0.08]=4.677606102293015
cloud_energy_hashmap[0.09]=4.680144208514929
cloud_energy_hashmap[0.10]=4.682682314736843
cloud_energy_hashmap[0.11]=4.685220420958757
EOF

# Extract the first 30 lines of the actual output for comparison
head -n 25 "$output_file" > tmp/actual_start.txt

# Use diff to compare
if diff -u tmp/actual_start.txt "$expected_file"; then
    echo "Validation passed: Output matches expected start."
    exit 0
else
    echo "Validation failed: Output does not match expected start."
    echo "Diff:"
    diff -u tmp/actual_start.txt "$expected_file"
    exit 1
fi
