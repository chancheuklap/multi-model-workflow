### Grill with docs

**You own the interview and the glossary and ADRs it writes.**

A relentless interview to sharpen a plan or design, which also creates docs (ADRs and glossary) as we go.

1. **Interview.** Use the **grilling** skill and the **domain-modeling** skill. Done when every branch of the plan the user brought has been walked to a decision or to one of the forks of step 2.
2. **Route each fork by whose decision it is.** Put to the user only what is theirs: what the user sees, what happens to money, what is in scope. A fact goes to the Investigation playbook (`playbooks/investigation.md`). An answer you could observe by running something goes to the **prototype** skill, and so does a question of what shape the code should take, which its sketch branch settles when that branch's conditions hold; the user is not asked either. Done when every fork is either answered by the user, or settled by the investigation or prototype it was handed to.
3. **Write the docs as you go.** Write each resolved term into the glossary as it resolves, and offer an ADR as the **domain-modeling** skill describes. These writes are part of the session, not the acting on it that **grilling** holds back. Done when every term resolved in this session is in the glossary and every hard-to-reverse decision has an ADR or the user declined one.
4. **Watch the size.** When the plan turns out too big to settle in one session, propose switching to the Chart the map playbook (`playbooks/chart-the-map.md`); the user decides. Done when the plan fits this session, or the user has chosen to keep going or to chart a map.
5. **Hand back to whoever opened it.** Opened from a grilling ticket on a wayfinder map, the decisions go back to that map: Work through the map (`playbooks/work-through-the-map.md`) records them. Opened by the user directly, go on to step 6. Done when the map's ticket has its resolution, or this session is the user's own.
6. **Name the next step.** When the session settles a change that takes more than one session to build, the next step is the To spec playbook (`playbooks/to-spec.md`), in this same session. When one session can build it, give the user two options: build it now from this conversation, or stop here with the decisions recorded. Done when the user has the next step, or both options.

**Reply:** the decisions reached; each glossary term and ADR written, by name; whether the prototype skill's sketch branch ran or was skipped, and why; the next step, or the two options.
