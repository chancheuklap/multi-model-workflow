---
name: refactoring
description: A behavior-preserving change to structure or shape (rename, extract, inline, dedupe, move).
---

# Refactoring

**You own the contract. The structure changes. The behavior does not.** Distinct from a ticket that adds behavior, and from diagnosing-bugs, which corrects it.

If the cleanup reveals a missing feature or a real bug, record it for the Coordinator and ship the structural change first against the pinned contract. A redesign is allowed, but name it; the Coordinator sends that work on its own ticket. Large or cross-cutting structural work is sequenced by the Coordinator with wayfinder, then to-tickets, before this skill runs. This skill is the focused-to-medium change already on the ticket. When this ticket is that larger change, return it to the Coordinator.

## 1. Pin the behavior

Read the contract from the glossary and the ticket. Use **how** for the affected subsystem. Use **write-tests** to pin it with a characterization test, snapshot, or equivalence harness before any structure moves. If the area has no coverage, write the pin before touching structure. Type check and lint are not a pin.

## 2. Name the missing structure

Use **principle-model-the-domain**. Boring code stays when the shape is already clear and local. The reshape must delete branches or invalid states, not add indirection.

## 3. Name the target shape

State what the module layout, types, and call graph should be if built today. Use **principle-redesign-from-first-principles**. If the target crosses a function boundary, use **codebase-design** for Phase A, Phase B, and Phase C before the move.

## 4. Subtract before you add

Use **principle-subtract-before-you-add**. Delete dead code, collapse one-caller wrappers, drop redundant validators, and remove orphan references before introducing the new shape. The smallest change that reaches the target shape ships. A speculative cleanup that "might help" gets reverted.

## 5. Move in small steps

Move in small behavior-preserving steps, each keeping the pin green. For API reshapes, use **principle-outcome-oriented-execution**: migrate every caller and delete the old API in the same wave. No compatibility shims, no parallel old-and-new paths. Make the mechanical edits on this ticket's branch, with the file paths, the names being moved, and the behavior to hold kept explicit. Spot-check every rename against the actual files. Renames silently miss usages in strings, prose, and back-references.

## 6. Prove the behavior is unchanged

Use **principle-prove-it-works**. Prove behavior is unchanged on the real artifact, not "it compiles". For larger reshapes, run an equivalence check: a script that diffs old-vs-new outputs, a recorded baseline replayed against the new code, or a smoke run on the surface the ticket names.

## 7. Keep only a lighter read

Use **principle-minimize-reader-load**. The success measure is reduced reader load. If the diff does not lower reader load somewhere, revert it.

## 8. Shape the commits

Rebase into small ordered commits. A subtraction commit, then the reshape, then any follow-on cleanup. Use **principle-sequence-verifiable-units**, so each behavior-preserving slice stays green before the next.

The PR record carries the structure that changed, the pin you held it against, the equivalence proof, the reader-load delta, what shipped and what got reverted. No new behavior.

Done when the pin is green, the proof has run, and the commits are in that order.
