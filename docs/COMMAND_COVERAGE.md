# Command Coverage Map

This table tracks CLI-level coverage against current documented MVP scope and immediate parity gaps.

## MVP CLI Commands

| Command | Status | Notes |
| --- | --- | --- |
| `roboclaw list` | Implemented | Scans `/dev/ttyACM*` + `/dev/ttyUSB*` with deterministic sort. |
| `roboclaw info --port ... [--address ...]` | Implemented | Uses Basicmicro transport and typed error mapping. |
| `roboclaw dump --port ... --out ... [--address ...]` | Implemented | Dumps schema `v1` config subset + deterministic hash. |
| `roboclaw flash --port ... --config ... [--verify]` | Implemented | Applies schema `v1`, writes NVM (`94` key flow), optional reload verify (`95`). |
| `roboclaw test --port ... --recipe smoke_v1` | Implemented | Mode-gated smoke recipe with safe-stop and telemetry summary. |

## Explicitly Unsupported (For Now)

| Area | Current Handling |
| --- | --- |
| Additional test recipes beyond `smoke_v1` | Rejected with `invalid_input`. |
| Motion Studio native file import/export | Not implemented; project uses JSON schema `v1`. |
| Full settings surface beyond schema `v1` subset | Rejected as unsupported parameters in transport apply flow. |
| GUI parity features | Deferred until backend/HIL validation is complete. |

## Validation Rule

When command surface changes:
1. Update this file in the same commit.
2. Update `TODO.md` bridge-gap tasks if support status changes.
