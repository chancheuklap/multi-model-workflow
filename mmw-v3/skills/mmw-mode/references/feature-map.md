# Feature map

A feature map is one product's standing account of what a user can do now, where they enter, and which check guards each behaviour. An agent in a day discussion reads it before that product's code, and does not rebuild the account from the source. A worker who changes a feature updates the feature file in the same commit as the code it describes.

Two failures make the file useless to the next agent. A behaviour with no executor is read as if a command guarded it. Implementation copied into the file goes stale, and the next agent opens the code instead.

## Where it lives

Each product has one directory, `docs/features/<product>/`. The directory holds one `<feature>.md` for each feature and one `README.md`.

The directory stays in the repository while the product does. A lint checks the format, the index, each `source` and each `check` target. The worker who changes a feature updates its file in the same commit as the code.

## The product README

`README.md` has five H2 sections, in this order.

1. `Baseline preconditions`. Conditions that hold before anyone operates the product.
2. `Driving conventions`. Identifiers a recipe uses to find a control.
3. `Proof and skip reporting`. Where evidence goes, and how a skipped path is reported.
4. `Feature entry contract`. Points at **How a feature is divided** and at **A feature file** below. Adds a rule only when that rule is true of this product and not of every product.
5. `Features`. The index. One line per feature file. The line links the file and says what the user can finish there.

Example of one index line. The notes app is an example, and the line is not a requirement.

- [Create a note](./create-note.md) covers saving a note, cancelling a draft, and reading the saved note back.

## How a feature is divided

A feature is one thing a user can finish from one entry. A sub-feature is one behaviour someone can observe.

The detail of an interface behaviour stays in the screen contract's row. The feature map names that row's id and does not copy the row.

A feature map writes down the owner's understanding of what the product does for a user, so the owner confirms it. Before you write or change what a feature file says a user can do (its opening paragraph, the sentences of `## Sub-features`, the entries of `## How to get to it (user POV)`, and the product README's `Features` line), list the change in the conversation, in the owner's words where they gave them, and write it once the owner confirms it. A spec's `## Feature map changes` is that list for a night: the owner confirms it with the spec, and a worker writes only what it lists. `## Driving it`, `## Gotchas`, `source` and `check` record how the product is operated and checked; the agent writes them without asking.

Leave out a behaviour that has no executor. `check: none:` is allowed when the same line states the reason. The lint lists those lines, and they do not fail the lint. A behaviour with no interface, which a user cannot finish from an entry, stays out of the feature map. A test can still guard it.

## Using it in a task

A playbook that drives one feature of the product reads its feature file before the first command: the entries from `## How to get to it (user POV)`, the steps from `## Driving it`, the traps from `## Gotchas`. The path it follows is the one the file states.

- A product with no `docs/features/<product>/` has no feature map. Drive the surface the owner named, say so in the reply, and tell the owner that the `setup-mmw` skill onboards the product.
- When no feature file covers the feature, write one in the shape below, with `source` `existing <YYYY-MM-DD>`, confirmed as **How a feature is divided** says, before you go on. Run `feature_map.py lint` (the `verify-ticket` skill's `scripts/feature_map.py`) from the repository root, commit the file on its own and push it: a worker starts from the base branch on origin and never sees a file left in this checkout.
- A change that alters what a feature file says changes it in the commit of the code it describes, after the owner confirmed it, with the lint run before that commit. When a ticket will make the change, the confirmed lines are quoted under **What to build** and the file is under **Owns**. With no `docs/features/`, there is nothing to lint.
- A session a script started that finds a feature file wrong and does not own it leaves it as it is and records a `deferred` child naming the line and what the product does.

## A feature file

The file starts with an H1 and one paragraph. The paragraph says what the user can finish here. Then exactly four H2 sections, in this order.

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it`
4. `Gotchas`

### Sub-features

Each observable behaviour is one bullet. The bullet is the id in backticks, then one sentence. Two indented lines follow.

```
- `<id>` <one sentence of the behaviour>.
  source: <source>
  check: <command>
```

`source` is one of these five.

- A decision ticket, `#<n>`.
- A spec subsection, `#<n> §<k>`.
- A screen-contract row, `row:<row id>`.
- An ADR, `ADR <number>`.
- `existing <YYYY-MM-DD>`, for a behaviour that was already in the product and that no decision record names. The date is the day the behaviour was written into the feature map.

`check` is a command that runs from the repository root and guards this behaviour. When no command guards it, the line is `check: none: <one line saying why>`.

Example. The notes app is an example, and the lines are not a requirement.

```
- `create-save` persists a title and body.
  source: existing 2026-01-15
  check: node tests/create-note.test.js
```

### How to get to it (user POV)

List every entry a user has. One entry is one line.

### Driving it

The heading is `## Driving it`. It names no tool. The feature map does not choose how a product is operated.

The section starts with `Preconditions:`. It then pairs each user action with the command and the result someone can observe.

A worker writes or changes this section only after that session has started the product and walked the feature. Whether the section is written, and whether it is right, is not a pass condition. A ticket passes or fails on its criteria and its pins.

### Gotchas

Traps that waste a run or make its result unusable.

## Feature map changes

A spec's `## Feature map changes` section uses this shape. One feature file is one entry. Under the file, each changed sub-feature is one line, beginning with `added`, `changed` or `removed`, in that order. Several sub-features of one kind are several lines. A kind with no change has no line. Publish-time `verify-ticket.py --lint` reads this shape.

```
- `docs/features/<product>/<feature>.md` (new|changed)
  - added `<sub-feature id>` source: <source>
  - changed `<sub-feature id>` source: <source>
  - removed `<sub-feature id>`
```

A spec that changes no behaviour a user can observe writes `none`.

Example. The notes app is an example, and the entry is not a requirement.

```
- `docs/features/notes/create-note.md` (changed)
  - added `create-cancel` source: #12 §2
```
