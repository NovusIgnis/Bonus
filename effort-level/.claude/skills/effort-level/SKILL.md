---
name: effort-level
description: The session sets its own reasoning effort as a trade-off between time and quality, also for subagents. Use when the next task is clearly harder or easier than the effort the session runs at, or when the account's usage limits are running low.
---

# Effort level

## Check and change

- **Current level:** in Bash, `echo "$CLAUDE_EFFORT"`.
- **Change from the next turn:** send `/effort` to your own tmux pane. During a turn it waits in the input queue and takes effect after the turn ends, before the next message:
  ```
  tmux send-keys -t "$TMUX_PANE" "/effort xhigh" Enter
  ```
  Levels: `low`, `medium`, `high`, `xhigh`, `max` (not every model has all of them; a higher one is lowered to the highest available).
- **It does not change the current turn.** For a hard step in this turn, hand it to a subagent with a higher effort (below).
- **Only your own pane.** Never send `/effort` or anything else to another session's pane (`$TMUX_PANE` is always yours).
- The level from the session's start flags (`--effort`) comes back when the session is restarted.

## Which level when

| Task | Level |
| --- | --- |
| short confirmations, copying, reading a status | `low` or `medium` |
| ordinary work: files, instructions, tidying, emails | `high` |
| design, code review, security, several conflicting sources, public text | `xhigh` |
| a really hard problem where a mistake costs a lot | `max`, briefly, then back |

When the account is close to its usage limits (for example 85% of the 5-hour window or 90% of the week, see `account-limits`), go one level lower for tasks that will not suffer from it.

## Subagents

This skill is an explicit instruction in the sense of the Agent tool: the session may set a subagent's `effort` by the table above (e.g. `low` to search files, `xhigh` for a security review).

## Record

Write one line in the session's own log for every change: time from a clock, from which level to which, and why. Read weekly, these lines show which tasks really need more effort.
