# Ketchup

Catch the user up on what changed in this chat since the last message they wrote before `/wait-what ketchup`, and help them understand each change, not only where it stands. Give them every pending decision with the context needed to understand it where they read it. Notifications and subagent results are not their messages. Assume the user remembers their last message and nothing after it.

Use `wait-what`'s opening voice: give a little context, use ASD-STE100 Simplified Technical English and the project's ubiquitous language from `CONTEXT.md` (follow `CONTEXT-MAP.md` to the right one if the repo has more than one), like one person catching up another. Say what changed for the user, not how you did it. Say "the tests pass", not "CI is green". Leave out hashes, file paths, commands, build numbers, and test counts unless the user needs one to act. Call each PR, branch, or agent by a name the user would know, not by a label you invented. If a fact needs context to make sense, give the context or leave the fact out.

## Gather what changed

Keep this turn read-only. Make visuals only from what you already have: do not change code, start an app or a job, or post anything. Collect your own work since that message, reports from subagents, and messages from anyone else in this chat. Check the current state of each PR, CI run, or agent this chat touched. Check each number you will show against the facts it comes from, and say so when you correct one.

An action item is a decision or step only the user can take, such as a product choice, an approval, an irreversible action, or access you lack. Include any still waiting on the user, even one raised before their last message. Work you can still do yourself is not an action item. Never make up a call to fill the reply. A step the user did not ask for and the work does not need is not an action item, unless it is irreversible and waiting on the user: give it one action line, no visual, and skip what happens if the user does not answer.

Group items that share one decision. For each item, collect its original source name and link when known, what it changes for the user, and the evidence and recommendation needed for the decision. Include prerequisites and consequences that affect the choice. Write "unknown" for a fact the decision needs that you do not know.

## Write the reply

Keep the progress account short. Let the reply grow with the pending decisions, keeping every item and the information needed to understand it. A count or link cannot replace an item. Links add detail. The reading place itself must carry the decision context. When something is easier to grasp as a picture than as sentences, draw it: how a design or system works, a PR stack or dependency chain with each PR's state, a before and after of a fix, or options side by side. Never draw a status list or boxes with nothing connecting them. Never give a fact twice, in text or across visuals. Leave out work that changed nothing for the user.

Open with one sentence that says how many things need the user, or that nothing does. If nothing happened and nothing waits on the user, say so and stop.

Then show what happened, pictures first. Embed inline the screenshots and videos the work produced, then any diagram that explains a change. Then sum up in one short bullet per thing the user asked for: what came of it, and whether it is done, still running, failed, or not checked. Write each line the way you would say it out loud: "Search was slow from a missing index", not "Search review: done" or "Slow search: missing index". Name any bug found and fixed on the way. Each line must stay true when read alone. Never mark something done that still waits on the user, and leave out anything the action items say. Under the summary, give at most three short lines that change what the user knows or must do. Then name in one line any work left that you can do yourself.

Then list the action items as plain bullets, never as a diagram or box. Name the decision the user owns, such as merge, approve, or pick, and give your recommendation and why. For one item, put its source, effect and decision context in that bullet. When items share a decision, state the decision and common recommendation once, then give each item its own bullet. State an item's recommendation separately only when it differs. Include what happens if the user does not answer, except for an unasked irreversible step. A step you would take first goes in your recommendation. So does anything that must happen first, and anything that cannot be undone.

For a choice between options, put the comparison beside the decision it informs. If existing screenshots show the options, write each option's gain and cost under its screenshot. Otherwise, compare the options side by side, with the current state when there is one. Give every option the work weighed, each with what it gets the user and what it costs.

The overview makes all pending decisions visible. Recommend which decision to discuss first, and ask only that decision's question. Continue one decision at a time.

## Visuals

A visual is a picture: a screenshot, a video, a Mermaid diagram, a chart or diagram from the **diagram-design** skill, or a generated image. A Markdown table is not a visual, even with before and after columns.

Keep each visual small enough to read at a glance: at most six boxes, with at most eight words in each. Write labels as plain words a person would say, not tags like "Tests: pass". A fact that needs a sentence belongs in the text, or nowhere.

Embed screenshots and videos inline when the change is visible, not only as links. If a visible change has none, mark its summary line "No screenshot yet," and say there what changed on screen. Draw diagrams and charts from facts you have: a Mermaid diagram for how things connect and a chart made with the **diagram-design** skill for numbers. Never invent a number, and never draw or generate a picture of a screen you did not capture. Link only artifacts that exist.
