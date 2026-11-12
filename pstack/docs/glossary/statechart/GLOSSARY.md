# Statechart

A pstack statechart shows a checked TLA+ model in the words of the person who judges the behavior. The chart shows possible moves. Its report identifies which rules hold, which break, and which the checker could not settle.

## Language

### Model and rules

**TLA+ specification**:
The `.tla` module that describes the modeled system's variables, possible starting states, and actions. Named rules express promises about those states or behaviors. A product spec records the agreed behavior in the operator's language. [Planning and tickets](../planning-and-tickets/GLOSSARY.md).

**TLC**:
The model checker that reads the TLA+ specification and checks the configured rules. The statechart command uses its results to label the chart and report.

**TLC configuration**:
The `.cfg` file that selects the behavior with `SPECIFICATION` or with `INIT` and `NEXT`. It also supplies constants and names the rules and constraints for a particular check. The same TLA+ specification can yield different results under different configurations.

**Model state**:
One assignment of values to all model variables. An initial state satisfies the initial predicate, usually `Init`. More than one assignment may qualify. If none qualifies, the report explains why no state could break a rule.

**Action**:
A relation between the values before and after one model step. The next-state relation, usually `Next`, collects the allowed actions. Named alternatives let TLC identify which action produced a step.

**State graph**:
The model states and the steps between them that TLC explores starting at the initial states.

**Rule**:
A check selected for the run. The driver distinguishes a configured `INVARIANT`, a configured `PROPERTY`, and TLC's deadlock check. Rule kind matters even when an invariant and a property have the same name.

**Invariant**:
A predicate named under `INVARIANT` that must hold in each state TLC checks, including the initial states. A reader's rule such as "Synced never appears while offline" becomes an invariant over the variables that represent the connection and displayed status.

**TLC property**:
A formula listed under `PROPERTY` in the TLC configuration. A temporal property can refer to a sequence of states, such as always (`[]`), eventually (`<>`), or leads to (`~>`). If a listed property is just a state predicate, TLC checks it only in initial states. The report identifies that scope when the predicate holds. For the general term, see [Formal verification](../formal-verification/GLOSSARY.md#the-property-and-its-scope).

**Liveness property**:
A temporal property that requires progress, such as a retry eventually completing. An execution that can stay in one state or cycle forever can disprove it. A liveness verdict requires TLC to check that property within the stated model.

**Fairness assumption**:
A restriction on which infinite behaviors the specification permits. Weak fairness (`WF`) rules out postponing an action forever while it stays enabled. Strong fairness (`SF`) also applies when the action becomes enabled infinitely often. The liveness result depends on the assumption in the specification.

**Deadlock**:
A model state with no step allowed by the next-state relation. TLC checks this by default, including at an intended end state. The built-in rule appears as `NoDeadlock`, or `CHECK_DEADLOCK` when a configured rule already uses that name. An explicit end-state action that leaves the variables unchanged gives the end state a valid step. `CHECK_DEADLOCK FALSE` disables this check.

Sources include [statechart](../../../skills/statechart/SKILL.md), the [configuration reader](../../../skills/statechart/scripts/frontends/config.ts), the [specification and rule reader](../../../skills/statechart/scripts/frontends/spec.ts), and the [generated models checked against TLC](../../../skills/statechart/scripts/test/differential.test.ts).

### Scope of the check

**Verdict run**:
A TLC run that checks configured rules. The first uses the configuration as written. After a failure, further runs can settle rules the first run did not reach.

**Drawing run**:
A separate exploration that collects states, steps, and violation marks for a chart within budget. It can continue past an invariant violation to show what happens next. A report can carry a confirmed violation even if the drawing run stops partway through.

**State constraint**:
A predicate named under `CONSTRAINT` that bounds exploration. TLC can check an invariant on a generated state outside the constraint, but does not explore its successors or check it for deadlock. The chart includes such a state if it ends a reported rule's shortest path.

**Action constraint**:
A predicate named under `ACTION_CONSTRAINT` that bounds which steps TLC follows. A rule can fail on the result of an excluded step even when another allowed step reaches that same state. The excluded step appears when it ends a reported failure path.

**TLC view**:
The `VIEW` in the TLC configuration that determines when TLC counts model states as the same. The checker retains one representative. An arrow can point to that representative even when the concrete step produced different variable values.
_Avoid_: view alone when it could also mean the chart's label module.

**Symmetry**:
A `SYMMETRY` in the TLC configuration that treats states related by the configured permutations as equivalent. TLC keeps a representative of each equivalence class. TLC's own output warns that symmetry can hide a liveness violation. [Symmetry and liveness example](../../../skills/statechart/scripts/test/corpus/PickWorker/verdict-1.out).

**Chart budget**:
The maximum of 500 distinct model states for drawing the whole graph. Above the budget, a chart can show just the bug paths. When no rule breaks, the report still records the check and state count, and the output has no chart file.

**Rerun bound**:
The limit of 100,000 distinct states on bounded verdict runs after a rule has broken. The driver removes known failures and checks the remaining rules. If the remaining exploration hits the bound or stops on an error, the report identifies each rule it could not check.

Sources include [statechart](../../../skills/statechart/SKILL.md), the [checking and drawing runs](../../../skills/statechart/scripts/run.ts), the [constraint and bound checks](../../../skills/statechart/scripts/test/plain-tlc.test.ts), and a [report with an excluded step](../../../skills/statechart/scripts/test/corpus/CounterDeadlock/report.md).

### Reader's view

**View module**:
The optional module passed with `--view`. Its `state(vars)` and `step(action, from, to)` answers supply the labels shared by the chart and report. It can also export `group(vars)`, `colors`, and `title`. With no custom labels the command uses the model values and TLC action names.

**Chart state**:
A label for one or more model states that the reader can treat alike. `state(vars)` receives the modeled variable values. A TLA+ sequence has keys starting at 1 and a set appears as an array. A label can name an observable condition such as "Waiting for payment".

**Flat chart**:
A chart with one level of states. A view's `state(vars)` returns one string for each model state.

**Parent state**:
A chart state that groups children. The view returns an array of names in order from parent to leaf. A path cannot identify both a leaf and its own parent. A common exit from every child can appear as one arrow from their parent.

**Parallel region**:
A named part of a chart whose state exists at the same time as the states in the other regions. The view returns an object with the same region names for each model state. Each region's value is a label or a path of parent and child labels. The driver draws the regions side by side only if their combinations of starts and moves match the model. Otherwise it draws parent states and the report gives the reason.

**Step label**:
The reader's description of an action between two states, returned by `step(action, from, to)`. Steps with the same endpoints can share an arrow. A label such as "the connection fails" can distinguish outcomes when the value that decides the next state is absent from the state label.

**Arrow condition**:
A condition shown in brackets on an arrow. A regions chart can derive a condition such as `[when Offline]` from the other regions' states. A bracketed condition supplied by the view takes the place of the generated one.

**Hidden step**:
A model step for which the view returns `null`. All steps represented by one arrow stay visible or are hidden together. The view preserves reachability, at least one exit wherever the model has one, the steps explaining a bug path, and exits from a counterexample loop. The report separately counts steps that stay within one chart label. In a single-region chart, such a step on a bug path can appear as a self-loop.

**Group**:
A phase named by `group(vars)` and assigned a color through `colors`. A chart state that combines model states from several groups has no group color. Rule marks have their own meaning in the legend.

Sources include [statechart](../../../skills/statechart/SKILL.md), the [view module contract](../../../skills/statechart/scripts/frontends/view.ts), the [state and step label rules](../../../skills/statechart/scripts/passes/label.ts), and the [chart behavior tests](../../../skills/statechart/scripts/test/chart.test.ts).

### Failures, marks, and reports

**Bug path**:
A numbered sequence from a model start to a demonstrated rule violation. For an invariant or a deadlock, a reconstructed path is a shortest path to a state that breaks that rule. A failure in an initial state takes zero steps. For a `PROPERTY`, the report gives TLC's counterexample, which can have a repeating part. A bug in the product also requires replay against the covered code. [Formal verification](../formal-verification/GLOSSARY.md#verification-tools-and-evidence).

**Counterexample loop**:
The part of a temporal counterexample that can repeat forever. Stuttering keeps the model in one state indefinitely. A looping run can instead revisit several states. In the chart, `bugPath` marks the approach to the violation and `repeats` marks the states in the repeating part.

**Rule mark**:
The class that indicates an invariant or deadlock violation on a chart state. `breaks` means at least one rule breaks in every model state behind the mark. With `mayBreak`, each implicated rule breaks in only some represented cases. The legend can combine rule names for several states. The report identifies the path to each violation.

**Region mark**:
A rule mark on a single region's state. The chart marks the region state when every reachable combination containing it can break a rule. If a failing combination would otherwise have no mark, all the states in that combination receive marks. A mark on one region can therefore depend on the other regions.

**Rule verdict**:
The result for one configured rule. A rule that `breaks` has a counterexample. `Rules that hold` lists the rules that TLC found to hold under the configuration. `Rules not checked` lists selected rules the runs could not settle. A liveness property may remain unchecked even when another rule has already produced a definite failure.

**Statechart report**:
The file `report.md` with model and chart counts, rule outcomes, numbered paths, and limits on what the drawing shows. `tlc.out` records TLC's output on the configuration as written. `tlc-RULE.out` preserves the checker's output for each broken property and for a broken rule whose counterexample the chart cannot show.

**Run exit status**:
The command's overall result. A completed run returns `0` when the configured rules hold or `1` when a rule breaks. A discovered violation keeps status `1` even if a later verdict run leaves other rules unchecked. A command or checking error can return `2`, and an interrupt or termination signal returns `130` or `143`. Only `0` and `1` publish the output files.

**Mermaid statechart**:
The `chart.mmd` drawing generated from the checked graph or the available bug paths. It carries the state and step labels, the rule marks, and their legend. Pele renders this Mermaid source to SVG for an image handoff.

Sources include the [command output contract](../../../skills/statechart/scripts/statechart.ts), the [report definitions](../../../skills/statechart/scripts/backends/report.ts), the [Mermaid output](../../../skills/statechart/scripts/backends/mermaid.ts), the [rendering reference](../../../skills/statechart/references/render.md), and the [example property report](../../../skills/statechart/scripts/test/corpus/MediaPlayerProps/report.md).
