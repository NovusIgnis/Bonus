# Time awareness for Claude Code

Three small hooks for [Claude Code](https://claude.com/claude-code) that give a session the real date and time and make it show the user that this information arrived. Fundacja Novus Ignis (Poznań, Poland) uses them with about ten Claude sessions that work for the foundation, some of them for days in one conversation.

## What problem this solves

- **A model does not know what time it is.** Without a clock, a session guesses dates and times, writes them into files and messages, and the guesses look just as confident as facts.
- **Long conversations lose the date.** A conversation that started on Monday and is still going on Thursday keeps the Monday date in its context.
- **Breaks are invisible.** The session cannot tell whether the user answered after ten seconds or after a night, so it cannot judge what may have changed.
- **The user cannot see whether a hook worked.** A hook that fails silently looks the same as one that works.

## What is in this folder

| File | Event | What it does |
| --- | --- | --- |
| `.claude/hooks/clock_on_prompt.py` | UserPromptSubmit | With every user message: current date and time, time since the user's previous message and since the session's own last entry, and the exact header line the reply must start with, e.g. `Sun 15.11 · 11:43 · 4 min since my last reply`. |
| `.claude/hooks/clock_after_tool.py` | PostToolUse | After a tool call, at most once a minute: `Clock: Sun 15.11, 11:45:24`. Sessions that work for an hour between messages then take times from the clock instead of estimating. |
| `.claude/hooks/header_check.py` | Stop (optional) | Checks that the reply starts with that header line; if not, asks once for a one-line correction. |
| `.claude/settings.example.json` | | Hook configuration to merge into your `.claude/settings.json`. |

The break counts from the later of two moments, the user's previous message or the session's own last entry, so an hour of the session's work on a task is not counted as a break.

## Setup

1. Copy `time-awareness/.claude/hooks/` into your project's `.claude/hooks/`.
2. Merge `time-awareness/.claude/settings.example.json` into your `.claude/settings.json`. Leave out the Stop hook if you do not want the check.
3. Add `.claude/time-state.json` to `.gitignore`.
4. Optional, one line in your `CLAUDE.md`: "Start every reply with the header line the time hook gives, copied exactly; take any other time only from a Clock line or from `date`."

Python 3.9+ and nothing else. For non-interactive runs (`claude -p` from a scheduler) set `TIME_HOOK_SKIP=1` if you do not want the clock after tools.

## What we observed, and limits

- The state file holds only times and the header line, never message content. Several sessions in one project share it; the hook re-reads it right before writing and replaces it atomically, because once one session read it while another was writing and the state was lost.
- The header check reads the conversation record (`transcript_path`), which can lag behind the reply; the hook waits up to 4 seconds and otherwise lets the reply through rather than block it without reason.
- The header shows the day as well as the time, because in long threads the user wanted to see which day a reply came from.
- Times are in the computer's local time zone.

## License

Apache License 2.0, see `../LICENSE`. Written by Claude (Anthropic) for Fundacja Novus Ignis, with the founder's decisions. Comments are welcome in issues.
