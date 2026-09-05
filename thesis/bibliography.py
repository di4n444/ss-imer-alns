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
    ("clauset2009", "Clauset i sur.", 2009),
    ("antulov2008", "Antulov-Fantulin", 2008),
    ("castellano2010", "Castellano i Pastor-Satorras", 2010),
    ("sheldon2010", "Sheldon i sur.", 2010),
    ("tong2012", "Tong i sur.", 2012),
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


# Full bibliography entries, in the faculty template's citation format.
ENTRIES = {
    "erdos1960":
        "Erdős, P., Rényi, A. On the Evolution of Random Graphs. Publicationes Mathematicae Debrecen, vol. 6, 1960.",
    "granovetter1973":
        "Granovetter, M. S. The Strength of Weak Ties. American Journal of Sociology, vol. 78, br. 6, 1973.",
    "valiant1979":
        "Valiant, L. G. The complexity of enumeration and reliability problems. SIAM Journal on Computing, vol. 8, br. 3, 1979.",
    "watts1998":
        "Watts, D. J., Strogatz, S. H. Collective dynamics of 'small-world' networks. Nature, vol. 393, 1998.",
    "albert2000":
        "Albert, R., Jeong, H., Barabási, A.-L. Error and attack tolerance of complex networks. Nature, vol. 406, 2000.",
    "albert2002":
        "Albert, R., Barabási, A.-L. Statistical mechanics of complex networks. Reviews of Modern Physics, vol. 74, br. 1, 2002.",
    "kempe2003":
        "Kempe, D., Kleinberg, J., Tardos, É. Maximizing the Spread of Influence through a Social Network. U: Proceedings of the ninth ACM SIGKDD international conference on Knowledge discovery and data mining, 2003.",
    "wang2003":
        "Wang, Y., Chakrabarti, D., Wang, C., Faloutsos, C. Epidemic Spreading in Real Networks: An Eigenvalue Viewpoint. U: 22nd International Symposium on Reliable Distributed Systems (SRDS), 2003.",
    "ropke2006":
        "Røpke, S., Pisinger, D. An Adaptive Large Neighborhood Search Heuristic for the Pickup and Delivery Problem with Time Windows. Transportation Science, vol. 40, br. 4, 2006.",
    "kimura2008":
        "Kimura, M., Saito, K., Nakano, R., Motoda, H. On the Contamination Minimization Problem in Social Networks. U: Proceedings of the 2008 Joint Conference on Information Sciences, 2008.",
    "clauset2009":
        "Clauset, A., Shalizi, C. R., Newman, M. E. J. Power-Law Distributions in Empirical Data. SIAM Review, vol. 51, br. 4, 2009.",
    "antulov2008":
        "Antulov-Fantulin, N. Utjecaj zaraze na svojstva kompleksne mreže. Završni rad br. 243. Zagreb: Fakultet elektrotehnike i računarstva, Sveučilište u Zagrebu, 2008.",
    "castellano2010":
        "Castellano, C., Pastor-Satorras, R. Thresholds for Epidemic Spreading in Networks. Physical Review Letters, vol. 105, br. 21, 2010.",
    "sheldon2010":
        "Sheldon, D., Dilkina, B., Elmachtoub, A., Finseth, R., Sabharwal, A., Conrad, J., Gomes, C., Shmoys, D., Phillips, A. Maximizing the Spread of Cascades Using Network Design. U: Proceedings of the 26th Conference on Uncertainty in Artificial Intelligence (UAI), 2010.",
    "tong2012":
        "Tong, H., Prakash, B. A., Eliassi-Rad, T., Faloutsos, M., Faloutsos, C. Gelling, and Melting, Large Graphs by Edge Manipulation. U: IEEE 12th International Conference on Data Mining, 2012.",
    "kumar2016":
        "Kumar, S., Spezzano, F., Subrahmanian, V. S., Faloutsos, C. Edge Weight Prediction in Weighted Signed Networks. U: IEEE International Conference on Data Mining (ICDM), 2016.",
    "kumar2018":
        "Kumar, S., Hooi, B., Makhija, D., Kumar, M., Subrahmanian, V. S., Faloutsos, C. REV2: Fraudulent User Prediction in Rating Platforms. U: 11th ACM International Conference on Web Search and Data Mining (WSDM), 2018.",
    "coro2021":
        "Coró, F., Castiglioni, M., Ferraioli, D., Gatti, N. Link Recommendation for Social Influence Maximization. U: Proceedings of the AAAI Conference on Artificial Intelligence, vol. 35, br. 6, 2021.",
    "castiglioni2021":
        "Castiglioni, M., Ferraioli, D., Gatti, N. Election Manipulation on Social Networks: Seeding, Edge Removal, and Edge Addition. U: Proceedings of the AAAI Conference on Artificial Intelligence, vol. 35, br. 6, 2021.",
    "predavanja":
        "Predavanja na kolegiju Kompleksne mreže. Fakultet elektrotehnike i računarstva, Sveučilište u Zagrebu, prezentacije.",
}


def sorted_entries():
    """The bibliography, alphabetically by author.

    Author-year citations are looked up by name, so the list has to be ordered by name;
    a chronological list would force the reader to scan the whole thing for every
    citation. Sorting the rendered entry sorts on the leading surname."""
    import unicodedata

    def key(entry):
        stripped = unicodedata.normalize("NFKD", entry)
        return "".join(c for c in stripped if not unicodedata.combining(c)).lower()

    return sorted(ENTRIES.values(), key=key)
