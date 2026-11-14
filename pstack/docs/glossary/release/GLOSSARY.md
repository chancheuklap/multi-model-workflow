# Release

The language of the exe-release skill: one product, one manifest, one engine loop, one install package from the current branch.

## Language

**release manifest**:
The JSON file that declares how one product is packaged. One product per file. The filename ends in `.release-adapter.json`. The filename and the `--adapter` flag use the word adapter as a literal the scripts read. Prose calls this file the release manifest. It is unrelated to the adapter at a seam in [Engineering design](../engineering-design/GLOSSARY.md).
_Avoid_: 钥匙, key, release adapter, and any invented Chinese name.

**release engine**:
The loop that owns release progress, the next action, the repair count, and success. Session memory is not a second copy of that state.
_Avoid_: 引擎, and any invented Chinese name.

**build machine**:
The machine that receives `git archive HEAD` and runs the remote build. Nothing else from the working tree is sent.
_Avoid_: 构建机, and any invented Chinese name.

**delivery record**:
The record written when a release closes: the product name and the ship commit. It outlives the task worktree.
_Avoid_: 交付记录, and any invented Chinese name.

**ship commit**:
The commit stored on a delivery record as the source of that shipment. The field name is `source_commit`. It names the source of an install package. [Shipping](../pull-request-delivery/GLOSSARY.md) lands PRs and builds no package.
_Avoid_: 交付提交, and any invented Chinese name.

**same-commit check**:
The check that the ship commit matches the packaging inputs for that product.
_Avoid_: 同 commit 校验, and any invented Chinese name.

**release fix brief**:
The brief written for the agent driving the release when a failure needs a code change. The file name is `release-fix-brief.md`.
_Avoid_: 简报, 修复简报, and any invented Chinese name.

**circuit breaker**:
The stop that fires when the same failure fingerprint has been observed three times. The loop does not continue past it on its own.
_Avoid_: 熔断, CIRCUIT-BREAK, and any invented Chinese name.

**install package**:
The installer this skill ships for a product, far enough that a person can install it.
_Avoid_: any invented Chinese name.

Sources include [exe-release](../../../skills/exe-release/SKILL.md) and the [Release an install package playbook](../../../skills/poteto-mode/playbooks/release-an-install-package.md).
