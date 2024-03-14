# pylint: disable=redefined-outer-name,invalid-name

from argparse import Namespace
import os
import time
import logging
import pandas as pd
import numpy as np
from xgboost import XGBRegressor

from src.auto_detect import CPUInfo
from src.models.models import Model

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

def infer_predictions(model, Z):
    predictions = {}

    for i in range(0,110,5):
        Z['utilization'] = i
        predictions[float(i)] = model.predict(Z)[0]
    return predictions

def interpolate_helper(predictions, lower, upper, step=501):

    diff = int(upper-lower)
    diff_value = predictions[upper] - predictions[lower]

    for i in np.linspace(0, diff, step):
        predictions[round(lower+i, 2)] = predictions[lower]+((diff_value/diff)*i)

    return predictions

def interpolate_predictions(predictions):
    predictions = interpolate_helper(predictions, 0.0, 5.0, 501)
    predictions = interpolate_helper(predictions, 5.0, 15.0, 1001)
    predictions = interpolate_helper(predictions, 15.0, 25.0, 1001)
    predictions = interpolate_helper(predictions, 25.0, 35.0, 1001)
    predictions = interpolate_helper(predictions, 35.0, 45.0, 1001)
    predictions = interpolate_helper(predictions, 45.0, 55.0, 1001)
    predictions = interpolate_helper(predictions, 55.0, 65.0, 1001)
    predictions = interpolate_helper(predictions, 65.0, 75.0, 1001)
    predictions = interpolate_helper(predictions, 75.0, 85.0, 1001)
    predictions = interpolate_helper(predictions, 85.0, 95.0, 1001)
    # Question: between 95 and 100 is no difference. How do we extrapolate?
    predictions = interpolate_helper(predictions, 95.0, 100.0, 501)

    return predictions

class XGBModel(Model):
    def __init__(self, cpu_info: CPUInfo, args: Namespace):
        super().__init__(cpu_info, args)
        
        # --- Determine Z
        Z = pd.DataFrame.from_dict({
            'HW_CPUFreq' : [cpu_info.freq],
            'CPUThreads': [cpu_info.threads],
            'CPUCores': [cpu_info.cores],
            'TDP': [cpu_info.tdp],
            'Hardware_Availability_Year': [cpu_info.release_year],
            'HW_MemAmountGB': [cpu_info.mem],
            'Architecture': [cpu_info.architecture],
            'CPUMake': [cpu_info.make],
            'utilization': [0.0]
        })

        Z = pd.get_dummies(Z, columns=['CPUMake', 'Architecture'])

        Z = Z.dropna(axis=1)
            
        df = pd.read_csv(f"{os.path.dirname(os.path.abspath(__file__))}/data/spec_data_cleaned.csv")

        X = df.copy()
        X = pd.get_dummies(X, columns=['CPUMake', 'Architecture'])

        if cpu_info.chips:
            logger.info('Training data will be restricted to the following amount of chips: %d', cpu_info.chips)

            X = X[X.CPUChips == cpu_info.chips] # Fit a model for every amount of CPUChips

        if X.empty:
            raise RuntimeError(f"The training data does not contain any servers with a chips amount ({cpu_info.chips}). Please select a different amount.")

        y = X.power

        X = X[Z.columns] # only select the supplied columns from the command line
        
    #    params = {
    #      'max_depth': 10,
    #      'learning_rate': 0.3037182109676833,
    #      'n_estimators': 792,
    #      'min_child_weight': 1,
    #      'random_state': 762
    #    }
        params = {} # we see no strong improvements with hyperparamters tuned by optune

        model = XGBRegressor(**params)
        model.fit(X,y)

        logger.info('Model will be trained on the following columns and restrictions: \n%s', Z)
        logger.info('Infering all predictions to dictionary')

        inferred_predictions = infer_predictions(model, Z)
        
        self.model = model
        self.energy = args.energy
        self.interpolated_predictions = interpolate_predictions(inferred_predictions)

    def predict(self, cpu_utilization: float, vhost_ratio: float) -> float:
        predicted_value = self.interpolated_predictions[cpu_utilization] * vhost_ratio
        if self.energy:
            # TODO: odd calculation.
            current_time = time.time_ns()
            print(predicted_value * \
                (time.time_ns() - current_time) / 1_000_000_000, flush=True)
        else:
            print(predicted_value, flush=True)
