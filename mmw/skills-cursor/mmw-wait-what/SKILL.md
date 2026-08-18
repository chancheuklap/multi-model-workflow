---
name: mmw-wait-what
description: Stop. That last message did not land — re-pitch it, or draw it. Use when the user says they did not follow, asks for it in simpler words, or asks to see it drawn.
---

Wait — I don't understand where you've got to here. Re-pitch that: give me a little bit of context, talk in ASD-STE100 Simplified Technical English, and use the ubiquitous language from the domain docs.

`mmw domain path` prints those docs. Use those terms. No domain docs: use the field's standard terms.

Unless the user names something else, re-pitch the last message. If they name a document, re-pitch that. Session output and repo documents are both in scope.

Re-pitch only what they named. Do not start a new direction. Expand abbreviations and identifiers the reader is missing.

| They need | Do |
| --- | --- |
| Simpler words | Add the context the last pitch skipped, then re-pitch in short sentences. Show it. Wait. |
| Drawn | Read [HTML.md](HTML.md). Write 解释 HTML. |
| To click through a state model, data shape, or business logic | Invoke `/mmw-prototype`. Pass what they did not get, the path of any existing state model or script, and the question. It uses the Logic HTML branch. |
