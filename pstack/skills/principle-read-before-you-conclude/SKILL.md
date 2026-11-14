---
name: principle-read-before-you-conclude
description: "Apply before you change a file or say how it works. Read the relevant source and callers, including handoffs when a rule spans agents. Distinguish what you observed from what you inferred."
---

# Read Before You Conclude

Read enough of a file to be sure of what you say about it, and read it before you change it.

**Pattern:**
- Decide from the file's size and what you need from it how much to read.
- For a local edit, read the affected passage and its relevant callers. For a change to authorization, role transitions or a shared invariant, trace the complete path that relies on it, including the instructions that hand work off or resume it. Read a file in full when its contract spans the file.
- A file you consult for one fact, or a generated, vendored, or log file, is read as far as the question needs.
- When a conclusion depends on a part you did not read, say what you observed and what you inferred. Leave the question open if you have no evidence.

Distinct from [principle-prove-it-works](../principle-prove-it-works/SKILL.md), which checks an output against the real thing. This governs what you read before you speak about a file. For a bulk read, use [principle-guard-the-context-window](../principle-guard-the-context-window/SKILL.md). The rule still binds whoever states the conclusion.
