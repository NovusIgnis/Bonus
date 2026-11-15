---
name: self-compaction
description: Compact your own conversation when you decide it is needed, with instructions on what to keep; check how much context you use; report when your context limit should change. Use before starting a large task with a large context, before long reading, or when old context gets in the way.
---

# Compaction on your own decision

**You decide.** You do not ask the user for permission to compact. (In our setup this was the founder's explicit wish: each session should decide this itself.)

## When

- You are starting a new large task and the context is already close to the limit. Automatic compaction would come in the middle of the task and summarise it without your choice.
- Before long reading (for example a set of documents you need to read in full).
- Old context gets in the way: finished threads, long tool output, outdated arrangements.
- Do not compact in the middle of a step that depends on details in the current context, or right before answering the user's question.

## How

1. Check usage: `compact-self usage`. It shows the context in tokens from your last reply and your limit, if one is set.
2. Before you schedule a compaction, write down in your own notes or log what must not be lost: open matters, deadlines, what you wait for and from whom.
3. Write the instructions: what the summary must keep. One line, because new lines become spaces. Usually:
   - open matters and the next step;
   - standing rules and the user's words verbatim;
   - file paths, case codes, checksums;
   - what to leave out, i.e. finished threads.
4. Schedule: `compact-self now "instructions" "next"`. The script waits in the background until your turn ends (status `idle`, at most 30 minutes) and types `/compact instructions` into your tmux pane. Then it waits for the compaction boundary to appear in the conversation and sends you the message "[compaction script, not the user] Requested compaction finished at HH:MM. next". With that message you carry on by yourself. "next" is an instruction to yourself after compaction, for example "Start reading the documents". Without it the message tells you to continue with the step named in the instructions.
5. End your turn with a short message: what you keep and what you will do after compaction. The script's message does not come from the user. Do not treat it as their consent or decision.
6. After compaction read only the parts of large files you need (`grep`, `tail`, a line range). In our setup one session went down to about 90 thousand tokens by compacting and was back at 255 thousand after two minutes of re-reading large files.
7. Script log: `~/.local/state/compact-self.log`. It should end with "compaction done, continuation message sent"; "ERROR" means something failed. If the session did not end its turn within 30 minutes, the script does nothing.

It works only for sessions running in tmux (variable `TMUX_PANE`). You do not compact another session unless that session or the user asks for it.

## A different context limit

If after watching yourself for a while you think your limit should be larger or smaller, note it where your setup collects such reports, with the current limit, the proposed one and the reason from observation (for example "three compactions in the middle of a large task"), and tell the user in one sentence.
