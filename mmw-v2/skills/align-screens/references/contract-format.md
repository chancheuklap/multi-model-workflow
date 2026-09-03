# The screen contract file

`docs/specs/<effort>/screen-contract.yaml`. One file per effort, read by `to-spec`, `to-tickets`, `implement`, `code-review` and the lint. YAML, because a linter reads it more often than a person does.

## Top level

```yaml
effort: chameleon-s3                      # the wayfinder map's title, as in docs/specs/<effort>/
baselines:
  look: docs/prototypes/<task>/claude-design   # the handoff package directory, unchanged
  precedence: "look & verbatim copy -> handoff package; calls, shows, next, on_failure, timing -> this file"
mechanisms:                               # the spec's mechanism registry, copied here so reach can be linted
  - seed:project-empty
  - stub:gateway-hold-429
  - dev:upgrade-required
readme_dispositions:                      # every README sentence that states a behaviour
  - text: "create 下一步 → analysis →（自动 1800ms）→ confirm"
    disposition: overridden by create-project.next (#420)
backend_without_ui:                       # decisions or operations with no control; one line each
  - "POST /api/recovery/finalize — runs at startup, no control"
retired_ids: []
rows: [...]
```

## A row

```yaml
- id: create-project.add-material         # <component>.<behaviour>; stable once published
  component: features/project-setup/CreateProjectView   # where the implementation owns it
  trigger: { role: button, name: "添加商品素材 拖入图片，或从本机选择" }   # exactly as the accessibility tree says
  precondition: { material: none }        # what must already be true; {} when nothing
  scenes: [empty, library-material-required, add-material]   # scenes.json names where the control is visible
  calls: ["ipc chameleon:image:select", "POST /api/projects/{project_id}/draft"]   # or [none]
  shows: { material_name: "basename(unconfirmed_material_path@GET /api/projects/{project_id}/draft)" }
  next: create-project.material-pending   # a row id, a scene name, or a state name from the domain doc
  on_failure: { dialog_cancelled: no-change, draft_4xx: toast:NEXT_FAILED_TITLE }
  source: ["#537 story 2", "#420", "README §5.3 (transition overridden)"]
  reach: seed:project-empty               # a mechanisms entry
  gap: aligned                            # aligned | design-only | backend-only
```

## Column rules

| Column | Rule | Lint |
| --- | --- | --- |
| `id` | `<component-short>.<behaviour>`, lowercase, dots and dashes. Never renumbered, never reused. | unique; every id in `retired_ids` absent from rows |
| `component` | A path or name the implementation owns the control under. | — |
| `trigger` | `role` and `name` copied from the skeleton. Hint text that the tree folds into the name stays in. | (role, name) exists in the skeleton; every skeleton control has ≥1 row |
| `precondition` | Key/value state that selects this row among rows with the same trigger. | rows sharing a trigger have distinct preconditions |
| `scenes` | Names from `scenes.json`. | each exists in the skeleton for this trigger |
| `calls` | `METHOD /path` exactly as in `openapi.json`; `ipc <channel>`; or `none`. Order is the order of effect. | HTTP entries exist in `openapi.json`; without an `openapi.json`, reported as `unverified` |
| `shows` | Displayed name → `field@OPERATION`, `key@RuntimePolicy`, or an expression over those. No literal numbers or strings. | value contains `@`; no bare digits |
| `next` | Where the user is after the call succeeds. | a row id, a scene name, or a state named in the domain doc |
| `on_failure` | Failure kind → what the user sees. Every non-`none` call has at least one. | present when `calls` is not `[none]` |
| `source` | Decision ticket numbers, ADR ids, story numbers, README sections. At least one that is not the README, or `gap` is not `aligned`. | non-empty |
| `reach` | One `mechanisms` entry. | resolves |
| `gap` | `aligned` when design and backend agree; `design-only` when the control has no backend behaviour to call; `backend-only` when a decision has no control. | `to-spec` refuses a file with any non-`aligned` row |

## What the downstream skills take from it

- `to-spec`: `calls` and `shows` → the **API contract** subsection; `mechanisms` → **How a test arrives at a state**; `baselines` → Sources.
- `to-tickets`: a UI ticket's **Read first** cites row ids; each row with a non-`none` call becomes one wiring criterion (trigger → assertion on the backend read surface named by `next` and `calls`), each row's `scenes` become visual-parity scenes.
- `implement`: `precedence` is the rule for a conflict between the handoff package and this file.
- `code-review` Spec axis: reviews the diff row by row for the ids the ticket cites.
