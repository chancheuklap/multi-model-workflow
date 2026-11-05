# Verification

The language of the project-local skill that drives a real app the way a person does, and of the upkeep that keeps that skill honest.

Do not invent a Chinese name for a term in this file, or for any MMW skill. Use the English name.

## Language

**verify-<app>**:
The project-local skill at `.agents/skills/verify-<app>/`. It is the project's verification system: later agents start the app, drive it, and keep evidence by reading it. `<app>` is the app's name.
_Avoid_: control skill, and any invented Chinese name.

**feature map**:
The `features/` directory of `verify-<app>`: a README index and one file per user-facing feature. It is the maintained source for how a person reaches each part and how to drive it.
_Avoid_: any invented Chinese name.

**feature file**:
One file in a feature map. It says what the feature is, how a person reaches it, how the harness drives it, and what observable end state proves it.
_Avoid_: any invented Chinese name.

**Doctor**:
The read-only check that answers whether this app instance is worth driving. When e2e is the harness, Doctor is `npx e2e list --config` and then one smoke script with the same `--config`.
_Avoid_: any invented Chinese name.

**e2e**:
The harness used when it can drive the surface a person touches. The e2e skill is not installed. Scripts and config live inside `verify-<app>/`.
_Avoid_: any invented Chinese name.

**drive script**:
The script a Worker writes from the expected results on a ticket. Review runs `verify-<app>` and checks that the script asserts those sentences.
_Avoid_: any invented Chinese name.

**doc drift**:
A feature-file description, from the user's point of view, that is wrong or missing. Upkeep fixes the feature map.
_Avoid_: any invented Chinese name.

**product regression**:
App behavior that is broken, found while maintaining a feature map. It is reported, and it stays out of the verification change.
_Avoid_: product gap, and any invented Chinese name.

**harness gap**:
Working behavior the harness cannot drive. Upkeep fixes the harness.
_Avoid_: any invented Chinese name.

**skill drift**:
A Doctor failure caused by the verification skill. Upkeep fixes the skill and retries once.
_Avoid_: any invented Chinese name.

**verified-unreachable**:
A feature that cannot be reached, recorded only with the concrete prerequisite and the route that was attempted.
_Avoid_: any invented Chinese name.

**clean**:
The upkeep outcome where every feature got source and live coverage and nothing is worth shipping. There is no branch and no PR.
_Avoid_: any invented Chinese name.

**changed**:
The upkeep outcome where one PR ships proven corrections to the verification skill, the feature map, or the harness.
_Avoid_: any invented Chinese name.

**blocked**:
The upkeep outcome where coverage could not finish, or a proven fix could not ship safely.
_Avoid_: any invented Chinese name.
