# Command-line syntax

> **这页管什么**：**方括号、花括号、省略号不能出现在可直接复制的命令里** —— 会把命令弄坏。
>
> 来源：<https://developers.google.com/style/code-syntax> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Optional arguments

Square brackets, one pair per optional item — `gcloud dns GROUP [GLOBAL_FLAG] [FILENAME]`.

**Avoid these in copyable command blocks** since brackets break the command if not removed first.

## Mutually exclusive arguments

Curly braces with pipes — the reader must choose one and only one — `{FILE_1|FILE_2}`. More than two choices allowed.

## Repeating arguments

Three dots, no spaces — `gcloud dns GROUP [GLOBAL_FLAG ...]`.

## Click-to-copy commands

Avoid brackets, braces, pipes, and ellipses — **they can break commands if not first removed**. Fixes:

- Trim to only the essential arguments.
- Split options into separate code blocks.
- Document variants as separate tasks.
- Explicitly warn the reader that optional syntax appears in the command.

## Formatting a command block

- `pre` in HTML or a code fence in Markdown.
- For long lines, indent each continued line by four spaces.
- **Continuation characters are required**: `\` for Linux and Cloud Shell, `^` for Windows. Commands without the continuation character don't work.
- Follow placeholder formatting, and put a descriptive list of placeholders after the command.

## Command prompts

- For multi-line input blocks, start each line of input with the prompt symbol.
- Don't display the current directory before the prompt.
- Add a new prompt indicator only when the context changes, such as switching to a remote shell.
- For single-line commands the prompt is optional, but be consistent within a page.
- Keep input and output in **separate code blocks**.

## Output

- Only show output **if it adds value** — when the reader must copy or verify a value.
- Intro: "The output is similar to the following:" or "The output is the following:".
- Omitted output lines use `...` alone on its own line, not the single-character ellipsis glyph.

## Terminology

Non-command-name elements are *flags*; a flag or command may take an *argument*; *option* is a generic catchall. Linux commands use *options*, *parameters*, *arguments* depending on context.
