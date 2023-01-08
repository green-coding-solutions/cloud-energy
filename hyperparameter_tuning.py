import os
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import optuna


def objective(trial):

    params = {
        "tree_method":"exact",
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.5),
        'n_estimators': trial.suggest_int('n_estimators', 50, 1000),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'random_state': trial.suggest_int('random_state', 1, 1000)
    }


    inner_model = XGBRegressor(
        **params,
        n_jobs=-1,
        early_stopping_rounds=10 #should be around 10% of amount of trials
    )

    inner_model.fit(X_train, y_train,         eval_set=[(X_valid, y_valid)]        ,

              verbose=0
   )

    y_hat = inner_model.predict(X_valid)

    # Note: This is only meaningful for Regressors. Use a different metric for Classifiers!
    return mean_squared_error(y_valid, y_hat, squared=False)


df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/data/spec_data_cleaned.csv")

X = df[df.CPUChips == 2] # Re-run script with a tuning for every amount of CPUChips
y = X["power"]
X = X.drop(columns=["power"])

Z = pd.DataFrame.from_dict({
    'HW_CPUFreq' : [],
    'CPUCores': [],
    'CPUThreads': [],
    'TDP': [],
    'Hardware_Availability_Year': [],
    'HW_MemAmountGB': [],
    'Architecture': [],
    'CPUMake': [],
    'utilization': []
})

X = X[Z.columns]


X = pd.get_dummies(X, columns=["CPUMake", "Architecture"])

X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, test_size=0.2)
study = optuna.create_study(direction='minimize', study_name='regression')
study.optimize(objective, n_trials=100) # Love to do 100, but this leads to an underflow error ... unclear why
print('Number of finished trials:', len(study.trials))
print('Best trial:', study.best_trial.params)
model = XGBRegressor(**study.best_trial.params, early_stopping_rounds=4)

model.fit(X_train,y_train,eval_set=[(X_valid, y_valid)],verbose=False)
y_pred_default = model.predict(X_valid)
print("Mean Absolute Error:" , mean_absolute_error(y_pred_default,y_valid))
print("Mean Squared Error:" , mean_squared_error(y_valid, y_pred_default, squared=False))


print("\n### BASE")
model = XGBRegressor(random_state=study.best_trial.params['random_state'])
model.fit(X_train,y_train,eval_set=[(X_valid, y_valid)],verbose=False)
y_pred_default = model.predict(X_valid)

print("Mean Absolute Error:" , mean_absolute_error(y_pred_default,y_valid))
print("Mean Squared Error:" , mean_squared_error(y_valid, y_pred_default, squared=False))
