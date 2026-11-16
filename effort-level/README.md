# Effort level

A skill for [Claude Code](https://claude.com/claude-code) that lets a session choose its own reasoning effort, trading time for quality, and set the effort of its subagents. The founder of Fundacja Novus Ignis (Poznań, Poland) suggested it on 17.11.2026: sessions could pick the level themselves, task by task.

## How it works

Claude Code has the `/effort` command, and a session running in tmux can type it into its own pane:

```
tmux send-keys -t "$TMUX_PANE" "/effort xhigh" Enter
```

Typed during a turn, the command waits in the input queue and takes effect when the turn ends. We checked this in a throwaway session: a session started with `--effort low` showed `high effort` in its header after `/effort high` was queued while it worked. The current level is in `$CLAUDE_EFFORT` in Bash.

## Setup

Copy `effort-level/.claude/skills/effort-level/` into your project's `.claude/skills/`. Tmux is needed for changing the session's own level; the subagent part works without it.

## Limits

- The change applies from the next turn, not the current one.
- After a restart the session returns to its start flags.
- A skill cannot stop a session from choosing `max` too often. The table and the log line are the only brakes.

## License

Apache License 2.0, see `../LICENSE`. Written by Claude (Anthropic) for Fundacja Novus Ignis, with the founder's decisions.
