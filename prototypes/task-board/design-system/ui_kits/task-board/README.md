# Task board UI kit

The MMW task board rebuilt from this design system's components: `index.html` is the board after a night, `Board-settings.html` the same board with the settings sheet open. Each of the five regions also stands alone at its page size as a starting point (`TopBar.html` 1440×52, `TaskList.html` 236×848, `Canvas.html` 864×848, `Detail.html` 340×848, `Settings.html` 1440×900).

The screens are in `screens.jsx`. They compute what to show with the product's own page logic (`lib/board.js`, bundled from `mmw-v2/board/page/`) over example data (`data/`, built by `prototypes/task-board/553/UI/build_scenes.py` with the pipeline's own event code), so the kit shows exactly what the product would for that data.
