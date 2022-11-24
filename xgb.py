import sys, os
import statsmodels.formula.api as smf
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

def train_model(cpu_chips, Z, silent=False):

    df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/data/spec_data_cleaned.csv")

    X = df.copy()
    X = pd.get_dummies(X, columns=["CPUMake", "Architecture"])

    if not silent:
        print("Model will be restricted to the following amount of chips:", cpu_chips)

    X = X[X.CPUChips == cpu_chips] # Fit a model for every amount of CPUChips
    y = X.power

    X = X[Z.columns] # only select the supplied columns from the command line

    if not silent:
        print("Model will be trained on:", X.columns)

    params = {'max_depth': 5, 'learning_rate': 0.4411788445980461, 'n_estimators': 469, 'min_child_weight': 2, 'gamma': 0.609395982216471, 'subsample': 0.7563030757274138, 'colsample_bytree': 0.8176008707736587, 'reg_alpha': 0.08305234496497138, 'reg_lambda': 0.930233948796124, 'random_state': 296}

    model = XGBRegressor(**params)
    model.fit(X,y)

    return model

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--cpu-chips", type=int, help="Number of CPU chips", default=1)
    parser.add_argument("--cpu-freq", type=int, help="CPU frequency")
    parser.add_argument("--cpu-cores", type=int, help="Number of CPU cores")
    parser.add_argument("--release-year", type=int, help="Release year of the CPU")
    parser.add_argument("--tdp", type=int, help="TDP of the CPU")
    parser.add_argument("--ram", type=int, help="Amount of DRAM for the bare metal system")
    parser.add_argument("--architecture", type=str, help="The architecture of the CPU. lowercase. ex.: haswell")
    parser.add_argument("--cpu-make", type=str, help="The make of the CPU (intel or amd)")
    parser.add_argument("--vhost-ratio", type=float, help="Virtualization ratio of the system. Input numbers between (0,1].", default=1.0)
    parser.add_argument("--debug", action='store_true', help="Activate debug mode (currently unused)")
    parser.add_argument("--silent", action="store_true", help="Will suppress all debug output. Typically used in production.")
    args = parser.parse_args()

    Z = pd.DataFrame.from_dict({
        'HW_CPUFreq' : [args.cpu_freq],
        'CPUCores': [args.cpu_cores],
        'TDP': [args.tdp],
        'Hardware_Availability_Year': [args.release_year],
        'HW_MemAmountGB': [args.ram],
        'Architecture': [args.architecture],
        'CPUMake': [args.cpu_make],
        'utilization': [0]
    })

    Z = pd.get_dummies(Z, columns=["CPUMake", "Architecture"])

    Z = Z.dropna(axis=1)

    model = train_model(args.cpu_chips, Z, args.silent)

    if not args.silent:
        print("Sending following dataframe to model:\n", Z)
        print("vHost ratio is set to ", args.vhost_ratio)

    for line in sys.stdin:
        Z['utilization'] = float(line.strip())
        y_pred_default = model.predict(Z)
        print(y_pred_default[0] * args.vhost_ratio)
