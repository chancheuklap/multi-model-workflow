# Final standards

**Who reads this:** the reviewer whose Goal starts with `Final standards`.

One question: does this diff match this repo's written coding standards.

## Where the standard is

Read should name this repo's file — `CODING_STANDARDS.md`, `CONTRIBUTING.md`, or whatever it uses. "This repo has no written standard" in Read also counts; then use only the smell baseline below.

Neither a file nor that note: `needs-context`.

## Smell baseline

These Fowler smells from *Refactoring* chapter 3 always apply, with two rules:

- The repo wins. A practice the repo writes down is not a finding even if the baseline would flag it.
- Every smell is a judgement ("this may be Feature Envy"), not a hard violation. Skip what a linter already owns.

Read each as *what it is* → *what to do*, against the diff:

- **Mysterious Name** — a function, variable, or type does not say what it does. → Rename; if you cannot, the design is still unclear.
- **Duplicated Code** — the same shape appears more than once in this diff. → Extract it.
- **Feature Envy** — a method uses another object's data more than its own. → Move it to that data.
- **Data Clumps** — the same fields always travel together. → Make a type and pass that.
- **Primitive Obsession** — a primitive stands in for a domain concept. → Give the concept a type.
- **Repeated Switches** — the same `switch` / `if` chain repeats. → Polymorphism or one shared map.
- **Shotgun Surgery** — one logical change edits many files. → Put what changes together in one module.
- **Divergent Change** — one module changes for unrelated reasons. → Split so each module changes for one reason.
- **Speculative Generality** — abstraction, parameters, or extension points nobody asked for. → Delete; wait for a real need.
- **Message Chains** — `a.b().c().d()` the caller should not know. → Hide the path behind one method.
- **Middle Man** — most of a type only forwards. → Call the real target.
- **Refused Bequest** — a subtype ignores or overrides most of what it inherited. → Compose instead.

## Report two kinds

- **Written standard** — cite the file and the rule. These may be hard violations.
- **Baseline smell** — name the smell and cite the code. Always a judgement.

Do not read spec. Do not read plan.
