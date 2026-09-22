# Journey

Whether one end-to-end path still works against the real product is
`<scripts>/journey.py`; `<scripts>` is the notation this skill's `SKILL.md` defines under
**Resolve `<scripts>` once**. It claims this worktree's lease,
runs `.mmw/target.json`'s `start`, runs `discover`, puts every printed address into the
environment under its uppercase key alongside the lease variables, runs the script, and
runs `stop` whether the script succeeded or not. With `--break`, it starts the product a
second time with one interface broken and requires the same script to fail. Without
`--break`, the contract ticket's smoke journey keeps the product stopped and repoints
every discovered address to a closed port before the same script runs again.

A journey is the only judge in this skill that starts the whole product. There are few
of them on purpose: the owner names which paths are worth one, and the default three are
money, sign-in, and one submit chain.

Two agents come here. The one **writing** the criterion needs the next two sections. The
one **reading** a line it printed needs the last.

## What the script gets, and what it must be

`<journeys>/<name>` is a directory with an executable `run`, or a `package.json`
declaring `scripts.run`; `journeys` in `.mmw/target.json` says where they live, default
`.mmw/journeys`. The script runs with that directory as its working directory, and with:

- **every key `discover` printed**, uppercased — `origin` arrives as `ORIGIN`. Read the
  address from there; ports come from the lease.
- **the lease variables** — `MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`,
  `MMW_PORT_COUNT`, `MMW_DATA_DIR`, `MMW_AUTOMATION`.

The script never receives `MMW_BREAK` or another signal saying which pass is running.
Playwright's own API is what drives the product; there is no driver between the script
and the page. Exit 0 for a pass, non-zero for a failure, and put what went wrong on the
last line of the output — that line is what the judge prints.

**End by reading the result back from another page.** A journey that clicks Submit and
accepts a success message or redirect has proved only that the click handler ran. Go to
the page that owns the saved result and assert the value there, so breaking the write or
read interface makes the second pass fail for the reason the user path would fail.

**A journey script starts nothing itself.** For a desktop application, `start` launches
the application and opens its debugging port, `discover` prints that address, and the
journey connects to it with Playwright.

## The criterion, in one shape

Written onto the ticket, run by a shell months later with no model between. The script
is named bare: `verify-ticket.py` puts `<scripts>` on the `PATH` of the shell that runs
the line (its `--tools`).

```
CHECK: journey.py run <name> --break "POST /items/{id}"
EXPECT: JOURNEY OK <name>
```

The value is one uppercase method, one space, and a route beginning with `/`. The route
is the product's own route pattern and may carry placeholders such as `{id}`. The
product's break switch matches that method and route, fails only that interface, and
affects only the product process. On the second start, and only then, `journey.py` puts
the exact value in `MMW_BREAK` for `start`. When the switch is active, `start` prints the
exact line `BREAK ARMED <METHOD> <route>`. A non-zero second `start`, or a successful one
without that line, is a refusal: the script does not run and the message points back to
this reference.

The contract ticket's smoke journey omits `--break`. Its purpose is to prove that the
whole product starts, answers through the discovered address, and stops; taking the
whole product down is the appropriate control for that one criterion. Acceptance and
owner-named journeys use `--break` so the control isolates the interface whose result
the journey must observe.

Journeys appear on the contract ticket, on the tickets the owner named, and on each
acceptance ticket, and nowhere else. `verify-ticket.py --lint` reports a
`journey.py run <name>` with no directory under `.mmw/journeys/`, unless the
`## Owns` covers that directory — then this is the ticket that builds it.

A break journey starts and stops the whole stack twice, so it is the slowest criterion
on a ticket. When it needs longer than the ten minutes every `CHECK:` gets, the ticket
says so on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`.

## The negative control

With `--break`, the first pass is the ordinary journey: `start`, `discover`, script,
`stop`. The second pass calls `start` again with `MMW_BREAK` only in that command's
environment, requires its `BREAK ARMED` line, runs `discover` again without the variable,
and runs the same script in the same environment as the first pass. **That pass has to
fail.** If it stays green, the judge prints `JOURNEY GREEN WITH BREAK`: the journey did
not prove that the interface named by its criterion matters to the result it asserted.

Without `--break`, the contract ticket's smoke journey runs its control after `stop`,
with the same environment except that every address `discover` printed has its port
replaced by one nothing on this machine listens on. It receives no signal saying this is
the second pass. A script that asserts nothing passes again and becomes `JOURNEY GREEN
WITHOUT PRODUCT`; a script that reaches the product goes red.

After either control, `stop` runs again and this run's lease ports must all be quiet.
Whatever still answers is named with its port and pid on a
`JOURNEY LEFT THE PRODUCT UP` line. A helper that starts the stack when it finds nothing
answering violates the journey contract: it brings the whole stack back during the
control and leaves the next run blocked.

## Exit codes

- **`0`**, `JOURNEY OK <name>`: the script passed against the normal product and failed
  when the named interface was broken, or for the contract smoke journey without the
  product.
- **`1`**, `JOURNEY FAILED <name> at <last line>`: the first script run failed. The
  control was not run. What to fix is what that last line names — the script's own
  output, not this judge's words. A `<name>` with no executable `run` and no
  `package.json` `scripts.run` reads the same way, naming the directory it looked in.
- **`1`**, `JOURNEY GREEN WITH BREAK <name> — <last line>`: the script passed normally
  and passed again with the interface from `--break` failing. Make the journey read the
  result back through a different page and assert it there.
- **`1`**, `JOURNEY GREEN WITHOUT PRODUCT <name> at <last line> — …`: the contract smoke
  journey passed both normally and with the product stopped and addresses repointed.
  Make the script assert something only the running product can satisfy.
- **`1`**, `JOURNEY LEFT THE PRODUCT UP <name> — …`: the passes produced their expected
  verdict, but something still listened on this run's lease ports after the last
  `stop`; the line names every port, pid, and process directory.
- **`2`**: the run could not safely reach the script. This includes an invalid `--break`
  value; every instance slot already claimed; an unreadable or incomplete
  `.mmw/target.json`; a failed `start` or `discover`; and a break switch whose second
  `start` failed or did not print its exact `BREAK ARMED` line. The refusal names the
  failed fact and the one next action.
