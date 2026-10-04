### Review a ticket

**You own one review report on one ticket, as its reviewer; the axes are dispatched from here.** The ticket's worker started you and is asleep until your report is on the ticket, and nobody else is watching, so the mode's **Unattended** paragraph holds from the first step. Distinct from Work a ticket: you change no code and write nothing but the report.

Your start prompt names the ticket and the base commit, and lists the reviewer Rules the owner approved, or `none`.

<!--
Shell. Pinning the diff comes here. Source in MMW v2 at 9df1ab67d:
mmw-v2/upstream/skills/engineering/code-review/references/session.md `## 1. Pin the
diff`. A lesson on how a reviewer works writes it.
-->

1. **Run the axes.** Read the ticket. A **story criterion** is a `CHECK:` that names `story-parity.py`. When the ticket has one, run four axes: Standards, Spec, Tests and UI; otherwise the first three. Run the `code-review` skill on the ticket and the base commit with those axes. Hold your turn until every axis has reported: the worker is asleep on your report, and what wakes it is step 2, which cannot run until the report exists.
   Done when every axis you started has reported.

<!--
Shell. Verifying every finding the axes report, sorting each into in-ticket or
out-of-ticket, writing the report, and applying the reviewer Rules come here. Source in
MMW v2 at 9df1ab67d: code-review references/session.md `## 3.`, `## 4.`, the shape of the
report in `## 5.`, and `## Active Rules`. A lesson on how a reviewer works writes them.
-->

2. **Post the report.** Write the report to a file and run the `verify-ticket` skill's `verify-ticket.py <ticket> --review <file>`. It posts the report and puts `reviewer.reported` on the ticket, which wakes the worker; it is the only way this review reaches anyone.
   Done when `--review` exits 0.

**Reply:** the report `--review` posted is this run's reply; this session's own last message is read by nobody.
