import numpy as np
import pandas as pd
import xarray as xr

from scripts.liveocean_explorer import (
    format_step_label,
    format_time_label,
    format_valid_time,
    lon_lat_variables,
)


def test_format_valid_time_combines_run_day_and_step():
    assert (
        format_valid_time(
            np.datetime64("2026-05-01T00:00:00"),
            np.timedelta64(36, "h"),
        )
        == "2026-05-02 12:00:00 UTC"
    )


def test_format_time_label_shows_seconds_not_nanoseconds():
    assert (
        format_time_label(np.datetime64("2026-05-01T00:00:00.000000000"))
        == "2026-05-01 00:00:00 UTC"
    )


def test_format_step_label_shows_hours_not_nanoseconds():
    assert format_step_label(np.timedelta64(4, "h")) == "4 h"
    assert format_step_label(pd.Timedelta(hours=72)) == "72 h"


def test_lon_lat_variables_include_2d_and_time_step_fields():
    ds = xr.Dataset(
        {
            "lon_rho": (("eta_rho", "xi_rho"), np.zeros((2, 3))),
            "lat_rho": (("eta_rho", "xi_rho"), np.zeros((2, 3))),
            "h": (("eta_rho", "xi_rho"), np.ones((2, 3))),
            "temp_surface": (
                ("time", "step", "eta_rho", "xi_rho"),
                np.ones((1, 2, 2, 3)),
            ),
            "profile": (("step",), np.ones(2)),
        },
        coords={
            "time": [pd.Timestamp("2026-05-01")],
            "step": [pd.Timedelta(0), pd.Timedelta(hours=4)],
        },
    )

    assert lon_lat_variables(ds) == ["h", "temp_surface"]
