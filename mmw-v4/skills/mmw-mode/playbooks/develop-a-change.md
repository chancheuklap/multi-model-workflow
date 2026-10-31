### Develop a change

**You own the preparation, not the implementation. Turn one agreed change into an executable ticket or spec batch.**

Keep settled decisions and demonstrated behavior as baselines. Diagnose the current problem before choosing its repair. Settle the intended behavior before preparing its acceptance. Small changes can go straight to one ticket; the worker writes the implementation.

1. **Keep or open the record.** Read the goal, existing issue, effort branch, decisions and execution Go. Start at the first unfinished step. For a missing record or branch, read the **to-tickets** skill and follow **Open**, with `Playbook: Develop a change` for a new problem. Keep an existing Problem unchanged.
   Done when the record, working branch, scope and authority are identified, with sources for completed preparation.
2. **Establish the current behavior.** Read affected source and relevant ADRs per **principle-read-before-you-conclude**. Reuse the affected-feature result; when missing, read **maintain-verification-skill** and follow **Find affected features**. Fill only the missing evidence:

   | Missing result | Method |
   | --- | --- |
   | A reported defect's reproduction or confirmed cause | Read **bug-fix** and follow **Diagnose** |
   | A slowdown's workload, baseline or trace | Read **perf-issue** and follow **Diagnose** |
   | A subsystem model needed to explain or change behavior | Read and run **how** |
   | An original design rationale that determines the correct change | Read and run **why** |

   Done when the current behavior and any reported cause have source or runtime evidence. If the required observation cannot be obtained, return its concrete prerequisite and stop this preparation at this step. Keep completed reproductions and measurements.
3. **Settle what will change.** Reuse recorded answers and confirmed designs. Use only the method needed by an open question:

   | Open question | Method and return |
   | --- | --- |
   | Product behavior or scope | Follow Grill with docs (`playbooks/grill-with-docs.md`); return its decisions |
   | Appearance or interaction | Follow Design a UI (`playbooks/design-a-ui.md`); return its winner, feature description and non-UI questions |
   | Logic, an empirical choice or cross-ticket code shape | Read **prototype** and follow its applicable branch; return its verdict |
   | Decisions exceed one session | Read **wayfinder**; keep its fresh-session hand-back |

   Settle returned non-UI questions when this change depends on their data, rules, permissions, recovery, integration or performance. Read **domain-modeling** when terms or important decisions are being settled.
   Done when the next preparation has its required decisions and their sources. A task with no open decision continues. A pending owner decision or unfinished map returns its recorded continuation and stops here.
4. **Prepare the approach and size the work.** Apply **principle-start-from-what-exists** before choosing an implementation. Read the applicable skill and follow its preparation entry for the missing result:

   | Work in hand | Preparation result |
   | --- | --- |
   | An agreed repair | **bug-fix**: cause, repair plan, seam and original reproduction |
   | One performance change | **perf-issue**: traced change, target and comparison command |
   | Sustained metric improvement | **hillclimb**: frozen harness, baseline, stop predicate and hypotheses |
   | A behavior-preserving structural unit | **refactoring**: contract, pins or missing UI-pin requirements, and target shape |

   Combine methods within the agreed scope. Name blocking prerequisites, independent work, shared writes and verification boundaries, applying **principle-separate-before-serializing-shared-state**. One verifiable unit uses one independent ticket; coordinated units use a spec. A long investigation alone does not require a spec. One bug stays focused unless a larger change is separately agreed.
   Done when the approach, baselines, required proof and independent-ticket or spec choice are justified.
5. **Write the executable work.** For one change, read **to-tickets** and follow **Independent ticket**. For coordinated work, read **to-spec** to create or revise the spec, then **to-tickets**, **Batch**. Pass the decisions, method results, baselines and authority. Those writers finalize interfaces, obtain missing verification methods, prepare tests, lint, publish and read back; follow their actual instructions. Keep the one-spec-per-invocation stop. When a spec replaces the initial problem, close that problem with the spec link and retain its branch and assets.
   Done when the ticket or approved batch is published, or its writer has returned a concrete prerequisite or spec-division continuation.
6. **Return or hand over.** Return a requested missing preparation result to its caller. For the complete change, existing execution Go starts One ticket (`playbooks/one-ticket.md`) outside a spec, or Run a night (`playbooks/run-a-night.md`) for a spec batch, including one ticket. Without Go, put the prepared problem in `needs-triage` and return it for the owner's decision. The executor owns the rest of the delivery.
   Done when the caller has the result, the authorized executor has taken over, or the owner has the published preparation and outstanding decision.

**Reply:** the prepared work by name and link, what it delivers, its evidence and decision sources, the proof prepared, and its execution or waiting state.
