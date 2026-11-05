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
cloud_energy_hashmap[5.00]=4.6573012525177
cloud_energy_hashmap[10.00]=5.926354343605041
cloud_energy_hashmap[15.00]=7.195407434692383
cloud_energy_hashmap[20.00]=7.574721682434082
cloud_energy_hashmap[25.00]=7.954035930175781
cloud_energy_hashmap[30.00]=8.588971873168944
cloud_energy_hashmap[35.00]=9.223907816162109
cloud_energy_hashmap[40.00]=9.672066326293946
cloud_energy_hashmap[45.00]=10.12022483642578
cloud_energy_hashmap[50.00]=10.304246565856934
cloud_energy_hashmap[55.00]=10.488268295288085
cloud_energy_hashmap[60.00]=11.158043476409912
cloud_energy_hashmap[65.00]=11.827818657531738
cloud_energy_hashmap[70.00]=12.944305827026367
cloud_energy_hashmap[75.00]=14.060792996520995
cloud_energy_hashmap[80.00]=14.917622198181151
cloud_energy_hashmap[85.00]=15.774451399841308
cloud_energy_hashmap[90.00]=15.677484211120605
cloud_energy_hashmap[95.00]=15.580517022399901
cloud_energy_hashmap[100.00]=16.24188457397461
cloud_energy_hashmap[105.00]=16.241884231567383
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
