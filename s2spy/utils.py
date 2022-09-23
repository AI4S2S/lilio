import re
import warnings
from typing import Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.patches import Rectangle


PandasData = (pd.Series, pd.DataFrame)
XArrayData = (xr.DataArray, xr.Dataset)


def check_timeseries(data) -> None:
    """Utility function to check input data.

    Checks if:
     - Input data is pd.Dataframe/pd.Series/xr.Dataset/xr.DataArray.
     - Input data has a time index (pd), or a dim named `time` containing datetime
       values
    """
    if not isinstance(data, PandasData + XArrayData):
        raise ValueError("The input data is neither a pandas or xarray object")
    if isinstance(data, PandasData):
        check_time_dim_pandas(data)
    elif isinstance(data, XArrayData):
        check_time_dim_xarray(data)


def check_time_dim_xarray(data) -> None:
    """Utility function to check if xarray data has a time dimensions with time data."""
    if "time" not in data.dims:
        raise ValueError(
            "The input DataArray/Dataset does not contain a `time` dimension"
        )
    if not xr.core.common.is_np_datetime_like(data["time"].dtype):
        raise ValueError("The `time` dimension is not of a datetime format")


def check_time_dim_pandas(data) -> None:
    """Utility function to check if pandas data has an index with time data."""
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("The input data does not have a datetime index.")


def check_empty_intervals(data: Union[pd.DataFrame, xr.Dataset]) -> None:
    """Utility to check for empty intervals in data.

    Note: For the Dataset, all values within a certain interval, anchor_year combination
    have to be NaN, to allow for, e.g., empty gridcells in a latitude/longitude grid.

    Args:
        data (Union[pd.DataFrame, xr.Dataset]): Data that should be checked for empty
            intervals. Should be done after resampling the data.

    Raises:
        UserWarning: If the data is insufficient.

    Returns:
        None
    """
    if isinstance(data, pd.DataFrame) and not np.any(np.isnan(data.iloc[:, 3:])):
        return None
    if isinstance(data, xr.Dataset) and not any(
        data[var].isnull().any(dim=["i_interval", "anchor_year"]).all()
        for var in data.data_vars
    ):
        return None

    warnings.warn(
        "The input data could not fully cover the calendar's intervals. "
        "Intervals without available data will contain NaN values."
    )
    return None


def check_input_frequency(calendar, data):
    """Checks the frequency of (input) data.

    Note: Pandas and xarray have the builtin function `infer_freq`, but this function is
    not robust enough for our purpose, so we have to manually infer the frequency if the
    builtin one fails.
    """
    if isinstance(data, PandasData):
        data_freq = pd.infer_freq(data.index)
        if data_freq is None:  # Manually infer the frequency
            data_freq = np.min(data.index.values[1:] - data.index.values[:-1])
    else:
        data_freq = xr.infer_freq(data.time)
        if data_freq is None:  # Manually infer the frequency
            data_freq = (data.time.values[1:] - data.time.values[:-1]).min()

    if isinstance(data_freq, str):
        data_freq.replace("-", "")
        if not re.match(r"\d+\D", data_freq):
            data_freq = "1" + data_freq

    if pd.Timedelta(calendar.freq) < pd.Timedelta(data_freq):
        warnings.warn(
            """Target frequency is smaller than the original frequency.
            The resampled data will contain NaN values, as there is no data
            available within all intervals."""
        )


def convert_interval_to_bounds(data: xr.Dataset) -> xr.Dataset:
    """Converts pandas intervals to bounds in a xarray Dataset.

    pd.Interval objects cannot be written to netCDF. To allow writing the
    calendar-resampled data to netCDF these intervals have to be converted to bounds.
    This function adds a 'bounds' dimension, with 'left' and 'right' coordinates, and
    converts the 'interval' coordinates to this system.

    Args:
        data: Input data with intervals as pd.Interval objects.

    Returns:
        Input data with the intervals converted to bounds.
    """
    stacked = data.stack(coord=["anchor_year", "i_interval"])
    bounds = np.array([[val.left, val.right] for val in stacked.interval.values])
    stacked["interval"] = (("coord", "bounds"), bounds)
    return stacked.unstack("coord")


def plot_interval(
    anchor_date: pd.Timestamp,
    interval: pd.Interval,
    ax: plt.Axes,
    color: str,
    add_freq: bool = False,
):
    """Utility for the calendar visualization.

    Plots a rectangle representing a single interval.

    Args:
        anchor_date: Pandas timestamp representing the anchor date.
        interval: Interval that should be added to the plot.
        ax: Axis to plot the interval in.
        color: (Matplotlib compatible) color that the rectangle should have.
        add_freq: Toggles if the frequency will be displayed on the rectangle
    """
    right = (anchor_date - interval.right).days
    hwidth = (interval.right - interval.left).days

    ax.add_patch(
        Rectangle(
            (right, anchor_date.year - 0.4),
            hwidth,
            0.8,
            facecolor=color,
            alpha=0.7,
            edgecolor="k",
            linewidth=1.5,
        )
    )

    if add_freq:
        ax.text(
            x=right + hwidth / 2,
            y=anchor_date.year,
            s=hwidth,
            c="k",
            size=8,
            ha="center",
            va="center",
        )
