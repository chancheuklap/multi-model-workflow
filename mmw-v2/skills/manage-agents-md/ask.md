# Ask the user

Branches **create** and **rewrite**. The survey list holds what the repository shows. Four things it cannot show: who the project serves and how serious it is, what this repository is not, the conventions nobody wrote down, and the reasons behind the odd choices. You get those from the user now, with the fixed questions below. Each question carries a recommended answer drawn from the survey list, so the user confirms or corrects instead of composing.

This is one round: the questions are fixed, there is no follow-up tree, and nothing else is asked here.

## Format

Ask the whole set in one message: number each question and give your recommended answer. Then wait for the user's answers before writing.

Each question should be formatted like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

The recommended answer quotes the survey entry and its evidence. When the survey list has nothing for a question, the recommended answer is "the survey found nothing for this". On the rewrite branch, the lines `destinations.md` sent to `ask` are the old file's identity lines; they are the recommended answers to the four identity questions, each marked "from the current file".

## Project identity, four questions

1. In one sentence: who is this project for, and what problem does it solve for them?
2. What stage is it at? Are there real users, real data, or real money running through it?
3. What lives outside this repository — related repositories, machines it deploys to? What has been split out, and which directories are frozen?
4. Is there anything in the repository an agent is likely to misread — content that looks like rules but is the product, files that look like code but are the user's assets?

## Key Conventions and Gotchas, seven questions

1. Which files are generated and must not be hand-edited? What command regenerates them?
2. Is there anything that must be done in a fixed order?
3. Where do two places record the same thing, and which one wins when they disagree?
4. Which problems have you debugged more than once?
5. Which practices look unconventional here but are deliberate? Why?
6. How do machines or environments differ from each other (local and production, one OS and another)?
7. Which areas are legacy and must be left alone?

## Nested purpose, one question per directory

A directory **earns a pair** when the survey list has at least one entry of type command, convention, or gotcha whose place is that directory; entries of type defect and reference do not count. Ask about every directory that earns a pair in one question: a table with one row per directory, the recommended purpose line in the second column, drawn from that directory's purpose entry in the survey list. The user edits rows or strikes directories out.

## Record

Append every answer to `survey-list.md` as an entry with `evidence: user, <date>`, the place it belongs to, and its type. An answer of "no" or "nothing" is appended too, so the writer does not go looking. Identity answers take the type `identity`; purpose answers the type `purpose`.

Done when every question has an appended answer or the user's explicit "skip".

Next: [write.md](write.md).
