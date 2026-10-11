---
name: create-verification-skill
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Create a verification skill

This skill writes `.mmw/<product>/` for each product the owner confirms, and drives one feature of that product. The owner confirms which products the repository has and how their feature map is divided. A later worker starts the product inside a lease and follows the map. A directory that was never driven is not onboarded, and the next run then meets a product that does not come up.

## Start

Open a todolist with one item per step below.

## Steps

1. **Confirm the products.** Read the repository and list what a person can run. Ask the owner only what you cannot observe. The owner confirms which of those are products and the name of each. A name is lowercase letters, digits and hyphens, which is what the `ui-acceptance` skill's `scripts/target_config.py --check` requires.
   Done when the owner has confirmed the list and each name.

2. **Write `.mmw/<product>/`.** For each confirmed product that has no `.mmw/<product>/` yet, write that directory. The `ui-acceptance` skill's `references/product-answers.md` says what `.mmw/<product>/target.json` must guarantee. `python3 scripts/target_config.py --check --product <product>`, from that same skill, exits 0 when nothing is left to answer. A line that begins `target_config.py --check:` names one thing still wrong. Fill the file until it exits 0.
   `start` and `stop` bring the product up and down. `doctor` answers whether this instance is worth driving. The product takes its ports and its data directory from the lease.
   A script an agent runs to drive the product goes in `.mmw/<product>/drive/`. The recipe the next agent follows is the feature map's `## Driving it`.
   Before the first `start`, read the `ui-acceptance` skill. Its **Five rules while the product is running** bind the drive. A web page or an Electron application is operated as that skill's `references/control-ui.md` says. A command-line product is operated as that skill's `references/control-cli.md` says.
   When the product's own code has to change before it can be driven, open a ticket in that repository and leave the product code unchanged. The usual case is a port written into the source.
   Done when `target_config.py --check --product <product>` exits 0, or the reply names the ticket that has to land first.

3. **Write the feature map.** Write `docs/features/<product>/` as the `mmw-mode` skill's `references/feature-map.md` says; the owner confirms it as that reference's **How a feature is divided** says. A behaviour already in the product, which no decision record names, uses the `existing <date>` source that reference defines. The date is the day that behaviour is written into the map.
   Done when the owner has confirmed what the map says a user can do and `feature_map.py lint` (the `verify-ticket` skill's `scripts/feature_map.py`), run from the repository root, exits 0. `## Driving it` is still empty here. Step 4 writes it after the walk.

4. **Drive one feature.** Run `start`, then `doctor`, through the `ui-acceptance` skill's `scripts/lease.py`, as `python3 scripts/lease.py run --product <product> -- <command>`. Each command is the one `.mmw/<product>/target.json` names. Drive one feature. The feature file says what the user finishes, and step 2 says how the product is operated. Write `## Driving it` from that walk, as that reference's **Driving it** says. Save a screenshot under `.scratch/` in the worktree. Then run `stop` through the same lease command. The screenshot file is still there after `stop`.
   When a step fails, run `stop` before the next attempt, so a broken attempt does not leave the product running.
   Done when `doctor` exited 0, the screenshot shows the feature after the action, `## Driving it` records that walk, and that file is still at its path after `stop`.

5. **Commit and name the upkeep.** Commit `.mmw/<product>/` and `docs/features/<product>/` and push them: a worker starts from the base branch on origin and sees nothing left in this checkout. The `maintain-verification-skill` skill keeps that product's feature map honest after the product changes, when the owner asks for a pass.
   Done when both directories are on the base branch on origin and the reply names the `maintain-verification-skill` skill.
