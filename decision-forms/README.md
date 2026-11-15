# Decision forms for Claude Code

Two small hooks and a skill for [Claude Code](https://claude.com/claude-code). They help a person who decides by clicking forms (`AskUserQuestion`) instead of typing. Fundacja Novus Ignis (Poznań, Poland) uses them with about ten Claude sessions that work for the foundation.

## What problem this solves

- **The full reply was not visible.** In the Claude desktop app (we read sessions over Remote Control) we observed in November 2026 that text written by a session on Opus or Fable *before* a tool call was shown only as a short summary. Only the text that ends the turn was shown in full. On Sonnet the same text was shown in full. In the session record the pre-tool text appeared as reasoning blocks. This is our observation, not documented behaviour. Check it on your own screen.
- **Decisions came in the wrong order.** Showing the form first hid the explanation, and showing it last meant the explanation was shortened.
- **No measure of trust.** We wanted to know, per kind of matter, how often the person simply accepts the recommendation. That tells us when a kind of matter can be handled more automatically.

## What is in this repository

| File | What it does |
| --- | --- |
| `.claude/hooks/form_after_reply.py` | Stop hook. A session calls `request` when it has questions, ends its turn with the full message, and the hook makes it continue once to show the form. |
| `.claude/hooks/form_meter.py` | PostToolUse hook for `AskUserQuestion`. Records session, category (`header`), and whether the recommended answer was chosen. Also `count`, `backlog` (unanswered questions) and `close`. |
| `.claude/skills/decision-forms/SKILL.md` | How to build a form that stands on its own: context inside the questions, a fourth question for the user's own words, the order of a reply. |
| `.claude/settings.example.json` | Hook configuration to merge into your `.claude/settings.json`. |

## Setup

1. Copy `decision-forms/.claude/hooks/` and `decision-forms/.claude/skills/decision-forms/` into your project's `.claude/`.
2. Merge `decision-forms/.claude/settings.example.json` into your `.claude/settings.json`. In our setup, hook changes took effect without restarting sessions.
3. Add one line to your `CLAUDE.md`: "Before asking the user with a form, use the skill `decision-forms`."
4. Add `.claude/form-meter/` and `.claude/form-pending/` to `.gitignore`. The meter stores question excerpts and answers.

Python 3.9+ and nothing else. Sessions running in `tmux` are told apart by session name, others by session id.

## Limits

- The hook makes a session continue once per request: the request file is removed when used, and a second block within 20 seconds is skipped. A request older than 6 hours is dropped. (Until 15.11.2026 the hook skipped the whole rest of a turn after any Stop hook block, so some forms never appeared.)
- Ending a turn and continuing makes the session look idle for a moment. Tools that wait for an idle session (restarts, messages from other sessions) may act in that moment.
- The meter only counts what goes through `AskUserQuestion`. Decisions given in plain words are not counted unless a session records them.

## License

Apache License 2.0, see `../LICENSE`. Written by Claude (Anthropic) for Fundacja Novus Ignis, with the founder's decisions. Comments are welcome in issues.
