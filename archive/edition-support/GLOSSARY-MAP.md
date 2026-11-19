# Glossary Map

MMW is a set of skills that call one another. This map is the language of this repository. Each context has its own `GLOSSARY.md`. A term means what that file says.

Do not invent a Chinese name for an MMW skill or for any term in these files. Use the English name. The workflow entry for ticket names one forbidden Chinese word on its own line.

## Contexts

- [Workflow](docs/glossary/workflow/GLOSSARY.md): how a spec becomes tickets, how a run branches, and who holds the work.
- [Verification](docs/glossary/verification/GLOSSARY.md): the project-local skill that drives the real app, and the map of features it keeps.
- [Release](docs/glossary/release/GLOSSARY.md): how exe-release declares and ships one product's install package.
- [Architecture](docs/glossary/architecture/GLOSSARY.md): the deep-module vocabulary. codebase-dic is the source of these words.
- [Artifacts](docs/glossary/artifacts/GLOSSARY.md): the HTML and throwaway artifacts the skills keep distinct.
- [Language](docs/glossary/language/GLOSSARY.md): the glossary files, a context, and an ADR.
- [Skills](docs/glossary/skills/GLOSSARY.md): the English name of every skill in the cloud edition.

## Relationships

- A workflow ticket that changes a surface a person uses names a verification feature file and copies that surface's expected result.
- A wayfinder map is an issue labelled `mmw:map`. A feature map is the `features/` directory of `verify-<app>`. A glossary map is this file. The bare word map does not travel between those three.
- A decision ticket labelled `wayfinder:prototype` is resolved by the prototype skill, which builds a logic demo or a UI prototype. Prototype is the working-flow fidelity mode of html-prototype. Those are different terms.
- An architecture adapter sits at a seam. A seam is the public boundary you test at, and boundary is not its name. In release, the letters `adapter` appear in the filename `.release-adapter.json` and in the `--adapter` flag. Prose for that file is release manifest. Chinese words in exe-release script comments stay in Avoid.
- A spec is an issue labelled `mmw:spec`. Spec is also a review axis. They share a word and are different terms.
- `scripts/check` is the landing check. The pre-commit hook is the check that runs on a commit.
- night is one unattended run. Its night branch is named `night/spec-N` or `night/ticket-N`. The project branch is named `project/<project name>` and is cut from the dev branch. The issue-N branch is named `ticket/issue-N`. N is the issue number.
- A sub-issue is the tracker's parent link. `mmw:child` is a label, not that link.
- A card carries one assignment and its model settings from dispatch to the sender. The sender starts a **FRESH AGENT** with those settings and passes it the card's prompt.
- The first verifier opens its own cloud checkout at the Worker's assigned issue-N commit. The Coordinator stays on the night branch in its cloud agent. Standards, Spec, Tests, and the second verifier each open a new cloud checkout at the reviewed commit of that night branch and leave that temporary branch unpushed.
- A PR merges the issue-N branch into the night branch. A delivery PR merges the night branch into the project branch. A finished project branch merges into the dev branch for testing, and the dev branch merges into the main branch for deployment. The ticket head is the current commit on the issue-N branch. The role candidate is a brief session that designs one answer. The word candidate is not a name for that commit.
- A verifier runs `verify-<app>` on the commit it is given. Dispatch says when and how the three axes are sent. code-review says how each axis judges.
- tracer bullet and vertical slice are both names for one ticket shape. Both stay.
- contract is promised behavior a caller or a test relies on. A sketch, a settled baseline, and the last step of expand-contract are not a contract. accepted baseline, smell baseline, measurement baseline, and settled baseline are different terms.
- product regression is broken app behavior found while maintaining a feature map. control skill is not a term. pinned comparison is the commit a review measures against.
- No ADR is current. `docs/adr/` was cleared. A new ADR is written only when a decision is hard to reverse, surprising without the record, and the result of a real trade-off.
