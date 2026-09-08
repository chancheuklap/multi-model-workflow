# Journey

Whether one end-to-end path still works against the real product is
`scripts/journey.py`, next to this skill's `SKILL.md`. It claims this worktree's lease,
runs `.mmw/target.json`'s `start`, runs `discover`, puts every printed address into the
environment under its uppercase key alongside the lease variables, runs the script, and
runs `stop` whether the script succeeded or not. Then it runs the script once more, with
the product stopped, as the negative control.

A journey is the only judge in this skill that starts the whole product. There are few
of them on purpose: the owner names which paths are worth one, and the default three are
money, the login gate, and one submit chain.

Two agents come here. The one **writing** the criterion needs the next two sections. The
one **reading** a line it printed needs the last.

## What the script gets, and what it must be

`<journeys>/<name>` is a directory with an executable `run`, or a `package.json`
declaring `scripts.run`; `journeys` in `.mmw/target.json` says where they live, default
`.mmw/journeys`. The script runs with that directory as its working directory, and with:

- **every key `discover` printed**, uppercased — `origin` arrives as `ORIGIN`. Read the
  address from there. A script that hardcodes one is a script that breaks on the next
  worktree, because ports come from the lease.
- **the lease variables** — `MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`,
  `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`.
- **`MMW_JOURNEY_NEGATIVE`**, set to `1` on the control pass and unset on the real one.

Playwright's own API is what a journey drives the product with; there is no driver
between the script and the page. Exit 0 for a pass, non-zero for a failure, and put what
went wrong on the last line of the output — that line is what the judge prints.

**Assert something only the running product can satisfy.** That is not style advice: it
is the condition the control pass measures, and the section after next says what happens
when it does not hold.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between. The script
is named bare: `verify-ticket.py` puts this skill's `scripts/` on the `PATH` of the shell
that runs the line (its `--tools`).

```
CHECK: journey.py run <name>
EXPECT: JOURNEY OK <name>
```

Journeys appear on the contract ticket and on the tickets the owner named, and nowhere
else. `verify-ticket.py --lint` reports a `journey.py run <name>` with no directory under
`.mmw/journeys/`, unless the ticket's `## Owns` covers that directory — then this is the
ticket that builds it.

A journey starts and stops the whole stack twice over, so it is the slowest criterion on
a ticket. When it needs longer than the ten minutes every `CHECK:` gets, the ticket says
so on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`.

## The negative control

After `stop`, the script runs a second time in the same directory, with the same
environment except that every address `discover` printed has its port replaced by one
nothing on this machine listens on, and `MMW_JOURNEY_NEGATIVE=1` is set. **That pass has
to fail.**

Two independent things make it fail for a real journey: the product is down, and the
addresses point nowhere. A script that asserts nothing, or that never reaches the
product, passes it exactly the way it passed the first time — and that is the difference
this run exists to print. The question every gate is judged by is whether a run that did
nothing at all would be noticed
(`docs/adr/0008-silence-is-never-a-pass.md` in the multi-model-workflow repository).

`MMW_JOURNEY_NEGATIVE` is a courtesy, not the mechanism: a script may read it to fail
fast instead of waiting out its own timeouts, and the pass counts the same whether it
does or not. It is deliberately not `MMW_NEGATIVE`, which is the boundary check's
variable: that one makes the product test suite's shared interaction helper do nothing,
and a journey sharing code with those tests would answer it by doing nothing at all,
which is the one result this pass must not reward.

**What it does not catch:** a journey that really drives the product but asserts
something thin — the page title, an element that is present before anything happens.
That pass goes red with the product down, so the control is satisfied. Whether a journey
asserts the thing worth asserting is read by the `code-review` Tests axis and by whoever
named the journey.

## Reading what it printed

- **`0`**, `JOURNEY OK <name>`: the script passed against the running product and failed
  without it.
- **`1`**, `JOURNEY FAILED <name> at <last line>`: the script failed against the running
  product. The control pass was not run. What to fix is what that last line names —
  it is the script's own output, not this judge's words. A `<name>` with no executable
  `run` and no `package.json` `scripts.run` reads the same way, naming the directory it
  looked in.
- **`1`**, `JOURNEY GREEN WITHOUT PRODUCT <name> at <last line> — …`: the script passed
  both times. Nothing is known about the product from this run. Fix the script, not the
  product: make it assert something the product has to be up to satisfy.
- **`2`**: the run could not get as far as the script. `start`'s own refusal is passed
  through unchanged — read it and do what its last sentence says; `.mmw/target.json` with
  no `start`, a `discover` that printed no JSON object, and a `target.json` that is not
  one object each say so on stderr. `stop` runs before this returns.
