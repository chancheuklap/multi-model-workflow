---
name: principle-read-before-you-conclude
description: Use before making a claim about a file or changing it. Read the source that establishes the affected behavior and identify material inferences.
---

# Read Before You Conclude

Read enough of a file to be sure of what you say about it, and read it before you change it.

**Pattern:**
- Decide from the file's size and what you need from it how much to read.
- For a local edit, read the affected passage and its relevant callers. For a change to authorization, role transitions or a shared invariant, trace the complete path that relies on it, including the instructions that hand work off or resume it. Read a file in full when its contract spans the file.
- A file you consult for one fact, or a generated, vendored, or log file, is read as far as the question needs.
- When your conclusion depends on a part you did not read, say so in the reply. A conclusion drawn from an unread part is inferred, not verified, and is labelled `inferred` in the same sentence.

Distinct from "principle-prove-it-works", which checks an output against the real thing. This governs what you read before you speak about a file. Where the step you follow sends a **FRESH AGENT** to read a large file whole and report, use **principle-guard-the-context-window**. The rule still binds whoever states the conclusion.
