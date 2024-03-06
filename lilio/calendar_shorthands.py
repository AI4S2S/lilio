"""Shorthands for calendars, to make generating commonly used calendars a one-liner."""

import re
import pandas as pd
from .calendar import Calendar


def daily_calendar(
    anchor: str,
    length: str = "1d",
    n_targets: int = 1,
    n_precursors: int = 0,
    allow_overlap: bool = False,
) -> Calendar:
    """Instantiate a basic daily calendar with minimal configuration.

    Set up a quick calendar revolving around intervals with day-based lengths.
    The intervals will extend back in time with as many intervals as fit within the
    cycle time of one year.

    Args:
        anchor: String in the form "12-31" for December 31st. The first target interval
            will contain the anchor, while the precursor intervals are built back in
            time starting at this date.
        length: The length of every target and precursor period.
        n_targets: integer specifying the number of target intervals in a period.
        n_precursors: Sets the maximum number of precursors of the Calendar. If
            `0`, the amount will be determined by how many fit in each anchor year.
            If a value is provided, the intervals can either only cover part
            of the year, or extend over multiple years. In case of a large max_lag
            number where the intervals extend over multiple years, anchor years will
            be skipped to avoid overlapping intervals. To allow overlapping
            intervals, use the `allow_overlap` kwarg.
        allow_overlap: Allows intervals to overlap between anchor years, if the
            max_lag is set to a high enough number that intervals extend over
            multiple years. `False` by default, to avoid train/test information
            leakage.

    Returns:
        An instantiated Calendar built according to the input kwarg specifications

    Example:
        Instantiate a calendar counting towards Christmas in 3-days steps.

        >>> import lilio
        >>> calendar = lilio.daily_calendar(anchor='12-25', length="3d", n_precursors=3)
        >>> calendar  # doctest: +NORMALIZE_WHITESPACE
        Calendar(
            anchor='12-25',
            allow_overlap=False,
            mapping=None,
            intervals=[
                Interval(role='target', length='3d', gap='0d'),
                Interval(role='precursor', length='3d', gap='0d'),
                Interval(role='precursor', length='3d', gap='0d'),
                Interval(role='precursor', length='3d', gap='0d')
            ]
        )

    """
    if not re.fullmatch(r"\d*d", length):
        raise ValueError("Please input a frequency in the form of '2d'")
    periods_per_year = pd.Timedelta("365days") / pd.to_timedelta(length)
    n_intervals = (
        (n_precursors + n_targets) if n_precursors > 0 else int(periods_per_year)
    )
    n_precursors = n_intervals - n_targets

    cal = Calendar(anchor=anchor, allow_overlap=allow_overlap)

    cal.add_intervals(role="target", length=length, n=n_targets)
    if n_precursors > 0:
        cal.add_intervals(role="precursor", length=length, n=n_precursors)

    return cal


def weekly_calendar(
    anchor: str,
    length: str = "1W",
    n_targets: int = 1,
    n_precursors: int = 0,
    allow_overlap: bool = False,
) -> Calendar:
    """Instantiate a basic monthly calendar with minimal configuration.

    Set up a quick calendar revolving around intervals with week-based lengths.
    The precursor intervals will extend back in time with as many intervals as fit
    within the cycle time of one year (i.e. 52 - n_targets).

    Note that the difference between this calendar and the daily_calendar revolves
    around the use of calendar weeks (Monday - Sunday), instead of 7-day periods.

    Args:
        anchor: Str in the form of "40W", denoting the week number. The first target
            interval will contain the anchor, while the precursor intervals are built
            back in time starting from this week.
        length: The length of every precursor and target interval, e.g. '2W'.
        n_targets: integer specifying the number of target intervals in a period.
        n_precursors: Sets the maximum number of precursors of the Calendar. If
            `0`, the amount will be determined by how many fit in each anchor year.
            If a value is provided, the intervals can either only cover part
            of the year, or extend over multiple years. In case of a large max_lag
            number where the intervals extend over multiple years, anchor years will
            be skipped to avoid overlapping intervals. To allow overlapping
            intervals, use the `allow_overlap` kwarg.
        allow_overlap: Allows intervals to overlap between anchor years, if the
            max_lag is set to a high enough number that intervals extend over
            multiple years. `False` by default, to avoid train/test information
            leakage.

    Returns:
        An instantiated Calendar built according to the input kwarg specifications

    Example:
        Instantiate a calendar counting down the quarters (3 month periods) from
        december.

        >>> import lilio
        >>> calendar = lilio.weekly_calendar(anchor="W40", length="1W", n_precursors=2)
        >>> calendar  # doctest: +NORMALIZE_WHITESPACE
        Calendar(
            anchor='W40-1',
            allow_overlap=False,
            mapping=None,
            intervals=[
                Interval(role='target', length='1W', gap='0d'),
                Interval(role='precursor', length='1W', gap='0d'),
                Interval(role='precursor', length='1W', gap='0d')
            ]
        )

    """
    if not re.fullmatch(r"\d*W", length):
        raise ValueError("Please input a frequency in the form of '4W'")
    periods_per_year = pd.Timedelta("365days") / pd.to_timedelta(length)
    n_intervals = (
        (n_precursors + n_targets) if n_precursors > 0 else int(periods_per_year)
    )
    n_precursors = n_intervals - n_targets

    cal = Calendar(anchor=anchor, allow_overlap=allow_overlap)

    cal.add_intervals(role="target", length=length, n=n_targets)
    if n_precursors > 0:
        cal.add_intervals(role="precursor", length=length, n=n_precursors)

    return cal


def monthly_calendar(
    anchor: str,
    length: str = "1M",
    n_targets: int = 1,
    n_precursors: int = 0,
    allow_overlap: bool = False,
) -> Calendar:
    """Instantiate a basic monthly calendar with minimal configuration.

    Set up a quick calendar revolving around intervals with month-based lengths.
    The intervals will extend back in time with as many intervals as fit within the
    cycle time of one year.

    Args:
        anchor: Str in the form 'January' or 'Jan'. he first target interval
            will contain the anchor, while the precursor intervals are built back in
            time starting at this Month.
        length: The length of every target and precursor period, in the form '1M',
            '2M', etc.
        n_targets: integer specifying the number of target intervals in a period.
        n_precursors: Sets the maximum number of precursors of the Calendar. If
            `0`, the amount will be determined by how many fit in each anchor year.
            If a value is provided, the intervals can either only cover part
            of the year, or extend over multiple years. In case of a large max_lag
            number where the intervals extend over multiple years, anchor years will
            be skipped to avoid overlapping intervals. To allow overlapping
            intervals, use the `allow_overlap` kwarg.
        allow_overlap: Allows intervals to overlap between anchor years, if the
            max_lag is set to a high enough number that intervals extend over
            multiple years. `False` by default, to avoid train/test information
            leakage.

    Returns:
        An instantiated Calendar built according to the input kwarg specifications

    Example:
        Instantiate a calendar counting down the quarters (3 month periods) from
        december.

        >>> import lilio
        >>> calendar = lilio.monthly_calendar(anchor='Dec', length="3M")
        >>> calendar  # doctest: +NORMALIZE_WHITESPACE
        Calendar(
            anchor='12',
            allow_overlap=False,
            mapping=None,
            intervals=[
                Interval(role='target', length='3M', gap='0d'),
                Interval(role='precursor', length='3M', gap='0d'),
                Interval(role='precursor', length='3M', gap='0d'),
                Interval(role='precursor', length='3M', gap='0d')
            ]
        )

    """
    if not re.fullmatch(r"\d*M", length):
        raise ValueError("Please input a frequency in the form of '2M'")
    periods_per_year = 12 / int(length.replace("M", ""))
    n_intervals = (
        (n_precursors + n_targets) if n_precursors > 0 else int(periods_per_year)
    )
    n_precursors = n_intervals - n_targets

    cal = Calendar(anchor=anchor, allow_overlap=allow_overlap)

    cal.add_intervals(role="target", length=length, n=n_targets)
    if n_precursors > 0:
        cal.add_intervals(role="precursor", length=length, n=n_precursors)

    return cal
