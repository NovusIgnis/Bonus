#!/usr/bin/env python3
"""PostToolUse hook for AskUserQuestion: records every answer to a decision form.

For each question it stores: time, session (tmux session name, else the Claude session id), category (the question's
`header`), choice (recommended / other / own / no_answer / no_recommended), a short excerpt of the question and the answer.
Nothing else from the conversation is stored. Output: <project>/.claude/form-meter/YYYY-MM.jsonl

Usage:
  form_meter.py hook               (hook input JSON on stdin)
  form_meter.py count [days]       table per session and category, default 30 days
  form_meter.py backlog <session>  questions left without an answer and not closed yet
  form_meter.py close <session> <id> [how]   close a backlog item (e.g. answered in plain words)
"""
import hashlib, json, os, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')) / '.claude' / 'form-meter'
RECOMMENDED = '(Recommended)'


def session_name(data=None):
    pane = os.environ.get('TMUX_PANE')
    if pane:
        try:
            name = subprocess.run(['tmux', 'display', '-p', '-t', pane, '#S'], capture_output=True, text=True, timeout=3).stdout.strip()
            if name:
                return name
        except Exception:
            pass
    return (data or {}).get('session_id', 'unknown')[:8]


def write(rec):
    now = datetime.now().astimezone()
    DIR.mkdir(parents=True, exist_ok=True)
    with open(DIR / f'{now:%Y-%m}.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def hook():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    if d.get('tool_name') != 'AskUserQuestion':
        return 0
    resp = d.get('tool_response') or {}
    if isinstance(resp, str):
        try: resp = json.loads(resp)
        except Exception: resp = {}
    answers = resp.get('answers') or {}
    now = datetime.now().astimezone().isoformat(timespec='seconds')
    s = session_name(d)
    for q in (d.get('tool_input') or {}).get('questions') or []:
        text = q.get('question', '')
        a = str(answers.get(text, ''))
        labels = [o.get('label', '').strip() for o in q.get('options') or []]
        rec_label = next((l for l in labels if RECOMMENDED in l), None)
        if not a or 'did not answer' in a:
            choice = 'no_answer'
        elif rec_label is None:
            choice = 'no_recommended'
        elif a.strip() == rec_label:
            choice = 'recommended'
        elif a.strip() in labels:
            choice = 'other'
        else:
            choice = 'own'
        write({'id': hashlib.sha1(text.encode()).hexdigest()[:6], 'time': now, 'session': s, 'category': q.get('header', ''),
               'choice': choice, 'question': text[:160], 'answer': a[:120]})
    return 0


def records():
    for p in sorted(DIR.glob('*.jsonl')):
        for line in p.open(encoding='utf-8'):
            try: yield json.loads(line)
            except Exception: pass


def count(days=30):
    since = datetime.now().astimezone() - timedelta(days=days)
    t = {}
    for r in records():
        if r.get('choice') == 'closed' or datetime.fromisoformat(r['time']) < since:
            continue
        k = (r.get('session', '?'), r.get('category') or '?')
        t.setdefault(k, {}).setdefault(r['choice'], 0)
        t[k][r['choice']] += 1
    if not t:
        return f'No answers recorded in the last {days} days.'
    out = [f'Decision forms, last {days} days', '', '| Session | Category | Recommended | Other | Own | No answer | % recommended |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for (s, c), v in sorted(t.items(), key=lambda x: -sum(x[1].values())):
        r, o, w, n = (v.get(x, 0) for x in ('recommended', 'other', 'own', 'no_answer'))
        tot = r + o + w
        out.append(f'| {s} | {c} | {r} | {o} | {w} | {n} | {round(100 * r / tot) if tot else "-"}% |')
    return '\n'.join(out)


def backlog(s):
    open_items = {}
    for r in records():
        if r.get('session') != s:
            continue
        if r.get('choice') == 'no_answer':
            open_items[r['id']] = r
        else:
            open_items.pop(r.get('id'), None)
    return '\n'.join(f"{i} | {r['time'][:16]} | {r['category']} | {r['question']}" for i, r in open_items.items()) or 'No open questions.'


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['hook']: sys.exit(hook())
    if a[:1] == ['count']: print(count(int(a[1]) if len(a) > 1 else 30)); sys.exit(0)
    if a[:1] == ['backlog'] and len(a) > 1: print(backlog(a[1])); sys.exit(0)
    if a[:1] == ['close'] and len(a) > 2:
        write({'id': a[2], 'time': datetime.now().astimezone().isoformat(timespec='seconds'), 'session': a[1], 'category': '',
               'choice': 'closed', 'question': '', 'answer': ' '.join(a[3:])[:120] or 'closed'})
        print('closed'); sys.exit(0)
    print(__doc__); sys.exit(2)
