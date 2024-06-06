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

test_matrix = (
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
        (False, 10, True, True),  # anchor width is 20d
        (False, 10, False, True),
        (False, 11, True, False),
        (False, 11, False, False),
    )


@pytest.mark.parametrize(
    "safe_mode, n_dropped_indices, inferable, valid", test_matrix,
)
def test_right_bounds(dummy_calendar, safe_mode, n_dropped_indices, inferable, valid):
    """Test right bounds of calendar are created correctly."""
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
            dummy_calendar.get_intervals()

@pytest.mark.parametrize(
    "safe_mode, n_dropped_indices, inferable, valid", test_matrix,
)
def test_left_bounds(dummy_calendar, safe_mode, n_dropped_indices, inferable, valid):
    """Test left bounds of the calendar are created correctly."""
    time_index = pd.date_range("20200131", "20210121", freq="2d")
    var = np.random.random(len(time_index))
    test_data = pd.Series(var, index=time_index)

    if not inferable:
        test_data = pd.concat((test_data[:2], test_data[3:]))
        assert pd.infer_freq(test_data.index) is None

    truncated_data = test_data[n_dropped_indices:]
    
    expected = np.array(
        [
            interval("2020-12-21", "2020-12-31", closed="left"),
            interval("2020-12-31", "2021-01-20", closed="left"),
        ]
    )
    
    if valid:
        calendar = dummy_calendar.map_to_data(truncated_data, safe=safe_mode)
        print(calendar._map_year(2020).min().left)
        print(truncated_data.index[-1])
        print(calendar._leftmost_time_bound)
        assert np.array_equal(calendar.flat, expected)
    else:
        expected_msg = "The input data could not cover the target advent calendar."  
        with pytest.raises(ValueError, match=expected_msg):  
            dummy_calendar.map_to_data(truncated_data, safe=safe_mode)
            print(truncated_data.index[-1])
            dummy_calendar.get_intervals()
            print(dummy_calendar.get_intervals())
