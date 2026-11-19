# Prepare environment

Read the caller's product, checkout, chosen stack and existing environment instructions. Reuse working local tools. Supply only the missing launch, test-account and isolation tools in the product's development scripts and operating skill. Existing interfaces and login use the real local backend. A new project prepares the standalone prototype launch with its chosen stack; it has no product launch to prove yet.

The product environment tool belongs in its development scripts directory, with
an operating skill for manual use, debugging, diagnosis, and verification. It
provides one command to start the whole local product and one to create test
accounts. Launch calls it rather than shipping environment scripts as Helpers.

It provides both isolation layers: each product run owns port 0 and a fresh data
directory, and each checkout owns its back-end stack and database. `workers`
limits tests inside one run, not two tickets' runs. For a separate back-end
repository, overlay that repository's Compose files. Allocate ports dynamically
and record them in the checkout. Label containers with the checkout path,
collect stacks of deleted checkouts on the next start, and limit the number of
stacks running at once. Reuse this checkout's reachable stack and start it only
when unreachable. Use the stack's existing idempotent lifecycle command so
overlapping calls converge on one stack. If the stack runs checkout code,
readiness must establish that its code is current, not just that a port answers.

If ports or data directories are fixed, or the stack cannot be separated by
checkout, register the prerequisite with the **register-problem** skill. This
product gets no UI ticket until that prerequisite lands.
Record the prerequisite in Hand over.

Run that launch and retain the readiness evidence. Return the exact operating instructions, checkout and seed data to the calling prototype step. Do not enter Generate and prove or require a prototype that the caller has not built yet. Report a missing credential, unsupported surface or product decision with what the caller needs next.

Done when the caller can run its local product or standalone prototype with the returned instructions, or has the specific unmet prerequisite.
