# Experiment Prototype

The **smallest runnable experiment** that exercises the thing in question — a library's API, an algorithm, an integration between two systems — and a `README.md` that records what it showed. Use this when the question is about **how to implement something**, not whether the logic is right or what it should look like: the kind of thing that reads fine in the docs but only becomes clear once real code calls it with real inputs.

## When this is the right shape

- "Can this library actually do X the way we need?"
- "Is this algorithm fast enough on our data sizes?"
- "How do these two systems talk to each other — what does the handshake really look like?"
- Anything where someone wants to **run a piece of the real approach before committing to it**.

If the question is "does this state model feel right" — wrong branch, use [LOGIC.md](LOGIC.md). If it's "what should this look like" — [UI.md](UI.md).

## Process

### 1. State the question and the bar

Open the leaf `README.md` with one paragraph: the question, and what result counts as "yes" — a number, a behaviour, an output shape. An experiment without a bar answers nothing; it just runs.

### 2. Write the smallest thing that runs

Use the project's own language and toolchain. One entry point, started with one command from the project's task runner (rule 2 in the [SKILL](SKILL.md)). Real inputs where they matter to the question — a sample of the actual data, the actual service — and stubs everywhere else.

### 3. Draw the boundary around the reusable part

The code that answers the question — the call sequence, the algorithm, the adapter — sits behind a clear boundary (a function, a module, a class) with the harness around it. The harness is a shell; the part inside the boundary is what the real code will be written from. No tests on either side: those come when the real code lands.

### 4. Run it and record what you see

Run the experiment and write the observations into the `README.md`: the numbers, the surprises, the version or platform that mattered, the thing the docs got wrong. Facts, as observed — not conclusions yet.

### 5. Record the answer, keep the experiment

Write the conclusion under the observations: yes or no against the bar, how the real code should draw on the reusable part, and what it should do differently. Then keep the experiment the way the [SKILL](SKILL.md) describes: it stays in the leaf directory, runnable, so the next question about the same approach starts by editing it.

## Anti-patterns

- **Don't build the feature.** The experiment answers one question; the moment it starts growing toward the whole feature, it's no longer an experiment.
- **Don't add tests.** The observations in the `README.md` are the evidence; tests belong to the real code.
- **Don't point it at production data or services** unless the question is specifically about them — and then read-only.
- **Don't generalise.** No "what if we wanted to support Y later."
- **Don't leave the result in your head.** An experiment whose `README.md` has no observations and no conclusion has to be re-run by the next reader.
