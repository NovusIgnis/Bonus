#!/usr/bin/env python3
"""PostToolUse hook: the current time after a tool call, at most once a minute per session (when the minute changes).
Without it, sessions working for a long time between user messages gave times in files and messages from estimates,
because the prompt hook gives the clock only when the user writes.
Set TIME_HOOK_SKIP=1 for non-interactive runs (`claude -p` from a scheduler) where the clock is not wanted.
State: ~/.local/state/clock-after-tool/<session id>.

Written by Claude (Anthropic) for Fundacja Novus Ignis. Apache-2.0.
"""
import json, os, sys
from datetime import datetime
from pathlib import Path

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main():
    if os.environ.get("TIME_HOOK_SKIP"):
        return
    try:
        sid = str(json.loads(sys.stdin.read() or "{}").get("session_id") or "no-id")
    except ValueError:
        sid = "no-id"
    now = datetime.now().astimezone()
    minute = f"{now:%Y-%m-%d %H:%M}"
    state = Path.home() / ".local/state/clock-after-tool" / "".join(c for c in sid if c.isalnum() or c == "-")[:80]
    try:
        if state.read_text() == minute:
            return
    except OSError:
        pass
    try:
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(minute)
    except OSError:
        pass
    sys.stdout.reconfigure(encoding="utf-8")
    text = f"Clock: {DAYS[now.weekday()]} {now:%d.%m}, {now:%H:%M:%S}. Use only this time (or `date`) in files and messages."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
