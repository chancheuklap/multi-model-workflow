### Design a UI

**You own the current UI design, from its scope through the owner's confirmation of a runnable winner.**

Keep the caller's goal, issue, effort branch, settled answers and authority. Reuse a confirmed design. The prototype skill constructs or updates the pages; you own the owner interaction and the design result. A design-only request returns that result, not an implementation ticket. A development caller receives the result and continues its original preparation.

1. **Read the design scope.** Keep the supplied issue, effort branch, settled decisions and affected-feature result. For a direct design request without its preparation record or effort branch, use the **to-tickets** skill's **Open the preparation record** entry with Playbook: Design a UI and this request's design goal. Reuse an existing record and create only its missing effort branch. Work there before writing durable design assets; opening the record does not authorize implementation. If existing product behavior is relevant and its affected-feature result is absent, call the **maintain-verification-skill** skill's **Find affected features** entry. Return here with the named features and baseline paths. With no verify skill, continue from the actual product and sources rather than starting whole-product maintenance.
   Done when the current UI question and the existing behavior it must preserve are known.

2. **Build or update the runnable UI.** Call the **prototype** skill's UI construction entry, including **Prepare the local product** in references/UI.md. Supply the current question, scope, checkout and previous candidate or winner. Read its runnable result and give the owner the launch or page to operate.
   Done when the owner can operate the current alternatives or the selected design.

3. **Iterate with the owner.**

   Give the owner the URL and variant keys. The owner operates the page, chooses a direction or combination, and gives feedback. Do not choose or accept it for them. Have the prototype skill's UI entry fuse the selected parts into `winner/`, retaining `candidates/<n>/` for reference. Post arena's synthesis note as a comment on the ticket that asked the question; with no ticket, the reply carries it.

   Once the direction is settled, work one to one with the owner. Ask one question per round, use the prototype skill's UI entry to edit the same prototype in place, and commit each round. Do not send a worker or reviewer. Do not generate a whole new set of designs. If one component remains uncertain, use a small arena just for it.

   Go through every API fake call and list where each button connects. Identify what the prototype cannot answer behind that interface: data and storage, interface fields and errors, business rules, permissions and security, failure and recovery, external systems, scale and performance, account or key preparation, and Electron native behavior. Settle these through the relevant grilling, domain-modeling, research, the prototype skill's LOGIC or EXP method, not from the UI alone.

   Settle questions that change the UI during iteration and update the prototype with the answers. On the map route, open decision tickets under the map. Outside a map, record the owner's answers on the existing ticket, then make each an item under **What to build** when writing the ticket. Record owner decisions in those tickets, not a separate design-decision log. Questions that do not affect the UI can wait until after design freeze.


   Done when the owner has chosen the direction, the winner reflects the iteration's answers, and every button's connection and UI-affecting decision is accounted for, or the existing record identifies the pending owner response. Resume that record and prototype after a pause.

4. **Reconcile the visible decisions.**

   1. Merge the latest project-branch code so the prototype runs on the current product.
   2. Read every closed decision and compare its visible rules with the prototype. On the map route, read the map's closed child tickets. Outside a map, read the owner's answers on the ticket and its cited specification sections. List what is displayed or marked, who sees each button, and what errors say. Find each rule in the prototype and add missing ones. Give states that actions cannot create, such as concurrent-save conflicts, a state URL. Leave invisible storage and computation rules for the spec.

   3. When the sources disagree, decisions govern rules, the glossary governs names, and the prototype governs appearance and interaction. Fix a prototype that lags behind decisions or the glossary. Settle unrecorded questions that change the UI by the iteration rules above, then update the prototype. Do not ask the owner to reconcile the written sources.

   Done when the current winner runs on the latest project code and demonstrates each settled visible rule; the caller has the questions that only backend work can answer.

5. **Capture design freeze.**

   1. Write the feature file's account of what the product can do with the **create-verification-skill** skill's `## 3. Seed the feature map`. Every sentence has a source in the winner, closed decisions, or glossary `CONTEXT.md`, and describes behavior the prototype demonstrates. Use the product UI's language, retaining the format's English headings.

   2. The owner says "That's it" on the real page. This is design freeze, the single approval of the prototype. Do not ask them to approve the feature file's sentences too.
   3. Commit that part of the feature file before writing tests. Only the environment tools, mount point, and prototype precede it on the effort branch.


   Done when the owner has approved the running winner and the feature description is committed on the effort branch before tests.

6. **Return the design.**

   The UI conclusion lives in the feature file. Hand back the winner's exact path and the feature file. The interface contract starts from the API fake and is finalized during spec or independent-ticket preparation. Once finalized, update the API fake to match it before writing tests.

   Keep the mount points until implementation. The final ticket removes them after all slice tickets. For a single ticket, removal is its last commit. In an effort with multiple specs, a later spec's mount points may enter the project branch with an earlier PR and stay until that spec lands. Tests use the same steps and assertions for the normal launch and the launch with the prototype variable. Removing a mount point reveals the product page without changing tests.



   Done when the caller has the winner, feature paths and decisions with any remaining non-UI preparation. Only an already authorized development request continues through Develop a change; this playbook does not write implementation tickets or start workers.

**Reply:** the runnable checkout and page, the confirmed winner or pending owner response, the source feature paths, what changed in this round and the design result returned to the caller.
