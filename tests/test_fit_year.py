"""Tests for the lilio.Calendar module."""

from typing import Literal
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from pandas.tseries.offsets import DateOffset
from lilio import Calendar
from lilio import Interval
from lilio import daily_calendar

def interval(start, end, closed: Literal["left", "right", "both", "neither"] = "left"):
    """Shorthand for more readable tests."""
    return pd.Interval(pd.Timestamp(start), pd.Timestamp(end), closed=closed)


@pytest.fixture
def dummy_calendar():
    cal = Calendar(anchor="12-31")
    # append building blocks
    cal.add_intervals("target", "20d")
    cal.add_intervals("precursor", "10d")
    # map years
    cal = cal.map_years(2021, 2021)
    return cal


@pytest.mark.parametrize(
    "safe_mode, n_dropped_indices, inferable, valid",
    (
        # Safe mode (default):
        (True, 0, True, True),
        (True, 0, False, True),
        (True, 1, True, True),  # Only if we can infer the freq do we know if valid
        (True, 1, False, False),  # Otherwise not
        (True, 2, True, False),
        (True, 2, False, False),
        # Greedy mode:
        (False, 0, True, True),
        (False, 0, False, True),
        (False, 1, True, True),
        (False, 1, False, True),
        (False, 2, True, False),
        (False, 2, False, False),
    ),
)
def test_edge_cases(dummy_calendar, safe_mode, n_dropped_indices, inferable, valid):
    """"""
    time_index = pd.date_range("20200131", "20210121", freq="2d")
    var = np.random.random(len(time_index))
    test_data = pd.Series(var, index=time_index)

    if not inferable:
        test_data = pd.concat((test_data[:2], test_data[3:]))
        assert pd.infer_freq(test_data.index) is None

    truncated_data = test_data[:len(test_data)-n_dropped_indices]
    
    expected = np.array(
        [
            interval("2020-12-21", "2020-12-31", closed="left"),
            interval("2020-12-31", "2021-01-20", closed="left"),
        ]
    )
    
    if valid:
        calendar = dummy_calendar.map_to_data(truncated_data, safe=safe_mode)
        assert np.array_equal(calendar.flat, expected)
    else:
        expected_msg = "The input data could not cover the target advent calendar."  
        with pytest.raises(ValueError, match=expected_msg):  
            dummy_calendar.map_to_data(truncated_data, safe=safe_mode)
    