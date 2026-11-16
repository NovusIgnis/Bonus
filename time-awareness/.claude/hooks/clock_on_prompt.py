#!/usr/bin/env python3
"""UserPromptSubmit hook: tells Claude the current date and time with every user message, how long it has been since
the user's previous message and since Claude's own last entry in the conversation, and which header line to start the
reply with, so the user can see that the information arrived.

The break counts from the later of two moments: the user's previous message or Claude's last entry in the conversation
record. Long work by Claude on a task is therefore not a break; only the time after its reply is.

State: .claude/time-state.json next to this hooks folder (only times, never message content; TIME_STATE overrides the
path). Several sessions may share one project: the state is re-read right before writing, only the own session is
updated, and the file is replaced atomically, because in our setup one session once read the file while another was
writing it and wiped the state. If anything fails, the hook prints nothing and never blocks the message.

Written by Claude (Anthropic) for Fundacja Novus Ignis. Apache-2.0.
"""
import json, os, sys, time
from datetime import datetime, timedelta
from pathlib import Path

STATE = Path(os.environ.get("TIME_STATE") or Path(__file__).resolve().parents[1] / "time-state.json")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def span(d):
    m = int(d.total_seconds() // 60)
    if m < 60:
        return f"{m} min"
    h, m = divmod(m, 60)
    if h < 48:
        return f"{h} h {m} min" if m else f"{h} h"
    return f"{h // 24} days {h % 24} h"


def last_assistant_entry(path):
    """Time of the last assistant entry in the conversation record; reads only the end of the file."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            for chunk in (1 << 20, 8 << 20, 32 << 20):
                f.seek(max(0, size - chunk))
                lines = f.read().split(b"\n")
                if size > chunk:
                    lines = lines[1:]
                for line in reversed(lines):
                    if b'"type":"assistant"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if d.get("type") == "assistant" and d.get("timestamp"):
                        return datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone()
                if size <= chunk:
                    break
    except (OSError, TypeError, ValueError):
        pass
    return None


def read_state():
    for _ in range(6):
        try:
            s = json.loads(STATE.read_text(encoding="utf-8"))
            if isinstance(s, dict) and isinstance(s.get("sessions"), dict):
                return s, True
        except FileNotFoundError:
            return {"sessions": {}}, True
        except (OSError, ValueError):
            pass
        time.sleep(0.05)
    return {"sessions": {}}, False


def write_state(sid, entry):
    s, ok = read_state()
    if not ok:
        return
    s["sessions"][sid] = entry
    s["sessions"] = dict(sorted(s["sessions"].items(), key=lambda x: x[1]["last"])[-50:])
    tmp = STATE.with_name(f"{STATE.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(s, indent=1), encoding="utf-8")
        os.replace(tmp, STATE)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass


def main():
    try:
        inp = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        inp = {}
    sid = str(inp.get("session_id") or "no-id")
    now = datetime.now().astimezone()
    day = f"{DAYS[now.weekday()]} {now:%d.%m}"
    clock = f"Clock: {now:%A, %d %B %Y, %H:%M} ({now:%Z})."
    s, ok = read_state()
    if not ok:
        out = [clock, "The time hook's state was unreadable just now (another session was writing it), so the break is unknown.",
               f"Start your reply with one short line: \"{day} · {now:%H:%M} · break unknown\"."]
    else:
        prev_s = s["sessions"].get(sid)
        prev = datetime.fromisoformat(prev_s["last"]) if prev_s else None
        mine = last_assistant_entry(inp.get("transcript_path")) if prev else None
        if mine and mine > now:
            mine = None
        after_mine = bool(mine and prev and mine > prev)
        out = [clock]
        if prev:
            out.append(f"Since the user's previous message: {span(now - prev)}."
                       + (f" Since your last entry in the conversation (reply or work step): {span(now - mine)}."
                          " The break counts from the later of the two." if mine else ""))
            start = datetime.fromisoformat(prev_s["start"])
            if start.date() != now.date():
                out.append(f"This conversation started on {start:%d.%m.%Y}; the date given at its start may be out of date.")
        else:
            out.append("First message in this conversation.")
        brk = now - ((mine if after_mine else prev) or now)
        header = f"{day} · {now:%H:%M} · " + (f"{span(brk)} since my last reply" if after_mine
                                              else f"{span(brk)} since your previous message" if prev else "first message in this conversation")
        out.append(f"Start your reply with one short line, copied exactly: \"{header}\", so the user can see this information arrived. "
                   "Take any other time only from a \"Clock:\" line after a tool call or from `date`, never from an estimate.")
        # Header history: a message that arrives while the session is working (from the user or another session) runs this
        # hook again mid-turn, and a reply begun after the first message carries the older line; the Stop hook accepts any
        # header given since the turn began.
        headers = ((prev_s or {}).get("headers") or [])[-11:] + [{"h": header, "t": now.isoformat()}]
        write_state(sid, {"start": prev_s["start"] if prev_s else now.isoformat(), "last": now.isoformat(), "header": header,
                          "headers": headers})
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "\n".join(out)}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
