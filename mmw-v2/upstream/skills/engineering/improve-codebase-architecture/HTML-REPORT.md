# HTML Report Format

The architectural review is rendered as a single self-contained HTML file in the OS temp directory. Its look (colours, type, page header, cards, footer) and every diagram on it follow the `diagram-design` skill. This file sets what goes on the page, top to bottom: the header, one card per candidate, the top recommendation, then a footer carrying the one line `diagram-design` asks for naming the style guide used.

## Header

Repo name and date. No introduction paragraph. Straight into the candidates.

Module, seam, leakage and deep module keep one look across every diagram in the report, so the reader learns the notation once:

- **Module**: `diagram-design`'s Backend / API / Step node treatment.
- **Deep module**: its Focal node treatment.
- **Seam**: a dashed `muted` hairline with a mono label.
- **Leakage**: a solid `accent` connector.

The accent goes to leakage in a before diagram and to the deep module in an after diagram, never both, and this takes precedence over a type reference's own accent assignment. Each diagram's legend strip names the ones it uses.

## Candidate card

The diagrams carry the weight. Prose is sparse, plain, and uses the glossary terms (from the `codebase-design` skill) without ceremony.

Each candidate is one `<article>`:

- **Title**: short, names the deepening (e.g. "Collapse the Order intake pipeline").
- **Badge row**: recommendation strength (`Strong` = `accent`, `Worth exploring` = `ink`, `Speculative` = `muted`), plus a tag for the dependency category (`in-process`, `local-substitutable`, `ports & adapters`, `mock`).
- **Files**: monospaced list.
- **Before / After diagram**: the centrepiece. Two columns, side by side. See Diagrams below.
- **Problem**: one sentence. What hurts.
- **Solution**: one sentence. What changes.
- **Wins**: bullets, ≤6 words each. e.g. "Tests hit one interface", "Pricing logic stops leaking", "Delete 4 shallow wrappers".
- **ADR callout** (if applicable): one line in an `accent-tint` box.

The reader knows nothing about this topic. Pictures show what things are and how they connect. Words do only what a picture cannot: say which question the picture answers, point at the part that matters, and state what follows from it. A sentence that repeats what the picture shows is deleted; a picture that needs a paragraph to be read is redrawn.

## Diagrams

Pick the `diagram-design` type that fits the candidate. Mix them. Don't make every diagram look the same. Variety is part of the point.

- "X calls Y calls Z, and look at the mess": **Dependency graph**, or **Architecture** when the modules sit in distinct runtime places.
- "Before: 6 round-trips; after: 1": **Sequence**.
- A call passing through thin layers that each do nothing: **Layer stack**. Before: many thin bands. After: one thick band labelled with the consolidated responsibility.
- One rule or vocabulary copied by hand into several modules: **Dependency graph**, the copies fanning in to the one module that owns it after.
- A tree of calls that collapses into one module: **Tree** before, **Nested** after, with the now-internal calls shown faded inside the deep module.
- An interface nearly as wide as its implementation: **Nested**, the interface drawn as the outer band around the implementation, thin in the after picture.

Before and after sit side by side, drawn with the same `viewBox` and each scaled to its column's width rather than the template's fixed minimum width, so the reader compares them by eye.

## Top recommendation section

One larger card. Candidate name, one sentence on why, anchor link to its card. That's it.

## Tone

Plain English, concise, but the architectural nouns and verbs come straight from the `codebase-design` skill. Concision is not an excuse to drift.

**Use exactly:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.

**Never substitute:** component, service, unit (for module) · API, signature (for interface) · boundary (for seam) · layer, wrapper (for module, when you mean module).

**Phrasings that fit the style:**

- "Order intake module is shallow: interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

**Wins bullets** name the gain in glossary terms: *"locality: bugs concentrate in one module"*, *"leverage: one interface, N call sites"*, *"interface shrinks; implementation absorbs the wrappers"*. Don't write *"easier to maintain"* or *"cleaner code"*, because those terms aren't in the glossary and don't earn their place.

No hedging, no throat-clearing, no "it's worth noting that…". If a sentence could be a bullet, make it a bullet. If a bullet could be cut, cut it. If a term isn't in the `codebase-design` skill's glossary, reach for one that is before inventing a new one.
