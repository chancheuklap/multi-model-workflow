# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual labels used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                             |
| -------------------------- | -------------------- | --------------------------------------------------- |
| `needs-triage`             | `needs-triage`       | The user needs to evaluate this issue               |
| `needs-info`               | `needs-info`         | Waiting on the user for more information            |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent             |
| `ready-for-human`          | `ready-for-human`    | One thing only a person can do, of kind `reaction` or `reach` |
| `wontfix`                  | `wontfix`            | Will not be done                                    |

When a skill mentions a role (e.g. "apply the ready-for-agent triage label"), use the corresponding label from this table.

## What carries a label here

Each label says which queue a ticket is in, and only that.

- `ready-for-agent` means the ticket is in the agent queue, waiting to be dispatched or being worked right now. Whether anyone is on it is the assignee's job to say. It comes off when the ticket closes and when the ticket leaves the agent queue.
- `ready-for-human` means the ticket is one thing only a person can do, of kind `reaction` or `reach`: it sits in the user's queue, and the ticket names which kind, what to look at and what makes it right.
- `needs-triage` means nobody has judged it yet: something arriving from outside, a ticket an agent could not finish, or a closed ticket reopened after the night because a criterion failed when re-run on the base branch. It is the one queue a skill picks up on its own — the triage skill reads it, reproduces what it can, and recommends one of the four outcomes: `needs-info`, `ready-for-agent`, `ready-for-human`, or `wontfix`.
- A spec carries no label. It is a container for the tickets underneath it, not a piece of work.

The category roles `bug` and `enhancement` belong to work arriving from outside. Tickets this repo plans for itself — a spec's tickets, a decision ticket under a `wayfinder:map` — carry a state role and no category.

Edit the right-hand column to match whatever vocabulary you actually use.
