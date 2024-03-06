"""lilio train/test splitting methods.

Wrapper around sklearn splitters for working with (multiple) xarray dataarrays.
"""

from collections.abc import Iterable
from typing import Optional
from typing import Union
from typing import overload
import numpy as np
import xarray as xr
from sklearn.model_selection._split import BaseCrossValidator
from sklearn.model_selection._split import BaseShuffleSplit


# Mypy type aliases
CVtype = Union[BaseCrossValidator, BaseShuffleSplit]


class CoordinateMismatchError(Exception):
    """Custom exception for unmatching coordinates."""


def _all_equal(arrays):
    """Return true if all arrays are equal."""
    try:
        arrays = iter(arrays)
        first = next(arrays)
        return all(np.array_equal(first, rest) for rest in arrays)
    except StopIteration:
        return True


class TrainTestSplit:
    """Split (multiple) xr.DataArrays across a given dimension."""

    def __init__(self, splitter: type[CVtype]) -> None:
        """Split (multiple) xr.DataArrays across a given dimension.

        Calling `split()` on this object returns an iterator that allows passing in
        multiple input arrays at once. They need to have matching coordinates along
        the given dimension.

        For an overview of the sklearn Splitter Classes see:
        https://scikit-learn.org/stable/modules/classes.html#module-sklearn.model_selection

        Args:
            splitter (SplitterClass): Initialized splitter class, much have a
                `fit(X)` method which splits up `X` into multiple folds of
                train/test data.
        """
        self.splitter = splitter

    @overload
    def split(
        self,
        x_args: xr.DataArray,
        y: Optional[xr.DataArray] = None,
        dim: str = "anchor_year",
    ) -> Iterable[tuple[xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray]]: ...

    @overload
    def split(
        self,
        x_args: Iterable[xr.DataArray],
        y: Optional[xr.DataArray] = None,
        dim: str = "anchor_year",
    ) -> Iterable[
        tuple[
            Iterable[xr.DataArray], Iterable[xr.DataArray], xr.DataArray, xr.DataArray
        ]
    ]: ...

    def split(
        self,
        x_args: Union[xr.DataArray, Iterable[xr.DataArray]],
        y: Optional[xr.DataArray] = None,
        dim: str = "anchor_year",
    ) -> Iterable[
        Union[
            tuple[xr.DataArray, xr.DataArray],
            tuple[xr.DataArray, xr.DataArray, xr.DataArray, xr.DataArray],
            tuple[Iterable[xr.DataArray], Iterable[xr.DataArray]],
            tuple[
                Iterable[xr.DataArray],
                Iterable[xr.DataArray],
                xr.DataArray,
                xr.DataArray,
            ],
        ]
    ]:
        """Iterate over splits.

        Args:
            x_args: one or multiple xr.DataArray's that share the same
                coordinate along the given dimension.
            y: (optional) xr.DataArray that shares the same coordinate along the
                given dimension.
            dim: name of the dimension along which to split the data.

        Returns:
            Iterator over the splits
        """
        x_args_list, x = self._check_dimension_and_type(x_args, y, dim)

        # Now we know that all inputs are equal.
        for train_indices, test_indices in self.splitter.split(x[dim]):
            x_train = [da.isel({dim: train_indices}) for da in x_args_list]
            x_test = [da.isel({dim: test_indices}) for da in x_args_list]

            if y is None:
                if isinstance(x_args, xr.DataArray):
                    yield x_train.pop(), x_test.pop()
                else:
                    yield x_train, x_test
            else:
                y_train = y.isel({dim: train_indices})
                y_test = y.isel({dim: test_indices})
                if isinstance(x_args, xr.DataArray):
                    yield x_train.pop(), x_test.pop(), y_train, y_test
                else:
                    yield x_train, x_test, y_train, y_test

    def _check_dimension_and_type(
        self,
        x_args: Union[xr.DataArray, Iterable[xr.DataArray]],
        y: Optional[xr.DataArray] = None,
        dim: str = "anchor_year",
    ) -> tuple[list[xr.DataArray], xr.DataArray]:
        """Check input dimensions and type and return input as list.

        Args:
            x_args: one or multiple xr.DataArray's that share the same
                coordinate along the given dimension.
            y: (optional) xr.DataArray that shares the same coordinate along the
                given dimension.
            dim: name of the dimension along which to split the data.

        Returns:
            List of input x and dataarray containing coordinate info
        """
        # Check that all inputs share the same dim coordinate
        coords = []
        x: xr.DataArray  # Initialize x to set scope outside loop

        if isinstance(x_args, xr.DataArray):
            x_args_list = [x_args]
        else:
            x_args_list = list(x_args)

        for x in x_args_list:
            try:
                coords.append(x[dim])
            except KeyError as err:
                raise CoordinateMismatchError(
                    f"Not all input data arrays have the {dim} dimension."
                ) from err

        if not _all_equal(coords):
            raise CoordinateMismatchError(
                f"Input arrays are not equal along {dim} dimension."
            )

        if y is not None and not np.array_equal(y[dim], x[dim]):
            raise CoordinateMismatchError(
                f"Input arrays are not equal along {dim} dimension."
            )

        if x[dim].size <= 1:
            raise ValueError(
                f"Invalid input: need at least 2 values along dimension {dim}."
            )

        return x_args_list, x
