import re
from .calendar import Calendar


def daily_calendar(
    anchor: str,
    freq: str = "1d",
    n_targets: int = 1,
    max_lag: int = 0,
    allow_overlap: bool = False,
) -> Calendar:
    """Instantiate a basic daily calendar with minimal configuration.

    Set up the calendar with given freq ending exactly on the anchor date.
    The index will extend back in time as many periods as fit within the
    cycle time of one year.

    Args:
        anchor: String in the form "12-31" for December 31st. Effectively the origin
            of the calendar. It will countdown to this date.
        freq: Frequency of the calendar.
        n_targets: integer specifying the number of target intervals in a period.
        max_lag: Sets the maximum number of lag periods after the target period. If
            `0`, the maximum lag will be determined by how many fit in each anchor year.
            If a maximum lag is provided, the intervals can either only cover part
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

        >>> import lilio.time
        >>> calendar = lilio.time.daily_calendar(anchor='12-25', freq="3d", max_lag=3)
        >>> calendar
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
    if not re.fullmatch(r"\d*d", freq):
        raise ValueError("Please input a frequency in the form of '2d'")
    n_freq = int(freq.replace("d", ""))

    cal = Calendar(
        anchor=anchor,
        allow_overlap=allow_overlap
        )

    cal.add_intervals(role="target", length=freq, n=n_targets)
    cal.add_intervals(
        role="precursor",
        length=freq,
        n=(365//n_freq - n_targets if max_lag==0 else max_lag)
    )

    return cal


def weekly_calendar(
    anchor: str,
    freq: str = "1W",
    n_targets: int = 1,
    max_lag: int = 0,
    allow_overlap: bool = False,
) -> Calendar:
    """Instantiate a basic monthly calendar with minimal configuration.

    Set up the calendar with given freq ending exactly on the anchor week.
    The index will extend back in time as many weeks as fit within the
    cycle time of one year (i.e. 52).

    Note that the difference between this calendar and the daily_calendar revolves
    around the use of calendar weeks (Monday - Sunday), instead of 7-day periods.

    Args:
        anchor: Str in the form of "40W", denoting the week number. Effectively the
            origin of the calendar. It will countdown to this week.
        freq: Frequency of the calendar, e.g. '2W'.
        n_targets: integer specifying the number of target intervals in a period.
        max_lag: Sets the maximum number of lag periods after the target period. If
            `0`, the maximum lag will be determined by how many fit in each anchor year.
            If a maximum lag is provided, the intervals can either only cover part
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

        >>> import lilio.time
        >>> calendar = lilio.time.weekly_calendar(anchor="W40", freq="1W", max_lag=2)
        >>> calendar
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
    if not re.fullmatch(r"\d*W", freq):
        raise ValueError("Please input a frequency in the form of '4W'")
    n_freq = int(freq.replace("W", ""))

    cal = Calendar(
        anchor=anchor,
        allow_overlap=allow_overlap
        )

    cal.add_intervals(role="target", length=freq, n=n_targets)
    cal.add_intervals(
        role="precursor",
        length=freq,
        n=(52//n_freq - n_targets if max_lag==0 else max_lag)
    )

    return cal


def monthly_calendar(
    anchor: str,
    freq: str = "1M",
    n_targets: int = 1,
    max_lag: int = 0,
    allow_overlap: bool = False,
) -> Calendar:
    """Instantiate a basic monthly calendar with minimal configuration.

    Set up the calendar with given freq ending exactly on the anchor month.
    The index will extend back in time as many periods as fit within the
    cycle time of one year.

    Args:
        anchor: Str in the form 'January' or 'Jan'. Effectively the origin
            of the calendar. It will countdown to this month.
        freq: Frequency of the calendar, in the form '1M', '2M', etc.
        n_targets: integer specifying the number of target intervals in a period.
        max_lag: Sets the maximum number of lag periods after the target period. If
            `0`, the maximum lag will be determined by how many fit in each anchor year.
            If a maximum lag is provided, the intervals can either only cover part
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

        >>> import lilio.time
        >>> calendar = lilio.time.monthly_calendar(anchor='Dec', freq="3M")
        >>> calendar
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
    if not re.fullmatch(r"\d*M", freq):
        raise ValueError("Please input a frequency in the form of '2M'")
    n_freq = int(freq.replace("M", ""))

    cal = Calendar(
        anchor=anchor,
        allow_overlap=allow_overlap
        )

    cal.add_intervals(role="target", length=freq, n=n_targets)
    cal.add_intervals(
        role="precursor",
        length=freq,
        n=(12//n_freq - n_targets if max_lag==0 else max_lag)
    )

    return cal
