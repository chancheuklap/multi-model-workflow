# How a repository becomes an automatable acceptance runtime

The product answers live in `.mmw/` at the repository root. mmw supplies the lease,
`start` / `stop` protocol, journey runner, story judge, and harness guard. Fill
`.mmw/target.json` until this command exits 0:

```
python3 <scripts>/screen_driver.py target --check [--repo <dir>] [--kind <kind> | --contract <yaml>]
```

It prints every field as `ok`, `missing` (one sentence and one example) or `absent`
(optional). That screen is the whole list. The reasons a field is shaped as it is
are the seven questions below.

## The seven questions

1. **起栈 — `start`.** One command brings the whole stack up and returns only once
   the product is usable, not merely alive. It is run every time, and is idempotent
   in both directions: it leaves its own current product alone, clears its own stale
   leftovers first (by its own `stop`, on its own record of what it started), and
   refuses over anything else holding its ports, naming what it found. Everything
   the product needs — which backing service, which data directory, which log — is
   found or chosen inside this command, from the lease in its environment
   (`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`,
   `MMW_AUTOMATION`). It refuses to start with no lease and prints the command that
   supplies one: `lease.py run -- <the start command>`.

2. **收栈 — `stop`.** The only way a run ends a process. It ends only what this run
   recorded as its own, leaves a neighbour's product alone, exits 0 with nothing to
   end, and does not release the lease. It ends the containers of this run's stack
   as well as its processes.

3. **地址与身份 — `discover`.** Prints one JSON object: an origin-class address
   (where the product is served), `instance` (a readable name for this run), and
   `instance_check` (one observe line, true only when the product answering is the
   one this run started). Identity turns "answering" into "answering and mine".

4. **story 页面 — `stories`.** Brings up the story page service and prints its
   `origin`. Addresses look like `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`.
   The pages themselves live in `.mmw/stories/`.

5. **旅程目录 — `journeys`.** The directory of journey scripts, default
   `.mmw/journeys`. Each `<name>` is a directory with an executable `run`, or a
   `package.json` that declares `scripts.run`. `journey.py run <name>` claims the
   lease, runs `start`, runs `discover`, puts the addresses and lease variables
   into the environment, runs that script, and runs `stop` whether the script
   succeeded or not.

6. **离机动作 — `leaves_machine`.** Each thing this product does in a run that
   reaches past this machine — opening the system browser, calling a paid service,
   writing a machine-global location — and how the run records it under
   `MMW_AUTOMATION=1`. `[]` is an answer; a missing key is not.

7. **实例上限 — `instance` (optional).** A product whose ports cannot move says
   `{"max": <n>, "why": "…"}`; absent means the product takes its ports from the
   lease and the machine's own limit applies. `checks` (optional) is the
   verify-ticket skill's: its `--closeout` runs them.

## `.mmw/` directory

Product answers live here, not scattered through the repository:

- `target.json` — the seven questions
- `harness/` — start the stack, vendor stubs, account seeds, the few seeds a
  journey uses, the entry that records an off-machine action
- `journeys/` — one directory per named journey
- `stories/` — story pages and their adapter

Scripts a person runs on their own machine may stay where they are, provided they
call the same start code `harness/` uses.

`harness-guard.py <repository-root>` fails the repository when an acceptance name
(`MMW_` variable reads, `/api/dev/`, `transport off`, `__stub`) appears outside
`.mmw/`, `tests/`, `scripts/dev/`, or a file `leaves_machine` names.

## Three rules

- Automation uses placeholder keys, vendor stubs, and local accounts. Real keys
  exist only on a paid-smoke ticket labelled `ready-for-human`.
- `start` refuses when the environment holds a Gateway address that points
  elsewhere.
- Every action `leaves_machine` names records instead of leaving the machine
  when `MMW_AUTOMATION=1`.
