#!/usr/bin/env python3
"""Stop hook (optional): checks the reply's header line. The final text of the turn must start with the exact line that
clock_on_prompt.py gave (saved in .claude/time-state.json as "header"), and any other text of the turn that starts with
a time must use the same line. On a difference it blocks the end of the turn once and asks for a one-line correction.
The reply is already visible by then, so the correction comes as a second, short message. Does nothing when
stop_hook_active is set (no loops).

Written by Claude (Anthropic) for Fundacja Novus Ignis. Apache-2.0.
"""
import json, os, re, sys, time
from datetime import datetime
from pathlib import Path

STATE = Path(os.environ.get("TIME_STATE") or Path(__file__).resolve().parents[1] / "time-state.json")
TIMELIKE = re.compile(r"^(?:\S{1,3} \d{2}\.\d{2} · )?\d{1,2}:\d{2} ·")


def texts(entry):
    c = (entry.get("message") or {}).get("content")
    if isinstance(c, str):
        return [c]
    return [b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text"]


def starts_turn(entry):
    """A message that starts a turn (not a tool result, not this hook's own feedback)."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    c = (entry.get("message") or {}).get("content")
    if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
        return False
    t = " ".join(texts(entry)).lstrip()
    return bool(t) and not t.startswith("Stop hook feedback")


def turn(path):
    entries = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entries.append(json.loads(line))
        except ValueError:
            pass
    start = max((i for i, e in enumerate(entries) if starts_turn(e)), default=-1)
    began = entries[start].get("timestamp", "") if start >= 0 else ""
    rest = [e for e in entries[start + 1:] if e.get("type") in ("user", "assistant")]
    out = [t for e in rest if e.get("type") == "assistant" for t in texts(e) if t.strip()]
    last = rest[-1] if rest else {}
    blocks = (last.get("message") or {}).get("content")
    ended = last.get("type") == "assistant" and isinstance(blocks, list) and bool(blocks) and blocks[-1].get("type") == "text"
    return out, ended, began


def main():
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    if inp.get("stop_hook_active") or not inp.get("transcript_path"):
        return
    try:
        e = json.loads(STATE.read_text(encoding="utf-8"))["sessions"][str(inp.get("session_id"))]
        want, when = e["header"], e["last"]
    except (OSError, ValueError, KeyError, TypeError):
        return
    # The conversation record can lag: wait up to 4 s for it to end with text, otherwise do not check
    # (better to let a reply through than to block it without reason).
    for _ in range(16):
        try:
            out, ended, began = turn(inp["transcript_path"])
        except OSError:
            return
        if ended:
            break
        time.sleep(0.25)
    else:
        return
    # The header applies only to the turn the prompt hook started: turn start within 3 minutes of its record.
    try:
        if abs((datetime.fromisoformat(began.replace("Z", "+00:00")) - datetime.fromisoformat(when)).total_seconds()) > 180:
            return
    except (ValueError, TypeError):
        return
    last = inp.get("last_assistant_message")
    if isinstance(last, str) and last.strip():
        out = out + [last]
    if not out:
        return
    firsts = [t.strip().splitlines()[0].replace("*", "").strip() for t in out]
    bad = [f for f in firsts if TIMELIKE.match(f) and not f.startswith(want)]
    if not firsts[-1].startswith(want):
        bad.append(firsts[-1][:80])
    if not bad:
        return
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"decision": "block", "reason":
        f"The header does not match the time hook: \"{bad[0]}\", but the hook gave \"{want}\". Write a short correction: first line "
        f"exactly \"{want}\", then one sentence saying which time was an estimate. Do not repeat the whole reply."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
