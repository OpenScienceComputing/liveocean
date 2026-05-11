import datetime as dt
import os
import unittest

import numpy as np
import xarray as xr

from scripts.liveocean_icechunk_example import (
    build_source_urls,
    concat_forecast_runs,
    get_target_config,
    make_target_s3_credentials,
    parse_run_date,
)


class LiveOceanPathTests(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        os.environ.pop("AWS_SESSION_TOKEN", None)
        os.environ.pop("SOURCE_COOP_ENDPOINT_URL", None)
        os.environ.pop("SOURCE_COOP_BUCKET", None)
        os.environ.pop("SOURCE_COOP_PREFIX", None)
        os.environ.pop("AWS_DEFAULT_REGION", None)
        os.environ.pop("LIVEOCEAN_S3_ENDPOINT_URL", None)
        os.environ.pop("LIVEOCEAN_ICECHUNK_PREFIX", None)
        os.environ.pop("LIVEOCEAN_S3_REGION", None)

    def test_parse_run_date_from_notebook_path(self):
        self.assertEqual(
            parse_run_date("s3://liveocean-share/f2026.05.08/layers.nc"),
            dt.date(2026, 5, 8),
        )

    def test_builds_seven_days_before_known_run(self):
        urls = build_source_urls(
            "s3://liveocean-share/f2026.05.08/layers.nc",
            days_before=7,
        )

        self.assertEqual(
            urls,
            [
                "s3://liveocean-share/f2026.05.01/layers.nc",
                "s3://liveocean-share/f2026.05.02/layers.nc",
                "s3://liveocean-share/f2026.05.03/layers.nc",
                "s3://liveocean-share/f2026.05.04/layers.nc",
                "s3://liveocean-share/f2026.05.05/layers.nc",
                "s3://liveocean-share/f2026.05.06/layers.nc",
                "s3://liveocean-share/f2026.05.07/layers.nc",
            ],
        )

    def test_target_credentials_require_env_values(self):
        with self.assertRaisesRegex(RuntimeError, "AWS_ACCESS_KEY_ID"):
            make_target_s3_credentials()

        os.environ["AWS_ACCESS_KEY_ID"] = "test-access-key"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret-key"

        self.assertIsNotNone(make_target_s3_credentials())

    def test_source_coop_target_config_uses_aws_s3_for_temporary_credentials(self):
        os.environ["SOURCE_COOP_ENDPOINT_URL"] = "https://data.source.coop"
        os.environ["SOURCE_COOP_BUCKET"] = "us-west-2.opendata.source.coop"
        os.environ["SOURCE_COOP_PREFIX"] = (
            "rsignell/liveocean/icechunk/liveocean-example"
        )
        os.environ["AWS_DEFAULT_REGION"] = "us-west-2"

        config = get_target_config("source-coop", "ignored-name")

        self.assertEqual(config.bucket, "us-west-2.opendata.source.coop")
        self.assertEqual(
            config.prefix,
            "rsignell/liveocean/icechunk/liveocean-example",
        )
        self.assertIsNone(config.endpoint_url)
        self.assertEqual(config.region, "us-west-2")
        self.assertFalse(config.force_path_style)

    def test_liveocean_source_target_config_uses_source_bucket_and_endpoint(self):
        os.environ["LIVEOCEAN_S3_ENDPOINT_URL"] = "https://s3.kopah.uw.edu"
        os.environ["LIVEOCEAN_ICECHUNK_PREFIX"] = "icechunk/liveocean-example"
        os.environ["LIVEOCEAN_S3_REGION"] = "not-used"

        config = get_target_config("liveocean-source", "ignored-name")

        self.assertEqual(config.bucket, "liveocean-share")
        self.assertEqual(config.prefix, "icechunk/liveocean-example")
        self.assertEqual(config.endpoint_url, "https://s3.kopah.uw.edu")
        self.assertEqual(config.region, "not-used")
        self.assertTrue(config.force_path_style)

    def test_concat_forecast_runs_keeps_lon_lat_coordinates_2d(self):
        def make_run(day, value):
            return xr.Dataset(
                {
                    "lon_rho": (("eta_rho", "xi_rho"), np.ones((2, 3))),
                    "lat_rho": (("eta_rho", "xi_rho"), np.ones((2, 3))),
                    "lon_u": (("eta_u", "xi_u"), np.ones((2, 2))),
                    "lat_u": (("eta_u", "xi_u"), np.ones((2, 2))),
                    "h": (("eta_rho", "xi_rho"), np.ones((2, 3))),
                    "temp_surface": (
                        ("step", "eta_rho", "xi_rho"),
                        np.full((2, 2, 3), value),
                    ),
                },
                coords={
                    "time": np.datetime64(f"2026-05-0{day}"),
                    "step": [np.timedelta64(0, "h"), np.timedelta64(4, "h")],
                },
            )

        combined = concat_forecast_runs([make_run(1, 1), make_run(2, 2)])

        self.assertEqual(combined["lon_rho"].dims, ("eta_rho", "xi_rho"))
        self.assertEqual(combined["lat_rho"].dims, ("eta_rho", "xi_rho"))
        self.assertEqual(combined["lon_u"].dims, ("eta_u", "xi_u"))
        self.assertEqual(combined["lat_u"].dims, ("eta_u", "xi_u"))
        self.assertIn("lon_rho", combined.coords)
        self.assertIn("lat_rho", combined.coords)
        self.assertIn("lon_u", combined.coords)
        self.assertIn("lat_u", combined.coords)
        self.assertEqual(
            combined["temp_surface"].dims,
            ("time", "step", "eta_rho", "xi_rho"),
        )


if __name__ == "__main__":
    unittest.main()
