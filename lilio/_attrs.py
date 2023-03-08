from typing import Union
import xarray as xr
import lilio
from lilio.calendar import Calendar


def add_attrs(data: Union[xr.DataArray, xr.Dataset], calendar: Calendar) -> None:
    """Update resampled xarray data with the Calendar's attributes and provenance."""
    data.attrs = {
        **data.attrs,  # Keep original attrs
        "lilio_version": lilio.__version__,
        "lilio_calendar_anchor_date": calendar.anchor,
        "lilio_calendar_code": str(calendar),
    }
    data["anchor_year"].attrs = {
        "name": "anchor year",
        "units": "year",
        "description": (
            "The anchor date is the start of the period you want to forecast, and is "
            "an abstract date and does not include a year. "
            "Anchor years are used to create a full date with the anchor date "
            f"(here: {calendar.anchor})."
        ),
    }
    data["i_interval"].attrs = {
        "name": "interval index",
        "units": "-",
        "description": (
            "The index of each Lilio Calendar interval. Positive values denote "
            "intervals after the anchor date, while negative values represent intervals"
            " before the anchor date."
        ),
    }
    data["is_target"].attrs = {
        "name": "Target flag",
        "description": (
            "Denotes if an interval was marked as a target interval in the"
            " Lilio Calendar."
        ),
    }
