# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

## What carries a label here

Each label says which queue a ticket is in, and only that.

- `ready-for-agent` means the ticket is in the agent queue, waiting to be dispatched or being worked right now. Whether anyone is on it is the assignee's job to say. It comes off when the ticket closes and when the ticket leaves the agent queue.
- `ready-for-human` means the ticket is in your queue, and the ticket says in one line why it cannot be delegated.
- `needs-triage` means nobody has judged it yet: something arriving from outside, or a ticket an agent could not finish. It is the one queue a skill picks up on its own — `/triage` reads it, reproduces what it can, and recommends one of the four outcomes.
- A spec carries no label. It is a container for the tickets underneath it, not a piece of work.

The category roles `bug` and `enhancement` belong to work arriving from outside. Tickets this repo plans for itself — a spec's tickets, a wayfinder decision ticket — carry a state role and no category.

Edit the right-hand column to match whatever vocabulary you actually use.
