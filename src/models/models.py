
import argparse
from enum import Enum

from auto_detect import CPUInfo

class Model():
  def __init__(self, cpu_info: CPUInfo, args: argparse.Namespace):
    self.cpu_info = cpu_info
  
  def predict(self, cpu_utilization: float, vhost_ratio: float) -> float:
    pass

class Models(Enum):
    OLS = 'ols'
    XGB = 'xgb'

    def __str__(self):
        return self.value
