# How dispatch works

Dispatch connects tracker-owned work, runner-managed sessions and local coordination processes. Its vocabulary is defined in [Night](../contexts/night/CONTEXT.md), [Ticket run](../contexts/ticket-run/CONTEXT.md) and [Toolbox](../contexts/toolbox/CONTEXT.md); this note explains why those responsibilities are separate.

## Ticket evidence survives a session

A worker or reviewer can disappear without a final answer. The ticket's event history therefore identifies its started sessions and records their results independently of the runner. The fold is the ticket's state, reconstructed from those events; labels and the newest visible message are insufficient to reconstruct a hold or a landing.

The [dispatch command entry](../../mmw-v4/skills/dispatch/scripts/dispatch.sh) connects this evidence to branch and session operations. The [status reader](../../mmw-v4/skills/dispatch/scripts/status.py) derives execution plans from tracker evidence; it is not another store of ticket state.

## Runners own processes, not ticket outcomes

The selected runner manages host sessions through its [runner adapter](../../mmw-v4/skills/dispatch/scripts/runners/). A runner's liveness report answers whether a session exists or is working; it cannot establish that the ticket passed. Ticket acceptance and closeout belong to [verify-ticket](../../mmw-v4/skills/verify-ticket/SKILL.md).

This separation lets a ticket preserve its work across a replacement session without treating a stopped process as a completed implementation. The recorded runner/session identity also keeps recovery attached to the session that actually held the work.

## A result needs a recipient

The [relay](../../mmw-v4/skills/dispatch/scripts/relay.py) associates tracked work with the session waiting for it. Ticket result events and completed brief batches become wakes addressed to that recipient. The wake points to the result; its content is not a second copy of the answer.

Acknowledgment means the recipient has read the result. It is separate from successful implementation, so delivery recovery can preserve a pending wake without changing the ticket's outcome.

## Coordination health is separate from product proof

The [watchdog](../../mmw-v4/skills/dispatch/scripts/watchdog.py) checks relay health and watched sessions. The [turn guard](../../mmw-v4/skills/dispatch/scripts/turn-guard.py) maintains watchdog health while watches are open. Their observations identify missing coordination or stopped work; they do not substitute for criterion evidence or owner acceptance.

One ticket and Run a night compose these capabilities for different implementation scopes. Their current task order, recovery actions and delivery authority remain in those Playbooks; command options, thresholds and exit codes remain with the scripts that implement them.
