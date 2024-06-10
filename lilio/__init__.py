"""lilio: Calendar generator for machine learning with timeseries data.

Time indices are anchored to the target period of interest. By keeping
observations from the same cycle (typically 1 year) together and paying close
attention to the treatment of adjacent cycles, we avoid information leakage
between train and test sets.

Example:
    Countdown the 4 weeks until New Year's Eve

    >>> import lilio
    >>> calendar = lilio.Calendar(anchor="12-31")
    >>> calendar.add_intervals("target", "1d")
    >>> calendar.add_intervals("precursor", "4W", n=4)
    >>> calendar # doctest: +NORMALIZE_WHITESPACE
    Calendar(
        anchor='12-31',
        allow_overlap=False,
        mapping=None,
        intervals=[
            Interval(role='target', length='1d', gap='0d'),
            Interval(role='precursor', length='4W', gap='0d'),
            Interval(role='precursor', length='4W', gap='0d'),
            Interval(role='precursor', length='4W', gap='0d'),
            Interval(role='precursor', length='4W', gap='0d')
        ]
    )

    Get the 180-day periods leading up to New Year's eve for the year 2020

    >>> calendar = lilio.daily_calendar(anchor="12-31", length="180d")
    >>> calendar = calendar.map_years(2020, 2020)
    >>> calendar.show() # doctest: +NORMALIZE_WHITESPACE
    i_interval                         -1                         1
    anchor_year
    2020         [2020-07-04, 2020-12-31)  [2020-12-31, 2021-06-29)

    Get the 180-day periods leading up to New Year's eve for 2020 - 2022 inclusive.

    >>> calendar = lilio.daily_calendar(anchor="12-31", length="180d")
    >>> calendar = calendar.map_years(2020, 2022)
    >>> # note the leap year:
    >>> calendar.show() # doctest: +NORMALIZE_WHITESPACE
    i_interval                         -1                         1
    anchor_year
    2022         [2022-07-04, 2022-12-31)  [2022-12-31, 2023-06-29)
    2021         [2021-07-04, 2021-12-31)  [2021-12-31, 2022-06-29)
    2020         [2020-07-04, 2020-12-31)  [2020-12-31, 2021-06-29)

    To get a stacked representation:

    >>> calendar.map_years(2020, 2022).flat
    anchor_year  i_interval
    2022         -1            [2022-07-04 00:00:00, 2022-12-31 00:00:00)
                  1            [2022-12-31 00:00:00, 2023-06-29 00:00:00)
    2021         -1            [2021-07-04 00:00:00, 2021-12-31 00:00:00)
                  1            [2021-12-31 00:00:00, 2022-06-29 00:00:00)
    2020         -1            [2020-07-04 00:00:00, 2020-12-31 00:00:00)
                  1            [2020-12-31 00:00:00, 2021-06-29 00:00:00)
    dtype: interval

"""

import logging
from lilio import calendar_shifter
from lilio import traintest
from .calendar import Calendar
from .calendar import Interval
from .calendar_shorthands import daily_calendar
from .calendar_shorthands import monthly_calendar
from .calendar_shorthands import weekly_calendar
from .resampling import resample


logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Claire Donnelly"
__email__ = "c.donnelly@esciencecenter.nl"
__version__ = "0.5.0"

__all__ = [
    "Calendar",
    "Interval",
    "resample",
    "daily_calendar",
    "monthly_calendar",
    "weekly_calendar",
    "calendar_shifter",
    "traintest",
]
