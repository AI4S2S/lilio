from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr


def generate_era5_file(
    start_time: np.datetime64, end_time: np.datetime64
) -> xr.Dataset:
    test_value = 20.0
    resolution = 0.25

    time_coords = pd.date_range(
        start=start_time, end=end_time, freq="6h", inclusive="left"
    )
    lat_coords = np.arange(
        start=0,
        stop=45,
        step=resolution,
    )
    lon_coords = np.arange(
        start=0,
        stop=45,
        step=resolution,
    )
    data = np.zeros((len(lon_coords), len(lat_coords), len(time_coords))) + test_value

    return xr.Dataset(
        data_vars={"t2m": (("longitude", "latitude", "time"), data)},
        coords={
            "longitude": lon_coords,
            "latitude": lat_coords,
            "time": time_coords,
        },
    )


for year in range(2000, 2003):
    start_time = np.datetime64(f"{year}-01-01T00:00")
    end_time = np.datetime64(f"{year}-12-31T23:59")
    fname = f"era5_dummy_{year}.nc"
    fpath = Path(__file__).parent / fname
    ds = generate_era5_file(start_time, end_time)
    ds.to_netcdf(fpath, encoding={"t2m": {"zlib": True, "complevel": 9}})
