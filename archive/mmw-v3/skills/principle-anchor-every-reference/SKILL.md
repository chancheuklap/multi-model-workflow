---
name: principle-anchor-every-reference
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Anchor Every Reference

Every reference in a reply or a document is anchored: the first mention of a thing, place, action, or event names it by its file path plus the section heading, identifier, or rule number that appears in the file, and every later mention uses the same name.

**Why:** The reader shares none of your working memory. A name they cannot find in the source is a name they cannot search, hand to the next agent, or put in a ticket.

**Rule:**
- Copy names verbatim from the source: the identifier, heading, or exact wording in the file or in the owner's message, in the language the source uses. An English term in the source, or a term with an established English name, stays in English even when the rest of the reply is in Chinese.
- A label you invented while working ("the wiring step", "the second helper", "接线那一步") exists only in your head. Replace it with the source wording and the location it points to, even when that is longer.
- Add line numbers only where a ticket, a `CHECK:` line, or a review comment needs a location that a shell or a reviewer will jump to.
- A path is an address, not content. Give the address so the reader can hand it on, and leave the code behind it out of the reply unless asked.

Distinct from **principle-write-for-where-it-is-read**, which decides what a reader needs from where they stand. This one decides how each thing in it is named.
