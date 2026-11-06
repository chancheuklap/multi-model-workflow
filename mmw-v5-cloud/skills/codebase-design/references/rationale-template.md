# Rationale template

The prose that ships alongside the type sketch. Sentence-case headings, no boilerplate. Replace the italic notes with actual content.

## Problem

*What we're trying to do, and what about the existing system or constraints makes the shape non-obvious. If [Phase A](../SKILL.md#phase-a-ground-the-problem) surfaced constraints the design must honor (existing types to interop with, callers we can't break, invariants that crossed our boundary), name them here so the reader sees the same constraints you saw.*

## Usage (caller's view)

*Write this first, before the type sketch. Show the README or quickstart the consumer reads, plus two or three realistic call sites in their own code. What they import, what they call, what comes back. The type sketch in [Shape](#shape) is derived from this. The two must agree. When they diverge, reconcile the sketch to the usage, not the reverse. The caller's experience is the spec. The types serve it.*

## Shape

*The recommended architecture. Data structures first. Then how data flows through the signatures. Name the load-bearing decisions. State which invariants are encoded in types, where validation lives, and what the system deliberately does not do. Judge interface depth explicitly. State what complexity the public surface hides, what remains exposed to callers, and why the interface is no larger than needed. Cite the principle behind each decision (e.g. use **principle-boundary-discipline**). Don't restate it.*

## Synthesis decision

*Record the constraint that determines the shape, or the trade-off that decided between viable candidates.*

## Tradeoffs accepted

*Describe each tradeoff the chosen shape makes. Form: "we accept X in exchange for Y." Name anything a future reader might mistake for an oversight, including things that look like premature optimization or premature simplification.*

## Alternatives considered

*Include this section when there were viable alternatives. Explain the consequences each had for callers and why the chosen shape won.*

## Open questions and risks

*Things you noticed during the sketch that the human needs to weigh in on, and risks worth flagging before implementation starts. Phrase as questions, not assertions, so the human's answer is the resolution rather than a comment.*

## Next implementation step

*The first thing to build against the sketch. What you'd start writing immediately after synthesis.*
