---
version: alpha
name: MMW Task Board
description: The local, read-only task board of the landing pipeline — paper and ink, with one alarm colour.
colors:
  paper: "#f3f3f1"
  canvas: "#ebecee"
  panel: "#ffffff"
  ink: "#2d3142"
  muted: "#4f5d75"
  soft: "#7a8399"
  faint: "#a3aabb"
  rule: "#2d31421f"
  line-grey: "#2d31424d"
  orange: "#eb6c36"
  orange-ink: "#b8471a"
  led-green: "#22a06b"
  led-green-ink: "#17784f"
  led-red: "#c9304f"
  closeout: "#5e7a9b"
  s-working: "#7c8f6f"
  s-waiting: "#9a8c58"
  s-review: "#7b6a9b"
  s-verify: "#4f8783"
typography:
  sans:
    fontFamily: Geist
  mono:
    fontFamily: Geist Mono
  serif:
    fontFamily: Instrument Serif
omitted:
  - section: rounded
    reason: "No named radius tokens; card and pill radii are local values."
  - section: spacing
    reason: "No named spacing scale."
---

## Overview

The task board is a local web page that reads the issue tracker and never writes to it. It shows one discussion's tickets as a pan-and-zoom canvas between a task list and a detail panel, so the owner can tell at a glance which tickets need them. The look is paper and ink: quiet neutrals carry every surface and every word, and colour is spent only on state.

## Colors

- **Ink (`ink`) on paper (`paper`, `canvas`, `panel`)** carries all text and surfaces. `muted`, `soft` and `faint` step text down by importance; `rule` separates regions.
- **Orange (`orange`, `orange-ink`) means "needs you" and nothing else.** It is the lamp colour for a ticket waiting on the owner and the text colour of that lamp's word. Selection, focus and emphasis use ink.
- **Green (`led-green`, `led-green-ink`) means "running".** The lamp of a running ticket and the moving blocking line into it share this one green.
- **Red (`led-red`) marks a blocking line whose blocker has not landed.** It is a crimson kept visibly apart from the orange lamp.
- **Grey (`line-grey`) draws containment and paths already walked**: the trunk, the lines from a container to its issues, and blocking lines whose blocker has landed while the blocked ticket is not running.
- **Step pills each take their own muted hue** (`s-working`, `s-waiting`, `s-review`, `s-verify`); `queued` is an outline and `landed` is solid ink. None of them is orange.
- **`closeout` is the inner bar on a card opened in the closeout round.**

## Typography

- **Geist (`sans`)** sets titles, labels and prose.
- **Geist Mono (`mono`)** sets everything a reader matches against the tracker: issue numbers, step names, event names, `host · model · effort`, times and counts.
- **Instrument Serif (`serif`)** appears only in the wordmark and in the title of an empty state.

## Layout

Three columns: tasks on the left, the canvas in the middle, details on the right. On the canvas a vertical trunk holds the containers (the map and its specs); a container opens to the right into its own issues, and blocking chains always read left to right. Child issues are listed in the detail panel and never drawn on the canvas.

## Components

- **Lamp**: one dot answering "does this need me" — orange needs you, green running, ink done, hollow not dispatched. The same lamp appears on task rows, containers, tickets, child rows and every event row.
- **Pill**: a capsule that names the current step (`queued`, `working`, `waiting`, `review`, `verify`, `landed`). A card shows only the current pill; the detail panel lays out the whole path with the current step bold and coloured and the rest grey.
- **Ticket card**: three rows — lamp, number and pill on top; the title, the largest text on the card, in the middle; `host · model · effort` at the bottom. A decision-ticket card is one row shorter and shows its kind where a ticket shows its pill.
- **Blocking line**: a smooth curve from the blocker's right edge into the blocked card's left edge with a small dot at each end and no arrowhead. A moving line carries a white-headed green comet toward the blocked card.

## Do's and Don'ts

- Don't use orange for anything but the "needs you" lamp and its word.
- Don't draw a segmented progress bar for a ticket's steps; name the step in the pill.
- Don't mark a closeout-round ticket with a text badge; use the `closeout` inner bar.
- Don't draw child issues on the canvas.
