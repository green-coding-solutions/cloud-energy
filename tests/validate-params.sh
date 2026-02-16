#!/bin/bash

# Run xgb.py with --dump and capture output
output=$(python3 ../xgb.py --cpu-chips=2 --cpu-freq=3300 --cpu-threads=48 --cpu-cores=24 --release-year=2019 --tdp=165 --ram=384 --architecture="cascadelake" --cpu-make="intel" --vhost-ratio=0.04167 --dump-hashmap)
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
cloud_energy_hashmap[0.00]=3.5727148155212403
cloud_energy_hashmap[5.00]=3.5727148155212403
cloud_energy_hashmap[10.00]=4.623978795776367
cloud_energy_hashmap[15.00]=5.675242776031494
cloud_energy_hashmap[20.00]=6.075715027313232
cloud_energy_hashmap[25.00]=6.476187278594971
cloud_energy_hashmap[30.00]=6.840004668502807
cloud_energy_hashmap[35.00]=7.203822058410644
cloud_energy_hashmap[40.00]=7.323876688156128
cloud_energy_hashmap[45.00]=7.443931317901611
cloud_energy_hashmap[50.00]=8.49183650642395
cloud_energy_hashmap[55.00]=9.539741694946288
cloud_energy_hashmap[60.00]=10.57221424484253
cloud_energy_hashmap[65.00]=11.60468679473877
cloud_energy_hashmap[70.00]=12.364932851257324
cloud_energy_hashmap[75.00]=13.12517890777588
cloud_energy_hashmap[80.00]=13.871673152160644
cloud_energy_hashmap[85.00]=14.61816739654541
cloud_energy_hashmap[90.00]=15.032332327423095
cloud_energy_hashmap[95.00]=15.44649725830078
cloud_energy_hashmap[100.00]=16.845166170043946
cloud_energy_hashmap[105.00]=16.845165252685547
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
