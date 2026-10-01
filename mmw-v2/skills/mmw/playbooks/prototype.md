### Prototype

**You own the design decision, not the code.**

This playbook settles a question only something built and run can answer: a state model, what a UI looks like, whether a library or an approach works. Its verdict in the leaf `README.md` is what a spec cites, what a ticket copies exact values from, and what a worker builds from at night with no one to ask. The temptation is to start building before the decision is named; a prototype without one has nothing to answer, and variants that differ only in colour or copy have nothing to compare, so name the decision first.

**Entry.**
- **A question to run.** A question the mode routes here, a runnable question from **Settle runnable questions** in **Write a spec and tickets**, or a `prototype` ticket on a wayfinder map starts at **Scope the decision**.
- **Another round.** A question whose leaf `README.md` already exists starts at **Build and observe it**, and iterates that leaf directory instead of starting over.
- **Unattended.** This playbook runs with the user present. An unattended session that reaches it records the product question where its role records a decision (mode `## Autonomy`) and stops.

1. **Scope the decision.** (judgement) Name the decision the prototype exists to make: which layout, which interaction, which density, or for an empirical fork which behavior, timing, or approach. No decision means no prototype. Route to **Write a spec and tickets**.
   Done when the decision is written down as one question the prototype will answer, or the work has gone to **Write a spec and tickets** because there is no decision to make.
2. **Pick the branch.** Pick the branch the question needs by the `prototype` skill's `## Pick a branch`.
   Done when one branch is chosen, and the user has confirmed it or the prototype states it as an assumption at its top.
3. **Build and observe it.** Build it with the file the `prototype` skill gives that branch, in a leaf directory and under that skill's `## Rules that apply to every branch`. Run it, and look at the state it surfaces for every variant or case before you show it to anyone.
   Done when the prototype starts from one command or opens as one file in its leaf directory, the leaf `README.md` states the question, and you have seen every variant or case run.
4. **Present the alternatives.** Present alternatives, tradeoffs, and a recommendation. The output is the decision plus the prototype in its leaf directory, not shippable code. Show each alternative running, the way that branch's file of the `prototype` skill hands it over; a request for another variant or case goes back to **Build and observe it**.
   Done when the user has chosen one direction from the alternatives.
5. **Hand the answer on.** Record the verdict and the question it settled in the leaf `README.md`, as the `prototype` skill's **Record the answer, keep the prototype** says. Hand the chosen direction on for the real build:
   - On a wayfinder map, a `prototype` ticket's verdict goes back to **Resolve one decision ticket at a time** in **Map a large effort**, which records the resolution.
   - A UI prototype's winner goes into Claude Design through **Design a UI**.
   - A LOGIC or EXP verdict goes to **Write the spec** in **Write a spec and tickets**, or to **Make a small change** when the user will check the change directly.
   Done when the leaf `README.md` states the verdict with its exact names and values, and the session has gone on to the step or playbook its case names.

**Reply:** the variants explored, the evidence (screenshots for a visual decision, the observed output or timing for a behavioral one), tradeoffs, your recommendation, the leaf directory, and the step or playbook the answer went to.
