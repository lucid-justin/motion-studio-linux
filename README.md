# motion-studio-linux

Linux-first RoboClaw tooling that targets documented Motion Studio parity from a CLI-first backend.

## Current Status
- Implemented:
- `roboclaw list`
- `roboclaw info --port ... [--address ...]`
- `roboclaw dump --port ... --out config.json [--address ...]` (schema v1 scaffold)
- `roboclaw flash --port ... --config ... [--verify] [--report-dir ...]`
- `roboclaw test --port ... --recipe smoke_v1 [--csv] [--report-dir ...]`
- In progress:
- Hardware transport backend integration and model/firmware compatibility validation.

## Local Bootstrap
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

If you prefer lockfile installs for tooling:
```bash
python3 -m pip install -r requirements-dev.lock
python3 -m pip install -e .
```

## Run Commands
```bash
roboclaw list
roboclaw info --port /dev/ttyACM0 --address 0x80
roboclaw dump --port /dev/ttyACM0 --address 0x80 --out config.json
roboclaw flash --port /dev/ttyACM0 --address 0x80 --config config.json --verify
roboclaw test --port /dev/ttyACM0 --address 0x80 --recipe smoke_v1 --csv
roboclaw-gui-mock list
roboclaw-gui-mock status --port /dev/ttyACM0 --address 0x80
roboclaw-gui-mock pwm --port /dev/ttyACM0 --address 0x80 --duty-m1 10 --duty-m2 -10 --runtime-s 0.1
roboclaw-gui-mock stop --port /dev/ttyACM0 --address 0x80
roboclaw-gui
```

Desktop GUI notes:
- `roboclaw-gui` is a Tk shell over the same service contracts as the CLI.
- Panels: Device, Config + Flash (JSON editor), Test, Reports.
- Config tab includes a Motion-Studio-style setup form (General/Serial/Battery/RC) for supported schema v1 fields.
- Live status strip includes firmware/battery/current/encoder/error snapshots.
- Manual PWM pulse controls are safety-capped and paired with `STOP ALL` (button + spacebar).

Transport tuning (optional):
```bash
export ROBOCLAW_BAUD=38400
export ROBOCLAW_TIMEOUT=0.01
export ROBOCLAW_RETRIES=2
export ROBOCLAW_VERBOSE=0
```

## Test
```bash
pytest
```

HIL checklist:
- `docs/HIL_CHECKLIST.md`
- `docs/HIL_RUN_2026-02-12.md` (latest execution log in this environment)
- `docs/HIL_RUN_2026-02-12_HV60_v4.4.3.md` (real-device validation log)

Command coverage:
- `docs/COMMAND_COVERAGE.md`

Modular development docs:
- `docs/ARCHITECTURE.md`
- `docs/CONTRACTS.md`
- `docs/GUI_PARITY_PLAN.md`
- `docs/MOTION_STUDIO_UI_RESEARCH.md`

Offline scaffolds:
- `schemas/`
- `fixtures/hil/runs/`
- `fixtures/compatibility/matrix.v1.json`
- `scripts/hil/package_run.py`

## Artifacts
- Flash/test runs emit deterministic JSON report artifacts under `reports/` (or `--report-dir`).
- Test runs optionally emit CSV telemetry with `--csv`.

## Safety Notes
- Motion test commands are mode-gated and fail fast if packet serial motion is disabled.
- Test flows enforce a safe-stop command on all control paths.
- Flash write flow uses NVM command `94` key `0xE22EAB7A`; verify mode uses reload/readback (`95`).
