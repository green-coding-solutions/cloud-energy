import os
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import RepeatedKFold
from sklearn.model_selection import cross_val_score

df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/../data/spec_data_cleaned.csv")

df_new = df.copy()
df_new = df_new[df_new.CPUChips == 2] # Fit a model for every amount of CPUChips

X = df_new[[
    'HW_MemAmountGB',
    'TDP',
    'utilization',
    'CPUCores',
    'CPUThreads',
    'HW_CPUFreq',
    'Hardware_Availability_Year',
    'HW_FormFactor',
    'HW_Vendor'
]]
X = pd.get_dummies(X, columns=['HW_FormFactor', 'HW_Vendor'])
y = df_new.power
model = XGBRegressor()
kfold = RepeatedKFold()
kf_cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_absolute_error')
# pylint: disable=consider-using-f-string
print(f"[Interact DC Original (untuned)] K-fold CV score range: \
    {kf_cv_scores.min():.2f} < {kf_cv_scores.mean():.2f} < {kf_cv_scores.max():.2f}"
)

X = df_new[[
    'HW_MemAmountGB',
    'TDP',
    'utilization',
    'CPUCores',
    'CPUThreads',
    'HW_CPUFreq',
    'Hardware_Availability_Year'
]]
y = df_new.power
model = XGBRegressor()
kfold = RepeatedKFold()
kf_cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_absolute_error')
# pylint: disable=consider-using-f-string
print(f"[Interact DC cloud available variables (untuned)] K-fold CV score range: \
        {kf_cv_scores.min():.2f} < {kf_cv_scores.mean():.2f} < {kf_cv_scores.max():.2f}"
)



X = df_new[[
    'HW_MemAmountGB',
    'TDP',
    'utilization',
    'CPUCores',
    'CPUThreads',
    'HW_CPUFreq',
    'Hardware_Availability_Year',
    'Architecture',
    'CPUMake'
]]
X = pd.get_dummies(X, columns=['Architecture', 'CPUMake'])
y = df_new.power
model = XGBRegressor()
kfold = RepeatedKFold()
kf_cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='neg_mean_absolute_error')
# pylint: disable=consider-using-f-string
print(f"[Our variable selection (untuned)] K-fold CV score range: \
        {kf_cv_scores.min():.2f} < {kf_cv_scores.mean():.2f} < {kf_cv_scores.max():.2f}"
)

## Expected output from 07.12.2022 with the pre-interpolated data
## [Interact DC Original (untuned)] K-fold CV score range: -4.70 < -4.54 < -4.33
## [Interact DC cloud available variables (untuned)] K-fold CV score range: -8.00 < -7.88 < -7.80
## [Our variable selection (untuned)] K-fold CV score range: -8.13 < -8.02 < -7.93
