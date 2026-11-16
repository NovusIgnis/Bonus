#!/usr/bin/env python3
"""Stop hook (optional): checks the reply's header line. The final text of the turn must start with the exact line that
clock_on_prompt.py gave (saved in .claude/time-state.json as "header"), or any header line given since the turn began
(a message that arrives while the session works, and a long-waiting decision form, give a newer line mid-turn), and
any other text of the turn that starts with a time must use one of these lines. On a difference it blocks the end of the turn once and asks for a one-line correction.
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
    r = entry.get("toolUseResult")  # an answer to a decision form starts a new part of the turn
    if isinstance(r, dict) and "answers" in r and "questions" in r:
        return True
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
    starts = [i for i, e in enumerate(entries) if starts_turn(e)]
    start = starts[-1] if starts else -1
    # Moments the header may come from: the last message or form answer, and the last plain message before forms.
    plain = [i for i in starts if not isinstance(entries[i].get("toolUseResult"), dict)]
    began = [entries[i].get("timestamp", "") for i in {start, plain[-1] if plain else start} if i >= 0]
    # Start of the whole turn: the message right after a finished reply (a text block), or the first one. Messages that
    # arrive mid-work (after a tool result) and form answers do not start a new turn for the header history.
    conv = [i for i, e in enumerate(entries) if e.get("type") in ("user", "assistant")]
    whole = start
    for i in reversed(starts):
        before = [j for j in conv if j < i]
        if not before:
            whole = i
            break
        b = (entries[before[-1]].get("message") or {}).get("content")
        if entries[before[-1]].get("type") == "assistant" and isinstance(b, list) and b and b[-1].get("type") == "text":
            whole = i
            break
    turn_began = entries[whole].get("timestamp", "") if whole >= 0 else ""
    rest = [e for e in entries[start + 1:] if e.get("type") in ("user", "assistant")]
    out = [t for e in rest if e.get("type") == "assistant" for t in texts(e) if t.strip()]
    last = rest[-1] if rest else {}
    blocks = (last.get("message") or {}).get("content")
    ended = last.get("type") == "assistant" and isinstance(blocks, list) and bool(blocks) and blocks[-1].get("type") == "text"
    return out, ended, began, turn_began


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
            out, ended, began, turn_began = turn(inp["transcript_path"])
        except OSError:
            return
        if ended:
            break
        time.sleep(0.25)
    else:
        return
    # The header applies only to the turn the prompt hook started: turn start within 3 minutes of its record.
    try:
        if min(abs((datetime.fromisoformat(b.replace("Z", "+00:00")) - datetime.fromisoformat(when)).total_seconds())
               for b in began) > 180:
            return
    except (ValueError, TypeError):
        return
    allowed = [want]
    try:
        since = datetime.fromisoformat(turn_began.replace("Z", "+00:00"))
        allowed += [h["h"] for h in e.get("headers") or [] if (datetime.fromisoformat(h["t"]) - since).total_seconds() >= -60]
    except (ValueError, TypeError, KeyError, AttributeError):
        pass
    ok = lambda f: any(f.startswith(a) for a in allowed)
    last = inp.get("last_assistant_message")
    if isinstance(last, str) and last.strip():
        out = out + [last]
    if not out:
        return
    firsts = [t.strip().splitlines()[0].replace("*", "").strip() for t in out]
    bad = [f for f in firsts if TIMELIKE.match(f) and not ok(f)]
    if not ok(firsts[-1]):
        bad.append(firsts[-1][:80])
    if not bad:
        return
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"decision": "block", "reason":
        f"The header does not match the time hook: \"{bad[0]}\", but the hook gave \"{want}\". Write a short correction: first line "
        f"exactly \"{want}\", then one sentence saying which time was an estimate. Do not repeat the whole reply."}, ensure_ascii=False))


if __name__ == "__main__":
    main()
