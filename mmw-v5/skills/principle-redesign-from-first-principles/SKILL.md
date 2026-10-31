---
name: principle-redesign-from-first-principles
description: Use when integrating a new requirement into an existing design or when repeated workarounds reveal a poor fit. Reconsider the structure as if the requirement had been known from the start.
---

# Redesign From First Principles

When integrating a change, don't bolt it onto the existing design. Redesign as if the requirement had been a foundational assumption from the start.

- Read all affected files and understand the current design
- Ask: "if we were writing this from scratch with this new requirement, what would we build?"
- Propagate the change through every reference: types, docs, examples, rationale sections
- Think about the whole redesign, then deliver it incrementally

This is the method for preserving option value when integrating changes into an existing design.

**In a diff:**

- A change patched onto the design rather than read as if the design always held it: ask whether the code would look like this had the requirement been known from the start, and write that form. One that reaches beyond the ticket's files is a finding outside the ticket.
