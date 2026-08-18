# Inclusive language

> **这页管什么**：该换掉的词：性别化、能力歧视、暴力隐喻、master/blacklist 这类。
>
> 来源：<https://developers.google.com/style/inclusive-documentation> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Gendered language

- man-hours → person-hours
- mankind → humanity
- Follow gender-neutral pronoun guidance in narrative examples.

## Figurative and idiomatic language

- Avoid idioms and figures of speech that confuse readers or complicate translation.
- Don't use terms in a metaphorical sense; use words in their primary meaning.
- Avoid the "pets versus cattle" comparison.

## Ableist language

| Avoid | Use |
| --- | --- |
| sanity-check | final check for completeness and clarity |
| crazy (for outliers) | baffling |
| cripples (for service impact) | slows down |
| dummy variable | placeholder |

Also flagged: *insane*, *blind to / turn a blind eye to*, *dumb*.

## Graphic or metaphorical technical terms

- STONITH → specific descriptive terms like "fence failed nodes"; mention the acronym once, de-emphasized.
- connection "hangs" → "doesn't respond"
- "hover over… hit" → "point to… click"

## Diverse examples

- Vary names, genders, ages, and locations to reflect a global audience.
- Avoid being too culturally specific to the US.
- For older adults: avoid *the elderly*, *the aged*, *seniors*, *80 years young*. Use *older adults* or *aging population*.

## Divisive or socially charged technical terms

- Avoid *native speakers* / *non-native speakers* — reframe around the feature itself.
- *blacklist* → use *allowlist*/*denylist*, or rewrite the sentence entirely.
- *native* (as in native feature) — avoid.
- *first-class citizen* — avoid despite common industry use.

## Replacing established industry terms

- *whitelist* → introduce as "allowlist (sometimes called a *whitelist*)" on first use, then use *allowlist*. Better: rewrite entirely — "allow requests from a range of IP addresses".
- *master* (Jenkins) → introduce as "Jenkins controller (master)", then use *controller*.

## Non-inclusive terms embedded in code

When `master`/`replica` or SQL's `SLAVE` keyword appear in real code or config:

- First mention: code font plus parentheses — "a parent node (which is named `master` in the file)".
- After that use the preferred term, and the original only in code formatting when necessary.

## Disability and accessibility language

- Don't call people without disabilities *normal* or *healthy*. Use *nondisabled person*, *sighted person*, *hearing person*, *neurotypical person*.
- Avoid terms that remove personhood — *the disabled*, *a quadriplegic*. Use *people with disabilities*, *a quadriplegic person*.
- Some communities (autistic, blind, Deaf) prefer identity-first language — research community preference.
- Use *see* for cross-references.
- Avoid *victim of*, *suffering from*, *wheelchair-bound* → *experiencing*, *living with*, *uses a wheelchair*.
- Avoid patronizing euphemisms — *physically challenged*, *special*, *differently abled*, *handi-capable*.
