"""Tests for the lilio._bokeh_plots module."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from bokeh import io as bokeh_io
import lilio


mpl.use("Agg")  # required for windows


class TestPlots:
    """Test the visualizations (rough check for errors only)."""

    @pytest.fixture
    def dummy_bokeh_file(self, tmp_path):
        bokeh_io.output_file(tmp_path / "test.html")

    custom_cal_pre = lilio.Calendar(anchor="12-31")
    custom_cal_pre.add_intervals("precursor", "10d")
    custom_cal_tar = lilio.Calendar(anchor="12-31")
    custom_cal_tar.add_intervals("target", "10d")

    calendars = [
        lilio.daily_calendar(anchor="12-31", length="60d"),
        lilio.monthly_calendar(anchor="December", length="1M"),
        lilio.weekly_calendar(anchor="W40", length="2W"),
        custom_cal_pre,
        custom_cal_tar,
    ]

    @pytest.fixture(params=calendars, autouse=True)
    def dummy_calendars(self, request):
        "Dummy that tests all available calendars."
        cal = request.param
        return cal.map_years(2018, 2021)

    @pytest.fixture(params=[True, False], autouse=True)
    def isinteractive(self, request):
        return request.param

    def test_visualize_relative(self, dummy_calendars, isinteractive):
        dummy_calendars.visualize(interactive=isinteractive, relative_dates=True)
        plt.close("all")

    def test_visualize_absolute(self, dummy_calendars, isinteractive):
        dummy_calendars.visualize(interactive=isinteractive, relative_dates=False)
        plt.close("all")

    def test_visualize_without_text(self, dummy_calendars, isinteractive):
        dummy_calendars.visualize(interactive=isinteractive, show_length=False)
        plt.close("all")

    def test_visualize_with_text(self, dummy_calendars, isinteractive):
        dummy_calendars.visualize(interactive=isinteractive, show_length=True)
        plt.close("all")

    def test_visualize_unmapped(self, isinteractive):
        lilio.daily_calendar(anchor="12-31").visualize(interactive=isinteractive)
        plt.close("all")


class TestPlotsSingle:
    """Test the visualization routines, where a single calendar suffices"""

    @pytest.fixture
    def dummy_bokeh_file(self, tmp_path):
        bokeh_io.output_file(tmp_path / "test.html")

    @pytest.fixture
    def dummy_calendar(self):
        "Dummy that will only test for daily_calendar (to avoid excess testing)"
        cal = lilio.daily_calendar(anchor="12-31", length="60d")
        return cal.map_years(2018, 2021)

    def test_bokeh_kwargs(self, dummy_calendar):
        """Testing kwargs that overwrite default kwargs."""
        dummy_calendar.visualize(
            interactive=True,
            width=800,
            height=200,
            tooltips=[("Interval", "@desc")],
        )

    def test_bokeh_kwarg_mpl(self, dummy_calendar):
        with pytest.warns():
            dummy_calendar.visualize(interactive=False, width=800)
            plt.close("all")

    def test_mpl_no_legend(self, dummy_calendar):
        dummy_calendar.visualize(interactive=False, add_legend=False)
        plt.close("all")

    def test_mpl_ax_kwarg(self, dummy_calendar):
        _, ax = plt.subplots()
        dummy_calendar.visualize(interactive=False, ax=ax)
        plt.close("all")

    def test_bokeh_ax_warning(self, dummy_calendar):
        _, ax = plt.subplots()
        with pytest.warns():
            dummy_calendar.visualize(interactive=True, ax=ax)
