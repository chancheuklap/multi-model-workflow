# Consulting the advisor

You have hit a decision. The advisor is a second opinion on a stronger model, started as its own session that holds none of your context and reads the code itself; writing nothing is a rule it keeps, not a limit its session enforces. It is slow and expensive next to the worker models.

## When it is worth a session

What you can settle by reading the code, settle by reading the code. One decision gets one consultation, and reading this page is not that consultation: the value is a session that has not spent the last hour convincing itself.

## Resolve `<dispatch>` once

`<dispatch>` is `bash <absolute path to scripts/dispatch.sh>` of the dispatch skill, installed beside this one; resolve it from that skill's directory, since the path differs by machine and by host.

## Start it

Write the packet to a file. Run `<dispatch> advise <file>`. Read the answer where the selected runner shows the session. Exit 0 prints the session id. Exit 2 starts nothing; the reason is on stderr, read it verbatim.

To change which host or model the advisor uses, read the dispatch skill's `references/editing-models.md`.

Done when `advise` exits 0 and you have told the user its session id.

## The packet

The advisor sees the packet and nothing else: not your session, not your tool trace, not the file you have open. All five parts:

1. The recent user/assistant exchange, quoted.
2. Your current understanding of the problem.
3. The constraints you believe bind.
4. The options you weighed, and which way you are leaning.
5. The file paths you believe are relevant.

## The question stays open

Your framing is the thing under review, so the packet leaves the advisor's work to the advisor: it reads what it decides to read, once it has looked, and reaches whatever conclusion that produces. Out of the packet, then: the list of what to check, the file you would have it skip, the conclusion you expect confirmed, and the narrowing of "which option" down to one option's details.

A second opinion you steered is your own opinion in a stronger model's voice.
