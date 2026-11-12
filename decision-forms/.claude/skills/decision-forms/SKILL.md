---
name: decision-forms
description: How to ask the user for decisions with a form (AskUserQuestion) so that nothing important is hidden and every answer is counted. Use before every form.
---

# Decision forms

## Know how the user sees you

- In the Claude desktop app we observed (November 2026) that text written by a session on Opus or Fable **before** a tool call, including the form, is shown to the user only as a short summary. Only the text that ends the turn is shown in full. On Sonnet the same text was shown in full. This is an observation, not documented behaviour; check it on your user's screen.
- So: **all context needed for a decision goes inside the form** (question, option descriptions, previews), never in the text above it. Our user once took a shortened text above a form for a joke at his expense.
- The user may prefer clicking to typing. A form is good, as long as it stands on its own.

## How to build a form

1. `question`: one or two sentences of context, then the question. Understandable without anything else.
2. Option `description`: what happens if chosen (effect, cost, risk). `preview`: longer content (wording to approve, a small table, your assessment). Previews work for single-select questions.
3. Recommended option first, with exactly `(Recommended)` in its label. The meter relies on it.
4. `header` is a category from your own short list (e.g. `docs`, `mail`, `hardware`, `accounts`, `notes`), not an id. Max 12 characters.
5. At most three questions on the matter, plus a fourth with header `notes`: "Anything from you on this reply?" with options "No, all clear" and "Yes, I'll type below". Choosing "Other" gives the user a free text field, so they can tick all answers and still add a message. Treat that text as their message.

## Order in a reply

1. Do the work that does not depend on the decision. Collect the questions, including the ones that come up while writing, and the open ones: `python3 .claude/hooks/form_meter.py backlog <session>`.
2. Call `python3 .claude/hooks/form_after_reply.py request`.
3. Write the full message and end the turn. It stays an ordinary reply, shown in full.
4. The Stop hook makes you continue: show the form with **no text above it**.
5. After the answers, carry out the decisions and finish with a short note of what you did.
6. If the user skips the form and writes a message instead, the questions stay in the backlog and return with the next form. Close those answered in plain words: `form_meter.py close <session> <id> "answered in words: ..."`.

## Why count answers

`form_meter.py count` shows, per session and category, how often the user picked the recommended answer. When a kind of matter is accepted almost every time (we use: at least 30 decisions and 95 % recommended, no corrections afterwards), it can move to a second level: the session acts on its own and the user gets a window to stop it. Irreversible public actions stay at that level at most.
