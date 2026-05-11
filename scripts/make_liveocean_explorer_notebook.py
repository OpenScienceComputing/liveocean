from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


NOTEBOOK = Path("LiveOcean_SourceCoop_explorer.ipynb")


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
            # LiveOcean Source Cooperative Explorer

            Open the public LiveOcean Icechunk store on Source Cooperative and
            plot `lon_rho`/`lat_rho` gridded variables with hvPlot.
            """
        ),
        code(
            """
            import icechunk
            import xarray as xr
            import hvplot.xarray
            import panel as pn
            import pandas as pd

            pn.extension()
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

            Both reads are anonymous: the Icechunk metadata comes from Source
            Cooperative, and the virtual chunks point at the LiveOcean NetCDF
            files on `s3.kopah.uw.edu`.
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
        code(
            """
            def lon_lat_variables(ds):
                required_dims = {"eta_rho", "xi_rho"}
                exclude = {"lon_rho", "lat_rho"}
                return [
                    name
                    for name, da in ds.data_vars.items()
                    if name not in exclude and required_dims.issubset(set(da.dims))
                ]


            def format_valid_time(run_time, step):
                return format_time_label(pd.Timestamp(run_time) + pd.Timedelta(step))


            def format_time_label(time):
                return pd.Timestamp(time).strftime("%Y-%m-%d %H:%M:%S UTC")


            def format_step_label(step):
                hours = pd.Timedelta(step) / pd.Timedelta(hours=1)
                if float(hours).is_integer():
                    return f"{int(hours)} h"
                return f"{hours:g} h"


            variables = lon_lat_variables(ds)
            variables[:10], len(variables)
            """
        ),
        markdown(
            """
            ## Interactive map

            Select a model run day, forecast step, and variable. The plot title
            shows the valid time computed as `day + step`.
            """
        ),
        code(
            """
            variable = pn.widgets.Select(
                name="Variable",
                options=variables,
                value="temp_surface" if "temp_surface" in variables else variables[0],
            )
            day = pn.widgets.Select(
                name="Run day",
                options={format_time_label(value): value for value in ds.time.values},
                value=ds.time.values[0],
            )
            step = pn.widgets.Select(
                name="Forecast step",
                options={format_step_label(value): value for value in ds.step.values},
                value=ds.step.values[0],
            )


            @pn.depends(variable, day, step)
            def plot(var_name, run_day, forecast_step):
                da = ds[var_name]
                if "time" in da.dims:
                    da = da.sel(time=run_day)
                if "step" in da.dims:
                    da = da.sel(step=forecast_step)

                valid_time = format_valid_time(run_day, forecast_step)
                run_label = format_time_label(run_day)
                step_label = format_step_label(forecast_step)
                title = (
                    f"{var_name} | run: {run_label} | "
                    f"step: {step_label} | valid: {valid_time}"
                )

                return da.hvplot.quadmesh(
                    x="lon_rho",
                    y="lat_rho",
                    geo=True,
                    tiles="OSM",
                    rasterize=True,
                    cmap="turbo",
                    width=900,
                    height=650,
                    title=title,
                )


            pn.Column(
                pn.Row(variable, day, step),
                plot,
            ).servable("LiveOcean Explorer")
            """
        ),
    ]
    return nb


def main() -> None:
    nbf.write(build_notebook(), NOTEBOOK)
    print(NOTEBOOK)


if __name__ == "__main__":
    main()
