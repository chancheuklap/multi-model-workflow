# Architecture report

The page This skill's review step 3 draws with the `diagram-design` skill. Its reader is the owner, who does not read code: no file, function or code is on it. Write the explanatory text and badges in the owner's language, with names governed by **principle-anchor-every-reference**. This file sets what goes on the page, top to bottom: the header, one card per candidate, then the top recommendation.

## Header

Repo name and date. No introduction paragraph. Straight into the candidates.

## Candidate card

The diagrams carry the weight. Each candidate is one `<article>`:

- **Title**: short, names the part made simpler (e.g. "One place takes in orders").
- **Badge row**: recommendation strength (`Strong` = `accent`, `Worth exploring` = `ink`, `Speculative` = `muted`), plus its size: one ticket, or a spec.
- **Before / After diagram**: the centrepiece. See Diagrams below.
- **What hurts now**: one sentence, as a person changing the product meets it: which kind of change is slow, easy to get wrong, or hard to test, and why.
- **What changes**: one sentence.
- **What gets better**: bullets of six words or fewer, each an effect on a later change (e.g. "A pricing fix touches one part", "Tests run the real path").
- **ADR callout** (if applicable): one line in an `accent-tint` box.

## Diagrams

Pick the `diagram-design` type that fits the candidate. Mix them. Don't make every diagram look the same. Variety is part of the point.

- "X calls Y calls Z, and look at the mess": **Dependency graph**, or **Architecture** when the modules sit in distinct runtime places.
- "Before: 6 round-trips; after: 1": **Sequence**.
- A call passing through thin layers that each do nothing: **Layer stack**. Before: many thin bands. After: one thick band labelled with the consolidated responsibility.
- One rule or vocabulary copied by hand into several modules: **Dependency graph**, the copies fanning in to the one module that owns it after.
- A tree of calls that collapses into one module: **Tree** before, **Nested** after, with the now-internal calls shown faded inside the deep module.
- An interface nearly as wide as its implementation: **Nested**, the interface drawn as the outer band around the implementation, thin in the after picture.

Draw both diagrams with the same `viewBox` about 560 wide, each scaled to its column's width (overriding the template's `min-width`), so 12px labels stay legible at half the page width.

Each kind of mark keeps one look across every diagram in the report, so the reader learns the notation once. The legend names them in plain words: a part, the part made deeper, where two parts meet, a change that spills from one part into another.

- **Module**: `diagram-design`'s Backend / API / Step node treatment.
- **Deep module**: its Focal node treatment.
- **Seam**: a dashed `muted` line with a plain label.
- **Leakage**: a solid `accent` connector. A leaking return in a Sequence keeps the type's dashed return line and turns `accent`.

The accent goes to leakage in a before diagram and to the deep module in an after diagram, never both, and this takes precedence over a type reference's own accent assignment. The two-accent cap per diagram still holds: when more than two paths leak, accent the two that make the point. Each diagram's legend strip names the ones it uses.

## Top recommendation section

One larger card. Candidate name, one sentence on why, anchor link to its card. That's it.

## Words

Plain words, short sentences. The architecture terms of the `codebase-design` skill (module, interface, depth, seam, adapter, leverage, locality) stay off the page; they go into the ticket written with the refactoring skill. No hedging, no throat-clearing. If a sentence could be a bullet, make it a bullet. If a bullet could be cut, cut it.
