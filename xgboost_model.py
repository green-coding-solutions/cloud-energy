import sys
import statsmodels.formula.api as smf
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

def drop_unneeded_columns(df):
    ## Test/Meta Related Columns
    df = df.drop(columns=['Test_Sponsor', 'SPEC_License', 'Test_Method', 'Tested_By', 'Test_Location',
                     'Test_Date', 'Publication', 'SW_WorkloadVersion', 'SW_DirectorLocation', 'HW_FormFactor'])

    # Columns which we believe to be irrelevant
    df = df.drop(columns=['HW_Vendor', "HW_Model", "HW_DiskDrive", "HW_Other", "SW_Others",
                                "SW_PowerManagement", "SW_OS", "SW_OSVersion", "SW_Filesystem",
                                 "SUT_BIOS", "hash", "CPUName"])

    ## (Assumed) Irrelevant Columns
    df = df.drop(['HW_OpticalDrive', 'Software_Availability', 'SW_JVMVendor', 'SW_JVMVersion',
            'SW_JVMCLIOpts', 'SW_JVMAffinity', 'SW_JVMInstances', 'SW_JVMInitialHeapMB', 'SW_JVMMaxHeapMB',
            'SW_JVMAddressBits' ,
            'HW_Keyboard', 'HW_Mouse', 'HW_Monitor'], axis=1)

    ## Empty /  One Category / Lopsided Columns
    df = df.drop(['Power_Provisioning', 'HW_OtherCache', 'HW_NetSpeedMbit', 'System_Source', 'System_Designation'], axis=1)
    # TODO: check System_Source and System_Designation to make sure the lopsided nature isn't totally irrelevant / create outliers

    ## Duplicated Columns
    df = df.drop(['HW_CPUChars', 'HW_CPUName', 'HW_CPUsEnabled', 'HW_PrimaryCache', 'HW_SecondaryCache',
             'HW_SecondaryCache', 'HW_TertiaryCache', 'HW_PSUQuantAndRating', 'HW_HardwareThreads'], axis=1)

    ## Sort of duplicated
    df = df.drop(columns=['HW_DIMMNumAndSize'])

    ## Too Dirty columns (Consider extracting info from, but probably irrelevant)
    df = df.drop(['HW_CPUsOrderable', 'HW_MemDetails', 'HW_PSUDetails', 'SW_BootFirmwareVersion',
             'SW_MgmtFirmwareVersion', 'SUT_Firmware', 'SUT_Notes', 'HW_NICSNumAndType',
             'HW_NICSFirm/OS/Conn', 'HW_DiskController'],axis=1)

    # Rename some columns for consistency/ease
    df = df.rename(columns={'HW_MemAmountGB': 'MemoryGB', 'HW_CPUFreq':'CPUFrequency'})
    return df

def train_model(cpu_chips, Z):

    df = pd.read_csv("./data/spec_data_cleaned.csv")

    X = df.copy()
    X = X[X.Hardware_Availability_Year >= 2015]
    if not args.silent:
        print("Model will be restricted to the following amount of chips:", cpu_chips)

    X = X[X.CPUChips == cpu_chips] # Fit a model for every amount of CPUChips
    y = X.power

    X = X[Z.columns] # only select the supplied columns from the command line

    if not args.silent:
        print("Model will be trained on:", X.columns)

    params = {'max_depth': 5, 'learning_rate': 0.4411788445980461, 'n_estimators': 469, 'min_child_weight': 2, 'gamma': 0.609395982216471, 'subsample': 0.7563030757274138, 'colsample_bytree': 0.8176008707736587, 'reg_alpha': 0.08305234496497138, 'reg_lambda': 0.930233948796124, 'random_state': 296}

    model = XGBRegressor(**params)
    model.fit(X,y)

    return model

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--cpu-chips", type=float, help="Number of CPU chips", default=1)
    parser.add_argument("--cpu-freq", type=float, help="CPU frequency")
    parser.add_argument("--cpu-cores", type=float, help="Number of CPU cores")
    parser.add_argument("--tdp", type=float, help="TDP of the CPU")
    parser.add_argument("--ram", type=float, help="Amount of DRAM for the bare metal system")
    parser.add_argument("--vhost-ratio", type=float, help="Virtualization ratio of the system. Input numbers between (0,1].", default=1.0)
    parser.add_argument("--debug", action='store_true', help="Activate debug mode (currently unused)")
    parser.add_argument("--silent", action="store_true", help="Will suppress all debug output. Typically used in production.")
    args = parser.parse_args()

    Z = pd.DataFrame.from_dict({
        'HW_CPUFreq' : [args.cpu_freq],
        'CPUCores': [args.cpu_cores],
        'TDP': [args.tdp],
        'HW_MemAmountGB': [args.ram],
        'utilization': [0]
    })

    Z = Z.dropna(axis=1)

    model = train_model(args.cpu_chips, Z)

    if not args.silent:
        print("Sending following dataframe to model:\n", Z)
        print("vHost ratio is set to ", args.vhost_ratio)

    for line in sys.stdin:
        Z['utilization'] = float(line.strip())
        y_pred_default = model.predict(Z)
        print(y_pred_default[0] * args.vhost_ratio)
