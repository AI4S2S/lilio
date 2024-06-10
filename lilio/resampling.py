"""The implementation of the resampling methods for use with the Calendar."""

import typing
from typing import Callable
from typing import Literal
from typing import Union
from typing import overload
import numpy as np
import pandas as pd
import xarray as xr
from lilio import utils
from lilio._attrs import add_attrs
from lilio.calendar import Calendar


# List of numpy statistical methods, with a single input argument and a single output.
ResamplingMethod = Literal[
    "mean",
    "min",
    "max",
    "median",
    "std",
    "var",
    "ptp",
    "nanmean",
    "nanmedian",
    "nanstd",
    "nanvar",
    "sum",
    "nansum",
    "size",
    "count_nonzero",
]
VALID_METHODS = typing.get_args(ResamplingMethod)


def _check_valid_resampling_methods(method: ResamplingMethod):
    """Check if a method is valid as a (numpy) resampling method."""
    if method not in VALID_METHODS:
        raise ValueError(
            f"{method} is not a valid resampling method. Choose from: {VALID_METHODS}"
        )


def _mark_target_period(
    input_data: Union[pd.DataFrame, xr.Dataset],
) -> Union[pd.DataFrame, xr.Dataset]:
    """Mark interval periods that fall within the given number of target periods.

    Pass a pandas Series/DataFrame with an 'i_interval' column, or an xarray
    DataArray/Dataset with an 'i_interval' coordinate axis. It will return an
    object with an added column in the Series/DataFrame or an
    added coordinate axis in the DataSet called 'target'. This is a boolean
    indicating whether the index time interval is a target period or not. This is
    determined by the instance variable 'n_targets'.

    Args:
        input_data: Input data for resampling. For a Pandas object, one of its
        columns must be called 'i_interval'. An xarray object requires a coordinate
        axis named 'i_interval' containing an interval counter for every period.

    Returns:
        Input data with boolean marked target periods, similar data format as
            given inputs.
    """
    if isinstance(input_data, (pd.Series, pd.DataFrame)):
        input_data["is_target"] = np.ones(input_data.index.size, dtype=bool)
        input_data["is_target"] = input_data["is_target"].where(
            input_data["i_interval"] > 0, other=False
        )

    else:
        # input data is xr.Dataset
        target = input_data["i_interval"] > 0
        input_data = input_data.assign_coords(coords={"is_target": target})

    return input_data


def _resample_bins_constructor(
    intervals: Union[pd.Series, pd.DataFrame],
) -> pd.DataFrame:
    """Restructures the interval object into a tidy DataFrame.

    Args:
        intervals: the output interval `pd.Series` or `pd.DataFrame` from the
            `map_to_data` function.

    Returns:
        Pandas DataFrame with 'anchor_year', 'i_interval', and 'interval' as
            columns.
    """
    # Make a tidy dataframe where the intervals are linked to the anchor year
    if isinstance(intervals, pd.DataFrame):
        bins = intervals.copy()
        bins.index.rename("anchor_year", inplace=True)
        bins = bins.melt(
            var_name="i_interval", value_name="interval", ignore_index=False
        )
        bins = bins.sort_values(by=["anchor_year", "i_interval"])
    else:
        # Massage the dataframe into the same tidy format for a single year
        bins = pd.DataFrame(intervals)
        bins = bins.melt(
            var_name="anchor_year", value_name="interval", ignore_index=False
        )
        bins.index.rename("i_interval", inplace=True)
    bins = bins.reset_index()

    return bins


def _contains(interval_index: pd.IntervalIndex, timestamps) -> np.ndarray:
    """Check elementwise if the intervals contain the timestamps.

    Will return a boolean array of the shape (n_timestamps, n_intervals).

    Args:
        interval_index: An IntervalIndex containing all intervals that should be
            checked.
        timestamps: A 1-D array containing

    Returns:
        np.ndarray: 2-D mask array
    """
    if interval_index.closed_left:
        a = np.greater_equal(timestamps, interval_index.left.values[np.newaxis].T)
    else:
        a = np.greater(timestamps, interval_index.left.values[np.newaxis].T)
    if interval_index.closed_right:
        b = np.less_equal(timestamps, interval_index.right.values[np.newaxis].T)
    else:
        b = np.less(timestamps, interval_index.right.values[np.newaxis].T)
    return a & b


def _resample_pandas(
    calendar: Calendar,
    input_data: Union[pd.Series, pd.DataFrame],
    how: Union[ResamplingMethod, Callable[[np.ndarray], np.ndarray]],
) -> pd.DataFrame:
    """Resample Pandas data.

    Args:
        calendar: Mapped Lilio Calendar object.
        input_data: Data provided by the user to the `resample` function
        how: Which resampling method should be used. Can also be a function that takes a
            single input argument and has a single output argument.

    Returns:
        pd.DataFrame: DataFrame containing the intervals and data resampled to
            these intervals.
    """
    resampling_method = getattr(np, how) if isinstance(how, str) else how

    if isinstance(input_data, pd.Series):
        name = "data" if input_data.name is None else input_data.name
        input_data = pd.DataFrame(input_data.rename(name))

    data = _resample_bins_constructor(calendar.get_intervals())
    contains_matrix = _contains(
        pd.IntervalIndex(data.interval.values), input_data.index.values
    )

    utils.check_empty_intervals(
        indices_list=[np.argwhere(row).T[0] for row in contains_matrix]
    )

    for colname in input_data.columns:
        resampled_data = np.zeros(contains_matrix.shape[0])
        for i, row in enumerate(contains_matrix):
            resampled_data[i] = resampling_method(input_data[colname].values[row])
        data[colname] = resampled_data

    return data


def _resample_dataset(
    calendar: Calendar,
    input_data: xr.Dataset,
    how: Union[ResamplingMethod, Callable[[np.ndarray], np.ndarray]],
) -> xr.Dataset:
    """Resample xarray data.

    Args:
        calendar: A mapped Lilio Calendar object
        input_data (xr.DataArray or xr.Dataset): Data provided by the user to the
            `resample` function
        how: Which resampling method should be used. Can also be a function that takes a
            single input argument and has a single output argument.

    Returns:
        xr.Dataset: Dataset containing the intervals and data resampled to
            these intervals.
    """
    resampling_method = getattr(np, how) if isinstance(how, str) else how
    data = calendar.flat.to_xarray().rename("interval")
    data = data.to_dataset()
    data = data.stack(anch_int=("anchor_year", "i_interval"))

    intervals = pd.IntervalIndex(data["interval"].values)
    timesteps = input_data["time"].to_numpy()

    indices_list: list[np.ndarray] = [np.ndarray(0)] * len(intervals)
    for i in range(len(intervals)):
        row = _contains(intervals[[i]], timesteps)[0]
        indices_list[i] = np.argwhere(row).T[0]

    utils.check_empty_intervals(indices_list)

    # Separate data with time dims (should be resampled), from data without time dims
    #   (which does not need resampling).
    input_data_time = input_data[
        [var for var in input_data.data_vars if "time" in input_data[var].dims]
    ]
    input_data_nontime = input_data[
        [var for var in input_data.data_vars if "time" not in input_data[var].dims]
    ]

    data_list = [xr.Dataset] * len(intervals)
    for i in range(len(intervals)):
        data_list[i] = xr.apply_ufunc(
            resampling_method,
            input_data_time.isel(time=indices_list[i]),
            input_core_dims=[["time"]],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",  # only does something when data is a Dask array
            dask_gufunc_kwargs={"allow_rechunk": True},  # Same as above
        )

    input_data_resampled = xr.concat(data_list, dim="anch_int")  # type: ignore

    if input_data_nontime.data_vars:
        data = xr.merge(
            [data, input_data_nontime, input_data_resampled]  # type: ignore
        )
    else:
        data = xr.merge([data, input_data_resampled])  # type: ignore

    data = data.unstack()
    data = utils.convert_interval_to_bounds(data)
    data = data.transpose("anchor_year", "i_interval", ...)
    return data.sortby("anchor_year", "i_interval")


@overload
def resample(calendar: Calendar, input_data: xr.Dataset) -> xr.Dataset: ...


@overload
def resample(calendar: Calendar, input_data: xr.DataArray) -> xr.DataArray: ...


@overload
def resample(
    calendar: Calendar, input_data: Union[pd.Series, pd.DataFrame]
) -> pd.DataFrame: ...


def resample(
    calendar: Calendar,
    input_data: Union[pd.Series, pd.DataFrame, xr.DataArray, xr.Dataset],
    how: Union[ResamplingMethod, Callable[[np.ndarray], np.ndarray]] = "mean",
) -> Union[pd.DataFrame, xr.DataArray, xr.Dataset]:
    """Resample input data to the Calendar's intervals.

    Pass a pandas Series/DataFrame with a datetime axis, or an
    xarray DataArray/Dataset with a datetime coordinate called 'time'.
    It will return the same object with the datetimes resampled onto
    the Calendar's Index by binning the data into the Calendar's intervals
    and calculating the mean of each bin.

    The default behavior is to calculate the mean for each interval. However, many other
    statistics can be calculated, namely:
        - mean, min, max, median
        - std, var, ptp (peak-to-peak)
        - nanmean, nanmedian, nanstd, nanvar
        - sum, nansum, size, count_nonzero

    "size" will compute the number of datapoints that are in each interval, and can be
    used to check if the input data is of a sufficiently high resolution to be resampled
    to the calendar.

    Note: this function is intended for upscaling operations, which means
    the calendar frequency is larger than the original frequency of input data (e.g.
    `freq` is "7days" and the input is daily data). It supports downscaling
    operations but the user need to be careful since the returned values may contain
    "NaN".

    Args:
        calendar: Calendar object with either a map_year or map_to_data mapping.
        input_data: Input data for resampling. For a Pandas object its index must be
            either a pandas.DatetimeIndex. An xarray object requires a dimension
            named 'time' containing datetime values.
        how: Which method for resampling should be used. Either a string or function.
            The following methods are supported as a string input:
                mean, min, max, median
                std, var, ptp (peak-to-peak)
                nanmean, nanmedian, nanstd, nanvar
                sum, nansum, size, count_nonzero
            Alternatively, a function can be passed. For example
            `resample(how=np.mean)`.

    Raises:
        UserWarning: If the calendar frequency is smaller than the frequency of
            input data

    Returns:
        Input data resampled based on the calendar frequency, similar data format as
            given inputs.

    Example:
        Assuming the input data is pd.DataFrame containing random values with index
        from 2021-11-11 to 2021-11-01 at daily frequency.

        >>> import lilio
        >>> import pandas as pd
        >>> import numpy as np
        >>> cal = lilio.daily_calendar(anchor="12-31", length="180d")
        >>> time_index = pd.date_range("2019-01-01", "2022-01-01", freq="1d")
        >>> var = np.arange(len(time_index))
        >>> input_data = pd.Series(var, index=time_index)
        >>> cal = cal.map_to_data(input_data)
        >>> bins = lilio.resample(cal, input_data)
        >>> bins # doctest: +NORMALIZE_WHITESPACE
           anchor_year  i_interval  ...   data  is_target
        0         2019          -1  ...  273.5      False
        1         2019           1  ...  453.5       True
        2         2020          -1  ...  639.5      False
        3         2020           1  ...  819.5       True
        [4 rows x 5 columns]
    """
    if calendar.mapping is None:
        raise ValueError("Generate a calendar map before calling resample")
    if calendar.n_targets + calendar.n_precursors == 0:
        raise ValueError("The calendar has no intervals: resampling is not possible.")

    if isinstance(how, str):
        _check_valid_resampling_methods(how)
    utils.check_timeseries(input_data)
    utils.check_input_frequency(calendar, input_data)
    utils.check_reserved_names(input_data)

    if isinstance(input_data, (pd.Series, pd.DataFrame)):
        resampled_data = _resample_pandas(calendar, input_data, how)
    elif isinstance(input_data, xr.DataArray):
        da_name = "data" if input_data.name is None else input_data.name
        input_data.name = da_name
        resampled_data = _resample_dataset(calendar, input_data.to_dataset(), how)
    else:
        resampled_data = _resample_dataset(calendar, input_data, how)

    resampled_data = _mark_target_period(resampled_data)

    if isinstance(input_data, xr.DataArray):
        resampled_dataarray = resampled_data[da_name]
        resampled_dataarray.attrs = input_data.attrs
        add_attrs(resampled_dataarray, calendar)
        return resampled_dataarray
    if isinstance(input_data, xr.Dataset):
        resampled_data.attrs = input_data.attrs
        add_attrs(resampled_data, calendar)
    return resampled_data
