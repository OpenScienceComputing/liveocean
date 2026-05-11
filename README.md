# LiveOcean Icechunk Example

This repository contains a small LiveOcean-to-Icechunk workflow and an
interactive notebook for exploring the result with hvPlot.

## What We Created

- `scripts/liveocean_icechunk_example.py` creates a virtual Icechunk store from
  seven LiveOcean forecast runs. It derives source paths from a known file:
  `s3://liveocean-share/f2026.05.08/layers.nc`, then uses the seven preceding
  daily paths (`f2026.05.01` through `f2026.05.07`).
- `scripts/make_liveocean_explorer_notebook.py` generates
  `LiveOcean_SourceCoop_explorer.ipynb`.
- `scripts/liveocean_explorer.py` contains small helper functions used by the
  notebook tests.
- `LiveOcean_SourceCoop_explorer.ipynb` opens the public Source Cooperative
  Icechunk store anonymously and plots LiveOcean variables with hvPlot.
- Tests in `tests/` cover path generation, target configuration, coordinate
  handling, notebook helper formatting, and the forecast-step label display.

The current public Icechunk store is:

```text
s3://us-west-2.opendata.source.coop/rsignell/liveocean/icechunk/liveocean-layers-icechunk-example
```

The shared notebook is available at:

```text
https://notebooksharing.space/view/101d2cfdb46704a2995bfaabee2dd26fcfafe532e70aab8b7b89a8821286d623
```

## Data Model Notes

The LiveOcean source NetCDF files are read from:

```text
s3://liveocean-share/fYYYY.MM.DD/layers.nc
```

using the S3-compatible endpoint:

```text
https://s3.kopah.uw.edu
```

The source files can be read anonymously by direct object path, but the bucket
does not allow anonymous listing. The example workflow therefore avoids source
bucket listing and derives file names from the known daily path pattern.

Before concatenating forecast runs, the script promotes `lon_*` and `lat_*`
variables to xarray coordinates so spatial coordinates such as `lon_rho` and
`lat_rho` remain 2D (`eta_rho`, `xi_rho`) rather than gaining a `time`
dimension during `xr.concat`.

## Reading the Public Icechunk

Reading does not require credentials for either the Source Cooperative Icechunk
metadata or the referenced LiveOcean NetCDF chunks.

```python
import icechunk
import xarray as xr

storage = icechunk.s3_storage(
    bucket="us-west-2.opendata.source.coop",
    prefix="rsignell/liveocean/icechunk/liveocean-layers-icechunk-example",
    region="us-west-2",
    anonymous=True,
)

config = icechunk.RepositoryConfig.default()
config.set_virtual_chunk_container(
    icechunk.VirtualChunkContainer(
        url_prefix="s3://liveocean-share/",
        store=icechunk.s3_store(
            region="not-used",
            anonymous=True,
            s3_compatible=True,
            force_path_style=True,
            endpoint_url="https://s3.kopah.uw.edu",
        ),
    )
)

credentials = icechunk.containers_credentials(
    {"s3://liveocean-share/": icechunk.s3_credentials(anonymous=True)}
)

repo = icechunk.Repository.open(
    storage,
    config,
    authorize_virtual_chunk_access=credentials,
)
ds = xr.open_zarr(repo.readonly_session("main").store, consolidated=False, chunks={})
```

## Credential Files

Credential files live outside the repository under `~/dotenv/`. Do not commit
these files or paste their values into notebooks, scripts, issues, or chat.

### Source Cooperative Upload Credentials

`~/dotenv/source-coop-liveocean.env` is used only when writing the Icechunk to
Source Cooperative:

```bash
AWS_ACCESS_KEY_ID="<temporary-source-coop-access-key>"
AWS_SECRET_ACCESS_KEY="<temporary-source-coop-secret-key>"
AWS_SESSION_TOKEN="<temporary-source-coop-session-token>"
AWS_DEFAULT_REGION="us-west-2"
SOURCE_COOP_ENDPOINT_URL="https://data.source.coop"
SOURCE_COOP_BUCKET="us-west-2.opendata.source.coop"
SOURCE_COOP_PREFIX="rsignell/liveocean/icechunk/liveocean-layers-icechunk-example"
```

Notes:

- The Source Cooperative temporary credentials are used through standard AWS S3
  for writing, so the script does not pass `SOURCE_COOP_ENDPOINT_URL` into
  Icechunk storage creation.
- `SOURCE_COOP_PREFIX` points at the Icechunk repository root inside the Source
  Cooperative product.
- These credentials are not needed for reading the public Icechunk.

### LiveOcean Source Bucket Upload Credentials

`~/dotenv/liveocean-source.env` can be used when writing Icechunk metadata back
to the same S3-compatible bucket and endpoint as the LiveOcean NetCDF files:

```bash
AWS_ACCESS_KEY_ID="<liveocean-write-access-key>"
AWS_SECRET_ACCESS_KEY="<liveocean-write-secret-key>"
AWS_SESSION_TOKEN="<optional-liveocean-session-token>"
LIVEOCEAN_S3_ENDPOINT_URL="https://s3.kopah.uw.edu"
LIVEOCEAN_S3_REGION="not-used"
LIVEOCEAN_ICECHUNK_PREFIX="icechunk/liveocean-layers-icechunk-example"
```

The `liveocean-source` target writes to:

```text
s3://liveocean-share/<LIVEOCEAN_ICECHUNK_PREFIX>
```

This target is useful if write credentials are available for the same bucket
that holds the NetCDF files. It still reads the source NetCDF files by direct
path and does not require bucket listing.

## Common Commands

Run tests:

```bash
conda run -n coawst-icechunk pytest -q
```

Dry-run the Source Cooperative Icechunk creation without reading or writing
objects:

```bash
conda run -n coawst-icechunk python scripts/liveocean_icechunk_example.py \
  --dry-run
```

Create the Source Cooperative Icechunk:

```bash
conda run -n coawst-icechunk python scripts/liveocean_icechunk_example.py \
  --target source-coop
```

Create an Icechunk in the LiveOcean source bucket when
`~/dotenv/liveocean-source.env` is available:

```bash
conda run -n coawst-icechunk python scripts/liveocean_icechunk_example.py \
  --target liveocean-source
```

Regenerate the explorer notebook:

```bash
conda run -n coawst-icechunk python scripts/make_liveocean_explorer_notebook.py
```

Upload the notebook to notebooksharing.space:

```bash
conda run -n coawst-icechunk nbss-upload LiveOcean_SourceCoop_explorer.ipynb
```
