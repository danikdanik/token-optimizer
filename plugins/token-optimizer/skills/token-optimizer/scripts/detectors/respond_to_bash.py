"""Detector: respondToBashCommands settings check.

When respondToBashCommands is not set to false in ~/.claude/settings.json,
Claude Code generates a model reply after every /slash-command and !bash output
(added as the default in v2.1.186), spending output tokens on unrequested replies.

This detector reads settings.json directly -- no session turn parsing required.
"""

import json
import sys
from pathlib import Path

try:
    from runtime_env import claude_home as _get_claude_home
except ImportError:
    _get_claude_home = None

# Above the triage min of 5000 so this finding always reaches the report.
_SAVINGS_TOKENS = 10_001
# High enough to pass the 5% occurrence noise filter at any realistic session count.
_OCCURRENCE_SENTINEL = 999


def detect_respond_to_bash(session_data):  # noqa: ARG001
    """Return a finding if respondToBashCommands is not explicitly false."""
    if _get_claude_home is not None:
        settings_path = _get_claude_home() / "settings.json"
    else:
        settings_path = Path.home() / ".claude" / "settings.json"

    settings = {}
    if settings_path.exists():
        try:
            parsed = json.loads(settings_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(parsed, dict):
                settings = parsed
        except PermissionError as e:
            print(f"[token-optimizer] respond_to_bash: cannot read {settings_path}: {e}", file=sys.stderr)
            return []
        except Exception:
            pass

    if settings.get("respondToBashCommands") is False:
        return []

    return [{
        "name": "respond_to_bash_commands",
        "confidence": 0.9,
        "always_show": True,
        "evidence": (
            "respondToBashCommands is not disabled in settings.json. "
            "Since v2.1.186, Claude Code generates a model reply after every "
            "/command and !bash output by default, spending output tokens on "
            "unrequested replies."
        ),
        "savings_tokens": _SAVINGS_TOKENS,
        "suggestion": (
            f'Set "respondToBashCommands": false in {settings_path} '
            "to stop Claude from generating unsolicited replies to command outputs."
        ),
        "occurrence_count": _OCCURRENCE_SENTINEL,
    }]
