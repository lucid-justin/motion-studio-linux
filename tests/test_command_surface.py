from __future__ import annotations

import pytest

from motion_studio_linux.cli import _build_parser


@pytest.mark.unit
def test_cli_command_surface_matches_mvp_scope() -> None:
    parser = _build_parser()
    subparsers_actions = [
        action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction"  # type: ignore[attr-defined]
    ]
    assert len(subparsers_actions) == 1
    choices = set(subparsers_actions[0].choices.keys())
    assert choices == {"list", "info", "dump", "flash", "test"}
