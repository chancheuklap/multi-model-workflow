# Targets — what a product has to answer before the two judges can drive it

Interface parity and the wiring check are two judgements over one drive. The drive is
`scripts/screen_driver.py`; what differs between products is not the judgement but how
the product is reached, put into a state, addressed, released, and read. Each of those
is one **platform capability**, and each kind of product answers the set in its own
reference file here: [electron.md](electron.md), [web.md](web.md),
[chrome-extension.md](chrome-extension.md). The screen contract names the kind and the
file (`target.kind`, `target.adapter`); the driver picks the adapter by kind; the file is
the human account of what that adapter does and what the repository has to provide.

## The nine questions a new target answers

A product kind that is not one of the three files above needs a new file here and a new
adapter class in the driver. Both answer the same nine questions, in this order.

1. **attach** — how does the driver get a page that drives the product, *as the identity
   the seeded state belongs to*? Authentication lives here, because attach is the only
   capability that touches the driven context and a session cookie is a context action.
   The answer includes the order: is the state put before attach (a user must exist
   before anyone can be that user) or after (an application that is already running
   takes its state while attached)? The driver never assumes an order; the adapter's
   `reach_before_attach` says it.
2. **ready** — how does the driver know the product is answering, *and can be driven*?
   This is a condition re-checked between scenes, not a start-up gate: an application can
   crash mid-run and every `DIFF` after that is noise; a service worker is recycled after
   thirty idle seconds.

   Answering is the cheap half and on its own it is a trap. A product whose own
   dependencies are unusable answers a health check and then refuses every control it
   shows: it sits in its service-unavailable state with every button disabled, and each
   criterion fails much later in a place that says nothing about the cause. So the answer
   names the surface that says the product is *usable*, not only alive, and `start` fails
   on it at once, quoting what the product said was missing. A run that cannot be driven
   is a refusal at the start, never a slow row of red.
3. **address** — how does the contract's `route` become something `goto()` accepts?
4. **release** — how is the product given back? A window the user owns is restored to
   its own size, clock and page; a browser the driver launched is closed.
5. **state transport (the write half)** — which path do `seed:` mechanisms write
   through? The strict answer, the product's own write surface, is the default and needs
   no declaration; a mechanism that writes storage directly declares `via: storage` and
   names the criterion that proves the product itself reaches that state (`proven_by`).
6. **observe surface (the read half)** — which path does an `observe` line read through,
   and in which grammar? The write half and the read half are two capabilities, not one:
   a server-rendered console writes SQL and reads rendered HTML, and declaring one says
   nothing about the other. The rule every read is held to:

   > A fresh read of persistent state, on a path the acting view did not produce, issued
   > after the action completed.

   That covers an HTTP GET, an SQL read and `chrome.storage.get` alike. It has one
   premise without which it is empty: **the surface read must be rebuilt from persistent
   state by the product's one code path.** A page that renders a preview projection when
   the database is absent renders its nodes whether or not anything was written, and an
   `observe` against it proves nothing. That is why the single-code-path guard in the
   consuming repository is not a style rule: on a server-rendered target it is the
   condition that makes `observe` mean anything. A target with a JSON read surface uses
   it — `node … exists` is one grade weaker than a field comparison, because it asserts
   that the rebuilt view offers a control, not that a value was stored.
7. **how to break the transport** — one command that takes the persistence away (an
   environment variable, a stopped container, an empty database) and one that puts it
   back. The wiring check's `--negative` runs every row with the transport broken and
   requires each to fail on an `observe` assertion — a specific `MISS <row> — … was …`,
   not a run that could not attach. That is the check that cannot be satisfied by
   narrowing: an `observe` line that goes green with nothing persisted is caught here
   and nowhere else. The commands are machine facts and live in `.mmw/target.json`.
8. **instance** — how many runs of this product can one machine hold at once, and how
   does a run take one of them? `dispatch` sends every startable ticket of a spec out
   together, each in its own worktree, and a worktree isolates files and nothing else:
   ports, the running application, the service behind it and the account inside that
   service are the machine's, so each of them has to be divided here.

   The driver claims a **lease** for the worktree before it runs any command declared
   here and puts it in that command's environment: `MMW_INSTANCE`, `MMW_SLOT`,
   `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`, and `MMW_AUTOMATION=1`. The
   repository takes its
   ports and directories from those and from nothing else — **at the moment it starts a
   process, never into the session or the test environment**: a suite that asserts its
   product's registered port number is right to, and a derived port leaking into it
   turns a correct suite red. A repository whose product cannot move — ports written
   into a container file, a callback registered at a fixed port, an installed product
   that hardcodes them — says so, and its tickets are serialised rather than left to
   interfere with each other:

   ```json
   "instance": {"max": 1, "why": "<what stops a second one>"}
   ```

   `discover` prints `instance` (a readable name for messages) and `instance_check` (one
   `observe` line in this target's own read surface whose truth means "the product
   answering is the one this run started"). Question 2 then means *answering and mine*.
9. **what leaves this machine** — what does this product do in a run that reaches past
   the machine it runs on, and how does a run neutralise it? Opening the system browser,
   calling a paid service, writing a machine-global location. `MMW_AUTOMATION=1` is the
   signal; recording what would have been done, in the run's own `MMW_DATA_DIR`, is
   usually both the neutral act and a stronger assertion than the one it replaces — a
   criterion that reads back the URL a button would have opened says more than one that
   reads that the application entered a waiting state. A repository that answers this
   question under a name of its own gives no criterion anything to rely on: a run that
   reached a live service, or waited for a person to finish something by hand, then
   looks exactly like one that did neither.

## What is the contract's and what is the repository's

The contract (`docs/specs/<effort>/screen-contract.yaml`) is a design artifact that
travels with the branch. It carries `target.kind`, `target.adapter`, `viewports`,
`pages` (`mount`, `route`, and for a `Component · ` page its `component`), `scenes`
(`page`, `reach`, `open`, and overrides of `mount` / `route`), and the mechanism table
with `via` and `built_by`. It carries **no address**.

The repository carries `.mmw/target.json` at its root — machine facts, answered afresh
on every machine:

```json
{
  "start": "uv run python scripts/testing/target.py start",
  "stop": "uv run python scripts/testing/target.py stop",
  "discover": "uv run python scripts/testing/target.py discover",
  "reach": "uv run python scripts/testing/reach.py",
  "transport_off": "uv run python scripts/testing/target.py transport off",
  "transport_on": "uv run python scripts/testing/target.py transport on",
  "checks": ["uv run ruff check .", {"run": "uv run pytest -q", "timeout": 1800}],
  "instance": {"max": 1, "why": "<what stops a second one>"}
}
```

- `start` brings the product up and returns once it answers. **Nobody starts the
  product by hand for a run**: the driver runs `start` before the first scene, every
  time, then `discover` and `ready` again. Every time, because only `start` knows
  whether the product that answers is the one this worktree's code builds; a product
  left over from before a merge answers just as well, and nothing on the run would say
  so. That is why `start` has to be cheap on a product that is already up and current. A
  repository without `start` gets a run that stops on the first scene naming what to
  declare. Everything the product needs in order to run — which backing service to point
  at, which data directory to use, which log to write — is found or chosen *inside* this
  command, by the repository's own rules, and never typed into a session: an agent told
  those facts in a message works once; the next agent is not told. `start` prints to
  stderr what it chose.

  **`start` is idempotent**, and idempotent covers both halves of what it may find. Its
  own current product, already answering, is left alone. Its own stale leftovers — this
  same worktree's earlier run, still holding the ports, no longer answering — it clears
  first, by reaching for its own `stop` on its own record of what it started (a pid file
  it wrote, a container project it named), and comes up again. Anything else holding its
  ports it refuses over, naming what it found.

  That exit is `start`'s own and cannot be lifted into the driver, because **whose a port
  is cannot be read off the port**: on a machine where a multiplexer or a container
  runtime holds the published port of every stack at once, a rule written from the
  holder's working directory would refuse a run its own addresses, or end the networking
  of every stack there. The only thing that knows what a run started is the command that
  started it — so a run's own leftovers are `start`'s to clear, and nothing else on the
  machine may clear them.

  It takes every port and directory from the lease in its environment (question 8), and
  **refuses to start at all when there is no lease**, printing the command that gives it
  one. Falling back to a default port instead would keep two allocation schemes alive,
  and the collisions come back with them.
- `stop` ends what `start` started, and nothing else. It is the only way a run may end a
  process: the pre-tool gate refuses `kill`, `pkill`, `killall` and `xargs kill`, and its
  refusal sends the reader here. So a repository that declares `start` declares `stop`
  too — without it the refusal points at a command that does not exist, and whoever hits
  it has no way forward. `stop` ends only what this run recorded as its own (a pid file
  it wrote, a process whose working directory is this worktree), leaves a neighbour's
  product alone, and exits 0 when there is nothing of its own to end. It does not release
  the lease; the driver does that.
- `discover` prints one JSON object of addresses; each kind's file says which keys. Two
  more are the same for every kind: `instance`, a readable name for this run, and
  `instance_check`, one `observe` line whose truth means the product at these addresses
  is the one this run started. Omit them and `ready` falls back to asking only whether
  something answers, which on a shared machine is a different question.
- `reach` is a command prefix; the driver appends the mechanism names of a scene or a
  row (`seed:library-ready dev:image-select-path`) and, for the perturbation run,
  `--perturb`. The script prints `KEY=VALUE` lines (`project_id=…`, and for a web target
  `cookie=name=value`); every `{key}` in a route, an `open` value, or an `observe` path
  is filled from them. It **establishes** the state: it runs once per scene and once per
  row, and it may skip only what it established itself in this same run. A state it
  merely finds is not evidence that the product can reach it, and accepting one hides the
  case that matters: a sign-in step that returns early whenever it finds the application
  signed in reports success over a sign-in that no longer works. Idempotent means running
  it twice gives the same result, not that what is already there can be trusted.
- `transport_off` / `transport_on` answer question 7.
- `checks` is optional: the consuming repository's own "run the tests yourself" rule,
  made a gate. `verify-ticket.py --closeout` runs the entries in order at the
  repository root after an `ALL MET` draft is accepted and before the ticket closes;
  any non-zero exit leaves the ticket open and posts `CHECKS FAILED` with each failed
  command and its last 20 lines; every exit 0 appends `CHECKS OK <n>/<n>` to the
  closing comment. An entry is a command string, held to the same bound as a `CHECK:`
  (`DEFAULT_TIMEOUT`, 600 s), or `{"run": "<command>", "timeout": <seconds>}` for a
  suite that needs longer. A key that is not a list, an entry of another shape, or a
  file that is not JSON is `CHECKS FAILED`, not absence. `--reverify`, `--lint`,
  `--check-only` and a `HANDOFF REQUIRED` draft do not run them. A repository without
  the key is unchanged.

## Two things no lint can check, so every new target answers them here

- **The count of seeded rows comes from `data/fixtures.js`, not only the values.** A
  seed that makes four members where the fixtures draw six produces a different height
  and a different tree, and no box measurement saves it. A fixed-height panel hides
  this; a growing table does not.
- **The one code path.** No request path may choose its projection by whether a data
  source is present, by a query parameter, or by a build switch. State how the guard in
  the consuming repository checks it for this kind — the static guard is the second
  line; the wiring check's `--negative` is the first.
