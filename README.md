# Tibetan ↔ Western Calendar Converter

A small, self-contained web tool that converts dates between the **Tibetan
lunisolar calendar** and the **Western (Gregorian) calendar**, in both
directions, for both the **Phugpa** and **Tsurphu** traditions.

The calendar mathematics follow Svante Janson, *"Tibetan Calendar Mathematics"*
([arXiv:1401.6285](https://arxiv.org/abs/1401.6285)) — exact rational
arithmetic, no ephemeris required.

**Live demo:** <https://justdharma.org/tibcal/>

## Features

- **Western → Tibetan** and **Tibetan → Western** conversion.
- **Phugpa** (default) and **Tsurphu** traditions, selectable.
- Handles the calendar's irregularities honestly:
  - **leap months** (a doubled month) and **leap days** (a duplicated day) —
    ambiguous Tibetan dates prompt you to choose which day you mean;
  - **skipped days** — reported as "no such day" rather than guessed.
- Shows the traditional **element–animal year name** (e.g. *Fire Male Horse*),
  the **rabjung** 60-year cycle number, and the **Tibetan royal year** (Bod
  rGyal-lo, Gregorian + 127).
- Tibetan years are presented by the Western-year span they cover
  (e.g. `2026/27`), since a Tibetan year runs Losar-to-Losar and straddles two
  Western years.

## How it works

```
index.php  ──▶  api.php  ──▶  convert.py  ──▶  tibetan_calendar.py
 (UI)           (JSON)         (bridge)         (the algorithm)
```

- **`tibetan_calendar.py`** — pure-Python, standard-library-only implementation
  of Janson's algorithm (both traditions). This is the core; it has no web
  dependencies.
- **`convert.py`** — a thin JSON command-line wrapper around it, adding the
  year-name / rabjung / royal-year labelling. Always emits JSON.
- **`lib.php` / `api.php`** — PHP locates a Python 3 interpreter and shells out
  to `convert.py`, relaying its JSON.
- **`index.php` / `style.css` / `app.js`** — the front end. PHP renders the
  page (and seeds today's date); the small `app.js` does the fetch and renders
  results without page reloads.

## Requirements

- **PHP** (7+).
- **Python 3** (3.7+) — standard library only, no packages to install.

No database, no build step, no third-party libraries.

## Layout

The web application lives entirely under [`public/`](public/) — that is the
only directory your web server needs to expose. Everything else (this README,
the licence, repository metadata) stays outside the served path.

```
tibcal/
├── README.md
├── LICENSE
└── public/            ← web root
    ├── index.php
    ├── api.php
    ├── lib.php
    ├── app.js
    ├── style.css
    ├── convert.py
    └── tibetan_calendar.py
```

## Installation

Point your web server at the `public/` directory. The simplest deployment is to
clone the repository outside the web root and symlink `public/` into place:

```bash
git clone https://github.com/dorjeduck/tibcal.git
ln -s "$PWD/tibcal/public" /path/to/your/webroot/tibcal
# update later:  cd tibcal && git pull
```

If PHP cannot find `python3` automatically, copy `public/config.example.php` to
`public/config.php` and set the interpreter path:

```php
<?php define('PYTHON_BIN', '/usr/bin/python3');
```

`config.php` is gitignored — it is per-server and never committed.

## Development

Run locally with PHP's built-in server from inside `public/`:

```bash
cd public
php -S 127.0.0.1:8000
```

then open <http://127.0.0.1:8000/>.

The Python layer can be exercised directly:

```bash
cd public
python3 convert.py g2t --date 2026-06-16
python3 convert.py t2g --year 2026 --month 5 --day 1
python3 convert.py names --from 1900 --to 2100
```

`tibetan_calendar.py` is self-contained and dependency-free; it is validated
against published Losar dates (2023–2027) and round-trips cleanly for both
traditions.

## License

[MIT](LICENSE).

Found a date that looks wrong? Please
[open an issue](https://github.com/dorjeduck/tibcal/issues).
