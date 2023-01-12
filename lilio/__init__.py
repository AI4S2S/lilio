"""
s2spy: integrating expert knowledge and ai to boost S2S forecasting.

This package is a high-level python package integrating expert knowledge
and artificial intelligence to boost (sub) seasonal forecasting.
"""
import logging
from . import calendar_shifter
from . import time

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Yang Liu"
__email__ = "y.liu@esciencecenter.nl"
__version__ = "0.2.1"

__all__ = ["time", "calendar_shifter"]
