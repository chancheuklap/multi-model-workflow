# Feature map

A feature map is one product's standing account of what a user can do now, where they enter, and which check guards each behaviour. An agent in a day discussion reads it before that product's code, and does not rebuild the account from the source. A worker who changes a feature updates the feature file in the same commit as the code it describes.

Two failures make the file useless to the next agent. A behaviour with no executor is read as if a command guarded it. Implementation copied into the file goes stale, and the next agent opens the code instead.

## Where it lives

Each product has one directory, `docs/features/<product>/`. The directory holds one `<feature>.md` for each feature and one `README.md`.

The directory stays in the repository while the product does. `docs/adr/0038-repository-files-are-layered-by-lifetime.md` takes a standing file into the repository when something keeps it true. Three things keep a feature map true. A lint checks the format, the index, each `source` and each `check` target. The worker who changes a feature updates its file in the same commit as the code. A periodic review turns each `check: none:` line into a command. That review is a later spec's procedure.

The directory is not under `.mmw/`. That tree holds what a script executes, and the search an agent uses skips a hidden directory. The directory does not sit with `CONTEXT.md`. A context is split by domain, not by product.

## The product README

`README.md` has five H2 sections, in this order.

1. `Baseline preconditions`. Conditions that hold before anyone operates the product.
2. `Driving conventions`. Identifiers a recipe uses to find a control.
3. `Proof and skip reporting`. Where evidence goes, and how a skipped path is reported.
4. `Feature entry contract`. Points at **How a feature is divided** below. Adds a rule only when that rule is true of this product and not of every product.
5. `Features`. The index. One line per feature file. The line links the file and says what the user can finish there.

Example of one index line. The notes app is an example, and the line is not a requirement.

- [Create a note](./create-note.md) covers saving a note, cancelling a draft, and reading the saved note back.

## How a feature is divided

A feature is one thing a user can finish from one entry. A sub-feature is one behaviour someone can observe.

The detail of an interface behaviour stays in the screen contract's row. The feature map names that row's id and does not copy the row.

An agent proposes the division. The owner confirms the first map when the product is adopted, and confirms each spec's change in `## Feature map changes`.

Leave out a behaviour that has no executor. `check: none:` is allowed when the same line states the reason. The lint lists those lines, and they do not fail the lint. A behaviour with no interface, which a user cannot finish from an entry, stays out of the feature map. A test can still guard it.

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
