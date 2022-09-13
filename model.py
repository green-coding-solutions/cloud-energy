import sys
import statsmodels.formula.api as smf
import pandas as pd
def train_model(cpu_chips, ram, tdp):

    df = pd.read_csv("./data/spec_data_cleaned.csv")

    formula = "power ~ utilization"

    if args.cpu_chips is not None:
        formula = f"{formula}*C(CPUChips)"

    if args.ram is not None:
        formula = f"{formula} + C(HW_MemAmountGB)"

    if args.tdp is not None:
        formula = f"{formula} + TDP"

    return smf.ols(formula=formula, data=df).fit()

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()

    parser.add_argument("--cpu-chips", type=float, help="Number of CPUChips")
    #parser.add_argument("--cpu-cores", type=float, help="Number of CPUCores")
    #parser.add_argument("--cpu-make", type=str, help="Make of the CPU")
    parser.add_argument("--tdp", type=float, help="TDP of the CPU")
    parser.add_argument("--ram", type=float, help="Amount of RAM for the bare metal system")
    parser.add_argument("--vhost-ratio", type=float, help="Virtualization ratio of the system. Input numbers between (0,1].")

    parser.add_argument("--debug", action='store_true', help="Activate debug mode (currently unused)")
    parser.add_argument("--silent", action="store_true", help="Will suppress all debug output. Typically used in production.")

    args = parser.parse_args()


    if args.cpu_chips is None and args.cpu_cores is None and args.tdp is None and args.ram is None:
        parser.print_help()
        print("Please supply at least one argument for the model to predict on")
        exit(2)

    model = train_model(cpu_chips = args.cpu_chips, ram = args.ram, tdp = args.tdp)
    my_data = pd.DataFrame.from_dict({
        "utilization": 0,
        "CPUChips": [args.cpu_chips],
        "HW_MemAmountGB": [args.ram],
        "TDP" : [args.tdp]
    })

    my_data = my_data.dropna(axis=1) # Drop all arguments that were not supplied

    if not args.silent: print("Sending following dataframe to model", my_data)

    for line in sys.stdin:
        my_data['utilization'] = float(line.strip())
        print(model.predict(my_data)[0])


