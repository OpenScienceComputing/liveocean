import numpy as np
import xarray as xr

from scripts.liveocean_rolodex import nearest_lon_lat_indices
from scripts.make_liveocean_rolodex_notebook import build_notebook


def test_nearest_lon_lat_indices_finds_grid_cell():
    lon = xr.DataArray(
        np.array([[-123.0, -122.5], [-123.0, -122.5]]),
        dims=("eta_rho", "xi_rho"),
    )
    lat = xr.DataArray(
        np.array([[47.0, 47.0], [47.5, 47.5]]),
        dims=("eta_rho", "xi_rho"),
    )

    iy, ix = nearest_lon_lat_indices(lon, lat, target_lon=-122.45, target_lat=47.45)

    assert (iy, ix) == (1, 1)


def test_rolodex_notebook_contains_best_estimate_offset_two():
    nb = build_notebook()
    source = "\n".join("".join(cell.get("source", "")) for cell in nb.cells)

    assert "BestEstimate(offset=2)" in source
    assert "create_lazy_valid_time_variable" in source
    assert "temp_surface" in source
    assert "target_lon = -122.45" in source
    assert "target_lat = 47.65" in source
