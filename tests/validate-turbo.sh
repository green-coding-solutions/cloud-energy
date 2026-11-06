#!/bin/bash

params="--cpu-chips=2 --cpu-freq=2000 --cpu-threads=224 --cpu-cores=112 --release-year=2023 --tdp=350 --ram=256 --cpu-make=intel --silent --dump"
actual_file="tmp/actual_start.txt"
expected_file="tmp/expected_start.txt"

mkdir -p tmp

# The first 11 lines are the predictions of the model at 0, 10, 20 ... 100
{
    echo "turbo yes"
    python3 ../xgb.py $params --turbo yes | head -n 11
    echo "turbo no"
    python3 ../xgb.py $params --turbo no | head -n 11
} > "$actual_file"

cat > "$expected_file" << 'EOF'
turbo yes
0.0 : 188.2284698486328
10.0 : 286.0191307067871
20.0 : 322.9798278808594
30.0 : 358.8629455566406
40.0 : 394.0746154785156
50.0 : 431.0144348144531
60.0 : 466.8782653808594
70.0 : 516.947998046875
80.0 : 582.8397827148438
90.0 : 659.6619873046875
100.0 : 714.2913818359375
turbo no
0.0 : 198.0268096923828
10.0 : 285.4599952697754
20.0 : 322.4131164550781
30.0 : 357.2528991699219
40.0 : 392.11102294921875
50.0 : 422.8811950683594
60.0 : 461.5776062011719
70.0 : 511.64739990234375
80.0 : 558.457275390625
90.0 : 594.4097290039062
100.0 : 633.9432983398438
EOF

if diff -u "$actual_file" "$expected_file"; then
    echo "Validation passed: Output matches expected start."
    exit 0
else
    echo "Validation failed: Output does not match expected start."
    exit 1
fi
