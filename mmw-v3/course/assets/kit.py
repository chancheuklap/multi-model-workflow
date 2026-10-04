"""SVG helpers in the course's vocabulary (classes from the shared stylesheet)."""
import html, re

def tw(s, size=13, mono=False):
    w = 0.0
    for ch in s:
        if ord(ch) > 0x2E80:
            w += size
        else:
            w += size * (0.6 if mono else 0.56)
    return w

SIZES = {"s": 11.5, "m": 12.0, "h": 14.0}


def fits(text, cls, room):
    """Refuse a line wider than the room it is drawn in; monospace fallbacks run wider."""
    need = tw(text, SIZES[cls], cls == "m") * (1.12 if cls == "m" else 1.0)
    if need > room:
        raise ValueError(f"{text!r} needs {need:.0f}px and has {room}px")


def txt(f, x, y, t, cls="s", anchor="start", room=None):
    if room is not None:
        fits(t, cls, room)
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f.e(f'<text x="{x}" y="{y:.1f}" class="{cls}"{a}>{html.escape(t)}</text>')


def tbox(f, kind, x, y, w, title, lines, mono_title=False, dashed=False):
    """A box with a title and lines below it; returns its height."""
    h = 30 + len(lines) * 17
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"{dash}/></g>', False)
    txt(f, x + 12, y + 20, title, "m" if mono_title else "h", room=w - 20)
    for i, line in enumerate(lines):
        txt(f, x + 12, y + 39 + i * 17, line, room=w - 20)
    return h


class Fig:
    def __init__(self, mid, W):
        self.mid, self.W, self.back, self.front = mid, W, [], []
    def e(self, s, front=True):
        (self.front if front else self.back).append(s)
    def zone(self, x, y, w, h, title):
        self.e(f'<rect class="zone" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>', False)
        self.e(f'<text x="{x+12}" y="{y+19}" class="h">{html.escape(title)}</text>', False)
    def box(self, kind, x, y, w, h, title, sub=(), mono=False, head=False, cls="box"):
        out = [f'<g class="k-{kind}"><rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/>']
        lines = [title] + list(sub)
        ty = y + (h - (len(lines) - 1) * 16) / 2 + 4.5
        for i, t in enumerate(lines):
            c = ("h" if head else ("m" if mono else "")) if i == 0 else "s"
            out.append(f'<text x="{x+12}" y="{ty + i*16:.1f}" class="{c}">{html.escape(t)}</text>')
        out.append('</g>')
        self.e(''.join(out))
    def frame(self, kind, x, y, w, h, title, sub=(), mono=True):
        """A box whose lines sit at its top, leaving room below for chips or boxes drawn inside it."""
        self.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>', False)
        self.e(f'<text x="{x+12}" y="{y+21}" class="{"m" if mono else "h"}">{html.escape(title)}</text>')
        for i, t in enumerate(sub):
            self.e(f'<text x="{x+12}" y="{y+39 + i*16}" class="s">{html.escape(t)}</text>')
    def chip(self, kind, x, y, label, note=None, mono=True, cls="box"):
        w = tw(label, 11.5, mono) + (18 if mono else 24)
        tc = "m" if mono else "s"
        self.e(f'<g class="k-{kind}"><rect class="{cls}" x="{x}" y="{y}" width="{w:.1f}" height="24" rx="4"/>'
               f'<text x="{x+9}" y="{y+16.5}" class="{tc}">{html.escape(label)}</text></g>')
        if note:
            self.e(f'<text x="{x+w+8:.1f}" y="{y+16.5}" class="s">{html.escape(note)}</text>')
        return x + w
    def dia(self, cx, cy, hw, hh, lines):
        self.e(f'<polygon class="dia" points="{cx},{cy-hh} {cx+hw},{cy} {cx},{cy+hh} {cx-hw},{cy}"/>')
        y0 = cy + 4.5 - (len(lines) - 1) * 8.5
        for i, t in enumerate(lines):
            self.e(f'<text x="{cx}" y="{y0 + i*17:.1f}" text-anchor="middle">{html.escape(t)}</text>')
    def pill(self, cx, y, text, left=None):
        w = tw(text) + 34
        if left is not None:
            cx = left + w / 2
        self.e(f'<rect class="pill" x="{cx - w/2:.1f}" y="{y}" width="{w:.1f}" height="34" rx="17"/>'
               f'<text x="{cx:.1f}" y="{y+21.5}" text-anchor="middle">{html.escape(text)}</text>')
        return cx - w / 2, cx + w / 2
    def ar(self, pts, label=None, lx=None, ly=None, anchor="start", cls="", head=True):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        m = f' marker-end="url(#{self.mid})"' if head else ""
        c = ("ar " + cls).strip()
        self.e(f'<path class="{c}" d="{d}"{m}/>', False)
        if label:
            self.lbl(lx, ly, label, anchor)
    def att(self, pts):
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.e(f'<path class="att" d="{d}"/>', False)
    def lbl(self, x, y, t, anchor="start"):
        self.e(f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="lbl">{html.escape(t)}</text>')
    def note(self, x, y, t, anchor="start"):
        self.e(f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="s">{html.escape(t)}</text>')
    def svg(self, H, aria):
        return (f'<svg viewBox="0 0 {self.W} {H}" role="img" aria-label="{html.escape(aria)}">'
                f'<defs><marker id="{self.mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="head"/></marker></defs>'
                + ''.join(self.back) + ''.join(self.front) + '</svg>')


def flow(fig_id, heading, steps, left_head, exit_head):
    """One session's steps down the left, what each names in the middle, where it stops on the right."""
    f = Fig(fig_id, 1000)
    txt(f, 10, 20, heading, "h")
    y = 66
    rows = []
    for title, lines, uses, exit_, gap_before in steps:
        y += gap_before
        h = 30 + len(lines) * 17
        rows.append((y, h, title, lines, uses, exit_))
        y += max(h, len(uses) * 30) + 18
    bottom = y + 4
    f.zone(4, 34, 384, bottom - 34, left_head)
    f.zone(394, 34, 336, bottom - 34, "用到的")
    f.zone(736, 34, 260, bottom - 34, exit_head)
    for y, h, title, lines, uses, exit_ in rows:
        tbox(f, "playbook", 16, y, 360, title, lines)
        uy = y
        for kind, u in uses:
            f.e(f'<g class="k-{kind}"><rect class="box" x="406" y="{uy}" width="312" height="24" rx="4"/></g>', False)
            txt(f, 416, uy + 16, u, room=296)
            uy += 30
        if uses:
            f.ar([(376, y + 14), (404, y + 14)])
        if exit_:
            et, el = exit_
            tbox(f, "other", 748, y, 236, et, el + [""] * (len(lines) - len(el)), dashed=True)
            # Below a single chip the arrow runs along the step's foot; past a stack of chips
            # it runs through the 6px gap under the first one.
            ey = y + h - 10 if len(uses) < 2 else y + 27
            f.ar([(376, ey), (746, ey)])
    return f, rows, bottom
