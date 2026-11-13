# Design and presentation

These terms distinguish what a design settles, what a running product shows, and what the operator sees in a catch-up.

## Language

### HTML artifacts

**HTML artifact**:
A self-contained HTML file that a person can open to read or use. For example, a visual explanation of a spec shows its decisions in pictures with enough text to preserve their meaning. [html](../../../skills/html/SKILL.md) · [big-pics-little-words](../../../skills/big-pics-little-words/SKILL.md) · [to-spec](../../../skills/to-spec/SKILL.md)

**HTML artifact form**:
The way a reader uses an HTML artifact. A document supports reading, a presentation paces one idea per screen, and an interface exposes actions and their results. A diagram shows relationships, while a data visualization shows a quantitative comparison. [Documents and presentations](../../../skills/html/references/documents-and-presentations.md) · [Interfaces and tools](../../../skills/html/references/interfaces.md) · [Charts and data](../../../skills/html/references/charts-and-data.md)

**HTML diagram**:
An HTML artifact whose layout answers a question about a relationship. A topology diagram shows what connects. A sequence diagram shows who sends what and in what order. **Everything at Hand** places labels and evidence beside the marks they explain. Views being compared use the same scale and sit side by side when they fit. [html-diagram](../../../skills/html-diagram/SKILL.md) · [Diagram forms](../../../skills/html/references/diagrams.md) · [principle-everything-at-hand](../../../skills/principle-everything-at-hand/SKILL.md)

**HTML plan**:
An HTML presentation of a plan. Its source supplies the scope, commitments, order and dependencies. An HTML plan can present a multi-phase plan that already describes the proposed work and its checks. [html-plan](../../../skills/html-plan/SKILL.md) · [Multi-phase plan playbook](../../../skills/poteto-mode/playbooks/multi-phase-plan.md)

**Source fidelity**:
How closely an HTML artifact preserves the source's wording and structure. The presentation preserves the wording and decisions the operator approved. [html](../../../skills/html/SKILL.md#read-the-room-before-designing)

**Public page**:
A published HTML artifact that anyone with its link can open. The author delivers the artifact first. Publication requires the operator's separate approval. [design-artifact](../../../skills/design-artifact/SKILL.md#after-the-artifact-ships)

### Visual and interaction design

**Review question**:
The decision a reviewer can make by inspecting or operating a design. A question about where an action belongs calls for a different artifact from a question about what happens after the action fails. [html](../../../skills/html/SKILL.md#route-the-request-first)

**Visual direction**:
The choices of color, typography and composition that give an artifact its appearance. Explicit requirements and the project's established design language guide those choices. [Creative direction](../../../skills/html/references/creative-direction.md)

**Visual design plan**:
The record of the colors, type roles and layout chosen for one artifact before it is built. An HTML plan can have its own visual design plan. [design-artifact](../../../skills/design-artifact/SKILL.md#process) · [Creative direction](../../../skills/html/references/creative-direction.md#make-a-visual-design-plan)

**Visual register**:
The treatment suited to the subject and audience. A workmanlike register uses restrained styling for reading or operating a tool. An editorial register gives the presentation a distinctive composition. An expressive register makes the visual or interactive experience part of the message. [Creative direction](../../../skills/html/references/creative-direction.md#find-the-direction-inside-the-brief)

**Wireframe**:
A low-fidelity HTML artifact for deciding what belongs on a screen, how a person moves through a task, and how the layout changes with screen size. Working links or tabs can help reviewers test that structure. [html-wireframe](../../../skills/html-wireframe/SKILL.md)

**Layout direction**:
One arrangement of the same content and task. Competing wireframe directions differ in decisions such as navigation, grouping or where the primary action sits. [html-wireframe](../../../skills/html-wireframe/SKILL.md#explore-structure-before-style)

**Fidelity mode**:
The choice in an HTML product model between showing appearance in a mockup and exercising behavior in an interactive prototype. The same content and structure can be shown in both modes. [html-prototype](../../../skills/html-prototype/SKILL.md#choose-the-fidelity-mode)

**Mockup**:
A polished, mostly static HTML artifact for judging appearance, such as layout, type and color. Controls can show how the interface will look before those controls perform any action. [html-prototype](../../../skills/html-prototype/SKILL.md#choose-the-fidelity-mode)
_Avoid_: `html-mockup` as a skill name.

**Interactive prototype**:
An HTML artifact with a working flow for a bounded scenario. A reviewer can enter data, trigger a state change or try recovery. The handoff names the modeled states and where the real product would take over. [html-prototype](../../../skills/html-prototype/SKILL.md)
_Avoid_: prototype alone when both an HTML fidelity mode and a throwaway experiment are under discussion.

### Design decisions and evidence

**Throwaway prototype**:
An experiment built to answer one design or behavior question. A timing script, a logic prototype and a set of UI variants can each answer a different question. The implementation carries forward the decision the experiment supports. [Prototype playbook](../../../skills/poteto-mode/playbooks/prototype.md)

**Logic prototype**:
A single shareable HTML file for trying business rules or state transitions. Free-play actions and resettable walkthroughs show the relevant state after each action. [Logic prototype](../../../skills/poteto-mode/references/prototype/logic.md)

**UI prototype**:
A comparison of structurally different interfaces on one route. The operator can switch variants, revisit one by URL and choose elements from several. If the decision depends on the real app, the prototype uses its surrounding page in an isolated checkout. [UI prototype](../../../skills/poteto-mode/references/prototype/ui.md)

**Prototype variant**:
One of the alternatives built for the same decision. For a visual comparison, each variant has a name and shares a switcher so a reviewer can try the alternatives and compare the tradeoffs. [Prototype playbook](../../../skills/poteto-mode/playbooks/prototype.md)

**Prototype evidence**:
What a prototype run shows about its question, such as a screenshot of each layout or a measured response time. For a logic or UI prototype, the runnable demo or full comparison is the primary source. A Wayfinder prototype ticket links the evidence alongside the operator's choice. A multi-phase plan records which question each observation answered and which questions remain open. [Prototype playbook](../../../skills/poteto-mode/playbooks/prototype.md) · [Multi-phase plan playbook](../../../skills/poteto-mode/playbooks/multi-phase-plan.md)

**Approved prototype**:
A prototype the operator accepts as the reference for a particular decision. The operator can use a timing run to set a target. When the operator approves a recovery interaction, the ticket links the prototype and the implemented interaction must match. [principle-baseline-is-the-contract](../../../skills/principle-baseline-is-the-contract/SKILL.md) · [to-tickets](../../../skills/to-tickets/SKILL.md#acceptance-criteria)

**Screenshot baseline**:
The reference screenshots frozen before the change. The baseline covers the current component across its states and includes the target when two implementations must match. [Visual parity playbook](../../../skills/poteto-mode/playbooks/visual-parity.md)
_Avoid_: baseline alone when an approved decision or a starting measurement could also be meant.

**Visual parity**:
Pixel-exact agreement between an implementation and its screenshot baseline for the same component states. An image diff must show zero differing pixels. [Visual parity playbook](../../../skills/poteto-mode/playbooks/visual-parity.md)

### Catch-ups

**Catch-up**:
A report of what changed in this chat since the operator's last message before the request. Subagent reports and notifications supply evidence within that window. The catch-up also includes older action items that still need the operator. [ketchup](../../../skills/ketchup/SKILL.md) · [ketchup-video](../../../skills/ketchup-video/SKILL.md)

**Action item**:
A decision or step only the operator can take. One recommendation can cover several items, such as approval to merge a set of PRs. Each item has its own outcome, evidence and risk. For a choice between options, each option has a gain and a cost. [ketchup](../../../skills/ketchup/SKILL.md#gather-what-changed)

**Visual**:
In a catch-up, a picture that shows a result or explains a relationship. Screenshots and recordings show what the work actually displayed. A diagram or chart can explain the facts already available. A Markdown table remains text. [ketchup](../../../skills/ketchup/SKILL.md#visuals)

**Catch-up video**:
A silent landscape video of up to ten slides built from the work's screenshots, recordings, diffs or data. Each slide makes one point, with its subtitle burned into a strip below the picture. The reply carries the operator's action items as text, including when the video cannot be rendered. [ketchup-video](../../../skills/ketchup-video/SKILL.md)

**Slide hold**:
The time a slide is fully visible in the rendered catch-up video, excluding transitions. Its minimum is one second per three words added. The subtitle and new or changed labels count. The first slide counts all its words. Text inside a screenshot is excluded throughout. [ketchup-video](../../../skills/ketchup-video/SKILL.md#render)

### Bot UIs

**Bot UI**:
A page whose controls ask a Grok Bot to take an action. A click reaches the page's local server, which sends the named action data to the bot's webhook routine. The page can be shared with peers on the operator's tailnet. [make-bot-ui](../../../skills/make-bot-ui/SKILL.md)

**Webhook routine**:
The saved Grok Bot routine whose prompt names the fields it accepts and the action they select. The routine treats submitted values as outside data and sends a message only when it has something to report. [make-bot-ui](../../../skills/make-bot-ui/SKILL.md#create-the-webhook-routine)

**Sender key**:
The credential that authorizes the bot UI's local server to wake one webhook routine. The operator supplies it privately for that routine. The key stays with the sending server. The bot receives the event body. [make-bot-ui](../../../skills/make-bot-ui/SKILL.md#request-the-sender-key)

**Webhook wake**:
The bot's routine turn triggered by the local server's submission. A successful submission confirms the routine woke. The routine reads the event body to decide what action to take and whether there is anything to report. [make-bot-ui](../../../skills/make-bot-ui/SKILL.md#handle-the-webhook-wake)
