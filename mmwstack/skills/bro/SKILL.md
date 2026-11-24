---
name: bro
description: "Single entry for aligning understanding and preparing prompts: route to the matching clarity skill, or restate your goal and last reply plainly. Use only for /bro."
---

Check what the user asks after `/bro`.

If they ask for one of the jobs below, open and read that skill's `SKILL.md`, then follow it in full instead of the default restatement:

- [ketchup](../ketchup/SKILL.md): catch up on what changed in this chat since my last message and list what waits on me.
- [ketchup-video](../ketchup-video/SKILL.md): the same catch-up as a short subtitled slide video.
- [recall](../recall/SKILL.md): rebuild context across recent chats, branches, and issues before resuming.
- [teach](../teach/SKILL.md): explain how a subsystem works, why it was built that way, or what a change does.
- [big-pics-little-words](../big-pics-little-words/SKILL.md): explain or draw this as a standalone HTML page, diagram, plan, wireframe, or mockup.
- [reframe](../reframe/SKILL.md): I can't name what I'm building yet; teach me the expert words and neighboring-field terms, then rewrite my description.
- [sharpen](../sharpen/SKILL.md): the task is already named; make my draft prompt deeper, not bigger, with expert raw material, methods, and an outside check.

Pick the best fit from intent, even when phrased informally. If two fit closely, pick the likelier one and deliver it directly; mention the alternative in one line only if needed.

Otherwise (bare `/bro`, or the user wants alignment on their ask or your last reply):

1. Restate in your own words what the user's goals are and what problem they are trying to solve.
2. If there is a prior reply they didn't follow, restate it with a little context in the user's language, in the style of ASD-STE100 Simplified Technical English, using the repository's `GLOSSARY.md` (follow `GLOSSARY-MAP.md` when there is more than one). Skip jargon and speak like one human talking to another.
