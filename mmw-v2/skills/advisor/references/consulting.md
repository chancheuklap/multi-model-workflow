# Consulting the advisor

You have hit a decision. The advisor is a second opinion on a stronger model, started as its own session that holds none of your context and reads the code itself; writing nothing is a rule it keeps, not a limit its session enforces. It is slow and expensive next to the worker models.

## When it is worth a session

What you can settle by reading the code, settle by reading the code. The test is the cost of being wrong: a choice that is expensive to undo once work is built on it, or a problem whose repeated failure says your model of it is off. A choice you could reverse in minutes is not worth a session.

Do not ask again to get a different answer. A second consultation is for a new decision, or for the evidence the advisor said would change its answer. Reading this page is not that consultation: the value is a session that has not spent the last hour convincing itself.

## Start it

Write the packet to a file. Run the `dispatch` skill's `dispatch.sh advise <file>`. Read the answer where the selected runner shows the session. It prints the advisor's session id; a refusal says what to fix.

Done when you have the answer and have acted on it as **The answer** says, and the user has the session id.

## The answer

The answer is advice, not a ruling: you still own the decision. Take it, or set it aside with a reason you can state. When it would change something the user decides (what the customer sees, scope, anything hard to undo), it goes to the user like any other such decision, with the advisor's reasoning attached.

## The packet

The advisor sees the packet and nothing else: not your session, not your tool trace, not the file you have open. All five parts:

1. The recent user/assistant exchange, quoted.
2. Your current understanding of the problem.
3. The constraints you believe bind.
4. The options you weighed, and which way you are leaning.
5. The file paths you believe are relevant.

The test for the packet: a stranger with only this and the repository can reconstruct the decision. For a problem that resisted two attempts, each attempt and what it produced is the core of the evidence.

## The question stays open

Your framing is the thing under review, so the packet leaves the advisor's work to the advisor: it reads what it decides to read, once it has looked, and reaches whatever conclusion that produces. Out of the packet, then: the list of what to check, the file you would have it skip, the conclusion you expect confirmed, and the narrowing of "which option" down to one option's details.

A second opinion you steered is your own opinion in a stronger model's voice.
