# Performance

The performance playbooks diagnose live or recorded behavior, measure a change against a baseline, and decide which experimental changes to keep.

## Language

### Diagnosing a capture

**Runtime forensics**:
Diagnosis of a symptom in a running process. The investigator captures a signal on the affected surface, tests the suspected mechanism in the live process, and identifies the source location. An idle CPU spin, for example, calls for a profile that shows the loop and a live check that confirms what schedules it.

**Trace forensics**:
Diagnosis from a capture that already exists. The investigator treats the artifact as a fixed dataset and queries its samples, frames, or nodes to locate the cause. With a single capture, the report names the strongest hypothesis the artifact supports.

**Reduced finding**:
The specific observation extracted from a capture that bears on the symptom. It might be a call path that accounts for most CPU samples, the chain of references keeping a leaked object reachable, or the reason a blocked thread is waiting.

**Source attribution**:
The link from the reduced finding to a file, symbol, and line in the affected code. A hot frame with unresolved symbols leaves that part of the diagnosis open.

**Paired capture**:
A before-and-after pair of artifacts whose difference can confirm the diagnosis. The report identifies both artifacts and states whether the comparison confirmed the suspected cause.

[Runtime forensics playbook](../../../skills/poteto-mode/playbooks/runtime-forensics.md) · [Trace forensics playbook](../../../skills/poteto-mode/playbooks/trace-forensics.md)

### Benchmark claims

**Measurement baseline**:
The starting measurement used to judge a change, such as the time a request takes on the existing version.
_Avoid_: baseline alone when it could mean either a settled decision or the starting point for a comparison.

Related terms are the [settled baseline](../engineering-design/GLOSSARY.md#engineering-decisions) and the [verification baseline](../product-verification/GLOSSARY.md#claims-and-verdicts).

**Perf issue**:
A one-off fix for measured slowness. A baseline trace identifies where time goes. A post-fix trace on the same surface shows the new value and its difference from the baseline. The report includes the artifact path.

**Performance claim**:
The sentence a benchmark is intended to test. It identifies the operation, workload, metric, and comparison closely enough for the result to change a decision. For example, the claim can concern median export time on a specified dataset.

**Ballpark**:
An explicitly requested rough measurement. It can use a single run when the report says so and checks the outputs, errors, and work completed. A decision about which option to adopt requires a comparison.

**Limiter**:
The resource or code path that bounds the measured result under the stated conditions. Under *Explain the Number*, a separate profiling run or system counters identify the limiter. If the load generator saturates first, the number measures the generator's capacity.

**Untuned side**:
A benchmark option whose settings still limit it under the workload, such as a debug build or a commit per row. A comparison for an adoption decision needs each option configured for production, including its actual cache state, before it can name a winner.

**Performance ceiling**:
A bound on the possible result from the available resources or the time the changed step originally consumed. For example, removing a step that took 10 ms in a 100 ms operation can save at most 10 ms. A larger reported saving requires an explanation of what the comparison measured.

**Error count**:
The number of failures or non-success responses during the run. The benchmark also checks the returned values. A fast rejection and a successful operation have different meanings even if both produce a response.

**Work count**:
A count of the intended work that actually completed inside the timed region, such as rows written or bytes read. It can expose an unconsumed result, a skipped path, or an operation that continued after timing stopped.

**Noise floor**:
The run-to-run variation that a claimed effect must exceed. The standard benchmark comparison alternates the two sides, measures each at least five times, and reports the median and range.

**Micro result**:
The measured change in one component of a user operation. The benchmark reports that component's share of the whole and measures the path a user actually waits for with realistic data and concurrency.

**Benchmark verdict**:
The conclusion a run supports. *Faster* and *slower* identify a measurable difference. *No measurable difference* means the gap falls within the observed run-to-run variation. *Inconclusive* means the comparison cannot support the claim, for example because a claimed difference has no identified limiter, one side ran untuned, or the run could not establish whether the intended work succeeded and took place.

[Perf issue playbook](../../../skills/poteto-mode/playbooks/perf-issue.md) · [benchmark-checklist](../../../skills/benchmark-checklist/SKILL.md) · [principle-explain-the-number](../../../skills/principle-explain-the-number/SKILL.md) · [Hillclimb playbook](../../../skills/poteto-mode/playbooks/hillclimb.md)

### Hillclimb experiments

**Hillclimb**:
A sequence of controlled attempts to improve one metric in a declared direction. The starting workload reproduces the operator's complaint. Each attempt tests one change against the same measurement and correctness checks.

**Target workload**:
The realistic combination of data size, history, state, and concurrency that reproduces the reported symptom. Easier comparison cases help establish whether the chosen metric can distinguish that workload.

**Frozen measurement harness**:
The repeatable measurement used for every attempt after its sensitivity has been demonstrated on contrasting workloads. It reports the metric from repeated samples, the error count, and the count of work done.

**Regression gate**:
The tests that must pass at baseline and after each experimental change. A faster result that breaks required behavior fails the gate.

**Stop predicate**:
The hillclimb's checkable target together with a minimum number of attempts. Meeting the target on the first attempt cannot satisfy a higher attempt floor. The playbook also permits ending a run when the remaining ideas would cost more than their marginal benefit.

**Performance mantras**:
The order in which the playbooks consider ways to improve performance. First eliminate unused work, then avoid repeating it, do less of it, defer it, move it outside the user's wait, run it concurrently, or make it cheaper. Perf issue stops once the target is met. A performance hillclimb uses the same order and its own stop predicate.

**Hillclimb iteration**:
One hypothesis about a specific mechanism, one change, a before-and-after measurement, a regression-gate result, and a decision to keep or revert the change. A performance win must exceed noise and preserve behavior. A simplification that holds the number can also be kept.

**Hillclimb decision log**:
The experiment's record of one row per attempt, including its hypothesis, change, before and after values, delta, test result, kept or reverted verdict, and note. Later attempts can consult the record of rejected changes. The general decision trail records one row per decision. [Decision trail](../unattended-runs/GLOSSARY.md#the-decision-trail).

**Plateau**:
A run of rejected attempts. It prompts another look at the source, a change of hypothesis category, or a combination of near misses before the remaining ideas are judged too costly.

[Hillclimb playbook](../../../skills/poteto-mode/playbooks/hillclimb.md) · [benchmark-checklist](../../../skills/benchmark-checklist/SKILL.md) · [Perf issue playbook](../../../skills/poteto-mode/playbooks/perf-issue.md)
