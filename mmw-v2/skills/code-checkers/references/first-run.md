# Taking a first run down to signal

A first run on an existing codebase reports thousands. Almost none of it is worth a human's attention, and reading it in the order the tool printed it is how the whole effort gets abandoned. Separate it in this order:

1. **Misconfiguration.** Import roots the checker cannot resolve, dependencies absent by design on this platform, framework idioms the rule was not written for. This is usually most of the count. Fix the config, not the code — and exempt precisely: a framework's specific calls, not the whole rule.
2. **Machine-fixable.** Run the fixer. Import order, dead suppressions, obsolete syntax — the diff is large and needs no reading.
3. **The formatter, once, as its own commit.** Add that commit's hash to `.git-blame-ignore-revs`.
4. **What's left is the real backlog — and it must never block a commit.** A checker that reports a file's existing problems every time someone edits one line of it has one outcome: everybody starts passing `--no-verify`, and the checker no longer checks anything. Two mechanisms, depending on what the tool offers:

   - **A checker baseline**, when the tool has one (type checkers usually do). Existing errors go in it and stay quiet; anything new is reported from day one. Commit the baseline — it belongs to the branch like the config does. Prefer this over the tool's bulk-suppress command, which writes an ignore comment at every site: thousands of lines of source noise to say nothing.
   - **Filter to the changed lines**, when it does not. Run the linter with JSON output, intersect its line numbers with `git diff --unified=0`, report only the overlap. Two traps: the linter reports absolute paths while git reports repo-relative ones, so normalise before comparing; and untracked files appear in no diff at all, so pull them in separately and treat every line as new.

   The formatter needs its own answer: it rewrites whole files, so running it on an existing file *is* touching the backlog. Run it on newly added files only.

The point of both is that the checker is **useful on day one** rather than after a cleanup nobody schedules.
