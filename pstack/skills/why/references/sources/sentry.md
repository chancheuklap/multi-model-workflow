# Sentry Error History

## How to search it

1. **Orient.** Find the organization and project slug if you do not already know them.

2. **Search for issues related to the target.**

   Try queries such as "errors in PaymentService timeout" or "unhandled exceptions in uploadFile".

   Build queries from the exception class names the target handles, its function or class name, the error message strings it checks for, and its file path.

3. **Narrow by release and time window.**

   Filter events by release, time, environment, trace ID, or tags. Check the issue's tag distribution across versions, users, and environments.

   For a suspected issue, check **first seen** and **last seen** (does the stop line up with the target's ship date?), the **affected releases** (which saw it, and which was the fix?), and the **frequency trajectory** (did it spike, then get resolved?).

4. **Pull the full event for context.**

   Open the event by URL or by resource type and ID.

   Does the stack trace pass through the target code? Do the tags and breadcrumbs match the conditions the target defends against?

5. **Check releases that landed near the target.**

   Find releases around the commit date.

   Cross-reference release version with the PR's merge date.

6. **Use Seer sparingly.**

   Seer's AI root-cause analyses are a hypothesis generator. Treat them as inference, not authoritative. The actual events and stack traces are the primary evidence.

## What to return

For each relevant issue:
- Issue ID and title
- Project and organization
- First seen / last seen timestamps
- Event count (and sampling rate if known)
- Affected releases
- A representative stack trace snippet showing relevance to the target (verbatim excerpt, not summary)
- First/last-seen correlation with the target's ship date
- Link to the issue
- Any author comments or resolution notes
