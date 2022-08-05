from typing import Union
import numpy as np
import pandas as pd
import xarray as xr


PandasData = (pd.Series, pd.DataFrame)
XArrayData = (xr.DataArray, xr.Dataset)


def mark_target_period(
    calendar, input_data: Union[pd.DataFrame, xr.Dataset]
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
    if isinstance(input_data, PandasData):
        input_data["target"] = np.zeros(input_data.index.size, dtype=bool)
        input_data["target"] = input_data["target"].where(
            input_data["i_interval"] >= calendar.n_targets, other=True
        )

    else:
        # input data is xr.Dataset
        target = input_data["i_interval"] < calendar.n_targets
        input_data = input_data.assign_coords(coords={"target": target})

    return input_data


def resample_bins_constructor(
    intervals: Union[pd.Series, pd.DataFrame]
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


def resample_pandas(
    calendar, input_data: Union[pd.Series, pd.DataFrame]
) -> pd.DataFrame:
    """Internal function to handle resampling of Pandas data.

    Args:
        input_data (pd.Series or pd.DataFrame): Data provided by the user to the
            `resample` function

    Returns:
        pd.DataFrame: DataFrame containing the intervals and data resampled to
            these intervals.
    """
    bins = resample_bins_constructor(calendar.get_intervals())

    interval_index = pd.IntervalIndex(bins["interval"])
    interval_groups = interval_index.get_indexer(input_data.index)
    interval_means = input_data.groupby(interval_groups).mean()

    # drop the -1 index, as it represents data outside of all intervals
    interval_means = interval_means.loc[0:]

    if isinstance(input_data, pd.DataFrame):
        for name in input_data.keys():
            bins[name] = interval_means[name].values
    else:
        name = "mean_data" if input_data.name is None else input_data.name
        bins[name] = interval_means.values

    return bins


def resample_xarray(
    calendar, input_data: Union[xr.DataArray, xr.Dataset]
) -> xr.Dataset:
    """Internal function to handle resampling of xarray data.

    Args:
        input_data (xr.DataArray or xr.Dataset): Data provided by the user to the
            `resample` function

    Returns:
        xr.Dataset: Dataset containing the intervals and data resampled to
            these intervals.
    """
    bins = resample_bins_constructor(calendar.get_intervals())

    # Create the indexer to connect the input data with the intervals
    interval_index = pd.IntervalIndex(bins["interval"])
    interval_groups = interval_index.get_indexer(input_data["time"])
    interval_means = input_data.groupby(
        xr.IndexVariable("time", interval_groups)
    ).mean()
    interval_means = interval_means.rename({"time": "index"})

    # drop the indices below 0, as it represents data outside of all intervals
    interval_means = interval_means.sel(index=slice(0, None))

    # Turn the bins dataframe into an xarray object and merge the data means into it
    bins = bins.to_xarray()
    if isinstance(input_data, xr.DataArray) and interval_means.name is None:
        interval_means = interval_means.rename("mean_values")
    bins = xr.merge([bins, interval_means])

    bins["anchor_year"] = bins["anchor_year"].astype(int)

    # Turn the anchor year and interval count into coordinates
    bins = bins.assign_coords(
        {"anchor_year": bins["anchor_year"], "i_interval": bins["i_interval"]}
    )
    # Also make the intervals themselves a coordinate so they are not lost when
    #   grabbing a variable from the resampled dataset.
    bins = bins.set_coords("interval")

    # Reshaping the dataset to have the anchor_year and i_interval as dimensions.
    #   set anchor_year or i_interval as the main dimension
    #   (otherwise index is kept as dimension)
    bins = bins.swap_dims({"index": "anchor_year"})
    bins = bins.set_index(ai=("anchor_year", "i_interval"))
    bins = bins.unstack()
    bins = bins.transpose("anchor_year", "i_interval", ...)

    return bins
