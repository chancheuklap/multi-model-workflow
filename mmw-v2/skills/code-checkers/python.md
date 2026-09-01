# Python

`ruff` for lint and format, `pyrefly` for types, `djlint` for Jinja/Django templates. All three through the project's dev dependency group, installed by `uv sync`.

```toml
[dependency-groups]
dev = [
    "ruff==0.16.5",        # also the formatter — exact pin
    "pyrefly>=1.0,<2.0",
    "djlint>=1.39,<2.0",   # only if the repo renders templates
]
```

## ruff

```toml
[tool.ruff]
target-version = "py311"
extend-exclude = ["archive"]   # whatever the test runner already ignores
```

`ruff` 0.16 enables 413 rules by default (up from 59 in 0.15). Leave them on — most of the count is machine-fixable, and the families that remain tend to be the ones that matter. Two calibrations:

**Line length.** Measure before choosing. Widening past the default usually *increases* the diff, because the formatter rejoins calls the old width had split. Compare before committing:

```bash
for w in 88 100 120; do
  printf '%s: ' "$w"
  uvx ruff@<version> format --check --line-length "$w" <paths> 2>&1 | tail -1
done
```

**Framework idioms.** A framework that puts calls in parameter defaults trips `B008` on every route. Exempt the specific calls, never the rule — a genuine mutable default must still be caught:

```toml
[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = [
    "fastapi.Body", "fastapi.Cookie", "fastapi.Depends", "fastapi.File",
    "fastapi.Form", "fastapi.Header", "fastapi.Path", "fastapi.Query",
    "fastapi.Security",
]
```

Rules worth reading rather than fixing in bulk, because each one names a place the code can lose an error or a fact: `BLE001` blind `except Exception`, `S110`/`S112` `except: pass` and `except: continue`, `B023` a closure capturing a loop variable, `DTZ` a naive `datetime` in a system that spans machines or handles money.

## pyrefly

```toml
[tool.pyrefly]
project-includes = ["src", "tests", "scripts", "migrations"]
project-excludes = ["**/archive/**", "**/.venv/**", "**/node_modules/**", "**/__pycache__/**"]
python-version = "3.11"
search-path = ["src", "."]
baseline = "pyrefly-baseline.json"
```

**`search-path` is where most of a first run comes from.** pyrefly infers one import root from the project layout — typically `src`. Scripts that import each other by repo-relative path (`scripts.dev.common`) resolve against the repository root instead, and every one of those imports fails until the root is on the path. Fix this before reading a single error.

**Dependencies absent by design.** A package behind an optional extra, or behind a `sys_platform` marker, is unresolvable on this machine and always will be. Say so, rather than leaving the errors:

```toml
replace-imports-with-any = ["cv2", "onnxruntime", "onnxruntime.*"]
```

**Baseline, not `pyrefly suppress`.** `suppress` writes an ignore comment at every site — thousands of lines of source noise. The baseline is one file the tool reads:

```bash
uv run pyrefly check --baseline=pyrefly-baseline.json --update-baseline   # record
uv run pyrefly check                                                      # only new errors
uv run pyrefly check --baseline=pyrefly-baseline.json --prune-baseline    # shrink after fixes
```

Commit the baseline; it belongs to the branch like the config does.

## djlint

```toml
[tool.djlint]
profile = "jinja"
ignore = "..."
```

Most of a first run is style opinion that buries the two things djlint is actually worth having: **syntax** (an unclosed tag, a mismatched block) and **accessibility** (an image with no alt text). Read the rule distribution and turn off what does not apply — rules naming another framework's helpers (`url_for` is Flask's; a FastAPI app has no such function), inline-style warnings in a project whose inline styles carry computed values, empty-tag warnings where empty tags are the icon-font convention, SEO hints on pages behind a login.

The target is a clean run, so that the next non-zero count means something.

## Commands

```bash
uv run ruff format <paths>            # writes
uv run ruff format --check <paths>    # reports
uv run ruff check <paths>
uv run ruff check --fix <paths>
uv run pyrefly check
uv run djlint <template-dir> --lint
```
