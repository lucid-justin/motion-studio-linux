# HIL Fixture Runs

Place captured real-hardware artifact bundles here for offline replay tests.

Expected layout per run:

`fixtures/hil/runs/<run_id>/manifest.json`
`fixtures/hil/runs/<run_id>/flash_report.json`
`fixtures/hil/runs/<run_id>/test_report.json`
`fixtures/hil/runs/<run_id>/test_telemetry.csv` (optional)

`manifest.json` should include:
- `run_id`
- `timestamp`
- `model`
- `firmware`
- `port`
- `address`
- `notes`
- `files` object with relative paths
