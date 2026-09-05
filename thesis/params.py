"""The running code's own constants, for chapters that state parameter values.

Chapters 5 and 6 quote a lot of numbers that are not measurements but *settings* — the
scenario counts, the seeds, R&P's score increments, the iteration budget. Those live in
`code/config.py`, and retyping them into prose has the same failure mode as retyping a
measurement: the text keeps saying 300 iterations long after the default changed, and
nothing in the document can reveal it.

So the chapters import the real module. `code/` is not a package and its modules import
their siblings by bare name, so the directory goes on `sys.path` rather than being
imported through a parent package.

Only `config` is pulled in deliberately: it is the one module with no side effects and no
heavy dependencies, so a thesis build never drags in igraph or reads a graph.
"""

import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

import config  # noqa: E402  (path must be set first)


def hr(value, decimals: int = 0) -> str:
    """A number formatted for Croatian prose: decimal comma, dot for thousands, and a
    real minus sign rather than the ASCII hyphen Python produces."""
    text = f"{value:,.{decimals}f}"
    return (text.replace(",", " ").replace(".", ",").replace(" ", ".")
                .replace("-", "−"))


def count(value, one: str, few: str, many: str) -> str:
    """Croatian numeral agreement: 1 brid, 22 brida, 411 bridova.

    The form follows the last digit, except that 11–14 always take the plural. Duplicated
    from chapter 2 deliberately — that copy formats measurements read from CSV, this one
    formats settings, and merging them would couple two chapters that share nothing else.
    """
    n = int(value)
    if 11 <= n % 100 <= 14:
        return f"{hr(n)} {many}"
    last = n % 10
    if last == 1:
        return f"{hr(n)} {one}"
    if last in (2, 3, 4):
        return f"{hr(n)} {few}"
    return f"{hr(n)} {many}"
