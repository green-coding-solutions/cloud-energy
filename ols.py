#pylint: disable=invalid-name

import sys
import statsmodels.formula.api as smf
import pandas as pd

def train_model(cpu_chips, ram, tdp, cpu_cores):

    df = pd.read_csv("./data/spec_data_cleaned.csv")

    formula = "power ~ utilization"

    if cpu_cores is not None:
        formula = f"{formula} + CPUCores"

    if cpu_chips is not None:
        formula = f"{formula}*C(CPUChips)"

    if ram is not None:
        formula = f"{formula} + HW_MemAmountGB"

    if tdp is not None:
        formula = f"{formula} + TDP"

    return smf.ols(formula=formula, data=df).fit()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--cpu-chips", type=float, help="Number of CPUChips")
    parser.add_argument("--cpu-cores", type=float, help="Number of CPUCores")
    parser.add_argument("--cpu-freq",
        type=float,
        help="CPU frequency. (Not used. Only for compatibility with XGBoost model)"
    )
    parser.add_argument("--tdp", type=float, help="TDP of the CPU")
    parser.add_argument("--ram", type=float, help="Amount of RAM for the bare metal system")
    parser.add_argument("--vhost-ratio",
        type=float,
        help="Virtualization ratio of the system. Input numbers between (0,1].",
        default=1.0
    )
    parser.add_argument("--silent",
        action="store_true",
        help="Will suppress all debug output. Typically used in production."
    )

    args = parser.parse_args()

    model = train_model(args.cpu_chips, args.ram, args.tdp, args.cpu_cores)
    my_data = pd.DataFrame.from_dict({
        "utilization": 0,
        "CPUChips": [args.cpu_chips],
        "CPUCores": [args.cpu_cores],
        "HW_MemAmountGB": [args.ram],
        "TDP" : [args.tdp]
    })

    # Drop all arguments that were not supplied
    my_data = my_data.dropna(axis=1)

    if not args.silent:
        print("Sending following dataframe to model", my_data)
        print("vHost ratio is set to ", args.vhost_ratio)


    for line in sys.stdin:
        my_data['utilization'] = float(line.strip())
        print(model.predict(my_data)[0] * args.vhost_ratio)
