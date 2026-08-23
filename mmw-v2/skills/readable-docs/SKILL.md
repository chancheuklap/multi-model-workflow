---
name: readable-docs
description: Write documents that people can understand — context before details, jargon defined on first use, every added explanation verified against its source. Use whenever writing a document a person will read: research findings, specs, handoffs, ADRs, READMEs, reports. Other skills name this skill at the step where they start writing.
---

# Readable docs

Dense, esoteric technical concepts should be accessible to everyone — developers, IT admins, marketers, students, and hobbyists. A document an agent writes is read by a person first: if they cannot understand it, they cannot tell whether it is right.

Apply this while writing, not afterwards. Then hand the finished document to the `claim-checker` agent before calling the work done.

## Philosophy

Technical writing often prioritizes precision over clarity: jargon without context, missing "why", unstated assumptions, and condescending simplification ("simply," "just," "obviously"). Fix this through:

1. **Context before details** — Start with "why" and "when" before "what" and "how"
2. **Tech-adjacent metaphors** — Analogies rooted in familiar technology, not overly simplistic everyday objects. Acknowledge where metaphors break down.
3. **Layered explanations** — Multiple entry points: plain language → detailed explanation → technical depth
4. **Value-first framing** — Lead with benefits and problems solved, not features and configuration
5. **Explicit pitfalls** — Address common misunderstandings directly
6. **Familiar connections** — Bridge new ideas to concepts readers already know

**Audience:** Readers are intelligent but lack specific context. Never write for the "lowest common denominator." Assume smart people who are unfamiliar with this particular domain.

**Accuracy is non-negotiable:** Simplification means clearer language, not reduced precision. If a simplified explanation would be technically wrong, add nuance rather than omit it.

**Fact-check all net new information:** Any explanation, analogy, or context you add that was not in the material you are documenting **must be verified for correctness** before inclusion. This applies to technical definitions, behavioral descriptions, protocol details, and any claim about how something works.

Do not assume that general industry knowledge applies to the thing you are documenting. A skill, a script, a product can diverge from how such things are typically done. When adding commentary about how something behaves:

1. **Verify against the source** — Cross-reference the code, the script, the test output, or the upstream document before stating how it works.
2. **Cite your sources** — When introducing net new information (explanations, comparisons, implementation details), include a reference to the specific file, page, or authoritative source that supports the claim. Use inline links or footnotes.
3. **Flag uncertainty** — If you cannot verify a claim, explicitly mark it for the reader to confirm rather than presenting it as fact.
4. **Verify terminology in context** — Established terms carry specific meaning. Verify not just that the term exists, but that it is used in the same context and with the same meaning as the source. A real term applied in the wrong context is as misleading as a fabricated one.

**Language:** Write in the language the surrounding documents of the repository use. If they are mixed, use the language of the file the reader will open right before this one.

**Tone:** Clear, direct, professional. Not condescending, not overly casual, not hyperbolic. Never use "simply," "just," "obviously," "clearly," "as everyone knows," or "it's easy to."

## Enhancement constraints

Enhance content with context; do not pad it.

**Maximum additions per document:**

- **Problem/value statement:** 2-4 sentences inline (not a separate section)
- **Use case examples:** 1-2 per major concept, 5-15 lines each
- **Inline "why":** 1-2 sentences when introducing features
- **Jargon definitions:** Brief inline on first use
- **Troubleshooting:** 1-2 critical issues only
- **Testing:** 3-5 verification commands max

**Do not add:** Separate conceptual pre-sections, diagram annotations, multiple examples per concept, comprehensive testing/troubleshooting sections, or best practices sections.

## Decision framework

**Should I simplify a term?**

- **Replace or explain** if: domain-specific jargon, most readers will not know it, a simpler term is equally accurate
- **Keep but define** if: industry standard readers should learn, no simpler term is accurate, term appears frequently

**Should I add content?**

- **Yes** if: "why" is missing, use cases are absent, common misunderstandings are not addressed
- **No** if: the text is already clear, addition would pad without value, reader can infer from context

**Should I spell out a consequence or implication?**

- **No** if the target audience can infer the consequence from the stated cause. For example, "blocking health checks" does not need "which means the tunnels may be considered unhealthy" for a networking audience. Trust domain expertise.
- **Yes** only if the consequence is non-obvious, counterintuitive, or the audience genuinely lacks the domain knowledge to connect the dots.

**Should I add synonyms or aliases for a term?**

- **No.** One inline definition is enough. Do not pile on "also called X" aliases when the definition already explains the concept through its behavior. Define terms by what they do, not by listing alternative names.

**Should I remove content?**

- **Rarely.** Only if genuinely redundant or tangential. Never remove caveats, accuracy qualifiers, or security warnings.

## Anti-patterns to avoid

These are patterns that feel like improvements but consistently make documentation worse. They were identified from human review of AI-generated edits.

**1. Rewriting correct prose for "friendliness"**

If a sentence is factually accurate and structurally sound, do not rewrite it to sound warmer or simpler. Rewrites introduce risk of mechanical inaccuracy. Only touch sentences that have a concrete problem (wrong fact, ambiguous referent, undefined term, broken logic).

**2. Adding consequence chains the reader can infer**

Do not spell out "If X happens, then Y, which causes Z" when the audience already understands the causal chain. Ask: "Would a reasonable reader of this page already know this consequence?" If yes, omit it.

**3. Adding synonym glosses ("also called X")**

Do not append "also called 'default deny'" or similar aliases when the concept is already defined by its behavior in the same sentence. One definition is enough. Synonym stacking clutters without adding understanding.

**4. Using rhetorical questions in documentation**

Do not convert example lists into questions ("do you run VPN, NTP, or database services?"). State examples as examples. Documentation is not a conversation.

**5. Implying mutual exclusivity between complementary features**

Do not add phrases like "rather than writing rules from scratch" that imply one feature replaces another when both are used together. When two features complement each other, cross-reference them instead of contrasting them.

**6. Describing the wrong mechanism with a plausible simplification**

When simplifying how a system works, verify the simplification describes the actual mechanism. For example, saying "a Custom rule can change a Managed rule's action" is wrong if Custom rules actually take precedence due to evaluation order. A plausible-sounding but mechanically incorrect explanation is worse than the original jargon.

**7. Over-specifying precision the audience already has**

Do not explain that `==` means "equals" to an audience writing filter expressions. Calibrate the level of inline definition to the actual audience of the page, not to a hypothetical beginner.

**8. Using casual register in formal docs**

Match the existing voice of the surrounding documentation, not a conversational ideal.

**9. Conflating related but distinct concepts in a single statement**

When simplifying, do not merge two separate concepts into one sentence in a way that implies they are the same thing or that one requires the other. Each concept should be introduced on its own terms, even if they often appear together. If two features interact, describe them separately and then explain the relationship.

## Quality checklist

Before handing the document to the checker, verify:

- [ ] Technical accuracy maintained
- [ ] Jargon identified and explained
- [ ] Assumptions stated explicitly
- [ ] "Why" comes before "what" and "how"
- [ ] Use cases are realistic
- [ ] Metaphors have clear 1:1 mapping with stated limitations
- [ ] No condescending language
- [ ] 1-2 examples max per concept
- [ ] No consequence chains the audience can infer
- [ ] No synonym glosses when behavior-based definitions exist
- [ ] No rhetorical questions (examples stated as examples)
- [ ] Every simplification describes the correct mechanism
- [ ] Register matches the surrounding documentation voice

## After writing: adversarial review

Once the document is written, launch the `claim-checker` subagent. Do not review the document yourself in the current session — the point is to eliminate confirmation bias by having a separate agent, with no access to your reasoning, evaluate the output cold. Do not skip this step.

Give the checker:

- the path of the document
- the sources the document was built from — file paths, URLs, command output — so it can verify claims against them; anything you do not list, it searches the repository for
- which parts are net new: explanations, analogies, "why" and "when" framing you added that the sources do not state

The checker returns a claim table with each claim marked ✅ sourced, ❌ unsourced, or ⚠️ misleading, each with a severity. Do not present the table to the user. Fix every ❌ and ⚠️ in the document — remove the claim, add a source, or adjust the wording. If any of the findings you fixed was **critical** or **high**, show those rows to the user. Run the checker once; do not run it again. A fresh checker always finds a few low-severity rows; a second pass spends a full cold read to surface more of the same.

The document is finished after the checker's findings are fixed.
