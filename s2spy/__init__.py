"""
s2spy: integrating expert knowledge and ai to boost S2S forecasting.

This package is a high-level python package integrating expert knowledge
and artificial intelligence to boost (sub) seasonal forecasting.
"""
import logging
from . import dimensionality
from . import time
from . import traintest
from ._RGDR import RGDR


logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Yang Liu"
__email__ = "y.liu@esciencecenter.nl"
__version__ = "0.1.0"
