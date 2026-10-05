"""Mark every mention of a component with its kind, so the page colours it the way the figures do.

Two passes over a page's HTML, both idempotent:
- a plain <code>name</code> whose name is a known component becomes <code class="c k-KIND">;
- a component's plain-text name (a playbook such as Bug fix, a principle such as Prove It Works)
  becomes <span class="c k-KIND">, outside figures, code, quotes, headings and links.

A quote's source is not guessed here; the page gives it as <q class="k-KIND" data-src="…">.
"""
import html
import re

MODE_SECTIONS = {"## Non-negotiables", "## Principles", "## Autonomy", "## Subagents",
                 "## Writing the reply", "## Comments", "## Playbooks"}

SKILLS = {
    # pstack
    "architect", "arena", "automate-me", "benchmark-checklist", "blast-radius", "bro", "correct",
    "create-verification-skill", "figure-it-out", "how", "interrogate", "maintain-verification-skill",
    "make-bot-ui", "no-comments", "recall", "reflect", "setup-pstack", "show-me-your-work", "swarm",
    "tdd", "teach", "technical-writing", "typescript-best-practices", "unslop", "why",
    "create-skill", "deslop", "control-cli", "control-ui",
    # MMW v2
    "code-review", "codebase-design", "diagnosing-bugs", "domain-modeling", "grill-with-docs",
    "implement", "improve-codebase-architecture", "prototype", "research", "resolving-merge-conflicts",
    "setup-matt-pocock-skills", "to-spec", "to-tickets", "triage", "wayfinder", "wizard", "grill-me",
    "grilling", "handoff", "to-questionnaire", "wait-what", "writing-for-agents", "design-pages",
    "exe-release", "verify-ticket", "ui-acceptance", "manage-agents-md", "dispatch", "code-checkers",
    "diagram-design", "write-screen-contract", "advisor", "retro",
}

SKILL_SECTIONS = {"## Closing steps", "## Find your moment", "## Start", "## Seam",
                  "### 4. Write each acceptance criterion"}

CONFIG = {"shared.md", "prompt/shared.md", "mmw-v2/prompt/shared.md", "~/.claude/CLAUDE.md",
          "mmw-v2/prompt/hosts/codex.md", "hosts/codex.md", "~/.mmw/models.json", "models.json",
          "skills.txt", "mmw-v2/skills.txt", "pstack-models.mdc", "~/.cursor/rules/pstack-models.mdc"}

# A principle is often named by its slug alone, without the principle- prefix.
PRINCIPLE_SLUGS = {
    "attack-the-premise", "boundary-discipline", "build-the-lever", "encode-lessons-in-structure",
    "exhaust-the-design-space", "experience-first", "explain-the-number", "fix-root-causes",
    "foundational-thinking", "guard-the-context-window", "laziness-protocol", "make-operations-idempotent",
    "migrate-callers-then-delete-legacy-apis", "minimize-reader-load", "model-the-domain",
    "never-block-on-the-human", "outcome-oriented-execution", "prove-it-works",
    "redesign-from-first-principles", "separate-before-serializing-shared-state",
    "sequence-verifiable-units", "subtract-before-you-add", "test-behavior-not-implementation",
    "type-system-discipline",
}

AGENTS = {"poteto-agent", "poteto-agent.md", "agents/poteto-agent.md", "comment-sicko.md"}

# Parts of one component written on their own: a playbook's labels and the files Orchestrate keeps,
# a principle's labels, the files a reference or script is known by.
PARTS = {
    "playbook": {"**Reply:**", "**You own …**", "**You own**", "authoring-a-skill", "gates.md", "REPORT"},
    "principle": {"**Why:**", "**Pattern:**"},
    "reference": {"bugbot-triage.md", "## 4. The closing pass"},
    "script": {"watch-pr", "--closeout", "advance", "finish", "summary", "reverify", "start"},
    "skill": {"writing-skill-sets", "skills/&lt;名&gt;/SKILL.md", "skills/<名>/SKILL.md"},
    "other": {"components.md"},
}
_PART_KIND = {n: k for k, names in PARTS.items() for n in names}


def kind_of(name):
    t = name.strip()
    first = t.split()[0] if t.split() else t
    if t in _PART_KIND:
        return _PART_KIND[t]
    if t in AGENTS or "agents/" in t:
        return "agent"
    if "principle-" in t or t in PRINCIPLE_SLUGS:
        return "principle"
    if "playbooks/" in t:
        return "playbook"
    if "references/" in t:
        return "reference"
    if "scripts/" in t or first.endswith((".sh", ".py", ".mjs", ".ts")):
        return "script"
    if t in CONFIG or t.endswith(".mdc"):
        return "config"
    if t in MODE_SECTIONS or t in {"poteto-mode", "poteto-mode/", "mmw-mode", "/poteto-mode", "/mmw-mode"} \
            or "poteto-mode/SKILL.md" in t or "mmw-mode/SKILL.md" in t or t.endswith("-mode"):
        return "mode"
    if t in SKILL_SECTIONS or t in SKILLS or (t.startswith("/") and t[1:] in SKILLS):
        return "skill"
    return None


PLAIN = {
    "playbook": ["Opening a PR", "Bug fix", "Hillclimb", "Perf issue", "Feature", "Refactoring",
                 "Investigation", "Babysit", "Shipping", "Autopilot-full", "Autopilot-stack",
                 "Multi-phase plan", "Orchestrate", "Autonomous run", "Pause safely", "Session pickup",
                 "Prototype", "Worktree cleanup", "Runtime forensics", "Trace forensics",
                 "Authoring a skill", "Visual parity",
                 # MMW v3 and the other course's playbooks
                 "Eval",
                 "Run a night", "Work a ticket", "Review a ticket", "Review the skill set",
                 "Authoring or modifying a skill", "Open a night", "Close a night", "Accept a night",
                 "Suspend a night", "Settle a contract child", "Route a finding", "Fix on the base branch",
                 "Run one ticket", "Answer a review", "Write a ticket", "Cut tickets", "Write a spec",
                 "Revise a spec", "Chart a map", "Resolve a map ticket", "Design pages", "Pull a design",
                 "Build a design system", "Write the screen contract", "Answer a question",
                 "Map a large effort", "Design an interface", "Write a spec and tickets",
                 "Make a small change", "Research a question", "Triage"],
    "principle": ["Laziness Protocol", "Foundational Thinking", "Redesign from First Principles",
                  "Attack the Premise", "Subtract Before You Add", "Minimize Reader Load",
                  "Outcome-Oriented Execution", "Experience First", "Exhaust the Design Space",
                  "Build the Lever", "Model the Domain", "Boundary Discipline", "Type System Discipline",
                  "Make Operations Idempotent", "Migrate Callers Then Delete Legacy APIs",
                  "Separate Before Serializing Shared State", "Prove It Works", "Fix Root Causes",
                  "Sequence Work into Verifiable Units", "Test Behavior, Not Implementation",
                  "Explain the Number", "Guard the Context Window", "Never Block on the Human",
                  "Encode Lessons in Structure"],
    "mode": ["Non-negotiables", "Writing the reply", "Autonomy", "Subagents"],
    "agent": ["Comment Sicko", "poteto-agent"],
}
# Single-word skill names safe to find in running text; common English words (how, why, teach,
# research, prototype, correct) are left to <code>.
PLAIN["skill"] = ["unslop", "bro", "swarm", "arena", "architect", "interrogate", "reflect", "recall", "tdd",
                  "implement", "dispatch", "advisor", "retro", "triage", "grilling", "wayfinder", "handoff"]
_PLAIN_KIND = {n: k for k, names in PLAIN.items() for n in names}
# Besides the names above: any hyphenated name or file name that kind_of() recognises
# (figure-it-out, principle-prove-it-works, shared.md, dispatch.sh).
_TOKEN = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+|[\w./~-]+\.(?:md|py|sh|mjs|ts|json|mdc)"
_PLAIN_RE = re.compile(r"(?<![\w/.-])(" + "|".join(re.escape(n) for n in sorted(_PLAIN_KIND, key=len, reverse=True))
                       + "|" + _TOKEN + r")(?![\w-])")

# Regions left untouched by the plain-text pass; each is matched whole, then the tags between them.
_PROTECTED = re.compile(
    r"<svg\b.*?</svg>|<style\b.*?</style>|<script\b.*?</script>|<title\b.*?</title>"
    r"|<code\b.*?</code>|<q\b.*?</q>|<h[1-4]\b.*?</h[1-4]>|<a\b.*?</a>|<span class=\"c [^\"]*\">.*?</span>"
    r"|<button\b.*?</button>|<[^>]+>",
    re.S)


def _tag_code(m):
    k = kind_of(html.unescape(m.group(1)))
    return f'<code class="c k-{k}">{m.group(1)}</code>' if k else m.group(0)


def _tag_word(m):
    w = m.group(1)
    k = _PLAIN_KIND.get(w) or kind_of(w)
    return f'<span class="c k-{k}">{w}</span>' if k else w


def _tag_text(text):
    return _PLAIN_RE.sub(_tag_word, text)


def tag(page):
    page = re.sub(r"<code>([^<]+)</code>", _tag_code, page)
    out, pos = [], 0
    for m in _PROTECTED.finditer(page):
        out.append(_tag_text(page[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_tag_text(page[pos:]))
    return "".join(out)
