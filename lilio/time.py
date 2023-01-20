"""lilio time utils.

Utilities designed to aid in seasonal-to-subseasonal prediction experiments in
which we search for skillful predictors preceding a certain event of interest.

Time indices are anchored to the target period of interest. By keeping
observations from the same cycle (typically 1 year) together and paying close
attention to the treatment of adjacent cycles, we avoid information leakage
between train and test sets.

Example:
    >>> import lilio.time
    >>>
    >>> # Countdown the weeks until New Year's Eve
    >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="7d")
    >>> calendar # doctest: +NORMALIZE_WHITESPACE
    AdventCalendar(
        anchor='12-31',
        freq='7d',
        n_targets=1,
        max_lag=0,
        allow_overlap=False,
        mapping=None
    )

    >>> # Get the 180-day periods leading up to New Year's eve for the year 2020
    >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="180d")
    >>> calendar = calendar.map_years(2020, 2020)
    >>> calendar.show() # doctest: +NORMALIZE_WHITESPACE
    i_interval                         -1                         1
    anchor_year
    2020         [2020-07-04, 2020-12-31)  [2020-12-31, 2021-06-29)

    >>> # Get the 180-day periods leading up to New Year's eve for 2020 - 2022 inclusive.
    >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="180d")
    >>> calendar = calendar.map_years(2020, 2022)
    >>> # note the leap year:
    >>> calendar.show() # doctest: +NORMALIZE_WHITESPACE
    i_interval                         -1                         1
    anchor_year
    2022         [2022-07-04, 2022-12-31)  [2022-12-31, 2023-06-29)
    2021         [2021-07-04, 2021-12-31)  [2021-12-31, 2022-06-29)
    2020         [2020-07-04, 2020-12-31)  [2020-12-31, 2021-06-29)

    >>> # To get a stacked representation:
    >>> calendar.map_years(2020, 2022).flat
    anchor_year  i_interval
    2022         -1            [2022-07-04, 2022-12-31)
                  1            [2022-12-31, 2023-06-29)
    2021         -1            [2021-07-04, 2021-12-31)
                  1            [2021-12-31, 2022-06-29)
    2020         -1            [2020-07-04, 2020-12-31)
                  1            [2020-12-31, 2021-06-29)
    dtype: interval

"""

# pylint: disable=unused-import
from ._resample import resample
from .calendar import Calendar
from .calendar import Interval
from .calendar_shorthands import daily_calendar
from .calendar_shorthands import monthly_calendar
from .calendar_shorthands import weekly_calendar
