"""Citations by key, rendered as author-year.

Chapters write "{kempe2003}" for a parenthetical citation and "{~kempe2003}" when the
authors are the subject of the sentence, and the text is substituted at build time.
Writing citations by hand would mean silently citing the wrong source the moment the
bibliography changes; the first draft of chapter 1 did exactly that, with eight of fifteen
citations pointing somewhere else.

Author-year rather than numeric so a claim can be checked against its source while
reading, without jumping to the bibliography each time.
"""

# key: (parenthetical form, narrative form, year)
SOURCES = [
    ("erdos1960", "Erdős i Rényi", 1960),
    ("granovetter1973", "Granovetter", 1973),
    ("valiant1979", "Valiant", 1979),
    ("watts1998", "Watts i Strogatz", 1998),
    ("albert2000", "Albert i sur.", 2000),
    ("albert2002", "Albert i Barabási", 2002),
    ("kempe2003", "Kempe i sur.", 2003),
    ("wang2003", "Wang i sur.", 2003),
    ("ropke2006", "Røpke i Pisinger", 2006),
    ("kimura2008", "Kimura i sur.", 2008),
    ("antulov2008", "Antulov-Fantulin", 2008),
    ("castellano2010", "Castellano i Pastor-Satorras", 2010),
    ("sheldon2010", "Sheldon i sur.", 2010),
    ("tong2012", "Tong i sur.", 2012),
    ("khalil2014", "Khalil i sur.", 2014),
    ("kumar2016", "Kumar i sur.", 2016),
    ("kumar2018", "Kumar i sur.", 2018),
    ("coro2021", "Coró i sur.", 2021),
    ("castiglioni2021", "Castiglioni i sur.", 2021),
    ("predavanja", "Predavanja, Kompleksne mreže", None),
]

AUTHORS = {key: authors for key, authors, _ in SOURCES}
YEAR = {key: year for key, _, year in SOURCES}


def _one(key: str) -> str:
    year = YEAR[key]
    return f"{AUTHORS[key]}, {year}" if year else AUTHORS[key]


def cite(*keys) -> str:
    """Parenthetical: "(Kempe i sur., 2003)", or several separated by a semicolon."""
    return "(" + "; ".join(_one(key) for key in keys) + ")"


def narrative(key: str) -> str:
    """In-sentence: "Kempe i sur. (2003) pokazuju da ..." - used when the authors are the
    grammatical subject, where a parenthetical citation would repeat their names."""
    year = YEAR[key]
    return f"{AUTHORS[key]} ({year})" if year else AUTHORS[key]


def expand(text: str) -> str:
    """Substitute every "{key}" and "{~key}" in a sentence.

    Co-cited sources share one bracket: "{wang2003,castellano2010}" becomes
    "(Wang i sur., 2003; Castellano i Pastor-Satorras, 2010)"."""
    if "{" not in text:
        return text
    out, rest = [], text
    while "{" in rest:
        head, _, tail = rest.partition("{")
        body, _, rest = tail.partition("}")
        out.append(head)
        if body.startswith("~"):
            key = body[1:].strip()
            if key not in AUTHORS:
                raise KeyError(f"unknown citation key: {key}")
            out.append(narrative(key))
        else:
            keys = [k.strip() for k in body.split(",")]
            unknown = [k for k in keys if k not in AUTHORS]
            if unknown:
                raise KeyError(f"unknown citation key(s): {unknown}")
            out.append(cite(*keys))
    out.append(rest)
    return "".join(out)
