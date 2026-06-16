"""Tibetan calendar helper (Phugpa and Tsurphu traditions).

Pure-Python, stdlib only. Implements Svante Janson, "Tibetan Calendar
Mathematics" (arXiv:1401.6285): Phugpa at the E806 epoch and Tsurphu at the
E1852 epoch, for which the paper gives fully explicit rational constants. No
ephemeris or external dependency is needed: the algorithm is exact integer /
rational arithmetic.

The Tibetan calendar is lunisolar. A synodic month has 30 *lunar days*
(``tithi``), but a calendar day runs dawn-to-dawn, so lunar days are
periodically **skipped** (``chad``, a lunar day wholly inside one calendar day)
or **duplicated** (``lhag``, a lunar day spanning an extra calendar day; the
first instance is the *leap day*). **Leap months** are inserted by the
intercalation rule. This stutter/repeat versus the Gregorian calendar is the
asymmetry the module exposes.

Both the Phugpa (epoch E806) and Tsurphu (epoch E1852) traditions are
implemented; all constants are transcribed verbatim from Janson (§3-5 and
Appendix A.2 respectively).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from fractions import Fraction
from typing import Optional

# Julian Day Number of proleptic-Gregorian 0001-01-01 minus 1
# (so jdn - _JDN_GREGORIAN_OFFSET == date.toordinal()).
# Verified via Gregorian 2000-01-01 == JDN 2451545, ordinal 730120.
_JDN_GREGORIAN_OFFSET = 1721425


class TibetanTradition(Enum):
    """Tibetan calendar tradition."""

    PHUGPA = "phugpa"
    TSURPHU = "tsurphu"


@dataclass(frozen=True)
class _Constants:
    """Janson's rational constants and intercalation rule for one tradition."""

    year0: int               # epoch Gregorian year (Y0)
    month0: int              # epoch month number (M0, always 3 — Remark 3)
    beta_star: int           # intercalation phase constant (beta*)
    m1: Fraction             # mean length of a lunar month (days)
    m2: Fraction             # mean length of a lunar day (= m1 / 30)
    m0: Fraction             # mean-date epoch constant (a Julian Day Number)
    s1: Fraction             # mean solar motion per month (circle fraction)
    s2: Fraction             # mean solar motion per lunar day (= s1 / 30)
    s0: Fraction             # mean-sun epoch constant
    a1: Fraction             # lunar-anomaly motion per month
    a2: Fraction             # lunar-anomaly motion per lunar day
    a0: Fraction             # lunar-anomaly epoch constant
    leap_ix: tuple[int, int]  # intercalation indices marking a leap month
    round_offset: int        # +17 for Phugpa (5.10); 0 for Tsurphu (A.9)


# Phugpa, epoch E806 (Y0 = 806, M0 = 3). Constants verbatim from Janson,
# "Tibetan Calendar Mathematics", §3-5; leap rule (5.8)/(5.10).
_PHUGPA = _Constants(
    year0=806,
    month0=3,
    beta_star=61,
    m1=Fraction(167025, 5656),
    m2=Fraction(167025, 5656) / 30,
    m0=2015501 + Fraction(4783, 5656),
    s1=Fraction(65, 804),
    s2=Fraction(65, 804) / 30,
    s0=Fraction(743, 804),
    a1=Fraction(253, 3528),
    a2=Fraction(1, 28),
    a0=Fraction(475, 3528),
    leap_ix=(48, 49),
    round_offset=17,
)

# Tsurphu, epoch E1852 (Y0 = 1852, M0 = 3). Same mean motions (m1/s1/a1) and
# astronomical functions as Phugpa; different epoch constants and the simpler
# leap rule (A.9): leap iff ix in {0, 1}, true month rounded down with no +17
# offset. Constants verbatim from Janson Appendix A.2, eqs (A.6)-(A.9).
_TSURPHU = _Constants(
    year0=1852,
    month0=3,
    beta_star=14,
    m1=Fraction(167025, 5656),
    m2=Fraction(167025, 5656) / 30,
    m0=2397598 + Fraction(1197103, 7635600),
    s1=Fraction(65, 804),
    s2=Fraction(65, 804) / 30,
    s0=Fraction(23, 27135),
    a1=Fraction(253, 3528),
    a2=Fraction(1, 28),
    a0=Fraction(1, 49),
    leap_ix=(0, 1),
    round_offset=0,
)

# moon equation table, base values for arguments 0..7 (Janson §4).
# Period 28, antisymmetric about 14: tab(14 - i) = tab(i), tab(14 + i) = -tab(i).
_MOON_TAB_BASE = (0, 5, 10, 15, 19, 22, 24, 25)

# sun equation table, base values for arguments 0..3 (Janson §4).
# Period 12, antisymmetric about 6: tab(6 - i) = tab(i), tab(6 + i) = -tab(i).
_SUN_TAB_BASE = (0, 6, 10, 11)


def _moon_tab(i: int) -> int:
    """Integer moon-equation table value at integer argument ``i`` (mod 28)."""
    i %= 28
    if i <= 7:
        return _MOON_TAB_BASE[i]
    if i <= 14:
        return _MOON_TAB_BASE[14 - i]
    if i <= 21:
        return -_MOON_TAB_BASE[i - 14]
    return -_MOON_TAB_BASE[28 - i]


def _sun_tab(i: int) -> int:
    """Integer sun-equation table value at integer argument ``i`` (mod 12)."""
    i %= 12
    if i <= 3:
        return _SUN_TAB_BASE[i]
    if i <= 6:
        return _SUN_TAB_BASE[6 - i]
    if i <= 9:
        return -_SUN_TAB_BASE[i - 6]
    return -_SUN_TAB_BASE[12 - i]


def _interp(arg: Fraction, table) -> Fraction:
    """Linear interpolation of an equation table at fractional ``arg``."""
    lo = arg.__floor__()
    frac = arg - lo
    a = table(lo)
    b = table(lo + 1)
    return a + (b - a) * frac


def _const(tradition: TibetanTradition) -> _Constants:
    return _PHUGPA if tradition is TibetanTradition.PHUGPA else _TSURPHU


@dataclass
class TibetanDate:
    """One Tibetan calendar day.

    A *skipped* lunar day has no calendar day, so ``gregorian`` is ``None``.
    A *leap day* is the first of a duplicated pair sharing the same number.
    """

    year: int
    month: int
    is_leap_month: bool
    day: int
    is_leap_day: bool
    is_skipped: bool
    gregorian: Optional[date]
    julian_day: int


@dataclass
class TibetanMonth:
    """One Tibetan month: its calendar days in order."""

    number: int
    is_leap_month: bool
    days: list[TibetanDate]


@dataclass
class TibetanYear:
    """Tibetan months overlapping a given Gregorian year."""

    western_year: int
    tradition: TibetanTradition
    months: list[TibetanMonth]


def _true_jdn(d: int, n: int, c: _Constants) -> int:
    """Julian Day Number of the calendar day ending lunar day ``d`` of true
    month ``n`` (Janson §5: floor of ``true_date``)."""
    mean_date = n * c.m1 + d * c.m2 + c.m0
    mean_sun = n * c.s1 + d * c.s2 + c.s0
    anomaly_moon = n * c.a1 + d * c.a2 + c.a0
    anomaly_sun = mean_sun - Fraction(1, 4)

    moon_equ = _interp((anomaly_moon % 1) * 28, _moon_tab)
    sun_equ = _interp((anomaly_sun % 1) * 12, _sun_tab)

    true_date = mean_date + moon_equ / 60 - sun_equ / 60
    return true_date.__floor__()


def _month_instances(year: int, month: int, c: _Constants) -> list[tuple[int, bool]]:
    """True-month instances for Tibetan ``(year, month)`` (Janson §5).

    A normal month yields one ``(n, is_leap=False)``. When the intercalation
    rule marks this month name as doubled, it yields the leap month first
    ``(n, True)`` then its regular partner ``(n + 1, False)``.
    """
    m_star = 12 * (year - c.year0) + month - c.month0
    ix = (2 * m_star + c.beta_star) % 65
    is_leap = ix in c.leap_ix
    n = (67 * m_star + c.beta_star + c.round_offset) // 65 - (1 if is_leap else 0)
    if is_leap:
        return [(n, True), (n + 1, False)]
    return [(n, False)]


def _build_month(year: int, month: int, n: int, is_leap: bool,
                  c: _Constants) -> TibetanMonth:
    """Build one Tibetan month (given its true-month count) with
    skip/duplicate resolution."""
    # JDN of the calendar day ending each lunar day 0..30 (0 = end of prev month).
    jdn = [_true_jdn(d, n, c) for d in range(0, 31)]

    days: list[TibetanDate] = []
    for d in range(1, 31):
        prev, cur = jdn[d - 1], jdn[d]
        if cur == prev:
            # Lunar day wholly inside one calendar day -> skipped, no date.
            days.append(TibetanDate(year, month, is_leap, d, False, True,
                                     None, cur))
            continue
        if cur - prev >= 2:
            # Duplicated: an extra calendar day carries this number first
            # (the leap day), then the regular one.
            leap_jdn = prev + 1
            days.append(TibetanDate(
                year, month, is_leap, d, True, False,
                date.fromordinal(leap_jdn - _JDN_GREGORIAN_OFFSET), leap_jdn))
        days.append(TibetanDate(
            year, month, is_leap, d, False, False,
            date.fromordinal(cur - _JDN_GREGORIAN_OFFSET), cur))

    return TibetanMonth(number=month, is_leap_month=is_leap, days=days)


def tibetan_calendar_for_year(
    western_year: int,
    tradition: TibetanTradition = TibetanTradition.PHUGPA,
) -> TibetanYear:
    """Full Tibetan calendar whose calendar days fall in ``western_year``.

    Iterates Tibetan months over a three-year window, keeps every month that
    contributes at least one calendar day inside ``western_year``, and exposes
    each day's skip / duplicate / leap-month status.

    Args:
        western_year: Gregorian year to cover.
        tradition: Tibetan tradition.

    Returns:
        A ``TibetanYear`` with the contributing ``TibetanMonth`` objects in
        chronological order. Months may carry days slightly outside the year
        at the boundaries; ``TibetanMonth.is_leap_month`` flags leap months.
    """
    c = _const(tradition)
    months: list[TibetanMonth] = []
    for y in (western_year - 1, western_year, western_year + 1):
        for m in range(1, 13):
            for n, is_leap in _month_instances(y, m, c):
                tm = _build_month(y, m, n, is_leap, c)
                if any(td.gregorian is not None
                       and td.gregorian.year == western_year
                       for td in tm.days):
                    months.append(tm)
    months.sort(key=lambda tm: next(
        td.julian_day for td in tm.days if td.gregorian is not None))
    return TibetanYear(western_year, tradition, months)


def gregorian_to_tibetan(
    g: date,
    tradition: TibetanTradition = TibetanTradition.PHUGPA,
) -> TibetanDate:
    """Convert a Gregorian date to its Tibetan calendar day.

    Args:
        g: Gregorian date.
        tradition: Tibetan tradition.

    Returns:
        The matching ``TibetanDate`` (never a skipped day).

    Raises:
        ValueError: if no Tibetan calendar day maps to ``g`` (should not occur).
    """
    c = _const(tradition)
    target = g.toordinal() + _JDN_GREGORIAN_OFFSET
    for y in (g.year - 1, g.year, g.year + 1):
        for m in range(1, 13):
            for n, is_leap in _month_instances(y, m, c):
                for td in _build_month(y, m, n, is_leap, c).days:
                    if td.julian_day == target and not td.is_skipped:
                        return td
    raise ValueError(f"no Tibetan calendar day maps to {g.isoformat()}")


def tibetan_to_gregorian(
    t: TibetanDate,
    tradition: TibetanTradition = TibetanTradition.PHUGPA,
) -> date:
    """Convert a ``TibetanDate`` back to its Gregorian date.

    Args:
        t: A non-skipped Tibetan date (only ``year``, ``month``, ``day``,
            ``is_leap_month``, ``is_leap_day`` are used).
        tradition: Tibetan tradition.

    Returns:
        The Gregorian date.

    Raises:
        ValueError: if ``t`` is a skipped day or cannot be located.
    """
    if t.is_skipped:
        raise ValueError("skipped Tibetan day has no Gregorian date")
    c = _const(tradition)
    for n, is_leap in _month_instances(t.year, t.month, c):
        if is_leap != t.is_leap_month:
            continue
        for td in _build_month(t.year, t.month, n, is_leap, c).days:
            if (td.day == t.day
                    and td.is_leap_day == t.is_leap_day
                    and td.gregorian is not None):
                return td.gregorian
    raise ValueError(
        f"Tibetan date {t.year}-{t.month}-{t.day} "
        f"(leap_month={t.is_leap_month}, leap_day={t.is_leap_day}) not found"
    )
