---
name: principle-write-for-where-it-is-read
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Write for Where It Is Read

Everything you produce is read or run somewhere other than this conversation: by a person on a web page, by a model starting with an empty context, by a shell that shows one truncated line. Before you write it, name who will pick it up, what they are trying to do at that moment, and what they can and cannot see from there. Then write for that person, agent, or program.

**Why:** A thing that only makes sense from where you sit has not been built yet. The reader cannot ask you what you meant.

**The test:**
- Who picks it up: a person, an agent, or a program?
- What are they trying to do at that moment?
- What can they see from there, and what can they not see (this conversation, your working memory, the files you read)?
- Every term the reader may not know is explained in one plain sentence where it first appears, or links to a place they can open.
- Read the draft as that reader. Everything they need is in it or one named pointer away.

Text an agent reads follows the **writing-for-agents** skill; text people read follows the **technical-writing** skill. Distinct from **principle-anchor-every-reference**, which names each thing the text mentions.
