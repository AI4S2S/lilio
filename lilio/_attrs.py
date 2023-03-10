from datetime import datetime
from datetime import timezone
from typing import Union
import xarray as xr
import lilio
from lilio.calendar import Calendar


def add_attrs(data: Union[xr.DataArray, xr.Dataset], calendar: Calendar) -> None:
    """Update resampled xarray data with the Calendar's attributes and provenance."""
    history = (
        f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S %Z} - "
        "Resampled with a Lilio calendar. "
        "See: https://github.com/AI4S2S/lilio\n"
    )
    if "history" in data.attrs.keys():
        history += data.attrs["history"]

    data.attrs = {
        **data.attrs,  # Keep original attrs. Conflicts will be overwritten attrs below:
        "lilio_version": lilio.__version__,
        "lilio_calendar_anchor_date": calendar.anchor,
        "lilio_calendar_code": str(calendar),
        "history": history,
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
            "intervals after the anchor date (targets), while negative values "
            "represent intervals before the anchor date (precursors)."
        ),
    }
    data["is_target"].attrs = {
        "name": "Target flag",
        "description": (
            "Denotes if an interval was marked as a target interval in the"
            " Lilio Calendar."
        ),
    }
