"""lilio time utils.

Utilities designed to aid in seasonal-to-subseasonal prediction experiments in
which we search for skillful predictors preceding a certain event of interest.

Time indices are anchored to the target period of interest. By keeping
observations from the same cycle (typically 1 year) together and paying close
attention to the treatment of adjacent cycles, we avoid information leakage
between train and test sets.

Example:
    >>> import lilio.time
    >>>
    >>> # Countdown the weeks until New Year's Eve
    >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="7d")
    >>> calendar # doctest: +NORMALIZE_WHITESPACE
    AdventCalendar(
        anchor='12-31',
        freq='7d',
        n_targets=1,
        max_lag=0,
        allow_overlap=False,
        mapping=None
    )

    >>> # Get the 180-day periods leading up to New Year's eve for the year 2020
    >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="180d")
    >>> calendar = calendar.map_years(2020, 2020)
    >>> calendar.show() # doctest: +NORMALIZE_WHITESPACE
    i_interval                         -1                         1
    anchor_year
    2020         [2020-07-04, 2020-12-31)  [2020-12-31, 2021-06-29)

    >>> # Get the 180-day periods leading up to New Year's eve for 2020 - 2022 inclusive.
    >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="180d")
    >>> calendar = calendar.map_years(2020, 2022)
    >>> # note the leap year:
    >>> calendar.show() # doctest: +NORMALIZE_WHITESPACE
    i_interval                         -1                         1
    anchor_year
    2022         [2022-07-04, 2022-12-31)  [2022-12-31, 2023-06-29)
    2021         [2021-07-04, 2021-12-31)  [2021-12-31, 2022-06-29)
    2020         [2020-07-04, 2020-12-31)  [2020-12-31, 2021-06-29)

    >>> # To get a stacked representation:
    >>> calendar.map_years(2020, 2022).flat
    anchor_year  i_interval
    2022         -1            [2022-07-04, 2022-12-31)
                  1            [2022-12-31, 2023-06-29)
    2021         -1            [2021-07-04, 2021-12-31)
                  1            [2021-12-31, 2022-06-29)
    2020         -1            [2020-07-04, 2020-12-31)
                  1            [2020-12-31, 2021-06-29)
    dtype: interval

"""
import calendar as pycalendar
import re
from os import linesep
from typing import List
from typing import Literal
from typing import Tuple
from typing import Union
import numpy as np
import pandas as pd
import xarray as xr
from ._base_calendar import BaseCalendar
from ._base_calendar import Interval
from ._base_calendar import MappingData
from ._base_calendar import MappingYears
from ._resample import resample  # pylint: disable=unused-import


PandasData = (pd.Series, pd.DataFrame)
XArrayData = (xr.DataArray, xr.Dataset)

month_mapping_dict = {
    **{v.upper(): k for k, v in enumerate(pycalendar.month_abbr)},
    **{v.upper(): k for k, v in enumerate(pycalendar.month_name)},
}


class AdventCalendar(BaseCalendar):
    """Countdown time to anticipated anchor date or period of interest."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        anchor: str,
        freq: str = "7d",
        n_targets: int = 1,
        max_lag: int = 0,
        allow_overlap: bool = False,
        mapping: Union[None, MappingYears, MappingData] = None,
    ) -> None:
        """Instantiate a basic calendar with minimal configuration.

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
            mapping: Calendar mapping. Input in the form: ("years", 2000, 2020) or
                ("data", pd.Timestamp("2000-01-01"), pd.Timestamp("2020-01-01")). The
                calendar mapping is usually set with the `map_years` or `map_to_data`
                methods.

        Example:
            Instantiate a calendar counting down the weeks until new-year's
            eve.

            >>> import lilio.time
            >>> calendar = lilio.time.AdventCalendar(anchor="12-31", freq="7d")
            >>> calendar
            AdventCalendar(
                anchor='12-31',
                freq='7d',
                n_targets=1,
                max_lag=0,
                allow_overlap=False,
                mapping=None
            )

        """
        if not re.fullmatch(r"\d*d", freq):
            raise ValueError("Please input a frequency in the form of '10d'.")
        self._anchor, self._anchor_fmt = self._parse_anchor(anchor)
        self.freq = freq
        self.n_targets = n_targets
        self.max_lag = max_lag
        self.allow_overlap = allow_overlap
        self._set_mapping(mapping)

    @property
    def n_intervals(self) -> int:
        """Calculates the number of intervals that should be generated by _map year.

        Returns:
            int: Number of intervals for one anchor year.
        """
        periods_per_year = pd.Timedelta("365days") / pd.to_timedelta(self.freq)
        return (
            (self.max_lag + self.n_targets)
            if self.max_lag > 0
            else int(periods_per_year)
        )

    @property
    def max_lag(self):
        return self._max_lag

    @max_lag.setter
    def max_lag(self, value):
        if (value < 0) or (value % 1 > 0):
            raise ValueError(
                "Max lag should be an integer with a value of 0 or greater"
                f", not {value} of type {type(value)}."
            )
        self._max_lag = value

    def get_intervals(self) -> pd.DataFrame:
        """Method to retrieve updated intervals from the Calendar object.

        The assembly of AdvantCalendar based on the user provided anchor dates,
        frequency, and number of targets/lags, takes place in this method.
        """
        if self._mapping is None:
            raise ValueError(
                "Cannot retrieve intervals without map_years or "
                "map_to_data having configured the calendar."
            )

        # generate target and precursor periods lists
        self.targets = [Interval("target", self.freq) for _ in range(self.n_targets)]
        self.precursors = [
            Interval("precursor", self.freq)
            for _ in range(self.n_intervals - self.n_targets)
        ]

        if self._mapping == "data":
            self._set_year_range_from_timestamps()

        year_range = range(
            self._last_year, self._first_year - 1, -(self._get_skip_nyears() + 1)  # type: ignore
        )

        intervals = pd.concat([self._map_year(year) for year in year_range], axis=1).T

        intervals = self._rename_intervals(intervals)

        intervals.index.name = "anchor_year"
        return intervals.sort_index(axis=0, ascending=False)

    def __repr__(self) -> str:
        """String representation of the Calendar."""
        if self._mapping == "years":
            mapping = ("years", self._first_year, self._last_year)
        elif self._mapping == "data":
            mapping = ("data", self._first_timestamp, self._last_timestamp)
        else:
            mapping = None

        props = [
            ("anchor", repr(self.anchor)),
            ("freq", repr(self.freq)),
            ("n_targets", repr(self.n_targets)),
            ("max_lag", repr(self.max_lag)),
            ("allow_overlap", repr(self.allow_overlap)),
            ("mapping", repr(mapping)),
        ]

        propstr = f"{linesep}\t" + f",{linesep}\t".join([f"{k}={v}" for k, v in props])
        return f"{self.__class__.__name__}({propstr}{linesep})".replace("\t", "    ")


class MonthlyCalendar(AdventCalendar):
    """Countdown time to anticipated anchor month, in steps of whole months."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        anchor: str,
        freq: str = "1M",
        n_targets: int = 1,
        max_lag: int = 0,
        allow_overlap: bool = False,
        mapping: Union[None, MappingYears, MappingData] = None,
    ) -> None:
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
            mapping: Calendar mapping. Input in the form: ("years", 2000, 2020) or
                ("data", pd.Timestamp("2000-01-01"), pd.Timestamp("2020-01-01")). The
                calendar mapping is usually set with the `map_years` or `map_to_data`
                methods.

        Example:
            Instantiate a calendar counting down the quarters (3 month periods) from
            december.

            >>> import lilio.time
            >>> calendar = lilio.time.MonthlyCalendar(anchor='Dec', freq="3M")
            >>> calendar
            MonthlyCalendar(
                anchor='12',
                freq='3M',
                n_targets=1,
                max_lag=0,
                allow_overlap=False,
                mapping=None
            )

        """
        if not re.fullmatch(r"\d*M", freq):
            raise ValueError("Please input a frequency in the form of '2M'")
        self._anchor, self._anchor_fmt = self._parse_anchor(anchor)
        self.freq = freq
        self.n_targets = n_targets
        self.max_lag = max_lag
        self.allow_overlap = allow_overlap
        self._set_mapping(mapping)

    @property
    def n_intervals(self) -> int:
        """Calculates the number of intervals that should be generated by _map year.

        Returns:
            int: Number of intervals for one anchor year.
        """
        periods_per_year = 12 / int(self.freq.replace("M", ""))
        return (
            (self._max_lag + self.n_targets)
            if self._max_lag > 0
            else int(periods_per_year)
        )

    def _get_skip_nyears(self) -> int:
        """Determine how many years need to be skipped to avoid overlapping data.

        Required to prevent information leakage between anchor years.

        Returns:
            int: Number of years that need to be skipped.
        """
        nmonths = int(self.freq.replace("M", ""))
        return (
            0
            if self._max_lag > 0 and self._allow_overlap
            else int(np.ceil(nmonths / 12) - 1)
        )

    def _interval_as_month(self, interval):
        """Turns an interval with pandas Timestamp values to a formatted string.

        The string will contain the years and months, for a more intuitive
        representation to the user.

        Args:
            interval (pd.Interval): Pandas interval.

        Returns:
            str: String in the form of '[2020 Jan, 2020 Feb)'
        """
        left = interval.left.strftime("%Y %b")
        right = interval.right.strftime("%Y %b")
        return f"[{left}, {right})"

    def show(self) -> pd.DataFrame:
        """Gives the intervals the Calendar will generate for the current setup.

        Returns:
            pd.Dataframe: Dataframe containing the calendar intervals, with the
                intervals shown as months instead of full dates.
        """
        return self.get_intervals().applymap(self._interval_as_month)


class WeeklyCalendar(AdventCalendar):
    """Countdown time to anticipated anchor week number, in steps of calendar weeks."""

    # pylint: disable=super-init-not-called, too-many-arguments
    def __init__(
        self,
        anchor: str,
        freq: str = "1W",
        n_targets: int = 1,
        max_lag: int = 0,
        allow_overlap: bool = False,
        mapping: Union[None, MappingYears, MappingData] = None,
    ) -> None:
        """Instantiate a basic week number calendar with minimal configuration.

        Set up the calendar with given freq ending exactly on the anchor week.
        The index will extend back in time as many weeks as fit within the
        cycle time of one year (i.e. 52).
        Note that the difference between this calendar and the AdventCalendar revolves
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
            mapping: Calendar mapping. Input in the form: ("years", 2000, 2020) or
                ("data", pd.Timestamp("2000-01-01"), pd.Timestamp("2020-01-01")). The
                calendar mapping is usually set with the `map_years` or `map_to_data`
                methods.

        Example:
            Instantiate a calendar counting down the weeks from week number 40.

            >>> import lilio.time
            >>> calendar = lilio.time.WeeklyCalendar(anchor="W40", freq="1W")
            >>> calendar
            WeeklyCalendar(
                anchor='W40-1',
                freq='1W',
                n_targets=1,
                max_lag=0,
                allow_overlap=False,
                mapping=None
            )
        """
        if not re.fullmatch(r"\d*W", freq):
            raise ValueError("Please input a frequency in the form of '4W'")

        self._anchor, self._anchor_fmt = self._parse_anchor(anchor)
        self.freq = freq
        self.n_targets = n_targets
        self.max_lag = max_lag
        self.allow_overlap = allow_overlap
        self._set_mapping(mapping)

    def _interval_as_weeknr(self, interval: pd.Interval) -> str:
        """Turns an interval with pandas Timestamp values to a formatted string.

        The string will contain the years and week numbers, for a more intuitive
        representation to the user.

        Args:
            interval (pd.Interval): Pandas interval.

        Returns:
            str: String in the form of '[2020-50, 2020-51)'
        """
        left = interval.left.strftime("%Y-W%W")
        right = interval.right.strftime("%Y-W%W")
        return f"[{left}, {right})"

    def show(self) -> pd.DataFrame:
        """Gives the intervals the Calendar will generate for the current setup.

        Returns:
            pd.Dataframe: Dataframe containing the calendar intervals, with the
                intervals shown as weeknumbers instead of dates.
        """
        return self.get_intervals().applymap(self._interval_as_weeknr)


class Calendar(BaseCalendar):
    """Build a calendar from sratch with basic construction elements."""

    def __init__(
        self,
        anchor: str,
        allow_overlap: bool = False,
        mapping: Union[
            None,
            Tuple[Literal["years"], int, int],
            Tuple[Literal["data"], pd.Timestamp, pd.Timestamp],
        ] = None,
        intervals: Union[None, List[Interval]] = None,
    ):
        """Instantiate a basic container for building calendar using basic blocks.

        This is a highly flexible calendar which allows the user to build their own
        calendar with the basic building blocks of target and precursor periods.

        Users have the freedom to create calendar with customized intervals, gap
        between intervals, and even overlapped intervals. They need to manage the
        calendar themselves.

        Args:
            anchor: String denoting the anchor date. The following inputs are valid:
                    - "MM-DD" for a month and day. E.g. "12-31".
                    - "MM" for only a month, e.g. "4" for March.
                    - English names and abbreviations of months. E.g. "December" or "jan".
                    - "Www" for a week number, e.g. "W05" for the fifth week of the year.
                    - "Www-D" for a week number plus day of week. E.g. "W01-4" for the
                        first thursday of the year.
            allow_overlap: If overlapping intervals between years is allowed or not.
                Default behaviour is False, which means that anchor years will be
                skipped to avoid data being shared between anchor years.
            mapping: Calendar mapping. Input in the form: ("years", 2000, 2020) or
                ("data", pd.Timestamp("2000-01-01"), pd.Timestamp("2020-01-01")). The
                calendar mapping is usually set with the `map_years` or `map_to_data`
                methods.
            intervals: A list of Interval objects that should be appended to the
                calendar when it is initialized.

        Example:
            Instantiate a custom calendar and appending target/precursor periods.

            >>> import lilio.time
            >>> calendar = lilio.time.CustomCalendar(anchor="12-31")
            >>> calendar
            CustomCalendar(
                anchor='12-31',
                allow_overlap=False,
                mapping=None,
                intervals=None
            )

        """
        self._anchor, self._anchor_fmt = self._parse_anchor(anchor)
        self._allow_overlap = allow_overlap
        self.targets: List[Interval] = []
        self.precursors: List[Interval] = []

        self._first_year: Union[None, int] = None
        self._last_year: Union[None, int] = None

        if intervals is not None:
            [
                self._append(iv) for iv in intervals
            ]  # pylint: disable=expression-not-assigned

        self._set_mapping(mapping)

    @property
    def n_targets(self):
        return len(self.targets)

    def add_intervals(
        self,
        role: Literal["target", "precursor"],
        length: str,
        gap: str = "0d",
        n: int = 1,
    ) -> None:
        """Add one or more intervals to the calendar.

        The interval can be a target or a precursor, and can be defined by its length,
        a possible gap between this interval and the preceding interval.

        Args:
            role: Either a 'target' or 'precursor' interval(s).
            length: The length of the interval(s), in a format of '5d' for five days, '2W'
                for two weeks, or '1M' for one month.
            gap: The gap between this interval and the preceding target/precursor
                interval. Same format as the length argument.
            n: The number of intervals which should be added to the calendar. Defaults
                to 1.
        """
        if not isinstance(n, int):
            raise ValueError(
                "Please input an 'int' type for the 'n' argument." f" Not a {type(n)}."
            )
        if n <= 0:
            raise ValueError(
                "The number of intervals 'n' has to be 1 or greater, " f"not '{n}'."
            )

        if role in ["target", "precursor"]:
            for _ in range(n):
                self._append(Interval(role, length, gap))
        else:
            raise ValueError(
                f"Type '{role}' is not a valid interval type. Please "
                "choose between 'target' and 'precursor'"
            )

    def show(self) -> pd.DataFrame:
        """Displays the intervals the Calendar will generate for the current setup.

        Returns:
            pd.Dataframe: Dataframe containing the calendar intervals.
        """
        return self.get_intervals()

    def __repr__(self) -> str:
        """String representation of the Calendar."""
        intervals = self.targets + self.precursors
        if len(intervals) == 0:
            intervals_str = repr(None)
        else:
            intervals_str = (
                f"[{linesep}\t\t"
                + f",{linesep}\t\t".join([repr(iv) for iv in intervals])
                + f"{linesep}\t]"
            )

        if self._mapping == "years":
            mapping = ("years", self._first_year, self._last_year)
        elif self._mapping == "data":
            mapping = ("data", self._first_timestamp, self._last_timestamp)
        else:
            mapping = None

        props = [
            ("anchor", repr(self.anchor)),
            ("allow_overlap", repr(self.allow_overlap)),
            ("mapping", repr(mapping)),
            ("intervals", intervals_str),
        ]

        propstr = f"{linesep}\t" + f",{linesep}\t".join([f"{k}={v}" for k, v in props])
        return f"{self.__class__.__name__}({propstr}{linesep})".replace("\t", "    ")
