---
name: mmw-mode
description: "How work runs in a repository that uses MMW: routes a task to its playbook, indexes the principles, says what an unattended session may decide and how a woken session picks up. Use in a repository that has a `.mmw/` directory, when a prompt names the mmw-mode skill, or when a message carries an `mmw <playbook>#<step>` pointer."
---

# MMW mode

## Non-negotiables

<!-- Situations that always route to one named skill, script or principle, whichever playbook is running: one line each, "situation → what to use". -->

## Principles

<!-- The index of `principles/`: one entry per principle file, its name and when it applies, grouped under bold group titles. -->

## Autonomy

<!-- Precedence when rules conflict; what a session decides with the user present; what an unattended session decides; where each role records a decision taken with nobody to ask. -->

## Re-entry

<!-- How a session that was woken, compacted or resumed finds the step it is at, before it does anything else. -->

## Subagents

<!-- When to start a subagent, what its brief carries, and who owns its output. -->

## Writing the reply

<!-- How every reply to the user is written; each playbook's **Reply:** line adds only what is unique to it. -->

## Playbooks

<!-- The route table: one line per playbook in `playbooks/`, saying which task it takes and how it differs from its neighbour, then one line per task that goes straight to a capability skill. -->
