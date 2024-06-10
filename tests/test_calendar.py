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


class TestInterval:
    """Test the Interval class."""

    def test_target_interval(self):
        target = Interval("target", "20d", "10d")
        assert isinstance(target, Interval)
        assert target.length_dateoffset == DateOffset(days=20)
        assert target.gap_dateoffset == DateOffset(days=10)
        assert target.is_target

    def test_precursor_interval(self):
        precursor = Interval("precursor", "20d", "10d")
        assert isinstance(precursor, Interval)
        assert precursor.length_dateoffset == DateOffset(days=20)
        assert precursor.gap_dateoffset == DateOffset(days=10)
        assert not precursor.is_target

    def test_interval_months(self):
        target = Interval("target", "2M", "1M")
        assert target.length_dateoffset == DateOffset(months=2)
        assert target.gap_dateoffset == DateOffset(months=1)

    def test_interval_weeks(self):
        target = Interval("target", "3W", "2W")
        assert target.length_dateoffset == DateOffset(weeks=3)
        assert target.gap_dateoffset == DateOffset(weeks=2)

    def test_target_interval_dict(self):
        a = {"months": 1, "weeks": 2, "days": 1}
        b = {"months": 2, "weeks": 1, "days": 5}
        target = Interval("target", length=a, gap=b)
        assert target.length_dateoffset == DateOffset(**a)
        assert target.gap_dateoffset == DateOffset(**b)

    def test_repr(self):
        target = Interval("target", "20d", "10d")
        expected = "Interval(role='target', length='20d', gap='10d')"
        assert repr(target) == expected

    def test_repr_eval(self):
        target = Interval("target", "20d", "10d")
        _ = eval(repr(target))  # pylint: disable=eval-used


class TestCalendar:
    """Test the (custom) Calendar methods."""

    @pytest.fixture
    def dummy_calendar(self):
        cal = Calendar(anchor="12-31")
        # append building blocks
        cal.add_intervals("target", "20d")
        cal.add_intervals("precursor", "10d")
        # map years
        cal = cal.map_years(2021, 2021)
        return cal

    def test_init(self):
        cal = Calendar(anchor="12-31")
        assert isinstance(cal, Calendar)

    def test_repr_basic(self):
        cal = Calendar(anchor="12-31")
        expected = (
            "Calendar(anchor='12-31',allow_overlap=False,mapping=None,intervals=None)"
        )
        calrepr = repr(cal)

        # Test that the repr can be pasted back into the terminal
        _ = eval(calrepr)  # pylint: disable=eval-used

        # remove whitespaces:
        calrepr = calrepr.replace(" ", "").replace("\r", "").replace("\n", "")
        assert calrepr == expected

    def test_repr_reproducible(self):
        cal = Calendar(anchor="12-31", allow_overlap=True)
        cal.add_intervals("target", "10d")
        cal.map_years(2020, 2022)
        repr_dict = eval(repr(cal)).__dict__  # pylint: disable=eval-used
        assert repr_dict["_anchor"] == "12-31"
        assert repr_dict["_mapping"] == "years"
        assert repr_dict["_first_year"] == 2020
        assert repr_dict["_last_year"] == 2022
        assert repr_dict["_allow_overlap"] is True
        assert (
            repr(repr_dict["targets"][0])
            == "Interval(role='target', length='10d', gap='0d')"
        )

    def test_show(self, dummy_calendar):
        expected_calendar_repr = (
            "i_interval -1 1\n anchor_year \n 2021"
            + "[2021-12-21, 2021-12-31) [2021-12-31, 2022-01-20)"
        )
        expected_calendar_repr = expected_calendar_repr.replace(" ", "")
        assert repr(dummy_calendar.show()).replace(" ", "") == expected_calendar_repr

    def test_no_intervals(self):
        cal = Calendar(anchor="12-31")
        with pytest.raises(ValueError):
            cal.get_intervals()

    def test_flat(self, dummy_calendar):
        expected = np.array(
            [
                interval("2021-12-21", "2021-12-31", closed="left"),
                interval("2021-12-31", "2022-01-20", closed="left"),
            ]
        )
        assert np.array_equal(dummy_calendar.flat, expected)

    def test_add_intervals(self, dummy_calendar):
        dummy_calendar.add_intervals("target", "30d")
        dummy_calendar = dummy_calendar.map_years(2021, 2021)
        expected = np.array(
            [
                interval("2021-12-21", "2021-12-31", closed="left"),
                interval("2021-12-31", "2022-01-20", closed="left"),
                interval("2022-01-20", "2022-02-19", closed="left"),
            ]
        )
        assert np.array_equal(dummy_calendar.flat, expected)

    def test_add_intervals_multiple(self, dummy_calendar):
        dummy_calendar.add_intervals("target", "30d", n=2)
        dummy_calendar = dummy_calendar.map_years(2021, 2021)
        expected = np.array(
            [
                interval("2021-12-21", "2021-12-31", closed="left"),
                interval("2021-12-31", "2022-01-20", closed="left"),
                interval("2022-01-20", "2022-02-19", closed="left"),
                interval("2022-02-19", "2022-03-21", closed="left"),
            ]
        )
        assert np.array_equal(dummy_calendar.flat, expected)

    @pytest.mark.parametrize("incorrect_n", (2.0, [1], 0, -10))  # non-int or <=0.
    def test_add_intervals_incorrect_n(self, dummy_calendar, incorrect_n):
        with pytest.raises(ValueError):
            dummy_calendar.add_intervals("target", "30d", n=incorrect_n)

    def test_gap_intervals(self, dummy_calendar):
        dummy_calendar.add_intervals("target", "20d", gap="10d")
        dummy_calendar = dummy_calendar.map_years(2021, 2021)
        expected = np.array(
            [
                interval("2021-12-21", "2021-12-31", closed="left"),
                interval("2021-12-31", "2022-01-20", closed="left"),
                interval("2022-01-30", "2022-02-19", closed="left"),
            ]
        )
        assert np.array_equal(dummy_calendar.flat, expected)

    def test_overlap_intervals(self, dummy_calendar):
        dummy_calendar.add_intervals("precursor", "10d", gap="-5d")
        dummy_calendar = dummy_calendar.map_years(2021, 2021)
        expected = np.array(
            [
                interval("2021-12-16", "2021-12-26", closed="left"),
                interval("2021-12-21", "2021-12-31", closed="left"),
                interval("2021-12-31", "2022-01-20", closed="left"),
            ]
        )
        assert np.array_equal(dummy_calendar.flat, expected)

    def test_map_to_data(self, dummy_calendar):
        # create dummy data for testing
        time_index = pd.date_range("2020-11-10", "2021-12-11", freq="10d")
        var = np.random.random(len(time_index))
        # generate input data
        test_data = pd.Series(var, index=time_index)
        # map year to data
        calendar = dummy_calendar.map_to_data(test_data)
        # expected intervals
        expected = np.array(
            [
                interval("2020-12-21", "2020-12-31", closed="left"),
                interval("2020-12-31", "2021-01-20", closed="left"),
            ]
        )
        assert np.array_equal(calendar.flat, expected)

    def test_non_day_interval_length(self):
        cal = Calendar(anchor="December")
        cal.add_intervals("target", "1M")
        cal.add_intervals("precursor", "10M")
        cal.map_years(2020, 2020)
        expected = np.array(
            [
                interval("2020-02-01", "2020-12-01", closed="left"),
                interval("2020-12-01", "2021-01-01", closed="left"),
            ]
        )
        assert np.array_equal(cal.flat, expected)

    @pytest.mark.parametrize(
        "allow_overlap, expected_anchors",
        ((True, [2022, 2021, 2020]), (False, [2022, 2020])),
    )
    def test_allow_overlap(self, allow_overlap, expected_anchors):
        cal = Calendar(anchor="12-31", allow_overlap=allow_overlap)
        cal.add_intervals("target", length="30d")
        cal.add_intervals("precursor", length="365d")
        cal.map_years(2020, 2022)
        assert np.array_equal(expected_anchors, cal.get_intervals().index.values)

    def test_extra_year_edgecase(self):
        """Weird things can happen when a calendar interval crosses over the new year.

        2 years have to be subtracted from the last datapoint's year.
        """
        cal = Calendar("12-25")
        cal.add_intervals("target", length="1M")
        dates_inclusive = pd.date_range(start="2007-01-01", end="2010-01-01", freq="1d")
        dates_exclusive = pd.date_range(start="2007-01-01", end="2009-12-31", freq="1d")
        test_data_incl = pd.Series(
            data=np.zeros(len(dates_inclusive)), index=dates_inclusive
        )
        test_data_excl = pd.Series(
            data=np.zeros(len(dates_exclusive)), index=dates_exclusive
        )

        cal.map_to_data(test_data_incl)
        n_years_inclusive = len(cal.get_intervals())
        cal.map_to_data(test_data_excl)
        n_years_exclusive = len(cal.get_intervals())

        assert n_years_exclusive == 2
        assert n_years_inclusive == 2


class TestAnchorKwarg:
    correct_inputs = [  # format: (anchor, anchor_fmt, anchor_str)
        ("5-5", "%m-%d", "5-5"),
        ("02-5", "%m-%d", "02-5"),
        ("06-05", "%m-%d", "06-05"),
        ("5-05", "%m-%d", "5-05"),
        ("11-30", "%m-%d", "11-30"),
        ("12-31", "%m-%d", "12-31"),
        ("W01", "W%W-%w", "W01-1"),
        ("W9", "W%W-%w", "W9-1"),
        ("W01-4", "W%W-%w", "W01-4"),
        ("W9-1", "W%W-%w", "W9-1"),
        ("December", "%m", "12"),
        ("dec", "%m", "12"),
        ("jan", "%m", "1"),
        ("Jan", "%m", "1"),
    ]

    incorrect_inputs = (
        10,  # non-str inputs
        (1, 2),
        "0",  # month number less than 1
        "13",  # month number greater than 12
        "12-0",  # day number less than 1
        "12-32",  # day number greater than 31
        "31-12",  # incorrect month/day order
        "4-31",  # 31 April (nonexistant date)
        "2-29",  # 29 February (doesn't exist in every year)
        "W60",  # Week number greater than 52 (only some years have 53 weeks)
        "W53",
        "W01-0",  # Weekday smaller than 1 (Monday)
        "W01-8",  # Weekday greater than 7 (Sunday)
        "w12",  # Small letter `w`.
        "juli",  # Non-English month name
        "July 5",  # Month name + day
        "July-5",
        "jan 20",
        "jan-20",
    )

    @pytest.mark.parametrize("test_input, expected_fmt, expected_str", correct_inputs)
    def test_correct_anchor_input(self, test_input, expected_fmt, expected_str):
        cal = Calendar(anchor=test_input)
        assert cal._anchor_fmt == expected_fmt  # pylint: disable=protected-access
        assert cal._anchor == expected_str  # pylint: disable=protected-access

    @pytest.mark.parametrize("test_input", incorrect_inputs)
    def test_incorrect_anchor_input(self, test_input):
        with pytest.raises(ValueError):
            _ = Calendar(anchor=test_input)


class TestMap:
    """Test map to year(s)/data methods"""

    @pytest.fixture
    def dummy_calendar(self):
        cal = Calendar(anchor="12-31")
        # append building blocks
        cal.add_intervals("target", "20d")
        cal.add_intervals("precursor", "10d")
        # map years
        cal = cal.map_years(2021, 2021)
        return cal

    def test_map_years(self):
        cal = daily_calendar(anchor="12-31", length="180d")
        cal.map_years(2020, 2021)
        expected = np.array(
            [
                [
                    interval("2021-07-04", "2021-12-31"),
                    interval("2021-12-31", "2022-06-29"),
                ],
                [
                    interval("2020-07-04", "2020-12-31"),
                    interval("2020-12-31", "2021-06-29"),  # notice the leap day
                ],
            ]
        )
        assert np.array_equal(cal.get_intervals(), expected)

    def test_map_years_single(self):
        cal = daily_calendar(anchor="12-31", length="180d")
        cal.map_years(2020, 2020)
        expected = np.array(
            [
                [
                    interval("2020-07-04", "2020-12-31"),
                    interval("2020-12-31", "2021-06-29"),
                ]
            ]
        )
        assert np.array_equal(cal.get_intervals(), expected)

    def test_map_to_data_edge_case_last_year(self):
        # test the edge value when the input could not cover the anchor date
        cal = daily_calendar(anchor="10-15", length="180d")
        # single year covered
        time_index = pd.date_range("2019-10-20", "2021-10-01", freq="60d")
        test_data = np.random.random(len(time_index))
        timeseries = pd.Series(test_data, index=time_index)
        cal.map_to_data(timeseries)
        expected = np.array(
            [
                [
                    interval("2020-04-18", "2020-10-15"),
                    interval("2020-10-15", "2021-04-13"),
                ]
            ]
        )
        assert np.array_equal(cal.get_intervals(), expected)

    def test_map_to_data_single_year_coverage(self):
        # test the single year coverage
        cal = daily_calendar(anchor="6-30", length="180d")
        # multiple years covered
        time_index = pd.date_range("2021-01-01", "2021-12-31", freq="7d")
        test_data = np.random.random(len(time_index))
        timeseries = pd.Series(test_data, index=time_index)
        cal.map_to_data(timeseries)

        expected = np.array(
            [
                [
                    interval("2021-01-01", "2021-06-30"),
                    interval("2021-06-30", "2021-12-27"),
                ]
            ]
        )

        assert np.array_equal(cal.get_intervals(), expected)

    def test_map_to_data_edge_case_first_year(self):
        # test the edge value when the input covers the anchor date
        cal = daily_calendar(anchor="10-15", length="180d")
        # multiple years covered
        time_index = pd.date_range("2019-01-01", "2021-12-25", freq="60d")
        test_data = np.random.random(len(time_index))
        timeseries = pd.Series(test_data, index=time_index)
        cal.map_to_data(timeseries)

        expected = np.array(
            [
                [
                    interval("2020-04-18", "2020-10-15"),
                    interval("2020-10-15", "2021-04-13"),
                ],
                [
                    interval("2019-04-18", "2019-10-15"),
                    interval("2019-10-15", "2020-04-12"),  # notice the leap day
                ],
            ]
        )

        assert np.array_equal(cal.get_intervals(), expected)

    def test_map_to_data_input_time_backward(self):
        # test when the input data has reverse order time index
        cal = daily_calendar(anchor="10-15", length="180d")
        time_index = pd.date_range("2020-01-01", "2021-12-25", freq="60d")
        test_data = np.random.random(len(time_index))
        timeseries = pd.Series(test_data, index=time_index[::-1])
        cal.map_to_data(timeseries)

        expected = np.array(
            [
                [
                    interval("2020-04-18", "2020-10-15"),
                    interval("2020-10-15", "2021-04-13"),
                ]
            ]
        )

        assert np.array_equal(cal.get_intervals(), expected)

    def test_map_to_data_xarray_input(self):
        # test when the input data has reverse order time index
        cal = daily_calendar(anchor="10-15", length="180d")
        time_index = pd.date_range("2020-01-01", "2021-12-25", freq="60d")
        test_data = np.random.random(len(time_index))
        dataarray = xr.DataArray(data=test_data, coords={"time": time_index})
        cal.map_to_data(dataarray)

        expected = np.array(
            [
                interval("2020-04-18", "2020-10-15"),
                interval("2020-10-15", "2021-04-13"),
            ]
        )

        assert np.all(cal.get_intervals() == expected)

    def test_missing_time_dim(self):
        cal = daily_calendar(anchor="10-15", length="180d")
        time_index = pd.date_range("2019-10-20", "2021-10-01", freq="60d")
        test_data = np.random.random(len(time_index))
        dataframe = pd.DataFrame(test_data, index=time_index)
        dataset = dataframe.to_xarray()
        with pytest.raises(ValueError):
            cal.map_to_data(dataset)

    def test_non_time_dim(self):
        cal = daily_calendar(anchor="10-15", length="180d")
        time_index = pd.date_range("2019-10-20", "2021-10-01", freq="60d")
        test_data = np.random.random(len(time_index))
        dataframe = pd.DataFrame(test_data, index=time_index)
        dataset = dataframe.to_xarray().rename({"index": "time"})
        dataset["time"] = np.arange(dataset["time"].size)
        with pytest.raises(ValueError):
            cal.map_to_data(dataset)

    # Note: add more test cases for different number of target periods!
    max_lag_edge_cases = [(73, [2019], 74), (72, [2019, 2018], 73)]
    # Test the edge cases of max_lag; where the max_lag just fits in exactly 365 days,
    # and where the max_lag just causes the calendar to skip a year

    @pytest.mark.parametrize("max_lag,expected_index,expected_size", max_lag_edge_cases)
    def test_max_lag_skip_years(self, max_lag, expected_index, expected_size):
        calendar = daily_calendar(anchor="12-31", length="5d", n_precursors=max_lag)
        calendar = calendar.map_years(2018, 2019)

        np.testing.assert_array_equal(
            calendar.get_intervals().index.values, expected_index
        )
        assert calendar.get_intervals().iloc[0].size == expected_size

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
            (False, 10, True, True),  # anchor width is 20d
            (False, 10, False, True),
            (False, 11, True, False),
            (False, 11, False, False),
        ),
    )
    def test_map_to_data_rightbounds(  # noqa: PLR0913 (too-many-arguments)
        self, dummy_calendar, safe_mode, n_dropped_indices, inferable, valid
    ):
        """Test right bounds of calendar are created correctly."""
        time_index = pd.date_range("2020-01-31", "2021-01-21", freq="2d")
        var = np.random.random(len(time_index))
        test_data = pd.Series(var, index=time_index)

        if not inferable:
            test_data = pd.concat((test_data[:2], test_data[3:]))
            assert pd.infer_freq(test_data.index) is None

        truncated_data = test_data[: len(test_data) - n_dropped_indices]

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
            (False, 5, True, True),  # anchor width is 10d
            (False, 5, False, True),
            (False, 6, True, False),
            (False, 6, False, False),
        ),
    )
    def test_map_to_data_leftbounds(  # noqa: PLR0913 (too-many-arguments)
        self, dummy_calendar, safe_mode, n_dropped_indices, inferable, valid
    ):
        """Test left bounds of the calendar are created correctly."""
        time_index = pd.date_range("2020-12-20", "2021-01-21", freq="2d")
        var = np.random.random(len(time_index))
        test_data = pd.Series(var, index=time_index)

        if not inferable:
            test_data = pd.concat((test_data[:-3], test_data[-2:]))
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
            assert np.array_equal(calendar.flat, expected)
        else:
            expected_msg = "The input data could not cover the target advent calendar."
            with pytest.raises(ValueError, match=expected_msg):
                dummy_calendar.map_to_data(truncated_data, safe=safe_mode)
                dummy_calendar.get_intervals()
