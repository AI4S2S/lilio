"""Commonly used utility functions for Lilio."""

import re
import typing
import warnings
from typing import Union
import numpy as np
import pandas as pd
import xarray as xr


if typing.TYPE_CHECKING:
    from lilio import Calendar


MONTH_LENGTH = 30  # Month length for Timedelta checks.


def check_timeseries(
    data: Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
) -> None:
    """Check if input data contains valid time data.

    Checks if:
     - Input data is pd.Dataframe/pd.Series/xr.Dataset/xr.DataArray.
     - Input data has a time index (pd), or a dim named `time` containing datetime
       values
    """
    if not isinstance(data, (pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset)):
        raise ValueError("The input data is neither a pandas or xarray object")
    if isinstance(data, (pd.Series, pd.DataFrame)):
        check_time_dim_pandas(data)
    elif isinstance(data, (xr.DataArray, xr.Dataset)):
        check_time_dim_xarray(data)


def is_dask_array(data: Union[xr.DataArray, xr.Dataset]) -> bool:
    """Check if the xarray dataset/array has any dask arrays."""
    if isinstance(data, xr.DataArray):
        return False if data.chunks is None else True

    if any([data[var].chunks is not None for var in list(data.variables)]):
        return True
    else:
        return False


def check_time_dim_xarray(data) -> None:
    """Check if an xarray data has a time dimensions with time data."""
    if "time" not in data.dims:
        raise ValueError(
            "The input DataArray/Dataset does not contain a `time` dimension"
        )
    if not xr.core.common.is_np_datetime_like(data["time"].dtype):  # type: ignore
        raise ValueError("The `time` dimension is not of a datetime format")


def check_time_dim_pandas(data) -> None:
    """Check if pandas data has an index with time data."""
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("The input data does not have a datetime index.")


def check_empty_intervals(indices_list: list[np.ndarray]) -> None:
    """Check for empty intervals in the resampling data.

    Args:
        indices_list: A list, where each item is an array with indices corresponding
            to the to-be-resampled data's time axis.

    Raises:
        UserWarning: If the data is insufficient.

    Returns:
        None
    """
    if any(len(interval_locs) == 1 for interval_locs in indices_list):
        warnings.warn(  # type: ignore
            message=(
                "\n  Some intervals only contains a single data point."
                "\n  This could lead to issues like aliasing or incorrect resampling."
                "\n  If possible: make the Calendar's intervals larger, or use data of"
                "\n  a higher time resolution."
            ),
            stacklevel=1,
        )
    elif any(len(interval_locs) == 0 for interval_locs in indices_list):
        warnings.warn(  # type: ignore
            message=(
                "\n  The input data could not fully cover the calendar's intervals."
                "\n  Intervals without available data will contain NaN values."
                "\n  If possible: make the Calendar's intervals larger, or use data of"
                "\n  a higher time resolution."
            ),
            stacklevel=1,
        )


def infer_input_data_freq(
    data: Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
) -> pd.Timedelta:
    """Infer the frequency of the input data, for comparison with the calendar freq.

    Args:
        data: Pandas or xarray data to infer the frequency of.

    Returns:
        a pd.Timedelta
    """
    if isinstance(data, (pd.Series, pd.DataFrame)):
        data_freq = pd.infer_freq(data.index)
        if data_freq is None:  # Manually infer the frequency
            data_freq = np.min(data.index.values[1:] - data.index.values[:-1])
    else:
        data_freq = xr.infer_freq(data.time)
        if data_freq is None:  # Manually infer the frequency
            data_freq = (data.time.values[1:] - data.time.values[:-1]).min()

    if isinstance(data_freq, str):
        data_freq.replace("-", "")  # Get the absolute frequency

        data_freq = data_freq.replace("ME", "M").replace("MS", "M")

        if not re.match(r"\d+\D", data_freq):  # infer_freq can return "d" for "1d".
            data_freq = "1" + data_freq

        data_freq = (  # Deal with monthly timedelta case
            replace_month_length(data_freq) if data_freq[-1] == "M" else data_freq
        )
    return pd.Timedelta(data_freq)


def replace_month_length(length: str) -> str:
    """Replace month lengths with an equivalent length in days."""
    ndays = int(length[:-1]) * MONTH_LENGTH
    return f"{ndays}d"


def get_smallest_calendar_freq(calendar: "Calendar") -> pd.Timedelta:
    """Return the smallest length of the calendar's intervals as a Timedelta."""
    intervals = calendar.targets + calendar.precursors
    lengthstr = [iv.length for iv in intervals]
    lengthstr = [ln.replace("-", "") for ln in lengthstr]  # Account for neg. lengths
    lengthstr = [replace_month_length(ln) if ln[-1] == "M" else ln for ln in lengthstr]
    lengths = [pd.Timedelta(ln) for ln in lengthstr]
    return min(lengths)


def check_input_frequency(
    calendar: "Calendar", data: Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset]
):
    """Compare the frequency of (input) data to the frequency of the calendar.

    Note: Pandas and xarray have the builtin function `infer_freq`, but this function is
    not robust enough for our purpose, so we have to manually infer the frequency if the
    builtin one fails.
    """
    data_freq = infer_input_data_freq(data)
    calendar_freq = get_smallest_calendar_freq(calendar)

    if calendar_freq < data_freq:
        raise ValueError(
            "The data is of a lower time resolution than the calendar. "
            "This would lead to incorrect data and/or NaN values in the resampled data."
            " Please make the Calendar's intervals larger, or use data of a higher time"
            " resolution."
            f"\nInfered data frequency: {str(data_freq)} < calendar frequency "
            f"{str(calendar_freq)}"
        )
    if calendar_freq < 2 * data_freq:
        warnings.warn(
            "\n  The input data frequency is very close to the Calendar's frequency."
            "\n  This could lead to issues like aliasing or incorrect resampling."
            "\n  If possible: make the Calendar's intervals larger, or use data of a"
            "\n  higher time resolution.",
            stacklevel=1,
        )


def convert_interval_to_bounds(data: xr.Dataset) -> xr.Dataset:
    """Convert pandas intervals to bounds in a xarray Dataset.

    pd.Interval objects cannot be written to netCDF. To allow writing the
    calendar-resampled data to netCDF these intervals have to be converted to bounds.
    This function adds a 'bounds' dimension, with 'left' and 'right' coordinates, and
    converts the 'interval' coordinates to this system.

    Args:
        data: Input data with intervals as pd.Interval objects.

    Returns:
        Input data with the intervals converted to bounds.
    """
    data = data.stack(coord=["anchor_year", "i_interval"])
    bounds = np.array([[val.left, val.right] for val in data.interval.values])
    data["left_bound"] = ("coord", bounds[:, 0])
    data["right_bound"] = ("coord", bounds[:, 1])
    data["left_bound"].attrs = {
        "name": "Left bound of the interval",
        "closed": "True",
    }
    data["right_bound"].attrs = {
        "name": "Right bound of the interval",
        "closed": "False",
    }
    data = data.unstack("coord")
    data = data.drop_vars(["interval"])
    data = data.set_coords(["left_bound", "right_bound"])
    return data


def check_reserved_names(
    input_data: Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
) -> None:
    """Check if reserved names are already in the input data. E.g. "anchor_year"."""
    reserved_names_pd = ["anchor_year", "i_interval", "is_target"]
    reserved_names_xr = reserved_names_pd + ["left_bound", "right_bound"]

    if isinstance(input_data, pd.DataFrame):
        if any(name in input_data.columns for name in reserved_names_pd):
            raise ValueError(
                "The input data contains one or more reserved names. Please remove or "
                f"rename these before continuing.\n Reserved names: {reserved_names_pd}"
            )
    elif isinstance(input_data, (xr.DataArray, xr.Dataset)):
        data_names = [
            input_data.keys()
            if isinstance(input_data, xr.Dataset)
            else list(input_data.coords) + [input_data.name]
        ]
        if any(name in data_names for name in reserved_names_xr):
            raise ValueError(
                "The input data contains one or more reserved names. Please remove or "
                f"rename these before continuing.\n Reserved names: {reserved_names_xr}"
            )


def assert_bokeh_available():
    """Util that attempts to load the optional module bokeh."""
    try:
        import bokeh as _  # noqa: F401 (unused import)

    except ImportError as e:
        raise ImportError(
            "Could not import the `bokeh` module.\nPlease install this"
            " before continuing, with either `pip` or `conda`."
        ) from e


def get_month_names() -> dict:
    """Generate a dictionary with English lowercase month names and abbreviations.

    Returns:
        Dictionary containing the English names of the months, including their
            abbreviations, linked to the number of each month.
            E.g. {'december': 12, 'jan': 1}
    """
    return {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }


def check_month_day(month: int, day: int = 1):
    """Check if the input day/month combination is valid.

    Months must be between 1 and 12, and days must be within 1 and 28/30/31 (depending
    on the month).

    Args:
        month: Month number
        day: Day number. Defaults to 1.
    """
    if month in {1, 3, 5, 7, 8, 10, 12}:
        if (day < 1) or (day > 31):
            raise ValueError(
                "Incorrect anchor input. "
                f"Day number {day} is not a valid day for month {month}"
            )
    elif month in {4, 6, 9, 11}:
        if (day < 1) or (day > 30):
            raise ValueError(
                "Incorrect anchor input. "
                f"Day number {day} is not a valid day for month {month}"
            )
    elif month == 2:
        if (day < 1) or (day > 28):
            raise ValueError(
                "Incorrect anchor input. "
                f"Day number {day} is not a valid day for month {month}"
            )
    else:
        raise ValueError(
            "Incorrect anchor input. Month number must be between 1 and 12."
        )


def check_week_day(week: int, day: int = 1):
    """Validate the week and day numbers."""
    if week == 53:
        raise ValueError(
            "Incorrect anchor input. "
            "Week 53 is not a valid input, as not every year contains a 53rd week."
        )
    if (week < 1) or (week > 52):
        raise ValueError(
            "Incorrect anchor input. Week numbers must be between 1 and 52."
        )
    if (day < 1) or (day > 7):
        raise ValueError(
            "Incorrect anchor input. Weekday numbers must be between 1 and 7."
        )


def parse_freqstr_to_dateoffset(time_str):
    """Parse the user-input time strings.

    Args:
        time_str: Time length string in the right formatting.

    Returns:
        Dictionary as keyword argument for Pandas DateOffset.
    """
    if re.fullmatch(r"[+-]?\d*d", time_str):
        time_dict = {"days": int(time_str[:-1])}
    elif re.fullmatch(r"[+-]?\d*M", time_str):
        time_dict = {"months": int(time_str[:-1])}
    elif re.fullmatch(r"[+-]?\d*W", time_str):
        time_dict = {"weeks": int(time_str[:-1])}
    else:
        raise ValueError("Please input a time string in the correct format.")

    return time_dict
