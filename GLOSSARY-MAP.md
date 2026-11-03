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
- night is one unattended run. night branch is the branch that night lands on. project branch is the branch a delivery PR merges into. dev branch and main branch follow it. issue-N branch is the branch a Worker pushes. A command token NIGHT or PROJECT means the branch of that name.
- A sub-issue is the tracker's parent link. `mmw:child` is a label, not that link.
- A PR is the pull request a Worker opens for one ticket. A delivery PR is the night branch opened into the project branch.
- tracer bullet and vertical slice are both names for one ticket shape. Both stay.
- contract is promised behavior a caller or a test relies on. A sketch, a settled baseline, and the last step of expand-contract are not a contract. accepted baseline, smell baseline, measurement baseline, and settled baseline are different terms.
- product regression is broken app behavior found while maintaining a feature map. control skill is not a term. pinned comparison is the commit a review measures against.
- No ADR is current. `docs/adr/` was cleared. A new ADR is written only when a decision is hard to reverse, surprising without the record, and the result of a real trade-off.
