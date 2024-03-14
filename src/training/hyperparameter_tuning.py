import os
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import train_test_split
import optuna


def objective(X_train, X_valid, y_train, y_valid):
    def objective_function(trial):
        params = {
            "tree_method": "exact",
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.5),
            'n_estimators': trial.suggest_int('n_estimators', 50, 1000),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'random_state': trial.suggest_int('random_state', 1, 1000)
        }

        inner_model = XGBRegressor(
            **params,
            n_jobs=-1,
            early_stopping_rounds=10  # should be around 10% of amount of trials
        )

        inner_model.fit(X_train, y_train, eval_set=[
                        (X_valid, y_valid)], verbose=0)

        y_hat = inner_model.predict(X_valid)

        # Note: This is only meaningful for Regressors. Use a different metric for Classifiers!
        return root_mean_squared_error(y_valid, y_hat)
    return objective_function


def get_data():
    data_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '../../data/spec_data_cleaned.csv')
    df = pd.read_csv(data_path)

    # Re-run script with a tuning for every amount of CPUChips
    X = df[df.CPUChips == 2]
    y = X["power"]
    X = X.drop(columns=["power"])

    Z = pd.DataFrame.from_dict({
        'HW_CPUFreq': [],
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
    return (X, y)


def get_study():
    study = optuna.create_study(direction='minimize', study_name='regression')
    return study


def train(study, X_train, X_valid, y_train, y_valid):
    # Love to do 100, but this leads to an underflow error ... unclear why
    study.optimize(objective(X_train, X_valid, y_train, y_valid), n_trials=100)
    print('Number of finished trials:', len(study.trials))
    print('Best trial:', study.best_trial.params)
    model = XGBRegressor(**study.best_trial.params, early_stopping_rounds=4)
    return model


def check_model(model, study, X_train, X_valid, y_train, y_valid):
    model.fit(X_train, y_train, eval_set=[(X_valid, y_valid)], verbose=False)
    y_pred_default = model.predict(X_valid)
    print("Mean Absolute Error:", mean_absolute_error(y_pred_default, y_valid))
    print("Mean Squared Error:", root_mean_squared_error(
        y_valid, y_pred_default))
    
    print("\n### BASE")
    model = XGBRegressor(random_state=study.best_trial.params['random_state'])
    model.fit(X_train, y_train, eval_set=[(X_valid, y_valid)], verbose=False)
    y_pred_default = model.predict(X_valid)

    print("Mean Absolute Error:", mean_absolute_error(y_pred_default, y_valid))
    print("Mean Squared Error:", root_mean_squared_error(
        y_valid, y_pred_default))


if __name__ == '__main__':
    (X, y) = get_data()
    study = get_study()
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, train_size=0.8, test_size=0.2)

    model = train(study, X_train, X_valid, y_train, y_valid)
    check_model(model, study, X_train, X_valid, y_train, y_valid)
