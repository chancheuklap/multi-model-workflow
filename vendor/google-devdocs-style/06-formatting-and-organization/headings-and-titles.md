# Headings and titles

> **这页管什么**：标题用句首大写；任务型标题用动词原形，不用 -ing。
>
> 来源：<https://developers.google.com/style/headings> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Sentence case and descriptiveness

- **Use sentence case for all headings and titles.**
- Headings should be unique and descriptive so readers can navigate between pages and sections.

## Task-based vs conceptual headings

- **Task-based** (tutorials, quickstarts, how-tos) start with a bare infinitive — "Create an instance", not "Creating an instance".
- **Conceptual** headings use a noun phrase that doesn't start with an *-ing* verb — "Migration to Google Cloud", not "Migrating to Google Cloud".
- Mixing both styles in one document is fine.
- Optional sections use the prefix `Optional:` **before** the heading text.

## Gerunds

Avoid *-ing* forms as the first word — they translate poorly and add length. Exceptions with no good alternative (*Billing*, *Pricing*) are fine. Gerunds are acceptable later in a heading: "Introduction to BigQuery monitoring".

## Titles

Each page needs one unique H1, used once. Don't repeat the exact page title as a heading elsewhere on the page.

## Format

- Keep punctuation simple — complex punctuation may signal an overly complex heading.
- Abbreviations only if commonly recognized; define in the first paragraph that follows.
- **Don't use numbers in headings to show sequence** — rely on hierarchy instead.
- Avoid code elements in headings; if unavoidable, pair the code item with a descriptive noun.
- Don't put links in headings.

## Hierarchy

- Don't reuse heading tags for visual styling — use CSS.
- Apply heading levels in order; **don't skip levels**.
- No empty headings — every heading is followed by content.

## Referring to grouped sections

Use "the following sections". Avoid ambiguous "this section" or "these sections" for a group.

## MMW note

The "don't number headings" rule assumes a human reader who judges sequence visually. In an MMW skill, a numbered step heading (`## 3. Draft vertical slices`) is a completion anchor an agent uses to tell what it has and hasn't done. Keep the numbers there.
