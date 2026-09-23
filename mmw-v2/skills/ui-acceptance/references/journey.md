# Journey

Whether one end-to-end path still works against the real product is
`<scripts>/journey.py`.

A journey is the only judge in this skill that starts the whole product. There are few
of them on purpose: the user names which paths are worth one, and the default three are
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

Written onto the ticket, run by a shell months later with no model between.

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
user-named journeys use `--break` so the control isolates the interface whose result
the journey must observe.

A break journey starts and stops the whole stack twice, so it is the slowest criterion
on a ticket. When it needs longer than the ten minutes every `CHECK:` gets, the ticket
says so on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`.

## The negative control

With `--break`, the second pass starts the product again with the named interface
failing and runs the same script with nothing telling it which pass it is; **that pass
has to fail**, or the journey did not prove the interface matters to the result it
asserted. Without `--break`, the smoke journey's second pass runs with the product
stopped and every discovered address pointing at a closed port.

After either control, `stop` runs again and this run's lease ports must all be quiet.
Whatever still answers is named with its port and pid on a
`JOURNEY LEFT THE PRODUCT UP` line. A helper that starts the stack when it finds nothing
answering defeats the negative control: it brings the whole stack back during the
control and leaves the next run blocked.

## Exit codes

- **`0`**, `JOURNEY OK <name>`: the script passed against the normal product and failed
  when the named interface was broken, or for the contract smoke journey without the
  product.
- **`1`**, `JOURNEY FAILED <name> at <last line>`: the first script run failed. The
  control was not run. What to fix is what that last line names — the script's own
  output, not this judge's words. A `<name>` with no executable `run` and no
  `package.json` `scripts.run` reads the same way, naming the directory it looked in.
- **`1`**, `JOURNEY GREEN WITH BREAK`, `JOURNEY GREEN WITHOUT PRODUCT` or
  `JOURNEY LEFT THE PRODUCT UP`: the line says what to change.
- **`2`**: a refusal naming the failed fact and the next action.
