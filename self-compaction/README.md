# Self-compaction for Claude Code

A script and a skill for [Claude Code](https://claude.com/claude-code) sessions that run in `tmux`. They let a session compact its own conversation when it decides to, with its own instructions on what the summary must keep, and then continue by itself. Fundacja Novus Ignis (Poznań, Poland) uses them with about ten Claude sessions that work for the foundation.

## What problem this solves

- **Automatic compaction comes at a bad moment.** When the context fills up during a large task, the conversation is summarised in the middle of the task, without the session choosing what to keep.
- **A session cannot run `/compact` itself.** `/compact` is typed by the user. A session that knows it is about to start a large task, or that its old context gets in the way, had no way to act on that.
- **After a manual `/compact` the session waits.** Someone has to tell it to carry on.

## How it works

`compact-self now "instructions" "next"` starts a background job and returns at once. The session ends its turn. The job waits until the session is idle, types `/compact instructions` into the session's tmux pane, waits until a compaction boundary appears in the conversation record, and then types one message so the session continues with "next". Everything is logged to `~/.local/state/compact-self.log`.

`compact-self usage` prints the context size of the session's last reply, so the session can judge when compaction is worth it.

| File | What it does |
| --- | --- |
| `bin/compact-self` | The script (bash with small inline Python, nothing to install). |
| `.claude/skills/self-compaction/SKILL.md` | When to compact, how to write the instructions, what to do after. |

## Setup

1. Put `bin/compact-self` on the `PATH` of the account that runs the sessions, e.g. `~/.local/bin/`, and make it executable.
2. Copy `.claude/skills/self-compaction/` into your project's `.claude/skills/`.
3. Run your Claude Code sessions in `tmux`, one tmux session per Claude session.
4. Optional: a limit per session in `~/.config/compact-self/limit/<tmux session>` (a number of tokens), shown by `usage`.

Requires bash, tmux and Python 3.9+.

## What we observed, and limits

- The script reads files that Claude Code writes but does not document: `<config>/sessions/<pid>.json` (with `status` and `tmux`) and the conversation record in `<config>/projects/…/<sessionId>.jsonl` (with `compact_boundary` entries). We observed them in Claude Code 2.1 in November 2026. They may change in any version.
- `<config>` is `CLAUDE_CONFIG_DIR` if set, otherwise `~/.claude`.
- A long string typed into the pane at once was taken as a paste and `/compact` did not run, so the script types in chunks of 100 characters.
- Messages typed by the script appear in the conversation, and over Remote Control, as ordinary user messages. The continuation message says it comes from the script, not the user.
- Only one compaction per scheduled job. If the session does not become idle within 30 minutes, nothing happens.
- After compaction a session that re-reads large files fills its context again quickly; the skill says to read only the parts needed.

## License

Apache License 2.0, see `../LICENSE`. Written by Claude (Anthropic) for Fundacja Novus Ignis, with the founder's decisions. Comments are welcome in issues.
