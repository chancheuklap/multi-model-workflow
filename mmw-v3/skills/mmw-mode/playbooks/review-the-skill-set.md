### Review the skill set

**You own the review. Nothing but the report is written until the user says go.**

1. **Review.** Follow the `writing-skill-sets` skill in this session to review what the user named, or the whole set when they named nothing.
   Done when that skill has handed back the load of each task walked and every finding with its evidence and fix.
2. **Report.** Before any edit, write what it handed back, in the order it gives, into the file `docs/reviews/<YYYY-MM-DD>-<slug>/README.md` of the repository, the slug naming what was reviewed.
   Done when every finding carries its evidence and its fix in that `README.md`.
3. **Fix every finding.** Run this step when the user asked for the fixes, or has read the report and said go; otherwise the review ends at **Report**, and this step stays in the todolist with its `skip:` line. Write every fix as the `writing-skill-sets` skill's `references/writing.md` says, without its **Walk a real task**, each with the address, the failure mode and the fix the report gives it; the review's walk is the walk of these fixes, and no task is walked again. Then commit the fixes and tell the user. A finding that waits on a decision the user holds stays in the report and does not hold the delivery back.
   Done when every finding is fixed or is a decision the user holds, and the fixes are committed.

**Reply:** the report's path; the load table; each finding with its fix, or the decision it waits on; what was not walked or not verified.
