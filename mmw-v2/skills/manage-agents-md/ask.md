# Ask the maintainer

The survey gives you what the repository shows. Four things it cannot show: who the project serves and how serious it is, what this repository is not, the conventions nobody wrote down, and the reasons behind the odd choices. You get those by asking the maintainer the fixed questions below, each with a recommended answer drawn from the survey, so the maintainer confirms or corrects instead of composing.

This is one round of questions and answers. It is not a design interview: the questions are fixed, there is no follow-up tree, and nothing else is asked here.

## Format

Ask the whole set in one message: number each question and give your recommended answer. Then wait for the user's answers before writing.

Each question should be formatted like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

The recommended answer comes from the survey: quote the fact and its evidence. When the survey has nothing for a question, say "the survey found nothing for this" as the recommended answer; do not invent one. On a rewrite, the old file's line is the recommended answer for the question it answers, marked "from the current file".

## Project identity, four questions

1. In one sentence: who is this project for, and what problem does it solve for them?
2. What stage is it at? Are there real users, real data, or real money running through it?
3. What lives outside this repository — related repositories, machines it deploys to? What has been split out, and which directories are frozen?
4. Is there anything in the repository an agent is likely to misread — content that looks like rules but is the product, files that look like code but are the user's assets?

## Conventions and pitfalls, seven questions

1. Which files are generated and must not be hand-edited? What command regenerates them?
2. Is there anything that must be done in a fixed order?
3. Where do two places record the same thing, and which one wins when they disagree?
4. Which problems have you debugged more than once?
5. Which practices look unconventional here but are deliberate? Why?
6. How do machines or environments differ from each other (local and production, one OS and another)?
7. Which areas are legacy and must be left alone?

## Nested scope, one question per directory

For every directory that will get its own `AGENTS.md`: "What is `<directory>` not responsible for?" The recommended answer is the directory group's scope finding.

## Recording

Write the answers into the survey list as entries with `evidence: maintainer, <date>` and the place and type they belong to. An answer of "no" or "nothing" is recorded too, so the writer does not go looking.

Done when every question has a recorded answer or the maintainer's explicit "skip".
