# Filenames

> **这页管什么**：文件名小写、用连字符不用下划线；正文里怎么称呼文件类型。
>
> 来源：<https://developers.google.com/style/filenames> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Case

Lowercase files and directories — most Unix-style operating systems are case sensitive.

## Hyphens vs underscores

**Use hyphens, not underscores.** Search engines interpret hyphens in file and directory names as spaces between words; underscores are generally not recognized.

Exception: if an existing directory already uses underscores consistently, new files may follow that pattern.

## Character set

Standard ASCII alphanumeric characters only.

## Generic names

Avoid placeholders like `document1.html`.

## Auto-generated docs

Reference documentation may not follow these conventions if the tooling enforces its own naming. That's acceptable.

## Referring to filenames in text

- Use code font.
- Add the word *file* after it.
- Preserve the filename's exact spelling even if it breaks the naming rules.
- If a code sample from that file appears on the page, introduce it with a sentence naming the file first.

## File interactions

**Don't turn file type names into verbs** — "Extract a zip file", not "Unzip a zip file".

## File types

**Use the formal type name, not the extension** — "a PNG file", not "a `.png` file". Many formal names are capitalized because they're acronyms.

Mappings: `.py` → Python file, `.sh` → Bash file, `.zip` → zip file, `.md` → Markdown file.

## MMW note

MMW deliberately uses uppercase fixed-role filenames (`SKILL.md`, `CRITERIA.md`, `AGENT-BRIEF.md`) — the case carries meaning. Don't apply the lowercase rule to those.
