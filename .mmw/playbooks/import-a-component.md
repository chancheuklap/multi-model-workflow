### Import a component

Import a pstack component only when the user names it: MMW takes pstack's components on demand, one at a time, and a component nobody named stays in `mmw-v2/upstream-pstack/`. The copy becomes MMW's own file, so each name in it that only pstack has is rewritten in place when it is imported, never explained by a table that every later reader has to look up.

1. **Pull the source.** Run **Pull an upstream** for `mmw-v2/upstream-pstack/`, so the component is copied from upstream's current text.
   Done when the subtree holds upstream's current `pstack/` directory, or the user has chosen to import from the commit it already pins.
2. **Pass the entry questions.** (judgement) Import the component only when every answer below allows it, and otherwise tell the user which answer stops it.
   - **A deliverable of its own.** Does it produce a deliverable you can name, and can it be used without the mode? If not, it is a playbook, and you import it with the type `playbook`.
   - **A way for every pstack name.** Does MMW have its own way to do what each name in it that only pstack has stands for (a tool, a setting, a control, a delivery or forge step, an alias, a skill not imported)? If one has none, do not import it.
   - **No pull request.** Does it depend on a pull request? MMW delivers changes without pull requests, so a component that does is not imported.
   - **No cross-vendor panel.** Does it depend on a panel of models from several vendors? Then first open a separate ticket that builds `dispatch.sh panel`, `panel-wait` and the panel roles in `models.json`, and import the component after that ticket lands.
   - **No re-reading from trunk.** Does it read itself again from trunk while it runs? Then do not import it, or drop that sentence from the copy as a judgement change.
   - **No name taken.** Does it share a name with an MMW skill, playbook or principle? The importer refuses a name that is taken: a same-name skill is not imported, because MMW's own skill already answers to that name, and a same-name playbook is merged into MMW's by hand as a judgement change.
   Done when the user has heard the answer to every question, and either every answer allows the import or the user knows which one stops it.
3. **Run the importer.** Run `python3 mmw-v2/import/import_component.py <type> <name>` in the main worktree. It copies a file component into the `mmw` skill, or gives a skill its `pstack/<name>` line in `mmw-v2/skills.txt`, and adds its row to `mmw-v2/skills/mmw/imports.tsv`. Before its last line, `IMPORTED <n>`, it prints a `NAME <file> <line> <name>` line for each name in the copied text that only pstack has, a skill the copy names but you did not import included. A refusal names what stopped the import; take the one next step it gives (**principle-refusals-name-one-next-step**).
   Done when it has exited 0 with `IMPORTED <n>` as its last line, and its `NAME` lines are kept for **Rewrite pstack names in place**.
4. **Rewrite pstack names in place.** (judgement) At each file and line a `NAME` line gives, rewrite that name in the copied file into the way MMW does the same thing; the subtree's own text never changes. Record each rewrite twice: at the start of the `judgement` column of that file's row in `mmw-v2/skills/mmw/imports.tsv`, as its number, and as a row of the `## 判断改动` table in `mmw-v2/merge-notes/pstack.md` (`编号`, `导入的文件`, `改了什么`, `为什么`), numbered after the highest `J<n>` already there. A name with no MMW way means the component fails **Pass the entry questions**: undo the import and tell the user.
   Done when no name a `NAME` line gave is left in its file, and each rewrite has its `imports.tsv` cell and its `## 判断改动` row.
5. **Register it.** Connect the component to the `mmw` skill where its type is reached from: a playbook gets a routing line, with its Distinct from, in `## Playbooks`, and a principle gets the index line its `INDEX` line carries, under the group that line names, in `## Principles`. The importer places a mode trigger or a mode section itself, and writes a skill's `pstack/<name>` line, with `+model-invoked` when the mode or a playbook names it.
   Done when the mode names every imported playbook and principle where its type is reached from, and a skill that the mode or a playbook names has `+model-invoked` on its `skills.txt` line.
6. **Prove the wiring.** Run `bash mmw-v2/tests/lib/run_shared_lints.sh`, which runs `check_wiring.py`, and `bash mmw-v2/install.sh --check`. Read the lines that name an imported file: a run that exits 0 still prints `report:` lines for the classes that only report, and one of them may be this import's broken connection (**principle-silence-is-never-a-pass**).
   Done when both exit 0 and no line either printed names a file this import wrote.
7. **Deliver.** Run **Deliver a change**. A skill the import added to `mmw-v2/skills.txt` reaches a host only in a new session.
   Done when the import is committed on `dev` and the user has heard how far **Deliver a change** took it.

**Reply:** the component's type and name; each file it wrote; each pstack name rewritten, with its `J<n>`; what still waits for the user.
