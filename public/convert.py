#!/usr/bin/env python3
"""JSON bridge between the PHP front-end and ``tibetan_calendar.py``.

Pure stdlib, no third-party dependencies, so it runs on any Python 3.7+.
Invoked by ``api.php`` via the shell; reads conversion parameters from CLI
arguments and writes a single JSON object to stdout. All error conditions are
reported as ``{"ok": false, "error": "..."}`` (never a non-zero exit), so the
PHP layer only has to decode JSON.

Two directions:

* ``g2t`` — Gregorian (Western) -> Tibetan
* ``t2g`` — Tibetan -> Gregorian (Western)

Both accept ``--tradition phugpa|tsurphu``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from tibetan_calendar import (
    TibetanDate,
    TibetanTradition,
    gregorian_to_tibetan,
)
# Building blocks for enumerating every real calendar day of a Tibetan month
# (handles doubled leap months and duplicated leap days).
from tibetan_calendar import _build_month, _const, _month_instances

# --- Tibetan year names (rabjung cycle) ------------------------------------
#
# Independent of the day-level astronomy in tibetan_calendar.py: the year name
# is a fixed 60-year sexagenary labelling — 12 animals x 5 elements (each
# element spanning two consecutive years, male then female). The cycle epoch is
# the first rabjung, whose year 1 is the Fire-Hare year = Gregorian 1027 CE.
# (Svante Janson, "Tibetan Calendar Mathematics", arXiv:1401.6285, year-naming
# section; standard Tibetan calendrics.) These are the convention's own
# constants, not free parameters — verified against known anchors:
# 2020 = Iron-Rat, 2024 = Wood-Dragon, 2026 = Fire-Horse.

_ANIMALS = ("Rat", "Ox", "Tiger", "Hare", "Dragon", "Snake",
            "Horse", "Sheep", "Monkey", "Bird", "Dog", "Pig")
# Forward element cycle (each element lasts two years).
_ELEMENTS = ("Wood", "Fire", "Earth", "Iron", "Water")
_RABJUNG_EPOCH = 1027   # Gregorian year of rabjung 1, year 1 (Fire-Hare).
_ANIMAL_EPOCH = 2020    # Iron-Rat: anchors the 12-animal phase.
_ELEMENT_EPOCH = 2024   # Wood-Dragon: anchors the 5-element (x2) phase.
# Tibetan royal year (Bod rGyal lo): Gregorian year + 127 (2026 -> 2153).
_ROYAL_OFFSET = 127


def year_name(western_year: int) -> dict:
    """Tibetan year name for the Tibetan year numbered ``western_year``.

    ``western_year`` is the year in which the Tibetan year's Losar falls, which
    is exactly ``TibetanDate.year`` as produced by ``tibetan_calendar.py``.
    """
    animal = _ANIMALS[(western_year - _ANIMAL_EPOCH) % 12]
    element = _ELEMENTS[((western_year - _ELEMENT_EPOCH) % 10) // 2]
    gender = "male" if (western_year - _ELEMENT_EPOCH) % 2 == 0 else "female"
    rabjung_cycle = (western_year - _RABJUNG_EPOCH) // 60 + 1
    # A Tibetan year runs Losar-to-Losar, so it spans this Western year and the
    # next; "2026/27" makes that explicit.
    span = f"{western_year}/{(western_year + 1) % 100:02d}"
    full_name = f"{element} {gender.capitalize()} {animal}"
    return {
        "element": element,
        "animal": animal,
        "gender": gender,
        "span": span,
        "full_name": full_name,            # "Fire Male Horse"
        "label": f"{span} · {full_name}",  # "2026/27 · Fire Male Horse"
        "rabjung_cycle": rabjung_cycle,
        "royal_year": western_year + _ROYAL_OFFSET,
    }


# --- serialisation ----------------------------------------------------------

def _tradition(name: str) -> TibetanTradition:
    return (TibetanTradition.TSURPHU if name == "tsurphu"
            else TibetanTradition.PHUGPA)


def _tibetan_payload(td: TibetanDate) -> dict:
    return {
        "year": td.year,
        "month": td.month,
        "is_leap_month": td.is_leap_month,
        "day": td.day,
        "is_leap_day": td.is_leap_day,
        "year_name": year_name(td.year),
    }


def _gregorian_payload(g: date) -> dict:
    return {
        "iso": g.isoformat(),
        "year": g.year,
        "month": g.month,
        "day": g.day,
        "weekday": g.strftime("%A"),
        "display": g.strftime("%A, %-d %B %Y"),
    }


def _candidate_label(td: TibetanDate) -> str:
    """Human label distinguishing one resolution of an ambiguous Tibetan date."""
    month_part = ("Leap month " if td.is_leap_month else "Month ") + str(td.month)
    day_part = f"day {td.day}" + (" (leap day)" if td.is_leap_day else "")
    return f"{month_part}, {day_part}"


def _t2g_candidates(year: int, month: int, day: int,
                    tradition: TibetanTradition) -> list[TibetanDate]:
    """Every real calendar day matching (year, month, day).

    A normal date yields exactly one; a leap month and/or a duplicated leap day
    can yield several; a skipped or non-existent day yields none. Leap instances
    come first (``_month_instances`` lists the leap month before its partner,
    and ``_build_month`` lists a leap day before its regular twin).
    """
    c = _const(tradition)
    out: list[TibetanDate] = []
    for n, is_leap in _month_instances(year, month, c):
        for td in _build_month(year, month, n, is_leap, c).days:
            if td.day == day and not td.is_skipped and td.gregorian is not None:
                out.append(td)
    return out


# --- main -------------------------------------------------------------------

def _run(args: argparse.Namespace) -> dict:
    tradition = _tradition(args.tradition)

    if args.mode == "names":
        # Tibetan year labels for a Western-year range (drives the year picker).
        # Tradition-independent: year naming is the same for Phugpa and Tsurphu.
        if args.to_year < args.from_year:
            raise ValueError("'to' must not be before 'from'")
        return {
            "ok": True,
            "mode": "names",
            "years": [
                {"year": y, "label": year_name(y)["label"]}
                for y in range(args.from_year, args.to_year + 1)
            ],
        }

    if args.mode == "g2t":
        g = date.fromisoformat(args.date)
        td = gregorian_to_tibetan(g, tradition)
        return {
            "ok": True,
            "mode": "g2t",
            "tradition": args.tradition,
            "input": _gregorian_payload(g),
            "result": _tibetan_payload(td),
        }

    # t2g
    if not 1 <= args.month <= 12:
        raise ValueError("month must be between 1 and 12")
    if not 1 <= args.day <= 30:
        raise ValueError("day must be between 1 and 30")

    candidates = [
        {
            "is_leap_month": td.is_leap_month,
            "is_leap_day": td.is_leap_day,
            "label": _candidate_label(td),
            "result": _gregorian_payload(td.gregorian),
        }
        for td in _t2g_candidates(args.year, args.month, args.day, tradition)
    ]
    return {
        "ok": True,
        "mode": "t2g",
        "tradition": args.tradition,
        "input": {
            "year": args.year,
            "month": args.month,
            "day": args.day,
            "year_name": year_name(args.year),
        },
        "candidates": candidates,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Tibetan calendar JSON converter")
    p.add_argument("--tradition", choices=("phugpa", "tsurphu"),
                   default="phugpa")
    sub = p.add_subparsers(dest="mode", required=True)

    g = sub.add_parser("g2t", help="Gregorian -> Tibetan")
    g.add_argument("--date", required=True, help="ISO date YYYY-MM-DD")

    t = sub.add_parser("t2g", help="Tibetan -> Gregorian")
    t.add_argument("--year", type=int, required=True)
    t.add_argument("--month", type=int, required=True)
    t.add_argument("--day", type=int, required=True)

    n = sub.add_parser("names", help="Tibetan year labels for a range")
    n.add_argument("--from", type=int, dest="from_year", required=True)
    n.add_argument("--to", type=int, dest="to_year", required=True)

    args = p.parse_args()
    try:
        out = _run(args)
    except ValueError as exc:
        out = {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — surface any failure as JSON
        out = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    json.dump(out, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
