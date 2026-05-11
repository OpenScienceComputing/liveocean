from __future__ import annotations

import numpy as np
import xarray as xr


def nearest_lon_lat_indices(
    lon: xr.DataArray,
    lat: xr.DataArray,
    target_lon: float,
    target_lat: float,
) -> tuple[int, int]:
    distance2 = (lon - target_lon) ** 2 + (lat - target_lat) ** 2
    flat_index = int(np.nanargmin(distance2.values))
    return tuple(int(index) for index in np.unravel_index(flat_index, lon.shape))
