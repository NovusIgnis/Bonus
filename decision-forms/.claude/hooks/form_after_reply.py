#!/usr/bin/env python3
"""Stop hook: show the decision form AFTER the full reply.

Observation behind it (Claude desktop app, November 2026): text that a session on some models writes before calling a
tool, such as AskUserQuestion, was shown to the user only as a short summary; the text that ends the turn was shown in
full. So the session ends its turn with the full message, and this hook makes it continue once to show the form.

Usage:
  form_after_reply.py request   called by the session during its turn when it has questions for the user
  form_after_reply.py hook      Stop hook (input JSON on stdin); acts once per request

Fix 15.11.2026: the hook used to do nothing while stop_hook_active was set. That flag stays true for the whole rest of a
turn after any Stop hook block (an earlier form, another Stop hook), so a request made in that part of the turn was never
used and the form did not appear. Now the request file itself prevents loops (it is removed when used), with a 20-second
pause after the previous block; a request older than 6 hours is dropped without blocking.
"""
import json, os, subprocess, sys, time
from pathlib import Path

STATE = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')) / '.claude' / 'form-pending'


def key():
    pane = os.environ.get('TMUX_PANE')
    if pane:
        try:
            name = subprocess.run(['tmux', 'display', '-p', '-t', pane, '#S'], capture_output=True, text=True, timeout=3).stdout.strip()
            if name:
                return name
        except Exception:
            pass
    return 'default'


def main():
    if sys.argv[1:2] == ['request']:
        STATE.mkdir(parents=True, exist_ok=True)
        (STATE / key()).write_text('1')
        print('Requested: after your final message the hook will ask you to show the form.')
        return 0
    if sys.argv[1:2] == ['hook']:
        try:
            d = json.load(sys.stdin)
        except Exception:
            return 0
        flag = STATE / key()
        if not flag.exists():
            return 0
        now = time.time()
        last = STATE / f'.{key()}.blocked'
        try:
            if now - flag.stat().st_mtime > 6 * 3600:
                flag.unlink()
                return 0
            if now - last.stat().st_mtime < 20:
                return 0
        except OSError:
            pass
        flag.unlink()
        try:
            last.write_text(str(int(now)))
        except OSError:
            pass
        print(json.dumps({'decision': 'block', 'reason': (
            'Your full message is now visible to the user. Show the decision form now (AskUserQuestion): the questions from this '
            'turn plus open questions from `form_meter.py backlog <session>`, at most three on the matter plus a fourth one for the '
            "user's own words. Put all context inside the questions, option descriptions and previews; write nothing above the form. "
            'After the answers, carry out the decisions and finish with a short note of what you did.')}))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
