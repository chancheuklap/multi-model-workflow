# How a repository becomes an acceptance runtime

The **product answers** live in `.mmw/` at the repository root; `target_config.py --check`
lists the fields. This page says what every answer must guarantee and why each field is
shaped as it is.

## What every product answer must guarantee

These hold for every product. How a given repository meets them is its own.

- **Story pages render the product's own components.** A `Component · ` page is
  that component in one scene. An `App · ` page mounts the product's own
  composition module (the code that wires the regions together in the running
  product) and feeds it scene data; it does not wire the components itself,
  so a region the product leaves unwired stays unwired on the story page.
  Neither page carries a Claude Design runtime (`sc-interp`, `data-dc-tpl`,
  `data-dc-script` or `dc-root`).
- **`[data-story-root]` and the `data-ui` ids sit where
  [story-parity.md](story-parity.md) puts them**, under **The story page the
  product serves**.
- **A `data-ui` id repeats only on the repeating part of a list.** The same id on
  two elements the design page shows as one each is a product defect: element
  parity pairs by id, so a repeated id outside a list makes one of them
  unpairable. A static check the contract ticket delivers holds this.
- **Time values come from scene data.** A client-rendered product loads the same
  paused clock the design side uses, so a clock reading is not a live instant.
- **A boundary test replaces the outbound call module** the consuming repository
  names — the layer that emits the call, whether the call travels as HTTP, IPC, or
  an extension message.
- **`.mmw/harness/` implements the break switch** that [journey.md](journey.md)
  **The break switch** specifies.
- **A journey script reads only the addresses `discover` printed.** It starts
  nothing of its own — no application, server, container, or backing service.
- **`harness_markers` declares this product's back-door strings** — the names it
  uses only to make itself drivable. `[]` is an answer.

## What the repository answers

- **`start`.** One command brings the whole stack up and returns only once the
  product is usable, not merely alive. It is run every time, and is idempotent in
  both directions: it leaves its own current product alone, clears its own stale
  leftovers first (by its own `stop`, on its own record of what it started), and
  refuses over anything else holding its ports, naming what it found. A port check tests for a listener the way the product's server binds (with `SO_REUSEADDR`, as Python's `http.server` does), because a product it just stopped leaves its closed connections in `TIME_WAIT` for a while and a plain `bind` then refuses a port nothing holds. Everything
  the product needs — which backing service, which data directory, which log — is
  found or chosen inside this command, from the lease in its environment
  (`MMW_INSTANCE`, `MMW_SLOT`, `MMW_PORT_BASE`, `MMW_PORT_COUNT`, `MMW_DATA_DIR`,
  `MMW_AUTOMATION`). Every per-user location the product reads or writes by default
  (a configuration home such as `~/.<product>` or the variable that moves it, an XDG
  directory, a user-level settings file) is pointed inside `MMW_DATA_DIR` here and
  seeded there, so a journey that saves changes nothing of this machine's own; a
  location that cannot be moved is listed under `leaves_machine`. It refuses to start with no lease and prints the command that
  supplies one: `python3 <scripts>/lease.py run -- <the start command>`. When
  `MMW_BREAK` is in that command's environment, this is also the process that
  arms the break switch.

- **Servers under a burst.** A page opens many connections at once (stylesheets, scripts, data). Every server the judges load a page from, the story service and the product itself, accepts at least 64 pending connections (`request_queue_size` for Python's `socketserver`, whose default of 5 lets a busy machine reset the rest and the page render empty).

- **`stop`.** The only way a run ends a process. It ends only what this run
  recorded as its own, leaves a neighbour's product alone, exits 0 with nothing to
  end, and does not release the lease. It ends the containers of this run's stack
  as well as its processes. When it returns, nothing listens on any port of this
  run's lease — that is what "stopped" means here.

- **`stories`.** Brings up the story service and prints its `origin`.
  Addresses look like `<origin>/?page=<mount>&scene=<name>&viewport=<WxH>`. The
  pages themselves live in `.mmw/stories/`. It takes **no lease**: a story page
  renders product components from scene data — presentational, fed by that data
  and nothing else — with no backend, no seed and no route behind it, so the one
  thing it needs is a port, and it asks the machine for a free one (bind port `0`,
  then print the port that came back) rather than deriving one from
  `MMW_PORT_BASE`. Its environment carries `MMW_AUTOMATION=1` and nothing else of
  the lease.

- **`journeys`.** One directory per journey; what a journey script must be is
  [journey.md](journey.md).

- **`harness_markers`.** Judged by [harness-guard.md](harness-guard.md).

- **`checks`.** The repository's own checks, which the `verify-ticket` skill's
  `--closeout` runs. `checks` is optional: a list run in order at the repository root, each entry a command string held to the same bound as a `CHECK:` (`DEFAULT_TIMEOUT`, 600 s) or `{"run": "<command>", "timeout": <seconds>}` for a suite that needs longer. Every command receives `MMW_BASE_REF=origin/<into>`, where `into` is from the newest `worker.started`. The run lands as a `ticket.checked` event of its own, run `repo-checks`, before the closing comment: result `met` and the count passed when every command exited 0, and the branch is then pushed and the ticket closes; result `unmet` with each failed command and its last 20 lines when any did not, and the ticket stays open. A key that is not a list, an entry of another shape, or a file that is not JSON is an `unmet` run naming that problem, not absence; a repository without the key runs nothing and posts no such event.

## `.mmw/` directory

Product answers live here, not scattered through the repository:

- `target.json` — the fields above
- `harness/` — start the stack, the break switch, vendor stubs, account seeds, the
  few seeds a journey uses, the entry that records an action that would leave the
  machine
- `journeys/` — one directory per named journey
- `stories/` — story pages and their adapter

Scripts a person runs on their own machine may stay where they are, provided they
call the same start code `harness/` uses.

## Rules

Real keys exist only on a paid-smoke ticket labelled `ready-for-human`.
