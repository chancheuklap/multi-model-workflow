# How a repository becomes an automatable acceptance runtime

The product answers live in `.mmw/` at the repository root. mmw supplies the lease,
`start` / `stop` protocol, journey runner, and harness guard. Fill `.mmw/target.json`
until this command exits 0:

```
python3 <scripts>/screen_driver.py target --check [--repo <dir>] [--kind <kind> | --contract <yaml>]
```

It prints every field as `ok`, `missing` (one sentence and one example) or `absent`
(optional), then the three rules below. That screen is the whole list. The reasons a
field is shaped as it is are the fields below.

## What the repository answers

Which of these a repository must answer is what `target --check` prints, field by
field. This section says why each one is shaped the way it is.

- **`start`.** One command brings the whole stack up and returns only once the
  product is usable, not merely alive. It is run every time, and is idempotent in
  both directions: it leaves its own current product alone, clears its own stale
  leftovers first (by its own `stop`, on its own record of what it started), and
  refuses over anything else holding its ports, naming what it found. Everything
  the product needs — which backing service, which data directory, which log — is
  found or chosen inside this command, from the lease in its environment
  (`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`,
  `MMW_AUTOMATION`). It refuses to start with no lease and prints the command that
  supplies one: `python3 <scripts>/lease.py run -- <the start command>`.

- **`stop`.** The only way a run ends a process. It ends only what this run
  recorded as its own, leaves a neighbour's product alone, exits 0 with nothing to
  end, and does not release the lease. It ends the containers of this run's stack
  as well as its processes. When it returns, nothing listens on any port of this
  run's lease — that is what "stopped" means here, and it is checked: `release`
  refuses a slot something still answers on, whatever address or family it is
  bound to, and `journey.py` says so rather than printing `JOURNEY OK`.

- **`discover`.** Prints one JSON object: an origin-class address (where the
  product is served), `instance` (a readable name for this run), and
  `instance_check` (one observe line, true only when the product answering is the
  one this run started). Identity turns "answering" into "answering and mine".

- **`stories`.** Brings up the story page service and prints its `origin`.
  Addresses look like `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. The
  pages themselves live in `.mmw/stories/`. It takes **no lease**: a story page
  renders presentational components from scene data, with no backend, no seed and
  no route behind it, so the one thing it needs is a port, and it asks the machine
  for a free one (bind port `0`, then print the port that came back) rather than
  deriving one from `MMW_PORT_BASE`. Its environment carries `MMW_AUTOMATION=1`
  and nothing else of the lease.

- **`journeys`.** The directory of journey scripts, default `.mmw/journeys`. Each
  `<name>` is a directory with an executable `run`, or a `package.json` that
  declares `scripts.run`. `python3 <scripts>/journey.py run <name>` claims the
  lease, runs `start`, runs `discover`, puts each discover key into the
  environment under its uppercase spelling (so `origin` arrives as `ORIGIN`)
  together with the lease variables, runs that script, and runs `stop`
  whether the script succeeded or not. Then it runs the script once more, with the
  product down and the addresses moved, as its negative control: what a journey script
  has to assert for that to work, and what each line it prints means, are
  [journey.md](journey.md).

- **`leaves_machine`.** Each thing this product does in a run that reaches past
  this machine — opening the system browser, calling a paid service, writing a
  machine-global location — naming the file that records it under
  `MMW_AUTOMATION=1`. `[]` is an answer; a missing key is not.

- **`instance`.** A product whose ports cannot move says
  `{"max": <n>, "why": "…"}`; absent means the product takes its ports from the
  lease. `lease.py` enforces two limits when a slot is claimed: the machine's slots,
  and `instance.max`, when present, counting every slot this repository already holds
  wherever its checkout is — the ticket worktrees and the main checkout re-running the night's
  criteria alike. A ticket takes its slot at the first run of its criteria that runs
  the product and keeps it until its work ends — landed, handed back, bounced, released,
  suspended or retracted — so `max` bounds how many tickets are past that point at
  once; how many workers write code at once is not bounded by it, and neither is how
  many story criteria run at once, since those start no product. A criterion or judge
  run outside a ticket worktree gives back the slot **it claimed** as that run ends,
  and leaves alone one the worktree already held: that slot is somebody's — a product
  started under `lease.py run`, a journey going in the same checkout — and ending it is
  ending a process this run never started. `MMW_DATA_DIR` remains
  while its ticket worktree remains and is removed after that worktree is archived.
  A worker's run that finds `max` reached takes no slot and exits at once; a
  `--reverify` waits inside the command. Either way its ticket says so.

- **`checks`.** The repository's own checks. The `verify-ticket` skill's
  `--closeout` runs them.

## `.mmw/` directory

Product answers live here, not scattered through the repository:

- `target.json` — the fields above
- `harness/` — start the stack, vendor stubs, account seeds, the few seeds a
  journey uses, the entry that records an action that would leave the machine
- `journeys/` — one directory per named journey
- `stories/` — story pages and their adapter

Scripts a person runs on their own machine may stay where they are, provided they
call the same start code `harness/` uses.

Reads of `MMW_` variables, `/api/dev/`, `transport off` and `__stub` belong in
`.mmw/`, `tests/`, `scripts/dev/`, and the files `leaves_machine` names; anywhere
else is a leak. The command that judges that, and the criterion that carries it,
are [harness-guard.md](harness-guard.md).

## Three rules

`target --check` prints these. It can see that `leaves_machine` is answered; it
cannot see a Gateway address in the environment or whether a key is a
placeholder. Those two are `start`'s job.

- Automation uses placeholder keys, vendor stubs, and local accounts. Real keys
  exist only on a paid-smoke ticket labelled `ready-for-human`.
- `start` refuses when the environment holds a Gateway address that points
  elsewhere.
- Every action `leaves_machine` names records instead of leaving the machine
  when `MMW_AUTOMATION=1`.
