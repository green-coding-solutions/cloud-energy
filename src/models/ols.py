#pylint: disable=invalid-name

from argparse import Namespace
import statsmodels.formula.api as smf
import pandas as pd

from auto_detect import CPUInfo
from models.models import Model

class OLSModel(Model):
    def __init__(self, cpu_info: CPUInfo, args: Namespace):
        super().__init__(cpu_info, args)

        df = pd.read_csv('./data/spec_data_cleaned.csv')

        formula = 'power ~ utilization'

        if cpu_info.threads is not None:
            formula = f"{formula} + CPUThreads"

        if cpu_info.chips is not None:
            formula = f"{formula}*C(CPUChips)"

        if cpu_info.mem is not None:
            formula = f"{formula} + HW_MemAmountGB"

        if cpu_info.tdp is not None:
            formula = f"{formula} + TDP"

        model = smf.ols(formula=formula, data=df).fit()
        self.model = model

        my_data = pd.DataFrame.from_dict({
            'utilization': 0,
            'CPUChips': [cpu_info.chips],
            'CPUThreads': [cpu_info.threads],
            'HW_MemAmountGB': [cpu_info.mem],
            'TDP' : [cpu_info.tdp]
        })

        # Drop all arguments that were not supplied
        my_data = my_data.dropna(axis=1)
        self.my_data = my_data

        # TODO: use logger
        if not args.silent:
            print('Sending following dataframe to model', my_data)
            print('vHost ratio is set to ', args.vhost_ratio)
    
    def predict(self, cpu_util: float, vhost_ratio: float) -> float:
        self.my_data['utilization'] = cpu_util
        return self.model.predict(self.my_data)[0] * vhost_ratio
    