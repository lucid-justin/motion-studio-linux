# Motion Studio Linux Plan (Refined)

## Two-Sentence Project Summary (Documented Info Only)
Based on RoboClaw and Motion Studio documentation, a Linux tool can connect over USB CDC serial, read/write controller settings through packet serial commands, persist settings to NVM (command `94` with key `0xE22EAB7A`), reload from NVM (command `95`), and run status/motion validation when packet-serial mode permits motor commands.  
The project goal is to reproduce as much of that documented Windows Motion Studio workflow as practical on Linux using existing maintained libraries (primarily Basicmicro's modern Python library), while explicitly tracking any documented parity gaps.

## North Star
- Mimic as much documented Motion Studio functionality as possible on Linux.
- Prefer existing maintained libraries over custom protocol reimplementation.
- Treat parity gaps as first-class tracked work, not hidden technical debt.

## Documented Baseline We Are Building Against
- RoboClaw appears as USB CDC virtual COM on Linux (`/dev/ttyACM*` or `/dev/ttyUSB*`).
- Packet serial mode gates motion commands over USB:
  - status/config operations can work outside motion-enabled packet serial mode
  - motion tests must fail fast with a clear mode-gating warning when disabled
- Configuration persistence is explicit:
  - command `94`: write settings to NVM (with key `0xE22EAB7A`)
  - command `95`: read settings from NVM
- Motion Studio supports save/restore configuration files.
- Packet serial command groups include status, settings, open-loop, and closed-loop operations.

## Delivery Strategy (Parity First)
1. Build a reliable backend/CLI parity core.
2. Add deterministic reporting, validation, and safety controls.
3. Expand command coverage toward broader Motion Studio parity.
4. Add GUI layer after backend workflows are stable and testable.

## Initial Feature Parity Matrix
Status legend: `Implemented`, `In Progress`, `Planned`, `Unknown/Needs Research`

| Capability | Linux Target | Status | Notes |
| --- | --- | --- | --- |
| Device discovery | Scan `/dev/ttyACM*` and `/dev/ttyUSB*` | Planned | Auto-detect + manual override |
| Device info | Read firmware/device identity | Planned | Needed for audit artifacts |
| Settings apply | Write selected config fields to device | Planned | Start with team-critical subset |
| Flash to NVM | Command `94` + key | Planned | Mandatory in flash workflow |
| Reload/verify | Command `95` + readback compare | Planned | Optional strict mode in MVP |
| Save config to file | Dump known setting subset | Planned | JSON first, YAML optional |
| Restore config from file | Apply saved config | Planned | Must preserve schema version |
| Quick functional test | Recipe execution + telemetry checks | Planned | Mode-gated and fail-safe |
| Deterministic reports | JSON per flash/test run | Planned | CSV telemetry optional |
| Multi-address support | `(port, address)` model | Planned | `0x80` default, future expansion |
| GUI parity | Motion Studio-like UI features | Planned (post-backend) | Backend maturity first |

## Differences To Outline and Track
These are the known areas where Linux implementation may diverge from Windows Motion Studio and must be explicitly documented.

1. UI/UX parity:
- Motion Studio is Windows GUI-first; this project is backend/CLI-first initially.

2. Config format parity:
- Motion Studio save-file structure may not match our JSON/YAML schema.
- We need import/export mapping rules or conversion utilities if formats differ.

3. Command coverage parity:
- Motion Studio may expose settings/actions not yet covered by the selected library wrappers.
- We need a command coverage inventory and explicit "unsupported" list.

4. Mode-dependent behavior:
- Motion commands are unavailable unless packet serial mode is motion-enabled.
- We need clear operator messaging so this does not look like random failure.

5. Hardware/firmware variance:
- Behavior can differ by RoboClaw model and firmware version.
- We need per-model validation notes and tested compatibility matrix.

## MVP Workstreams
1. Core connection and session layer:
- connect/disconnect
- firmware read
- mode checks

2. Config workflows:
- load schema
- apply settings
- write NVM (`94`)
- optional reload/verify (`95`)
- dump/save config

3. Test workflows:
- smoke recipe execution
- telemetry polling
- pass/fail rules
- guaranteed safe stop on any exception

4. Reporting and error taxonomy:
- structured JSON report artifacts
- typed errors: timeout, no-response, CRC/error response, mode mismatch, safety abort

5. CLI surface:
- `roboclaw list`
- `roboclaw info --port ...`
- `roboclaw flash --config ...`
- `roboclaw test --recipe smoke_v1`
- `roboclaw dump --out config.json`

## Immediate Next Actions
1. Build a documented command-coverage map:
- Motion Studio documented actions vs library-exposed commands vs project status.

2. Define `config schema v1`:
- only high-value settings first (PID/mode/limits/encoder-related fields used by your team).

3. Define `smoke_v1` test recipe:
- short forward/reverse test with encoder/status verification and strict safety limits.

4. Scaffold CLI and service interfaces:
- implement stubs with typed errors and report artifact contracts before full command coverage.

## MVP Acceptance Criteria
- A user can connect to a RoboClaw on Linux and read device info.
- A user can apply a config and persist it to NVM (`94`) with a clear success/failure report.
- A user can run a smoke test that always exits in a safe stop state.
- A user can dump and restore config using project schema files.
- Every flash/test run produces reproducible machine-readable artifacts.
- Known parity gaps are listed explicitly, not implicit.

## Risks and Mitigations
1. Hidden parity gaps:
- Mitigation: maintain the parity matrix as an active checklist.

2. Unsafe test behavior:
- Mitigation: enforce safety bounds + always-stop in exception handlers.

3. Firmware-specific command differences:
- Mitigation: include firmware in all reports and build compatibility notes by model/version.

4. Scope creep before stability:
- Mitigation: freeze MVP contracts first, then expand command coverage intentionally.
