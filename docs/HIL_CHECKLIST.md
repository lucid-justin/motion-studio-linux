# HIL Checklist

Use this checklist for each RoboClaw model/firmware pair under test.

## Test Metadata
- Date/time (UTC):
- Operator:
- Host Linux distro/kernel:
- USB adapter/cable notes:
- RoboClaw model:
- Firmware version:
- Target port/address:

## Preconditions
- [ ] Controller powered with known-safe load.
- [ ] Emergency stop path confirmed.
- [ ] Motors mechanically safe for smoke motion.
- [ ] Packet serial mode state recorded before test.
- [ ] `reports/` output directory clean for this run.

## Command Validation
- [ ] `roboclaw list` returns expected port.
- [ ] `roboclaw info --port ... --address ...` returns firmware payload.
- [ ] `roboclaw dump --port ... --address ... --out config.json` succeeds.
- [ ] `roboclaw flash --port ... --address ... --config config.json --verify` succeeds.
- [ ] `roboclaw test --port ... --address ... --recipe smoke_v1` succeeds or fails with safe stop.

## Artifact Validation
- [ ] Flash JSON report present, deterministic fields populated.
- [ ] Test JSON report present, deterministic fields populated.
- [ ] CSV telemetry generated when `--csv` is used.
- [ ] Firmware/address/port in artifacts match tested device.

## Safety and Failure Validation
- [ ] Motion disabled mode produces clear mode mismatch behavior.
- [ ] Exception path verifies safe stop (`duty=0`/stop command observed).
- [ ] Verify mismatch path (`--verify`) returns non-zero and logs report.

## Notes
- Observed caveats by model/firmware:
- Unexpected behavior:
- Follow-up tasks:

## Latest Completed Run
- Date (UTC): `2026-02-12`
- Device: `RoboClaw HV60 2x60A v4.4.3`
- Run log: `docs/HIL_RUN_2026-02-12_HV60_v4.4.3.md`
- Summary:
- Command set executed on real hardware.
- Smoke test passed.
- Verify path caveat captured (`ReadNVM` timeout).
- Controller restored to original state at end of run.
