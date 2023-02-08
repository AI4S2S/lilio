"""Calendar shifter to create staggered calendars."""
import copy
from typing import Dict
from typing import List
from typing import Union
import xarray as xr
from . import calendar
from . import utils
from .resampling import resample


def _gap_shift(
    interval: calendar.Interval, shift: Union[str, Dict[str, int]]
) -> Dict[str, int]:
    """Shift a calendar interval's gap property by the given amount.

    Args:
        interval: The interval that will be shifted
        gap: the pandas DateOffset from a calendar interval's `gap` property.
        shift: the shift for the gap, in the form of a pandas-like frequency
            string (e.g. "10d", "2W", or "3M"), or a pandas.DateOffset compatible
            dictionary such as {days=10}, {weeks=2}, or {months=1, weeks=2}.

    Returns:
        A Pandas DateOffset compatible dictionary, with the gap offset by shift
    """
    if isinstance(interval.gap, str):
        gap_time_dict = utils.parse_freqstr_to_dateoffset(interval.gap)
    else:
        gap_time_dict = interval.gap

    if isinstance(shift, str):
        shift_time_dict = utils.parse_freqstr_to_dateoffset(shift)
    else:
        shift_time_dict = shift
    # make the shift negative for the precursor to shift forward in time
    if interval.role == "precursor":
        shift_time_dict.update(
            (key, value * -1) for key, value in shift_time_dict.items()
        )
    return {
        k: gap_time_dict.get(k, 0) + shift_time_dict.get(k, 0)
        for k in set(gap_time_dict) | set(shift_time_dict)
    }


def calendar_shifter(
    calendar: calendar.Calendar, shift: Union[str, dict]
) -> calendar.Calendar:
    """Shift a Calendar instance by a given time offset.

    Instead of shifting the anchor date, this function shifts two things in reference
    to the anchor date:
        target period(s): as a gap between the anchor date and the start of the first
            target period
        precursor period(s): as a gap between the anchor date and the start of the
            first precursor period
    This way, the anchor year from the input calendar is maintained on the returned
    calendar. This is important for train-test splitting at later stages.

    Args:
        calendar: a lilio.Calendar instance
        shift: a pandas-like
            frequency string (e.g. "10d", "2W", or "3M"), or a pandas.DateOffset
            compatible dictionary such as {days=10}, {weeks=2}, or {months=1, weeks=2}

    Example:
        Shift a calendar by a given dateoffset.

        >>> import lilio
        >>> cal = lilio.Calendar(anchor="07-01")
        >>> cal.add_intervals("target", "7d")
        >>> cal.add_intervals("precursor", "7d", gap="14d")
        >>> cal.add_intervals("precursor", "7d", n=3)
        >>> cal_shifted = lilio.calendar_shifter.calendar_shifter(cal, "7d")
        >>> cal_shifted  # doctest: +NORMALIZE_WHITESPACE
        Calendar(
            anchor='07-01',
            allow_overlap=False,
            mapping=None,
            intervals=[
                Interval(role='target', length='7d', gap={'days': 7}),
                Interval(role='precursor', length='7d', gap={'days': 7}),
                Interval(role='precursor', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='0d')
            ]
        )
    """
    calendar_shifted = copy.deepcopy(calendar)
    calendar_shifted.targets[0].gap = _gap_shift(calendar.targets[0], shift)
    calendar_shifted.precursors[0].gap = _gap_shift(calendar.precursors[0], shift)

    return calendar_shifted


def staggered_calendar(
    calendar: calendar.Calendar, shift: Union[str, dict], n_shifts: int
) -> List[calendar.Calendar]:
    """Create a staggered calendar list by shifting a calendar by an offset n-times.

    Args:
        calendar: an lilio.Calendar instance
        shift: a pandas-like
            frequency string (e.g. "10d", "2W", or "3M"), or a pandas.DateOffset
            compatible dictionary such as {days=10}, {weeks=2}, or {months=1, weeks=2}
        n_shifts: strictly positive integer for the number of shifts

    Example:
        Shift an input calendar n times by a given dateoffset and return a list of these
        shifted calendars.

        >>> import lilio
        >>> cal = lilio.Calendar(anchor="07-01")
        >>> cal.add_intervals("target", "7d")
        >>> cal.add_intervals("precursor", "7d", gap="14d")
        >>> cal.add_intervals("precursor", "7d", n=3)
        >>> cal_shifted = lilio.calendar_shifter.staggered_calendar(cal, "7d", 1)
        >>> cal_shifted  # doctest: +NORMALIZE_WHITESPACE
        [Calendar(
            anchor='07-01',
            allow_overlap=False,
            mapping=None,
            intervals=[
                Interval(role='target', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='14d'),
                Interval(role='precursor', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='0d')
            ]
        ),
        Calendar(
            anchor='07-01',
            allow_overlap=False,
            mapping=None,
            intervals=[
                Interval(role='target', length='7d', gap={'days': 7}),
                Interval(role='precursor', length='7d', gap={'days': 7}),
                Interval(role='precursor', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='0d'),
                Interval(role='precursor', length='7d', gap='0d')
            ]
        )]
    """
    if not isinstance(n_shifts, int):
        raise ValueError(
            "Please input an 'int' type for the 'n' argument."
            f" Not a {type(n_shifts)}."
        )
    if n_shifts <= 0:
        raise ValueError(
            "The number of shifts 'n' has to be 1 or greater, " f"not '{n_shifts}'."
        )
    cal_staggered = [calendar]
    for _ in range(n_shifts):
        cal_shifted = calendar_shifter(cal_staggered[-1], shift)
        cal_staggered.append(cal_shifted)

    return cal_staggered


def calendar_list_resampler(
    cal_list: list, ds: xr.Dataset, dim_name: str = "step"
) -> xr.Dataset:
    """Return a dataset, resampled to every calendar in a list of calendars.

    The resampled calendars will be concatenated along a new dimension (with the default
    name 'step') into a single xarray Dataset.

    Args:
        cal_list: List of calendars.
        ds: Dataset to resample.
        dim_name: The name of the new dimension that will be added to the output
            dataset.

    Returns:
        Resampled xr.Dataset
    """
    ds_r = xr.concat([resample(cal, ds) for cal in cal_list], dim=dim_name)
    ds_r = ds_r.assign_coords({dim_name: ds_r[dim_name].values})

    return ds_r
