# Dates and times

> **这页管什么**：**日期必须无歧义。** 发给外部的文档（问卷 deadline）尤其重要。
>
> 来源：<https://developers.google.com/style/dates-times> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Time format

- Default to the 12-hour clock; use 24-hour if the feature being documented does.
- If the UI, a command, or a code sample uses 24-hour format, use that format throughout the page.
- Prefer exact times; *noon* and *midnight* are OK.
- For round hours, remove the minutes — "3 PM", not "3:00 PM".
- Capitalize AM/PM with a space before — "3:45 PM".

## Durations and ranges

Use hyphens with no spaces — "5-10 minutes ago".

## Time zones

- **Avoid time zones unless absolutely necessary.**
- Clarify if the time is local to the reader — "10 AM your local time".
- Match the format shown in the actual UI when available.
- Spell out the full region name and append the offset — "US and Canadian Pacific Standard Time (UTC-8)". Don't abbreviate.
- If a zone never shifts for daylight saving, name it without a UTC reference.

## Unambiguous date format

- **Spell out month and day names in full, with a four-digit year** — "January 19, 2017".
- Day of week goes before the month — "Tuesday, April 27, 2021".
- Month + year only: no comma — "She was hired in January 2017".
- Three-letter abbreviations (capitalized, no period) only in space-constrained contexts like headings and tables, applied consistently to the whole date.
- Mid-sentence full dates need a trailing comma after the year — "The January 19, 2017, release of…".
- **Avoid numeric-only dates** — "04/05/09" is read differently across regions.
- When numeric format is unavoidable, use ISO 8601 `YYYY-MM-DD` — "2017-04-15". For fictional examples, pick a day above 12 to avoid month confusion.
- Date and time combined: date first — "2017-04-15 at 3 PM".

## Divisions of the year

Avoid seasons — they invert between hemispheres. Use specific months, quarters, or descriptions like "warmer months".
