"""Tests for Lilio's traintest module."""
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from sklearn.model_selection import KFold
import lilio
import lilio.traintest


@pytest.fixture
def dummy_data():
    # Generate random data
    n = 50
    time_index = pd.date_range("20151020", periods=n, freq="60d")
    time_coord = {"time": time_index}
    x1 = xr.DataArray(np.random.randn(n), coords=time_coord, name="x1")
    x2 = xr.DataArray(np.random.randn(n), coords=time_coord, name="x2")
    y = xr.DataArray(np.random.randn(n), coords=time_coord, name="y")

    # Map data to calendar and store for later reference
    calendar = lilio.daily_calendar(anchor="10-15", length="180d")
    calendar.map_to_data(x1)
    x1 = lilio.resample(calendar, x1)
    print(x1)
    x2 = lilio.resample(calendar, x2)
    y = lilio.resample(calendar, y)
    return x1, x2, y


def test_kfold_x(dummy_data):
    """Correctly split x."""
    x1, _, _ = dummy_data
    cv = lilio.traintest.TrainTestSplit(KFold(n_splits=3))
    x_train, x_test = next(cv.split(x1))
    expected_train = [2019, 2020, 2021, 2022]
    expected_test = [2016, 2017, 2018]
    assert np.array_equal(x_train.anchor_year, expected_train)
    xr.testing.assert_equal(x_test, x1.sel(anchor_year=expected_test))


def test_kfold_xy(dummy_data):
    """Correctly split x and y."""
    x1, _, y = dummy_data
    cv = lilio.traintest.TrainTestSplit(KFold(n_splits=3))
    x_train, x_test, y_train, y_test = next(cv.split(x1, y=y))
    expected_train = [2019, 2020, 2021, 2022]
    expected_test = [2016, 2017, 2018]

    assert np.array_equal(x_train.anchor_year, expected_train)
    xr.testing.assert_equal(x_test, x1.sel(anchor_year=expected_test))
    assert np.array_equal(y_train.anchor_year, expected_train)
    xr.testing.assert_equal(y_test, y.sel(anchor_year=expected_test))


def test_kfold_xxy(dummy_data):
    """Correctly split x1, x2, and y."""
    x1, x2, y = dummy_data
    cv = lilio.traintest.TrainTestSplit(KFold(n_splits=3))
    x_train, x_test, y_train, y_test = next(cv.split(x1, x2, y=y))
    expected_train = [2019, 2020, 2021, 2022]
    expected_test = [2016, 2017, 2018]

    assert np.array_equal(x_train[0].anchor_year, expected_train)
    xr.testing.assert_equal(x_test[1], x2.sel(anchor_year=expected_test))
    assert np.array_equal(y_train.anchor_year, expected_train)
    xr.testing.assert_equal(y_test, y.sel(anchor_year=expected_test))


def test_kfold_too_short(dummy_data):
    "Fail if there is only a single anchor year: no splits can be made"
    x1, _, _ = dummy_data
    x = x1.isel(anchor_year=1)
    cv = lilio.traintest.TrainTestSplit(KFold(n_splits=3))

    with pytest.raises(ValueError):
        next(cv.split(x))


def test_kfold_different_xcoords(dummy_data):
    x1, x2, _ = dummy_data
    x1 = x1.isel(anchor_year=slice(1, None, None))
    cv = lilio.traintest.TrainTestSplit(KFold(n_splits=3))

    with pytest.raises(lilio.traintest.CoordinateMismatchError):
        next(cv.split(x1, x2))


def test_custom_dim(dummy_data):
    x1, _, _ = dummy_data
    x = x1.rename(anchor_year="custom_coord")
    cv = lilio.traintest.TrainTestSplit(KFold(n_splits=3))
    x_train, _ = next(cv.split(x, dim="custom_coord"))
    expected_train = [2019, 2020, 2021, 2022]

    assert np.array_equal(x_train.custom_coord, expected_train)
