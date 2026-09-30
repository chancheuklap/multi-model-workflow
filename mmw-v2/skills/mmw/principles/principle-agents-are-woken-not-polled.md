---
name: principle-agents-are-woken-not-polled
description: "Apply when you have started another agent, or are waiting on one. End your turn and let its event wake you; never poll another agent or hold your turn open to wait."
---

# Agents are woken, not polled

An agent that has started another agent ends its turn. It does not wait, does not poll, and does not hold its turn open, because being woken is guaranteed. No agent polls another.

**Why:** The wake already arrives when the other agent is done, so a polling loop buys nothing. Moving the poll to another agent only moves its cost.

**Boundaries:** A tool call that blocks inside your host does not count: it is one read, not a loop.
