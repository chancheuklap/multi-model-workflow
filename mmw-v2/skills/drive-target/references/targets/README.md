# Targets — what a product answers before the two judges can drive it

Interface parity and the wiring check are two judgements over one drive. The drive is
`scripts/screen_driver.py`; what differs between products is not the judgement but how
the product is reached, put into a state, addressed, released, and read. Two parties
answer that, and this file keeps them apart:

- **The adapter** answers for a *kind* of product — `electron`, `web-spa`,
  `web-server-rendered`, `chrome-extension` — in code, as a class in the driver, with a
  file here as its account: [electron.md](electron.md), [web.md](web.md),
  [chrome-extension.md](chrome-extension.md). The screen contract names the kind
  (`target.kind`); the driver picks the adapter by it.
- **The repository** answers for *this product on this machine* in `.mmw/target.json`
  at its root: the commands only it knows.

## What the repository answers: `.mmw/target.json`

The fields are declared once, in the driver, and the driver prints them:

```
python3 <scripts>/screen_driver.py target --check [--repo <dir>] [--kind <kind> | --contract <yaml>]
```

It prints the adapter's own account for the kind, then every field as `ok`, `missing`
(with one sentence and one example) or `absent` (optional); exit 0 once the file is
complete. That screen is the whole list, so it is not repeated here. What the command
cannot fit in a sentence — the reasons a field is shaped as it is — is below.

- **`start` is run every time, and is idempotent in both directions.** The driver runs
  it before the first scene whether or not something answers, because only `start`
  knows whether the product answering is the one this worktree's code builds; a product
  left over from before a merge answers just as well. So it leaves its own current
  product alone, clears its own stale leftovers first (by its own `stop`, on its own
  record of what it started), and refuses over anything else holding its ports, naming
  what it found. That refusal cannot be lifted into the driver: **whose a port is
  cannot be read off the port** — on a machine where a multiplexer or a container
  runtime publishes every stack's ports, a rule written from the holder's working
  directory would refuse a run its own addresses or end the networking of every stack.
  Everything the product needs — which backing service, which data directory, which
  log — is found or chosen *inside* this command, from the lease in its environment
  (`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`,
  `MMW_AUTOMATION`), never typed into a session, and it refuses to start with no lease.
  `start` returns only once the product is *usable*, not merely alive: a product whose
  own dependencies are missing answers a health check and then disables every control,
  so `start` reads the surface that says so and fails on it, quoting what was missing.
- **`stop` is the only way a run ends a process.** `hook.py pretool` refuses `kill`,
  `pkill`, `killall` and `xargs kill` and sends the reader to it; it ends only what this
  run recorded as its own, leaves a neighbour's product alone, exits 0 with nothing to
  end, and does not release the lease — the driver does.
- **`discover` prints addresses per kind, plus identity.** The kind's keys are in the
  adapter's account. `instance` (a readable name for this run) and `instance_check`
  (one `observe` line in this kind's read surface, true only when the product answering
  is the one this run started) turn `ready` from *answering* into *answering and
  mine* — the check is asked again between scenes, because an application replaced
  mid-run is what a start-up gate cannot see.
- **`reach` establishes a state; it never merely finds one.** It runs once per scene
  and once per row with the mechanism names appended, prints `KEY=VALUE` lines that fill
  every `{placeholder}`, and may skip only what it established itself in this run. A
  sign-in step that returns early whenever it finds the application signed in reports
  success over a sign-in that no longer works. Idempotent means running it twice gives
  the same result, not that what is already there can be trusted.
- **`transport_off` breaks persistence of the observed rows, not the session.** The
  wiring check's `--negative` runs every row with it and requires each to fail on an
  `observe` assertion. If `attach` itself needs what was broken (a session lookup),
  nothing is evaluated and the run proves nothing (exit 2).
- **`leaves_machine` is the ninth answer.** Opening the system browser, calling a paid
  service, writing a machine-global location: each is named with how the run
  neutralises it under `MMW_AUTOMATION=1`. Recording what would have been done, in the
  run's own `MMW_DATA_DIR`, is usually both the neutral act and the stronger assertion —
  a criterion that reads back the URL a button would have opened says more than one that
  reads that the application entered a waiting state. `[]` is an answer; a missing key
  is not, because a run that reached a live service looks exactly like one that did not.
- **`instance` is the eighth answer, and optional.** A product whose ports cannot move
  says `{"max": <n>, "why": "…"}`, and `dispatch.sh advance` serialises its tickets;
  absent means the product takes its ports from the lease and the machine's own limit
  applies. A repository reads the lease variables **at the moment it starts a process,
  never into the session or the test environment**: a suite that asserts its product's
  registered port number is right to, and a derived port leaking into it turns a
  correct suite red.
- **`checks`** is the verify-ticket skill's: its `--closeout` runs them, and its
  `references/closeout.md` says the shape.

## What the adapter answers: the seven capabilities

A kind's adapter is a class in `scripts/screen_driver.py` that answers these in code;
its file here is the account of those answers. `target --check` prints the account's
first sentence and the `discover` keys.

1. **attach** — how the driver gets a page that drives the product, *as the identity
   the seeded state belongs to*. Authentication lives here, because attach is the only
   capability that touches the driven context. It includes the order: state put before
   attach (a user must exist before anyone can be that user) or after (an application
   already running takes its state while attached); `reach_before_attach` says which.
2. **ready** — how the driver knows the product is answering *and can be driven*,
   re-checked between scenes: an application can crash mid-run, a service worker is
   recycled after thirty idle seconds.
3. **address** — how the contract's `route` becomes something `goto()` accepts.
4. **release** — how the product is given back: a window the user owns restored to its
   own size, clock and page; a browser the driver launched closed.
5. **transport (the write half)** — which path `seed:` mechanisms write through. The
   product's own write surface is the default; `via: storage` is the declared exception
   and names the criterion proving the product reaches that state itself (`proven_by`).
6. **observe (the read half)** — which path an `observe` line reads through, in which
   grammar. Every read is held to one rule: *a fresh read of persistent state, on a path
   the acting view did not produce, issued after the action completed*. Its premise is
   that **the surface read is rebuilt from persistent state by the product's one code
   path** — a page that renders a preview projection when the database is absent
   renders its nodes whether or not anything was written. A kind with a JSON read
   surface uses it; `node … exists` asserts only that the rebuilt view offers a
   control, one grade weaker than a field comparison.
7. **how to break the transport** — what `transport_off` has to take away for this kind
   while the product keeps answering, and what `transport_on` puts back.

## Adding a kind

A product kind not among the four needs an adapter class in the driver — the seven
capabilities, its `kind`, `read_surface`, `reach_before_attach`, and `discover_keys`,
registered in `ADAPTERS` — and a file here in the shape of the three, giving the seven
answers and what the repository provides for that kind. `target --check` then knows
the kind on its own.

## Two things no lint can check, so every kind's file answers them

- **The count of seeded rows comes from `data/fixtures.js`, not only the values.** A
  seed that makes four members where the fixtures draw six produces a different height
  and a different tree, and no box measurement saves it. A fixed-height panel hides
  this; a growing table does not.
- **The one code path.** No request path may choose its projection by whether a data
  source is present, by a query parameter, or by a build switch. State how the guard in
  the consuming repository checks it for this kind — the static guard is the second
  line; the wiring check's `--negative` is the first.
