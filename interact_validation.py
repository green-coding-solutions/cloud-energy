import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import RepeatedKFold
from sklearn.model_selection import cross_val_score

df = pd.read_csv("./data/spec_data_cleaned.csv")

df_new = df.copy() 
df_new = df_new[df_new.Hardware_Availability_Year >= 2015]
df_new = df_new[df_new.CPUChips == 2] # Fit a model for every amount of CPUChips

## their variable selection
X = df_new[[ 'HW_MemAmountGB', 'TDP', 'utilization', 'CPUCores', 'CPUThreads', 'HW_CPUFreq', 'Hardware_Availability_Year']]
X = pd.get_dummies(X, columns=['HW_FormFactor', 'HW_Vendor'])

## our variable selection
X = df_new[[ 'HW_MemAmountGB', 'TDP', 'utilization', 'CPUCores', 'HW_CPUFreq']]

y = df_new.power


model = XGBRegressor()
kfold = RepeatedKFold()
kf_cv_scores = cross_val_score(model, X, y, cv=kfold, scoring="neg_mean_absolute_error")
print("K-fold CV score range: %.2f < %.2f < %.2f" % (kf_cv_scores.min(), kf_cv_scores.mean(), kf_cv_scores.max()) )
