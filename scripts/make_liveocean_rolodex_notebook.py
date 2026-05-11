from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


NOTEBOOK = Path("LiveOcean_Rolodex_BestEstimate.ipynb")


def code(source: str):
    return nbf.v4.new_code_cell(dedent(source).strip() + "\n")


def markdown(source: str):
    return nbf.v4.new_markdown_cell(dedent(source).strip() + "\n")


def build_notebook():
    nb = nbf.v4.new_notebook()
    nb["metadata"]["kernelspec"] = {
        "display_name": "Python [conda env:coawst-icechunk]",
        "language": "python",
        "name": "conda-env-coawst-icechunk-py",
    }
    nb["metadata"]["language_info"] = {
        "name": "python",
        "pygments_lexer": "ipython3",
    }
    nb["cells"] = [
        markdown(
            """
            # LiveOcean Rolodex BestEstimate

            Open the public LiveOcean Icechunk store, use Rolodex to extract a
            best-estimate time series with a 2-hour forecast offset, and plot
            surface temperature.
            """
        ),
        code(
            """
            import numpy as np
            import pandas as pd
            import icechunk
            import xarray as xr
            import hvplot.xarray
            import holoviews as hv
            import rolodex.forecast
            from rolodex.forecast import BestEstimate, ForecastIndex

            hv.extension("bokeh")
            """
        ),
        code(
            """
            SOURCE_COOP_BUCKET = "us-west-2.opendata.source.coop"
            SOURCE_COOP_PREFIX = "rsignell/liveocean/icechunk/liveocean-layers-icechunk-example"
            LIVEOCEAN_URL_PREFIX = "s3://liveocean-share/"
            LIVEOCEAN_ENDPOINT_URL = "https://s3.kopah.uw.edu"
            """
        ),
        markdown(
            """
            ## Open the public Icechunk store

            Both the Source Cooperative Icechunk metadata and the referenced
            LiveOcean NetCDF virtual chunks are read anonymously.
            """
        ),
        code(
            """
            storage = icechunk.s3_storage(
                bucket=SOURCE_COOP_BUCKET,
                prefix=SOURCE_COOP_PREFIX,
                region="us-west-2",
                anonymous=True,
            )

            config = icechunk.RepositoryConfig.default()
            config.set_virtual_chunk_container(
                icechunk.VirtualChunkContainer(
                    url_prefix=LIVEOCEAN_URL_PREFIX,
                    store=icechunk.s3_store(
                        region="not-used",
                        anonymous=True,
                        s3_compatible=True,
                        force_path_style=True,
                        endpoint_url=LIVEOCEAN_ENDPOINT_URL,
                    ),
                )
            )

            credentials = icechunk.containers_credentials(
                {LIVEOCEAN_URL_PREFIX: icechunk.s3_credentials(anonymous=True)}
            )

            repo = icechunk.Repository.open(
                storage,
                config,
                authorize_virtual_chunk_access=credentials,
            )
            session = repo.readonly_session("main")
            ds = xr.open_zarr(session.store, consolidated=False, chunks={})
            ds
            """
        ),
        markdown(
            """
            ## Extract a Rolodex BestEstimate dataset

            Rolodex indexes the forecast reference time, forecast step, and
            valid time so a single monotonic best-estimate series can be
            selected. Here the selected offset is 2 hours.
            """
        ),
        code(
            """
            ds.coords["valid_time"] = rolodex.forecast.create_lazy_valid_time_variable(
                reference_time=ds.time,
                period=ds.step,
            )

            fmrc = ds.drop_indexes(["time", "step"]).set_xindex(
                ["time", "step", "valid_time"],
                ForecastIndex,
            )

            ds_best = fmrc.sel(valid_time=BestEstimate(offset=2))
            ds_best
            """
        ),
        markdown(
            """
            ## Surface temperature at the last valid time
            """
        ),
        code(
            """
            def format_time(value):
                return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S UTC")


            last_temp = ds_best["temp_surface"].isel(valid_time=-1)
            last_valid_time = ds_best.valid_time.values[-1]

            surface_map = last_temp.hvplot.quadmesh(
                x="lon_rho",
                y="lat_rho",
                geo=True,
                tiles="OSM",
                rasterize=True,
                cmap="turbo",
                width=900,
                height=650,
                title=f"Surface temperature | valid: {format_time(last_valid_time)}",
            )
            surface_map
            """
        ),
        markdown(
            """
            ## Time series near Puget Sound
            """
        ),
        code(
            """
            def nearest_lon_lat_indices(lon, lat, target_lon, target_lat):
                distance2 = (lon - target_lon) ** 2 + (lat - target_lat) ** 2
                flat_index = int(np.nanargmin(distance2.values))
                return tuple(
                    int(index) for index in np.unravel_index(flat_index, lon.shape)
                )


            target_lon = -122.45
            target_lat = 47.65

            eta_index, xi_index = nearest_lon_lat_indices(
                ds_best.lon_rho,
                ds_best.lat_rho,
                target_lon=target_lon,
                target_lat=target_lat,
            )

            selected_lon = float(ds_best.lon_rho.isel(eta_rho=eta_index, xi_rho=xi_index))
            selected_lat = float(ds_best.lat_rho.isel(eta_rho=eta_index, xi_rho=xi_index))

            eta_index, xi_index, selected_lon, selected_lat
            """
        ),
        code(
            """
            point = hv.Points(
                [(selected_lon, selected_lat)],
                kdims=["lon", "lat"],
            ).opts(color="red", marker="x", size=12)

            point_map = surface_map * point
            point_map
            """
        ),
        code(
            """
            temp_series = ds_best["temp_surface"].isel(
                eta_rho=eta_index,
                xi_rho=xi_index,
            )

            temp_series.hvplot(
                x="valid_time",
                grid=True,
                width=900,
                height=350,
                title=(
                    "Surface temperature near Puget Sound "
                    f"({selected_lon:.3f}, {selected_lat:.3f})"
                ),
            )
            """
        ),
    ]
    return nb


def main() -> None:
    nbf.write(build_notebook(), NOTEBOOK)
    print(NOTEBOOK)


if __name__ == "__main__":
    main()
