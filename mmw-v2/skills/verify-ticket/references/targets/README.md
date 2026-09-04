# Targets — what a product has to answer before the two judges can drive it

Interface parity and the wiring check are two judgements over one drive. The drive is
`scripts/screen_driver.py`; what differs between products is not the judgement but how
the product is reached, put into a state, addressed, released, and read. Each of those
is one **platform capability**, and each kind of product answers the set in its own
reference file here: [electron.md](electron.md), [web.md](web.md),
[chrome-extension.md](chrome-extension.md). The screen contract names the kind and the
file (`target.kind`, `target.adapter`); the driver picks the adapter by kind; the file is
the human account of what that adapter does and what the repository has to provide.

## The seven questions a new target answers

A product kind that is not one of the three files above needs a new file here and a new
adapter class in the driver. Both answer the same seven questions, in this order.

1. **attach** — how does the driver get a page that drives the product, *as the identity
   the seeded state belongs to*? Authentication lives here, because attach is the only
   capability that touches the driven context and a session cookie is a context action.
   The answer includes the order: is the state put before attach (a user must exist
   before anyone can be that user) or after (an application that is already running
   takes its state while attached)? The driver never assumes an order; the adapter's
   `reach_before_attach` says it.
2. **ready** — how does the driver know the product is answering? This is a condition
   re-checked between scenes, not a start-up gate: an application can crash mid-run and
   every `DIFF` after that is noise; a service worker is recycled after thirty idle
   seconds.
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
  "discover": "uv run python scripts/testing/target.py discover",
  "reach": "uv run python scripts/testing/reach.py",
  "transport_off": "uv run python scripts/testing/target.py transport off",
  "transport_on": "uv run python scripts/testing/target.py transport on"
}
```

- `start` brings the product up and returns once it answers. **Nobody starts the
  product by hand for a run**: when `ready` says the product is not answering, the
  driver runs `start` once, then `discover` and `ready` again; a repository without
  `start` gets a run that stops on the first scene naming what to declare. Everything
  the product needs in order to run — which backing service to point at, which data
  directory to use, which log to write — is found or chosen *inside* this command, by
  the repository's own rules, and never typed into a session: an agent told those
  facts in a message works once; the next agent is not told. `start` is idempotent (a
  product already answering is left alone), refuses rather than kills when something
  else holds its ports (naming what it found), and prints to stderr what it chose.
- `discover` prints one JSON object of addresses; each kind's file says which keys.
- `reach` is a command prefix; the driver appends the mechanism names of a scene or a
  row (`seed:library-ready dev:image-select-path`) and, for the perturbation run,
  `--perturb`. The script prints `KEY=VALUE` lines (`project_id=…`, and for a web target
  `cookie=name=value`); every `{key}` in a route, an `open` value, or an `observe` path
  is filled from them. It is **idempotent**: it runs once per scene and once per row,
  and a state already there is left there.
- `transport_off` / `transport_on` answer question 7.

## Two things no lint can check, so every new target answers them here

- **The count of seeded rows comes from `data/fixtures.js`, not only the values.** A
  seed that makes four members where the fixtures draw six produces a different height
  and a different tree, and no box measurement saves it. A fixed-height panel hides
  this; a growing table does not.
- **The one code path.** No request path may choose its projection by whether a data
  source is present, by a query parameter, or by a build switch. State how the guard in
  the consuming repository checks it for this kind — the static guard is the second
  line; the wiring check's `--negative` is the first.
