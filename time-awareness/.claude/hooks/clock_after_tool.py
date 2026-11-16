#!/usr/bin/env python3
"""PostToolUse hook: the current time after a tool call, at most once a minute per session (when the minute changes).
Without it, sessions working for a long time between user messages gave times in files and messages from estimates,
because the prompt hook gives the clock only when the user writes.
Set TIME_HOOK_SKIP=1 for non-interactive runs (`claude -p` from a scheduler) where the clock is not wanted.
State: ~/.local/state/clock-after-tool/<session id>.

After a decision form (AskUserQuestion) that waited 3 minutes or more, the answer does not run the prompt hook, so the
reply would carry the header from before the form, possibly hours old. This hook then gives a new header line
("… · form answer after …") and records it in the shared state, as the prompt hook does.

Written by Claude (Anthropic) for Fundacja Novus Ignis. Apache-2.0.
"""
import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WAIT = timedelta(minutes=3)


def after_form(inp, sid, now):
    """A new header line after a decision form that waited long enough, or None."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import clock_on_prompt as c  # same state file, same writing and the same spans as the prompt hook
    asked = c.last_assistant_entry(inp.get("transcript_path"))  # the form call itself is the last assistant entry
    if not asked or now - asked < WAIT:
        return None
    s, ok = c.read_state()
    entry = s["sessions"].get(sid)
    if not ok or not entry:
        return None
    header = f"{DAYS[now.weekday()]} {now:%d.%m} · {now:%H:%M} · form answer after {c.span(now - asked)}"
    headers = (entry.get("headers") or [])[-11:] + [{"h": header, "t": now.isoformat()}]
    c.write_state(sid, dict(entry, last=now.isoformat(), header=header, headers=headers))
    return header


def main():
    if os.environ.get("TIME_HOOK_SKIP"):
        return
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        inp = {}
    sid = str(inp.get("session_id") or "no-id")
    now = datetime.now().astimezone()
    text = f"Clock: {DAYS[now.weekday()]} {now:%d.%m}, {now:%H:%M:%S}. Use only this time (or `date`) in files and messages."
    if inp.get("tool_name") == "AskUserQuestion":
        try:
            header = after_form(inp, sid, now)
        except Exception:
            header = None
        if header:
            sys.stdout.reconfigure(encoding="utf-8")
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text
                + f" The form waited a long time, so start the rest of your reply with a new line, copied exactly: \"{header}\"."}},
                ensure_ascii=False))
            return
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
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
