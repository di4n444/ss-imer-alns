"""Citation keys resolved to the numbers used in the bibliography.

Chapters cite by name - "{kempe2003}" inside a sentence - and the number is substituted
when the paragraph is written. Writing "[7]" by hand would mean every citation silently
becomes wrong the moment a source is inserted into the list, and there is no way to notice
that by reading the text.

The order here IS the order of the "Literatura" list in the document, which the faculty
template orders chronologically. Changing one means changing the other.
"""

SOURCES = [
    ("erdos1960", "Erdős, Rényi (1960)"),
    ("granovetter1973", "Granovetter (1973)"),
    ("valiant1979", "Valiant (1979)"),
    ("watts1998", "Watts, Strogatz (1998)"),
    ("albert2000", "Albert, Jeong, Barabási (2000)"),
    ("albert2002", "Albert, Barabási (2002)"),
    ("kempe2003", "Kempe, Kleinberg, Tardos (2003)"),
    ("wang2003", "Wang i sur. (2003)"),
    ("ropke2006", "Røpke, Pisinger (2006)"),
    ("kimura2008", "Kimura i sur. (2008)"),
    ("antulov2008", "Antulov-Fantulin (2008)"),
    ("castellano2010", "Castellano, Pastor-Satorras (2010)"),
    ("sheldon2010", "Sheldon i sur. (2010)"),
    ("tong2012", "Tong i sur. (2012)"),
    ("khalil2014", "Khalil, Dilkina, Song (2014)"),
    ("kumar2016", "Kumar i sur. (2016)"),
    ("kumar2018", "Kumar i sur. (2018)"),
    ("coro2021", "Coró i sur. (2021)"),
    ("castiglioni2021", "Castiglioni i sur. (2021)"),
    ("predavanja", "Predavanja, Kompleksne mreže"),
]

NUMBER = {key: n for n, (key, _) in enumerate(SOURCES, start=1)}


def cite(*keys) -> str:
    """"[7]" for one source, "[16, 17]" for several, always in bibliography order."""
    numbers = sorted(NUMBER[key] for key in keys)
    return "[" + ", ".join(str(n) for n in numbers) + "]"


def expand(text: str) -> str:
    """Replace every "{key}" in a sentence with its citation number.

    Several keys in one bracket are written "{kumar2016,kumar2018}" and collapse to a
    single "[16, 17]", which is how the template's examples group co-cited sources."""
    if "{" not in text:
        return text
    out, rest = [], text
    while "{" in rest:
        head, _, tail = rest.partition("{")
        key, _, rest = tail.partition("}")
        out.append(head)
        keys = [k.strip() for k in key.split(",")]
        unknown = [k for k in keys if k not in NUMBER]
        if unknown:
            raise KeyError(f"unknown citation key(s): {unknown}")
        out.append(cite(*keys))
    out.append(rest)
    return "".join(out)
