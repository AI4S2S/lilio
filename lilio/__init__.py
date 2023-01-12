"""
lilio: Calendar generator for machine learning with timeseries data
"""
import logging
from . import calendar_shifter
from . import time


logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Yang Liu"
__email__ = "y.liu@esciencecenter.nl"
__version__ = "0.2.1"

__all__ = ["time", "calendar_shifter"]
