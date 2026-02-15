# AGENTS.md

## Mission
Build a Linux-first RoboClaw tool that mimics as much documented Windows Motion Studio behavior as practical using existing libraries.
Prioritize backend parity first (flash/test/dump reliability), then add GUI parity.

This file is the operational contract for human and AI contributors.

## Source of Truth
- Product plan: `PLAN.md`
- If code and this file disagree, update one of them in the same change.
- If behavior changes, update this file in the same PR/commit.
- Git history is the changelog; no in-file changelog is required.

## MVP Scope (v1)
- Discover devices on `/dev/ttyACM*` and `/dev/ttyUSB*`.
- Target model is `(port, address)` where default address is `0x80`.
- Implement:
  - `list`
  - `info --port ...`
  - `flash --config ... [--verify] [--report-dir ...]`
  - `test --recipe smoke_v1 [--csv] [--report-dir ...]`
  - `dump --out config.json`

## Safety-Critical Rules (Do Not Violate)
1. Always force safe stop on exceptions in test flow (`duty=0` / stop command).
2. Never run motion commands unless packet serial mode permits motion.
3. Flash flow must persist config to NVM with command `94` and key `0xE22EAB7A`.
4. Support reload/readback verification (command `95`) for flash verification mode.
5. Every flash/test run must emit deterministic artifacts (JSON report; CSV optional).

## Required Service Contracts
- `DeviceManager.list_ports()`
- `RoboClawSession.connect(port)` / `disconnect()`
- `RoboClawSession.get_firmware()`
- `Flasher.apply_config(config)`
- `Flasher.write_nvm()`
- `Flasher.reload_from_nvm()`
- `Tester.run_recipe(recipe)`
- `Telemetry.poll(snapshot_fields...)`

## Audit and Reporting Requirements
Each flash report includes:
- timestamp
- port
- address
- firmware
- config hash/version
- applied parameters
- write-to-NVM result
- verification result (if enabled)
- schema version

Verification semantics:
- `verification result = pass|mismatch|error`.
- `error` means verification transport/readback failed after retry; write-to-NVM result is still reported independently.

Each test report includes:
- recipe ID + safety limits
- pass/fail + reason
- sampled telemetry summary
- abort reason (if any)
- schema version

## Engineering Defaults
- Prefer simple, composable workflows over opaque orchestration.
- Keep workflows explicit before adding autonomous behavior.
- Add typed errors for: timeout, CRC/error response, no response, mode mismatch, safety abort.
- Add tests whenever changing flash/test logic (unit first, hardware-in-loop when possible).

## Commit/Push Defaults
For large change sets (for example: multi-file feature slices, broad refactors, or >5 files changed):
1. Run relevant tests before finalizing the slice.
2. Create a checkpoint commit with a clear, scoped message.
3. Push to the current upstream branch by default.

Exceptions:
- If the user explicitly says not to commit or not to push.
- If tests are failing and the commit would hide unresolved breakage.
- If credentials/remote access are unavailable.

## Long Codex Session Protocol
For long coding sessions (multi-hour or multi-day), optimize for clean handoff and low context loss:

1. Start each session by reading `AGENTS.md`, `PLAN.md`, and current git status.
2. Work in small vertical slices with verifiable outcomes.
3. After each slice:
   - update `PLAN.md` status/checklist items if scope or ordering changed
   - run relevant tests/commands and record outcomes in commit/PR notes
4. Keep unfinished work resumable:
   - avoid leaving partial refactors without a clear TODO block
   - preserve backward-compatible behavior unless the plan explicitly changes
5. Before ending a session:
   - ensure repo state is understandable from `git status`, commit messages, and `PLAN.md`
   - include explicit next step(s) in the final handoff message

## Make This a Living Document
Treat `AGENTS.md` as code, not prose.

Update triggers:
- New documented Motion Studio behavior identified.
- New command/recipe/config field added.
- Any incident/postmortem from flash/test failures.
- Any change to CLI contract or report schema.

Maintenance loop:
1. Keep sections small; split specialized guidance into nested `AGENTS.md` files when needed.
2. Review at least once per milestone (or biweekly) and remove stale rules.
3. When uncertain, prefer explicit examples over abstract guidance.
