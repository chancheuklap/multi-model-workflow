# Setup mode

If any of the four criteria and wiring files from [SKILL.md](SKILL.md) step 3 is missing, read this file, create the missing ones, then return to step 5 and continue this run. If all four exist, do not read this file.

One missing file and four missing files take the same path. The questionnaire content differs.

## Intake questionnaire

**Ask only what this skill cannot look up. Seven questions, once.**

Do not ask what the skill can look up: whether a design-system file exists, which component specs it declares, how the app starts (scripts in the build config), usability requirements the user already stated in `/mmw-grilling` and the spec.

**Prefill only from reading code.** The questionnaire runs at main-file step 4. The wiring file does not exist yet, so the app cannot start, so there is no screen map and no runtime element sizes — questions 2 and 3 prefill from source only.

| # | Ask | What the skill does first, so the user types less |
| --- | --- | --- |
| 1 | Who this product is for, and in which situations | Draft a paragraph from spec or shared understanding. The user edits |
| 2 | Which flows are core | Read routes and state machines, list jump chains from the entry route. The user picks |
| 3 | Which elements are intentionally small and presentational | Read design-system frontmatter `components` and size constants in component source. List components below the generic floor. The user ticks |
| 4 | Is the start command right | Read candidate commands from the build config. The user confirms or edits |
| 5 | Where this product runs: a local server, or a test account on a real server | Cannot prefill. **Two options, no third** |
| 6 | How to prepare login and test data | Cannot prefill. If unanswered, record empty; unreached states go in the coverage report (main-file step 6) |
| 7 | Windows remote-debug port | Default `9222`. The user edits or leaves it |

Question 5 is the data-safety gate. After the product has landed, walkthrough tasks are full user paths and include at least one failure path — they really click, really create, really submit, really trigger errors. Local servers and test accounts are isolated from production data, so **there is no forbidden-action list, and no per-irreversible-action pause**.

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

## The design system is created by `/impeccable`

**Do not write it yourself.** DESIGN.md format is an upstream practice. The `document` flow covers scanning existing tokens, components, and render output, then confirming descriptive language. Step 2 already required this dependency; it is stop-level, so it is present here.

Hand it three things: the product id, the intake answers, and **do not extract current values from a running page** — that reverse-extracts current defects into the standard.

After it returns a file, this skill does two things:

1. Lint with `mmw-ui-qa design-lint <file>`. Handle the result as main-file step 5.
2. Write the path into wiring `designSystem`, **then read-only, never write it again**.

If `/impeccable` will not start or returns no file, **stop** and say the design system could not be created. Do not fall back to writing one yourself — two sources produce different DESIGN.md files, and this file is the criterion for A3 and B1. The next run would not match.
