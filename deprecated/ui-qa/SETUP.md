# Setup mode

If any of the four criteria and wiring files from [SKILL.md](SKILL.md) step 3 is missing, read this file, create the missing ones, then return to step 5 and continue this run. If all four exist, do not read this file.

One missing file and four missing files take the same path. The questionnaire content differs.

## Intake questionnaire

**Ask only what this skill cannot look up, and only what an answer changes. Four questions, once.**

Do not ask what the skill can look up: whether a design-system file exists, which component specs it declares, how the app starts (scripts in the build config), usability requirements the user already stated in `grilling` and the spec.

**Prefill only from reading code.** The questionnaire runs at main-file step 4. The wiring file does not exist yet, so the app cannot start, so there is no screen map and no runtime element sizes.

| # | Ask | What the skill does first, so the user types less |
| --- | --- | --- |
| 1 | Who this product is for, and in which situations | Draft a paragraph from spec or shared understanding. The user edits |
| 2 | Is the start command right | Read candidate commands from the build config. The user confirms or edits |
| 3 | Where this product runs: a local server, or a test account on a real server | Cannot prefill. **Two options, no third** |
| 4 | How to prepare login and test data | Cannot prefill. If unanswered, record empty; unreached states go in the coverage report (main-file step 6) |

The Windows remote-debug port is not here. It has a working default and only matters on the Windows pass, so [WINDOWS.md](WINDOWS.md) asks it there, when it is about to be used.

Question 3 is the data-safety gate. After the product has landed, walkthrough tasks are full user paths and include at least one failure path — they really click, really create, really submit, really trigger errors. Local servers and test accounts are isolated from production data, so **there is no forbidden-action list, and no per-irreversible-action pause**.

**Show extracted usability criteria from shared understanding and spec once. Default: accept all. The user crosses out what they do not want.** Do not confirm item by item. Do not silently adopt — extract is model judgment, and a wrong item becomes a long-lived B5 criterion. Show extract results with the questionnaire. Do not add another interaction.

## Four missing files, four natures

| Missing | Nature | If the user refuses to create it |
| --- | --- | --- |
| Threshold table | Must create | **Stop.** A1 has no criteria |
| This product's usability criteria | Must create | **Stop.** B5 has no criteria |
| This product's wiring file | Must create | **Stop.** The app will not start. None of the nine checks can run |
| Design system | **Offer to create** | **Continue.** Skip A3 and B1. Run the other seven. The report header states why |

The design-system row is different: missing it drops two checks. Missing any of the first three stops the skill.

New cross-boundary files always write `"version": 1`. Fields and format are in [CRITERIA.md](CRITERIA.md) under "Fields of the three cross-boundary files".

## The design system is created by `create-design-md`

**Do not write it yourself.** DESIGN.md format is an upstream practice, and that skill is the one that knows it: it works from repository sources, and it will not return a file until both lint and export pass. Step 2 already required this capability; it is stop-level, so it is present here.

Hand it two things: the product id, and the intake answers.

**Use its repository mode.** Its other mode reconstructs a design system from a rendered page, and a value read off a rendered page is the current state, not the intended standard — a contrast failure that exists today would be written down as the rule, and A3 would then judge the interface against its own defect. Repository sources say what was intended; rendered pages only say what happened.

The same reasoning governs a DESIGN.md published by another company: read it as a model for how one is written, and hand it over as a model. It becomes criteria for this product only by passing lint with zero errors — published by a well-known company is not the same as correct, and renaming someone else's file is not authoring this product's.

After it returns a file, this skill does two things:

1. Lint it as main-file step 5 does, and handle the result the same way.
2. Write the path into wiring `designSystem`, **then read-only, never write it again**.

If `create-design-md` will not start or returns no file, **stop** and say the design system could not be created. Do not fall back to writing one yourself — two sources produce different DESIGN.md files, and this file is the criterion for A3 and B1. The next run would not match.
