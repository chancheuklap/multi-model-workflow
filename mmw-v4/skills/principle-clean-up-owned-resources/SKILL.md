---
name: principle-clean-up-owned-resources
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Clean Up Owned Resources

Cleanup ends the task's resources and removes disposable state while preserving the evidence the task must keep.

**Why:** A failed attempt can strand a process or port. Broad cleanup can instead stop someone else's work or erase the proof of this task.

**Pattern:**
- Track the handles and ownership of resources you start. Clean up failed attempts as well as successful ones, when their resources are no longer needed.
- Stop only resources this task owns or is authorized to manage, using their handles rather than a process name. Keep a shared resource while another task needs it; remove only this task's residue.
- Preserve required evidence at its named paths and check it survives teardown. Remove evidence only under the task's explicit retention policy.
- Report a resource cleanup could not release, with its identifier and the next recovery step. Retain a resource for handover only with its owner and reason recorded.

**Stop:** cleanup is complete when owned resources are released or accounted for by a recorded handover, and required evidence remains readable.
