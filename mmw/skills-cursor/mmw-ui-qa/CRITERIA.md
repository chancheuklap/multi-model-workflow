# Criteria and check details

How each check judges, where its criteria come from, and how the probe collects what they judge. Creating missing criteria is in [SETUP.md](SETUP.md).

## Five kinds of criteria, five producers

The "Criteria from" column of the nine-check table in [SKILL.md](SKILL.md) says which check reads which kind. This table adds the part that table does not carry: who produces each kind, and in what shape.

| Criteria | Shape | Who produces |
| --- | --- | --- |
| Threshold table | JSON, one per repo | UI QA. Intake questionnaire creates it; verdicts append |
| Usability criteria | Markdown, one per product | UI QA. Questionnaire, extract from shared understanding and spec, verdict flow-back |
| Design system | DESIGN.md-format file | **Target repo**. This skill reads only |
| Accessibility rules | Engine's own set | The engine |
| Method criteria | Body of [SEMANTIC.md](SEMANTIC.md) | This skill |

Method criteria are not target-repo config. Every repo with MMW has them.

**The design system is a read-only boundary.** UI QA reads it, the target repo owns it, and the one exception is creating it once when it is missing ([SETUP.md](SETUP.md)).

The design system uses **DESIGN.md format** — one Markdown file, YAML frontmatter for machine-readable tokens (`colors`, `typography`, `rounded`, `spacing`, `components`), body for named rules and Do's/Don'ts. A3 judges the former. B1 judges the latter.

## A3 judges the declaration layer

The design-system file is the **declaration** (written intent). Runtime CSS variables are the **implementation** (what actually applies). **A3 judges the declaration:** is the element's value in the declared set. It does not judge the implementation.

**Still read the implementation, to test whether the criteria are trustworthy.** Compare the two key/value sets:

| Compare | Action |
| --- | --- |
| Implementation has it, declaration does not | Undeclared token. One report item **per token, not per element that uses it**. Elements that use it also fail A3, because they are outside the declared set |
| Declaration has it, implementation does not | Stale declaration. One report item |

**On the first "implementation has it, declaration does not", the report must say "A3 results may be distorted".** That class flips A3. The other class (declaration without implementation) does not flip A3. Report it, and leave that sentence out.

Show the split to the user, so the criteria source stays visible. Also suggest: the target repo should emit CSS variables from design-system tokens at build time. **A suggestion only. The target repo's build stays as it is.**

## A2 coverage

The rules are the engine's own set. Its declared scope is the `purpose` field of the `accessibility` capability in the runtime dependency declaration — read it there, so an engine swap does not leave a stale list here.

**It does not verify actual keyboard traversal order.** The engine rule with the same name as focus order is experimental, off by default, and only checks that elements already in the focus sequence have roles fit for interactive content. It does not track the order Tab actually walks. **The report must say this**, so the user knows focus order was left uncovered.

## What the probe collects

Step 6 of [SKILL.md](SKILL.md) runs the nine checks against this data. Four sources, all from one browser session driven by `mmw-ui-qa browser`:

| Input | How | Feeds |
| --- | --- | --- |
| Accessibility-tree snapshot | ARIA snapshot from the browser automation | Element location; all of class B |
| Computed style and layout box | Batch `getComputedStyle` and `getBoundingClientRect` on candidates | A1, A3 |
| Runtime CSS custom properties | `getComputedStyle(document.documentElement)` | A3 implementation-layer compare |
| Renderer console | Listen for console and page error | A4 |

**A2:** `mmw-ui-qa accessibility-source` prints the absolute path of the engine's inject script. Inject the whole file, call the engine's analyze entry, and each violation is one A2.

To `require` the browser automation from a Node script, the module root is `mmw-ui-qa home`.

**Five numeric fields** (used by `interactive elements` and B2 question 2):

| Field | How |
| --- | --- |
| In first screen | Element `getBoundingClientRect` intersects the viewport |
| Size | `getBoundingClientRect` width and height, px |
| Contrast | WCAG contrast of foreground against actual background |
| Occluded | `elementFromPoint` at the element's center is not the element and not a descendant |
| Stacking | `z-index` of the first ancestor that forms a stacking context |

## The three cross-boundary files

All three carry an integer `version`. Format changes use it to recognize an old file and explain, not to silently misread. The screen map is not in this set — it is in-process and does not cross a boundary.

**The version this skill knows is `1`.** Greater than 1: stop, and say a newer skill wrote the file. Less than 1: read as 1, and leave one report line. Corrupt or not JSON: stop, print the parser's raw error, and leave the file alone.

**Unknown content follows the consumer-behavior table in the design-system format spec.** Keep unknown sections, no error; accept unknown keys when the value is valid; accept unknown attributes and leave one report line; duplicate same-named sections error and reject the file. These four are that spec's consumer behavior, not ours.

### Wiring file · owned by the target repo

**Field names, types, required conditions and value shapes live in `wiring.schema.json`, next to the linter that reads it.** `mmw-ui-qa wiring-lint` judges a wiring file against it, and `mmw-ui-qa preflight <product-id>` runs that for you (step 3 of [SKILL.md](SKILL.md)).

Two things the linter cannot decide, so they live here:

- **A missing `designSystem` costs two checks.** Skip A3 and B1, run the other seven, and say so in the report header. Every other required field missing is a stop — the app will not start.
- **`environment.kind` has two values and no third.** A prototype mockup is still a local server: write `local-server`. Questionnaire question 5 always asks, two options only.

**Secrets are refs, never plaintext.** The linter rejects any other shape, which is why it runs before the app starts: a wiring file with a plaintext password in it must not reach a running session.

### Threshold table · owned by UI QA

One per repo. Besides `version`, the top level is a map of threshold items. Each item has four fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `value` | number | yes | Threshold |
| `unit` | enum | yes | `px` or `ratio`. No unitless number |
| `appliesTo` | enum | yes | `interactive` or `presentational` |
| `compare` | enum | yes | `min` or `max` |

The last two are required. `appliesTo` splits clickable from presentational. `compare` is the direction.

**Setup mode must create these three keys.** Names are fixed. A1 looks them up by name:

| Key | Judges | Generic floor | `unit` | `appliesTo` | `compare` |
| --- | --- | --- | --- | --- | --- |
| `minTargetHeight` | Clickable height | 24 | `px` | `interactive` | `min` |
| `minTargetWidth` | Clickable width | 24 | `px` | `interactive` | `min` |
| `minBodyFontSize` | Body font size | 12 | `px` | `presentational` | `min` |

**Contrast belongs to A2, not to this table.** The engine already has WCAG's two contrast rules. A second copy here would report the same element twice. When the engine is missing and A2 is skipped, contrast stays out of this table too — the report header already says contrast was not checked this run.

The "generic floor" column is the compare baseline when scanning candidates in questionnaire question 3, and the fallback when the target repo has no matching spec. **When a spec exists, use the spec, not this column.**

Component specs live in design-system frontmatter `components`, or size constants in component source. If neither has it, use the generic floor, and tell the user at setup which source each of the three used.

A user-requested fourth item uses the same four fields (`compare: max` is for those). A1 treats every top-level item the same. There is no whitelist beyond these three keys.

### Usability criteria · owned by UI QA

One Markdown file per product. `version` is in YAML frontmatter — people read this file, criteria are prose, the machine only needs version and per-item splits:

```markdown
---
version: 1
product: <product-id>
---

## U-001

Body: <criterion text>
Source: <which discussion, spec, or UI QA run>
Status: confirmed
```

One criterion per level-2 heading. The heading is the id. Six fields per item:

| Field | Required | Content |
| --- | --- | --- |
| Id | yes | Level-2 heading. Shape `U-001`, increasing at create time. Deleted ids are not reused |
| Body | yes | Criterion text |
| Source | yes | Which discussion, spec, or UI QA run |
| Status | yes | `confirmed`, `rejected`, or `waived` — the user verdict |
| Fingerprint | required on items created from a verdict | One of the four shapes in [VERDICTS.md](VERDICTS.md). This skill generates it |
| Last hit | required on items created from a verdict | Date this item last matched at level 1 or level 2 |

**B5 judges `confirmed` items only.** The other two statuses stay in the file for two-level matching. They do not judge.
