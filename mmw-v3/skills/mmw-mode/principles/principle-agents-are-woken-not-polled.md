# Agents are woken, not polled

An agent that has started another agent ends its turn. It does not wait, does not poll, and does not hold its turn open, because being woken is guaranteed. No agent polls another.

**Why:** The wake already arrives when the other agent is done, so a polling loop buys nothing. Moving the poll to another agent only moves its cost.

**Boundaries:** A tool call that blocks inside your host does not count: it is one read, not a loop. A research session, which `dispatch.sh research <n>` starts, writes no event on its ticket, so nothing wakes you when it ends: end your turn without waiting, and read what it left on the tracker when you next pick up the work.
