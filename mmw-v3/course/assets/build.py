"""Refill the shared blocks of every course page from ./assets and ./figures.

A page carries what it uses, so it still renders when opened away from this folder:
- <!--CSS-->...<!--/CSS--> gets assets/course.css inside a <style>;
- <!--JS-->...<!--/JS--> gets assets/course.js inside a <script>;
- <!--FIG:name-->...<!--/FIG:name--> gets the SVG that figures/*.py returns under that name;
- every mention of a component is marked with its kind by assets/tag.py, so it is coloured like the figures.

Each figures/*.py module defines FIGS = {name: function returning an SVG string}.
Run after editing a component or a figure: python3 assets/build.py
"""
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "assets"))
import tag  # noqa: E402


def load_figures():
    figs = {}
    for path in sorted((ROOT / "figures").glob("*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name, fn in mod.FIGS.items():
            if name in figs:
                sys.exit(f"figure {name} is defined twice")
            figs[name] = fn
    return figs


def main():
    css = (ROOT / "assets" / "course.css").read_text()
    js = (ROOT / "assets" / "course.js").read_text()
    figs = load_figures()
    pages = [ROOT / "index.html", *sorted((ROOT / "lessons").glob("*.html")), *sorted((ROOT / "reference").glob("*.html"))]
    for page in pages:
        if not page.exists():
            continue
        text = page.read_text()
        text = re.sub(r"<!--CSS-->.*?<!--/CSS-->", lambda m: f"<!--CSS--><style>\n{css}</style><!--/CSS-->", text, flags=re.S)
        text = re.sub(r"<!--JS-->.*?<!--/JS-->", lambda m: f"<!--JS--><script>\n{js}</script><!--/JS-->", text, flags=re.S)

        def fig(m):
            name = m.group(1)
            if name not in figs:
                sys.exit(f"{page.name}: no figure named {name}")
            return f"<!--FIG:{name}-->{figs[name]()}<!--/FIG:{name}-->"

        text = re.sub(r"<!--FIG:([\w-]+)-->.*?<!--/FIG:\1-->", fig, text, flags=re.S)
        text = tag.tag(text)
        page.write_text(text)
        print(f"built {page.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
