#!/bin/bash

params="--cpu-chips=2 --cpu-freq=2000 --cpu-threads=224 --cpu-cores=112 --release-year=2023 --tdp=350 --ram=256 --cpu-make=intel --silent --dump"
actual_file="tmp/actual_start.txt"
expected_file="tmp/expected_start.txt"

mkdir -p tmp

# The first 11 lines are the predictions of the model at 0, 10, 20 ... 100
{
    for flag in "--form-factor 2U" "--vendor hpe" "--power-profile power-saver"; do
        echo "$flag"
        python3 ../xgb.py $params $flag 2>/dev/null | head -n 11
    done
} > "$actual_file"

cat > "$expected_file" << 'EOF'
--form-factor 2U
0.0 : 184.95521545410156
10.0 : 285.07657051086426
20.0 : 325.63836669921875
30.0 : 361.5328674316406
40.0 : 399.64569091796875
50.0 : 435.9176330566406
60.0 : 477.0279235839844
70.0 : 533.1035766601562
80.0 : 613.193115234375
90.0 : 694.9983520507812
100.0 : 755.9241943359375
--vendor hpe
0.0 : 192.1084442138672
10.0 : 286.5699806213379
20.0 : 323.99432373046875
30.0 : 357.477294921875
40.0 : 390.72698974609375
50.0 : 426.0078430175781
60.0 : 462.5207824707031
70.0 : 514.637939453125
80.0 : 576.7301635742188
90.0 : 648.5735473632812
100.0 : 701.2958984375
--power-profile power-saver
0.0 : 188.2540740966797
10.0 : 284.50854682922363
20.0 : 321.3250732421875
30.0 : 355.1532897949219
40.0 : 387.6937255859375
50.0 : 423.5396728515625
60.0 : 453.531982421875
70.0 : 499.5248718261719
80.0 : 556.710693359375
90.0 : 618.6759033203125
100.0 : 685.1058349609375
EOF

if diff -u "$actual_file" "$expected_file"; then
    echo "Validation passed: Output matches expected start."
    exit 0
else
    echo "Validation failed: Output does not match expected start."
    exit 1
fi
