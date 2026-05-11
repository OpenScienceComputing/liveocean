from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr


def format_valid_time(run_time, step) -> str:
    valid_time = pd.Timestamp(run_time) + pd.Timedelta(step)
    return format_time_label(valid_time)


def format_time_label(time) -> str:
    return pd.Timestamp(time).strftime("%Y-%m-%d %H:%M:%S UTC")


def format_step_label(step) -> str:
    hours = pd.Timedelta(step) / pd.Timedelta(hours=1)
    if float(hours).is_integer():
        return f"{int(hours)} h"
    return f"{hours:g} h"


def lon_lat_variables(ds: xr.Dataset) -> list[str]:
    required_dims = {"eta_rho", "xi_rho"}
    exclude = {"lon_rho", "lat_rho"}
    names = []
    for name, data_array in ds.data_vars.items():
        dims = set(data_array.dims)
        if name not in exclude and required_dims.issubset(dims):
            names.append(name)
    return names


def scalar_to_python(value):
    if isinstance(value, np.ndarray):
        return value.item()
    if hasattr(value, "item"):
        return value.item()
    return value
