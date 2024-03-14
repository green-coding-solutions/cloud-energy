
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from xgboost import XGBRegressor
from .hyperparameter_tuning import get_data, get_study, train_test_split, train

def test_hyperparameter_tuning_quality():
    (X, y) = get_data()
    study = get_study()
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, train_size=0.8, test_size=0.2)
    model = train(study, X_train, X_valid, y_train, y_valid)
    
    model.fit(X_train, y_train, eval_set=[(X_valid, y_valid)], verbose=False)
    y_pred_default = model.predict(X_valid)
    mae = mean_absolute_error(y_pred_default, y_valid)
    mse = root_mean_squared_error(y_valid, y_pred_default)
    
    # TODO: pick sensible values
    assert mae < 30
    assert mse < 30
  