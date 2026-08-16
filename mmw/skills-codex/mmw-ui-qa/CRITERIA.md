# Criteria and check details

How each check judges, where its criteria come from, and the fields of the three cross-boundary files. Creating missing criteria is in [SETUP.md](SETUP.md).

## Five kinds of criteria, five producers

| # | Criteria | Shape | Who produces | Feeds |
| --- | --- | --- | --- | --- |
| 1 | Threshold table | JSON, one per repo | UI QA. Intake questionnaire creates it; verdicts append | A1 |
| 2 | Usability criteria | Markdown, one per product | UI QA. Questionnaire, extract from shared understanding and spec, verdict flow-back | B5 |
| 3 | Design system | DESIGN.md-format file | **Target repo**. This skill reads only | A3, B1 |
| 4 | Accessibility rules | Engine's own set | The engine | A2 |
| 5 | Method criteria | Body of [SEMANTIC.md](SEMANTIC.md) | This skill | B2, B3, B4 |

Kind 5 is not target-repo config. Every repo with MMW has it.

**The design system is a read-only boundary.** UI QA reads it, does not write it, and the target repo owns it. The only exception is creating it once when it is missing. See below.

The design system uses **DESIGN.md format** — one Markdown file, YAML frontmatter for machine-readable tokens (`colors`, `typography`, `rounded`, `spacing`, `components`), body for named rules and Do's/Don'ts. A3 judges the former. B1 judges the latter. Lint command: `mmw-ui-qa design-lint <file>`. `mmw-ui-qa check` prints this linter's actual package name and version.

## A3 judges the declaration layer

The design-system file is the **declaration** (written intent). Runtime CSS variables are the **implementation** (what actually applies). **A3 judges the declaration:** is the element's value in the declared set. It does not judge the implementation.

**Still read the implementation, to test whether the criteria are trustworthy.** Compare the two key/value sets:

| Compare | Action |
| --- | --- |
| Implementation has it, declaration does not | Undeclared token. One report item **per token, not per element that uses it**. Elements that use it also fail A3, because they are outside the declared set |
| Declaration has it, implementation does not | Stale declaration. One report item |

**On the first "implementation has it, declaration does not", the report must say "A3 results may be distorted".** That class flips A3. The other class (declaration without implementation) does not flip A3. Report it. Do not add that sentence.

Show the split to the user. Do not silently switch criteria source. Also suggest: the target repo should emit CSS variables from design-system tokens at build time. **A suggestion only. Do not change the target repo's build.**

## A2 coverage

The engine covers contrast, ARIA misuse, missing label, missing alt, `tabindex` values, focusable `aria-hidden` elements, nested interactive controls, scroll-region access, skip links.

**It does not verify actual keyboard traversal order.** The engine rule with the same name as focus order is experimental, off by default, and only checks that elements already in the focus sequence have roles fit for interactive content. It does not track the order Tab actually walks. **The report must say this.** Do not let the user think focus order was covered.

## Fields of the three cross-boundary files

All three must have integer `version`. Format changes use it to recognize an old file and explain, not to silently misread. The screen map is not in this set — it is in-process and does not cross a boundary.

**The version this skill knows is `1`.** All three use that value. Greater than 1: stop, and say a newer skill wrote the file. Less than 1: read as 1, and leave one report line. Corrupt or not JSON: stop, print the parser's raw error, do not guess.

**Unknown content follows the consumer-behavior table in the design-system format spec.** Do not invent another: keep unknown sections, no error; accept unknown keys when the value is valid; accept unknown attributes and leave one report line; duplicate same-named sections error and reject the file. These four are that spec's consumer behavior, not ours.

### Wiring file · owned by the target repo

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `version` | integer | yes | Format version |
| `product` | string | yes | Product id. Lowercase letters, digits, hyphens. Matches the usability-criteria filename |
| `launch` | object | yes | Below |
| `mainWindow` | object | yes | Below |
| `environment` | object | yes | Below |
| `prepare` | object | no | Below. If missing, related states go in the coverage report |
| `designSystem` | string | no | Repo-relative path of the design-system file. If missing, skip A3 and B1 |
| `windows` | object | no | Below. Required only when running on Windows |

Inner fields:

| Object | Field | Type | Required | Notes |
| --- | --- | --- | --- | --- |
| `launch` | `command` | string array | yes | Start command and args, one element per item, not one line to parse |
| `launch` | `cwd` | string | no | Repo-relative. Default: repo root |
| `launch` | `env` | string-to-string map | no | Start env. Values may be secret refs |
| `launch` | `readyTimeoutMs` | integer | no | Wait for the main window. Default 30000 |
| `mainWindow` | `titlePattern` | string | one of two required | Regex on window title |
| `mainWindow` | `urlPattern` | string | one of two required | Regex on renderer URL |
| `environment` | `kind` | enum | yes | `local-server` or `test-account` |
| `environment` | `endpoint` | string | yes | Local server URL, or real server URL |
| `environment` | `account` | object | required when `kind` is `test-account` | `id` (string, test-account id) and `secret` (string, secret ref, format below) |
| `prepare` | `steps` | object array | no | Each item has `name` and `command` (string array), in order |
| `windows` | `debugPort` | integer | yes | Remote debug port. Questionnaire question 7 defaults to `9222` |
| `windows` | `host` | string | no | Default `127.0.0.1` |

Missing `environment`, or `kind` not one of those two: **stop and explain**. Do not guess. No exemption: questionnaire question 5 always asks, two options only. A prototype mockup is still a local server — write `local-server`.

**Secrets are refs, never plaintext.** A ref is a fixed prefix plus a name: `env:<env-var>` or `keychain:<entry>`. Resolve by prefix at run time. **Any other shape is plaintext: refuse it and stop.** Missing required fields: stop and explain. Do not fill defaults.

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

**Contrast is not in this table.** It belongs to A2 — the engine already has WCAG's two contrast rules, first item in "A2 coverage" above. A second copy in this table would report the same element twice. When the engine is missing and A2 is skipped, do not add contrast here either — the report header already says contrast was not checked this run.

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
