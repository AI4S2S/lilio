"""Response Guided Dimensionality Reduction."""
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.stats import pearsonr as _pearsonr
from sklearn.cluster import DBSCAN
from . import utils


RADIUS_EARTH_KM = 6371
SURFACE_AREA_EARTH_KM2 = 5.1e8
XrType = TypeVar("XrType", xr.DataArray, xr.Dataset)


def spherical_area(latitude: float, dlat: float, dlon: float = None) -> float:
    """Approximate the area of a square grid cell on a spherical (!) earth.
    Returns the area in square kilometers of earth surface.

    Args:
        latitude (float): Latitude at the center of the grid cell (deg)
        dlat (float): Latitude grid resolution (deg)
        dlon (float): Longitude grid resolution (deg), optional in case of a square grid.

    Returns:
        float: Area of the grid cell (km^2)
    """
    if dlon is None:
        dlon = dlat
    dlon = np.radians(dlon)
    dlat = np.radians(dlat)

    lat = np.radians(latitude)
    h = np.sin(lat + dlat / 2) - np.sin(lat - dlat / 2)
    spherical_area = h * dlon / np.pi * 4

    return spherical_area * SURFACE_AREA_EARTH_KM2


def cluster_area(ds: XrType, cluster_label: float) -> float:
    """Determines the total area of a cluster. Requires the input dataset to have the
    variables `area` and `cluster_labels`.

    Args:
        ds (xr.Dataset or xr.DataArray): Dataset/DataArray containing the variables
            `area` and `cluster_labels`.
        cluster_label (float): The label (as float) for which the area should be
            calculated.

    Returns:
        float: Area of the cluster `cluster_label`.
    """
    return (
        ds["area"]
        .where(ds["cluster_labels"] == cluster_label)
        .sum(skipna=True)
        .values.item()
    )


def remove_small_area_clusters(ds: XrType, min_area_km2: float) -> XrType:
    """Removes the clusters where the area is under the input threshold.

    Args:
        ds (xr.DataArray, xr.Dataset): Dataset containing `cluster_labels` and `area`.
        min_area_km2 (float): The minimum allowed area of each cluster

    Returns:
        xr.DataArray, xr.Dataset: The input dataset with the labels of the clusters set
            to 0 when the area of the cluster is under the `min_area_km2` threshold.
    """
    clusters = np.unique(ds["cluster_labels"])
    areas = [cluster_area(ds, c) for c in clusters]
    valid_clusters = np.array([c for c, a in zip(clusters, areas) if a > min_area_km2])

    ds["cluster_labels"] = ds["cluster_labels"].where(
        np.isin(ds["cluster_labels"], valid_clusters), 0
    )

    return ds


def masked_spherical_dbscan(
    precursor: xr.DataArray,
    corr: xr.DataArray,
    p_val: xr.DataArray,
    dbscan_params: dict,
) -> xr.DataArray:

    """Determines the clusters based on sklearn's DBSCAN implementation. Alpha determines
    the mask based on the minimum p_value. Grouping can be adjusted using the `eps_km`
    parameter. Cluster labels are negative for areas with a negative correlation coefficient
    and positive for areas with a positive correlation coefficient. Areas without any
    significant correlation are put in the cluster labelled '0'.

    Args:
        precursor (xr.DataArray): DataArray of the precursor field, containing
            'latitude' and 'longitude' dimensions in degrees.
        corr (xr.DataArray): DataArray with the correlation values, generated by
            correlation_map()
        p_val (xr.DataArray): DataArray with the p-values, generated by
            correlation_map()
        dbscan_params (dict): Dictionary containing the elements 'alpha', 'eps',
            'min_area_km2'. See the documentation of RGDR for more information.

    Returns:
        xr.DataArray: Precursor data grouped by the DBSCAN clusters.
    """
    orig_name = precursor.name
    data = precursor.to_dataset()
    data["corr"], data["p_val"] = corr, p_val  # Will require less tracking of indices

    data = data.stack(coord=["latitude", "longitude"])
    coords = np.asarray(data["coord"].values.tolist())
    coords = np.radians(coords)

    # Prepare labels, default value is 0 (not in cluster)
    labels = np.zeros(len(coords))

    for sign, sign_mask in zip([1, -1], [data["corr"] >= 0, data["corr"] < 0]):
        mask = np.logical_and(data["p_val"] < dbscan_params["alpha"], sign_mask)
        if np.sum(mask) > 0:  # Check if the mask contains any points to cluster
            db = DBSCAN(
                eps=dbscan_params["eps"] / RADIUS_EARTH_KM,
                min_samples=1,
                algorithm="auto",
                metric="haversine",
            ).fit(coords[mask])

            labels[mask] = sign * (db.labels_ + 1)

    precursor = precursor.stack(coord=["latitude", "longitude"])
    precursor["cluster_labels"] = ("coord", labels)
    precursor = precursor.unstack(("coord"))

    dlat = np.abs(precursor.latitude.values[1] - precursor.latitude.values[0])
    dlon = np.abs(precursor.longitude.values[1] - precursor.longitude.values[0])
    precursor["area"] = spherical_area(precursor.latitude, dlat, dlon)

    if dbscan_params["min_area"]:
        precursor = remove_small_area_clusters(precursor, dbscan_params["min_area"])

    precursor.name = orig_name
    return precursor


def _pearsonr_nan(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """NaN friendly implementation of scipy.stats.pearsonr. Calculates the correlation
    coefficient between two arrays, as well as the p-value of this correlation. However,
    instead of raising an error when encountering NaN values, this function will return
    both the correlation coefficient and the p-value as NaN.

    Args:
        x: 1-D array
        y: 1-D array
    Returns:
        r_coefficient
        p_value

    """
    if np.any(np.isnan(x)) or np.any(np.isnan(y)):
        return np.nan, np.nan
    return _pearsonr(x, y)


def correlation(
    field: xr.DataArray, target: xr.DataArray, corr_dim: str = "time"
) -> Tuple[xr.DataArray, xr.DataArray]:
    """Calculate correlation maps.

    Args:
        field: Spatial data with a dimension named `corr_dim`, over which each
            location should have the Pearson correlation coefficient calculated with the
            target data.
        target: Data which has to be correlated with the spatial data. Requires a
            dimension named `corr_dim`.
        corr_dim: Dimension over which the correlation coefficient should be calculated.

    Returns:
        r_coefficient: DataArray filled with the correlation coefficient for each
            non-`corr_dim` coordinate.
        p_value: DataArray filled with the two-tailed p-values for each computed
            correlation coefficient.
    """
    assert (
        corr_dim in target.dims
    ), f"input target does not have contain the '{corr_dim}' dimension"
    assert (
        corr_dim in field.dims
    ), f"input field does not have contain the '{corr_dim}' dimension"
    assert np.all(
        [dim in field.dims for dim in target.dims]
    ), "Field and target dims do not match"

    return xr.apply_ufunc(
        _pearsonr_nan,
        field,
        target,
        input_core_dims=[[corr_dim], [corr_dim]],
        vectorize=True,
        output_core_dims=[[], []],
    )


def partial_correlation(field, target, z):
    """Calculate partial correlation maps."""
    raise NotImplementedError


def regression(field, target):
    """Regression analysis on entire maps.

    Methods include Linear, Ridge, Lasso.
    """
    raise NotImplementedError


class RGDR:
    """Response Guided Dimensionality Reduction."""

    def __init__(
        self,
        eps_km: float = 600,
        alpha: float = 0.05,
        min_area_km2: float = 3000**2
    ) -> None:
        """Response Guided Dimensionality Reduction (RGDR).

        Dimensionality reduction based on the correlation between precursor field and target timeseries.

        Args:
            alpha (float): p-value below which the correlation is considered significant
                enough for a location to be included in a cluster.
            eps_km (float): The maximum distance (in km) between two samples for one to
                be considered as in the neighborhood of the other. This is not a maximum
                bound on the distances of points within a cluster. This is the most
                important DBSCAN parameter to choose appropriately.
            min_area_km2 (float): The minimum area of a cluster. Clusters smaller than
                this minimum area will be discarded.
        """
        self._clusters = None
        self._area = None
        self._dbscan_params = {"eps": eps_km, "alpha": alpha, "min_area": min_area_km2}

    def get_correlation(
        self,
        precursor: xr.DataArray,
        timeseries: xr.DataArray,
    ) -> Tuple[xr.DataArray, xr.DataArray]:
        """Calculates the correlation and p-value between input precursor and timeseries.

        Args:
            precursor: Precursor field data with the dimensions
                'latitude', 'longitude', and 'anchor_year'
            timeseries: Timeseries data with only the dimension 'anchor_year'

        Returns:
            (correlation, p_value): DataArrays containing the correlation and p-value.
        """
        if not isinstance(precursor, xr.DataArray):
            raise ValueError("Please provide an xr.DataArray, not a dataset")

        return correlation(precursor, timeseries, corr_dim="anchor_year")

    def get_clusters(
        self,
        precursor: xr.DataArray,
        timeseries: xr.DataArray,
    ) -> xr.DataArray:
        """Generates clusters for the precursor data.

        Args:
            precursor: Precursor field data with the dimensions
                'latitude', 'longitude', and 'anchor_year'
            timeseries: Timeseries data with only the dimension 'anchor_year'

        Returns:
            DataArray containing the clusters as masks.
        """
        corr, p_val = self.get_correlation(precursor, timeseries)
        return masked_spherical_dbscan(precursor, corr, p_val, self._dbscan_params)

    def plot_correlation(
        self,
        precursor: xr.DataArray,
        timeseries: xr.DataArray,
        ax1: Optional[plt.Axes] = None,
        ax2: Optional[plt.Axes] = None,
    ) -> List[Type[mpl.collections.QuadMesh]]:
        """Generates a figure showing the correlation and p-value results with the
        initiated RGDR class and input precursor field.

        Args:
            precursor: Precursor field data with the dimensions
                'latitude', 'longitude', and 'anchor_year'
            timeseries: Timeseries data with only the dimension 'anchor_year'
            ax1: a matplotlib axis handle to plot
                the correlation values into. If None, an axis handle will be created
                instead.
            ax2: a matplotlib axis handle to plot
                the p-values into. If None, an axis handle will be created instead.

        Returns:
            List[mpl.collections.QuadMesh]: List of matplotlib artists.
        """
        corr, p_val = self.get_correlation(precursor, timeseries)

        if (ax1 is None) and (ax2 is None):
            _, (ax1, ax2) = plt.subplots(ncols=2)
        elif (ax1 is None) or (ax2 is None):
            raise ValueError(
                "Either pass axis handles for both ax1 and ax2, or pass neither."
            )

        plot1 = corr.plot.pcolormesh(ax=ax1, cmap="viridis")  # type: ignore
        plot2 = p_val.plot.pcolormesh(ax=ax2, cmap="viridis")  # type: ignore

        ax1.set_title("correlation")
        ax2.set_title("p-value")

        return [plot1, plot2]

    def plot_clusters(
        self,
        precursor: xr.DataArray,
        timeseries: xr.DataArray,
        ax: Optional[plt.Axes] = None,
    ) -> Type[mpl.collections.QuadMesh]:
        """Generates a figure showing the clusters resulting from the initiated RGDR
        class and input precursor field.

        Args:
            precursor: Precursor field data with the dimensions
                'latitude', 'longitude', and 'anchor_year'
            timeseries: Timeseries data with only the dimension 'anchor_year'
            ax (plt.Axes, optional): a matplotlib axis handle to plot the clusters
                into. If None, an axis handle will be created instead.

        Returns:
            matplotlib.collections.QuadMesh: Matplotlib artist.
        """
        clusters = self.get_clusters(precursor, timeseries)

        if ax is None:
            _, ax = plt.subplots()

        return clusters.cluster_labels.plot(cmap="viridis", ax=ax)

    def fit(self, precursor: xr.DataArray, timeseries: xr.DataArray):
        """Fits RGDR clusters to precursor data.

        Performs DBSCAN clustering on a prepared DataArray, and then groups the data by
        their determined clusters, using an weighted mean. The weight is based on the
        area of each grid cell.

        Density-Based Spatial Clustering of Applications with Noise (DBSCAN) clusters
        gridcells together which are of the same sign and in proximity to
        each other using DBSCAN.

        Clusters labelled with a positive value represent a positive correlation with
        the target timeseries, the clusters labelled with a negative value represent a
        negative correlation. All locations not in a cluster are grouped together under
        the label '0'.

        Args:
            precursor: Precursor field data with the dimensions 'latitude', 'longitude',
                and 'anchor_year'

        Returns:
            xr.DataArray: The precursor data, with the latitute and longitude dimensions
                reduced to clusters.
        """

        corr, p_val = correlation(precursor, timeseries, corr_dim="anchor_year")

        masked_data = masked_spherical_dbscan(
            precursor, corr, p_val, self._dbscan_params
        )

        self._clusters = masked_data.cluster_labels
        self._area = masked_data.area

        return self

    def transform(self, data: xr.DataArray) -> xr.DataArray:
        """Apply RGDR on the input data, based on the previous fit.

        Transform will use the clusters previously generated when RGDR was fit, and use
        these clusters to reduce the latitude and longitude dimensions of the input
        data."""

        if self._clusters is None:
            raise ValueError(
                "Transform requires the model to be fit on other data first"
            )
        data["cluster_labels"] = self._clusters
        data["area"] = self._area

        # Add the geographical centers for later alignment between, e.g., splits
        reduced_data = utils.weighted_groupby(
            data, groupby="cluster_labels", weight="area"
        )

        return utils.geographical_cluster_center(data, reduced_data)
