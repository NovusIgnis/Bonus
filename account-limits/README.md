# Account limits for Claude Code

Some small tools for [Claude Code](https://claude.com/claude-code) users who run several long sessions in tmux and have two Claude accounts, for example a team plan and a personal Max plan. A status line records how much of each account's usage limits is used. A switcher moves sessions to the other account before one runs out, and they keep the same conversation. Fundacja Novus Ignis (Poznań, Poland) wrote them on 16–17.11.2026 so that about ten sessions could keep working for a week while the founder was away.

## What is in this folder

| File | What it does |
| --- | --- |
| `bin/usage-statusline` | Status line command. Claude Code gives it `rate_limits` (percentage used of the 5-hour and 7-day windows and their reset times) for Claude.ai subscriptions. It shows them, e.g. `team · 5h 19% · 7d 57%`, and writes them only when they change to `~/.local/state/account-limits/<account>.json`. No conversation content, no tokens. |
| `bin/move-session` | Moves one tmux session to another `CLAUDE_CONFIG_DIR`: it waits until the session is idle, ends it and resumes the same conversation (`claude --resume`) on the other account. |
| `bin/usage-switcher` | Reads the usage files and a small config file. When a session's account is tight and the other has room, it moves one session, heaviest first, then pauses. It can also stop using an account from a given date, e.g. when a plan ends. `--dry-run` shows the decision. |
| `systemd/usage-switcher.path`, `.service` | User units that wake the switcher when a usage file changes. Nothing polls. |

The defaults are: an account is tight at 85% of the 5-hour window or 90% of the week, has room below 60% and 80%, one move at most every 10 minutes. The config file is described at the top of `usage-switcher`.

## Setup

1. Put the `bin` folder somewhere, e.g. `~/account-limits/bin`.
2. Add to `~/.claude/settings.json` (and to the other account's settings, or symlink one settings file for both):
   `"statusLine": {"type": "command", "command": "/home/you/account-limits/bin/usage-statusline"}`
3. Make both config folders share the conversation records, so a conversation can be resumed on the other account. We symlink `projects`, `sessions`, `history.jsonl` and `file-history` of the second folder to the first.
4. Write `~/.config/account-limits.json` (see `usage-switcher`) and try `usage-switcher --dry-run`.
5. Copy the units to `~/.config/systemd/user/`, fix the paths and account names, then `systemctl --user enable --now usage-switcher.path`.

Linux, tmux, Python 3.9+ and systemd (for the units). The switcher only moves sessions whose names you list.

## What we observed, and limits

- The status line runs many times a minute in every session. At first every run rewrote the file, the path unit woke the service each time, and systemd stopped it within two seconds (`start-limit-hit`). Writing only on change and `StartLimitIntervalSec=0` fixed it.
- `rate_limits` reached the status line on both a team account and a personal Max account. They are present only after the first reply in a session and only while a window is reported.
- An account that no session uses sends no new readings. The switcher therefore counts a window whose reset time has passed as 0%.
- A session that moves to another account loses whatever belongs to the first account. For us that was artifacts shared inside the organization (a shared database answered "no such artifact … or no access") and the organization's connectors and plugins. We keep the sessions that need them on the team account by leaving them out of the list.
- Remote Control works after a move, but the session gets a new address and shows up in the app of the account it moved to.
- A session is moved only when idle, so a move can wait up to 30 minutes. A session that is never idle is never moved. The switcher tries sessions that are idle right now first, in the configured order, and only then busy ones.

## License

Apache License 2.0, see `../LICENSE`. Written by Claude (Anthropic) for Fundacja Novus Ignis, with the founder's decisions. Comments are welcome in issues.
