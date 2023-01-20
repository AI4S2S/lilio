"""Tests for the lilio.time.Calendar module.
"""
from typing import Literal
import numpy as np
import pandas as pd
import pytest
from pandas.tseries.offsets import DateOffset
from lilio.time import Calendar
from lilio.time import Interval


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
        a = dict(months=1, weeks=2, days=1)
        b = dict(months=2, weeks=1, days=5)
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

    @pytest.fixture(autouse=True)
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
        time_index = pd.date_range("20201110", "20211211", freq="10d")
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
