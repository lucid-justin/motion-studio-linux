# Motion Studio UI Research (Primary Sources)

Date: 2026-02-17

## Sources Reviewed

1. Motion Studio software overview and platform support:
- https://resources.basicmicro.com/roboclaw-basics/

2. Motion Studio layout and section behavior (General/Serial/Battery/RC-PWM, PWM/Velocity/Position tabs, status indicators, stop-all guidance):
- https://resources.basicmicro.com/roboclaw-motion-studio-app-notes/

3. RoboClaw user manual (Motion Studio workflow details including display sections, status panel behavior, setup fields, PID/encoder and serial options):
- https://downloads.basicmicro.com/docs/roboclaw_user_manual.pdf

## Documented Motion Studio Capability Inventory

From the sources above, Motion Studio includes:

1. Device/session workflow:
- Connect to a selected controller, set packet address, choose serial baud, and open/close communications.

2. General setup workflow:
- View/apply configuration options, battery cutoff options, and input mode settings.

3. Control-mode and tuning screens:
- PWM settings.
- Velocity settings (P/I/D, qpps per motor).
- Position settings (P/I/D, deadzone, limits, encoder info).

4. Live status and safety workflow:
- Status section with battery, current, temperature/error-related indicators.
- Visual status indicators (normal/warning/error semantics).
- Immediate motor halt behavior (`Stop All` equivalent in app notes and manual workflow language).

5. File/report workflow:
- Save current settings and open previously saved settings from file-oriented controls.

## Current Project Mapping (After This Slice)

Implemented now in `roboclaw-gui`:

1. Device/session:
- Port/address selection.
- `info` action (firmware).

2. Config/file workflow:
- Dump to JSON, load/edit/save JSON, flash from file/editor, verify toggle.

3. Live status:
- One-click status refresh with firmware + telemetry strip:
  - main battery, logic battery, currents, encoders, error bits.

4. Safety + manual control:
- Global `STOP ALL` button.
- Spacebar `STOP ALL` shortcut.
- Manual PWM pulse panel for M1/M2 duty and bounded runtime (safety-capped and auto-safe-stop).

5. Test/report workflow:
- `smoke_v1` test execution.
- Reports explorer for JSON/CSV artifacts.

## Explicit Remaining Gaps To Reach Broader Motion Studio Parity

1. Dedicated editable forms for setup categories (General, Serial, Battery, RC/Analog) instead of JSON-first editing.
2. Velocity/Position tuning screens (PID/qpps/encoder limits) with backend field support.
3. Rich status indicator decoding (warning/error classes from raw error bits) and trend charts.
4. Multi-controller simultaneous session UX comparable to Windows app behavior.

These gaps remain intentionally tracked so UI expansion continues without bypassing backend contract discipline.
