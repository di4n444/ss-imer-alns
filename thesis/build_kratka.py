"""Build the short version of the thesis.

Same machinery as build_thesis.py, and deliberately so: the template rules, the equation
objects, the numbering and the citation substitution are already solved in doc.py, omml.py
and bibliography.py. What is new here is only the chapter text, which lives in c1..c8.

The 57pg draft is used purely as a shell. Everything between "Uvod" and "Literatura" is
thrown away and rewritten; the title page, the two abstract pages, the table-of-contents
field and the AI statement survive because they are outside that range.

Run:
    python build_kratka.py            # the whole document
    python build_kratka.py c1 c2      # only those chapters, for review
"""

import sys
import warnings
from pathlib import Path

import bibliography as bib
import doc
import docx

warnings.filterwarnings("ignore", message="style lookup by style_id")

ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES = Path(__file__).resolve().parent.parent / "figures"
SOURCE = ROOT / "Optimizacija protoka informacije u grafovima 57pg.docx"
OUTPUT = ROOT / "Optimizacija protoka informacije u grafovima - kratka.docx"

CHAPTERS = [
    "c1_teorija",
    "c2_mreza",
    "c3_problem",
    "c4_metode",
    "c5_postav",
    "c6_rezultati",
    "c7_poboljsanja",
    "c8_zakljucak",
]

UNNUMBERED = ("Sažetak", "Summary", "Sadržaj", "Uvod", "Zaključak", "Literatura",
              "Izjava o korištenju umjetne inteligencije")


SAZETAK = [
    "Optimizacija protoka informacije u grafovima",
    "U radu se razmatra problem smanjenja dosega kaskade iz jednog zadanog izvora "
    "uklanjanjem unaprijed zadanog broja bridova, uz nezavisni kaskadni model širenja. "
    "Problem je formuliran kao SS-IMER, uža varijanta problema minimizacije utjecaja "
    "uklanjanjem bridova. Budući da doseg nije submodularan u skupu uklonjenih bridova, "
    "pohlepni postupci koji bridove biraju jedan po jedan ne prepoznaju bridove koji se "
    "isplate tek zajedno, pa je za rješavanje prilagođena metaheuristika ALNS. Njezino se "
    "prilagodljivo učenje ispituje na dvije razine: koji je topološki kriterij bolji "
    "procjenitelj i koliko daleko od izvora leže korisni bridovi. Metoda je uspoređena sa "
    "šest pohlepnih kriterija na mreži povjerenja Bitcoin Alpha. Pretraga nadmašuje pet "
    "kriterija uvjerljivo, a izjednačena je s odabirom najboljeg kriterija unatrag. "
    "Korisni bridovi gotovo su isključivo oni uz izvor, što se objašnjava time da u toj "
    "mreži gotovo svaki izvor doseže isti skup čvorova.",
    "Ključne riječi: kompleksne mreže, minimizacija utjecaja, nezavisni kaskadni model, "
    "metaheuristika, ALNS, uklanjanje bridova, Bitcoin Alpha",
]

SUMMARY = [
    "Optimization of Information Flow in Graphs",
    "This thesis studies the problem of reducing the reach of a cascade from a single "
    "fixed source by removing a given number of edges, under the Independent Cascade "
    "model. The problem is formulated as SS-IMER, a narrower variant of influence "
    "minimization by edge removal. Because reach is not submodular in the set of removed "
    "edges, greedy procedures that pick edges one at a time cannot see edges that only "
    "pay off together, so an Adaptive Large Neighborhood Search metaheuristic is adapted "
    "to the problem. Its adaptive learning is examined on two levels: which topological "
    "criterion is the better estimator, and how far from the source the useful edges lie. "
    "The method is compared against six greedy criteria on the Bitcoin Alpha trust "
    "network. The search beats five criteria clearly and matches the hindsight choice of "
    "the best criterion. Useful edges are almost exclusively those incident to the "
    "source, which is explained by the fact that almost every source in this network "
    "reaches the same set of nodes.",
    "Keywords: complex networks, influence minimization, independent cascade model, "
    "metaheuristics, ALNS, edge removal, Bitcoin Alpha",
]

AI_STATEMENT = [
    "Pri izradi rada korišten je Claude (Anthropic) za pomoć pri pisanju programskog koda, "
    "oblikovanju teksta na hrvatskom jeziku i provjeri dosljednosti navoda.",
    "Osvrt na korištenje umjetne inteligencije: sve odluke o formulaciji problema, "
    "postavu eksperimenta i tumačenju rezultata donesene su samostalno. Svi brojčani "
    "podaci u radu čitaju se pri izgradnji dokumenta izravno iz datoteka s rezultatima, a "
    "ne prepisuju se u tekst, čime je uklonjena mogućnost izmišljenih vrijednosti. Navodi "
    "iz literature provjereni su usporedbom s izvornim radovima, pri čemu su otkrivene i "
    "ispravljene dvije pogreške: tvrdnja o epidemiološkom pragu pripisana je pogrešnom "
    "izvoru te su dva podatka o dosegu izvora bila netočno navedena u radnim bilješkama.",
    "Izjava o korištenju umjetne inteligencije: Potvrđujem da sam tijekom izrade ovog "
    "završnog rada koristila umjetnu inteligenciju u skladu s Politikom primjerenog "
    "korištenja umjetne inteligencije na Fakultetu elektrotehnike i računarstva, te da "
    "umjetna inteligencija nije zamijenila moje kritičko razmišljanje i samostalan rad.",
]


def _replace_section(document, heading, paragraphs, stop_heading=None):
    """Swap the template's placeholder text under one Heading 1 for our own.

    The abstract pages and the AI statement sit outside the Uvod..Literatura range that
    `clear_body` owns, so they are rewritten here instead - and from this file, so a
    rebuild never silently restores the placeholder."""
    body = document.element.body
    children = list(body)

    def index_of(title):
        for i, element in enumerate(children):
            if not element.tag.endswith("}p"):
                continue
            paragraph = next((p for p in document.paragraphs if p._p is element), None)
            if (paragraph is not None and paragraph.style.name == "Heading 1"
                    and paragraph.text.strip() == title):
                return i
        return None

    start = index_of(heading)
    if start is None:
        raise ValueError(f"heading '{heading}' not found")
    end = index_of(stop_heading) if stop_heading else len(children)
    if end is None:
        end = len(children)

    anchor = children[start]
    for element in children[start + 1:end]:
        body.remove(element)
    for text in reversed(paragraphs):
        paragraph = document.add_paragraph(text)
        anchor.addnext(paragraph._p)
    return start


def _front_and_back_matter(document):
    _replace_section(document, "Sažetak", SAZETAK, stop_heading="Summary")
    _replace_section(document, "Summary", SUMMARY, stop_heading="Sadržaj")
    _replace_section(document, "Izjava o korištenju umjetne inteligencije", AI_STATEMENT)


def _render(chapters, sections=None):
    document = docx.Document(SOURCE)
    doc.base_style(document)
    numbering = doc.capture_heading_numbering(document)
    doc.clear_body(document, "Uvod", "Literatura")
    doc.numbering_into_heading_styles(document, numbering, unnumbered=UNNUMBERED)

    thesis = doc.Thesis(document, marker_heading="Literatura", numbering=numbering,
                        sections=sections)
    for name in chapters:
        __import__(name).write(thesis, FIGURES)

    doc.write_bibliography(document, bib.sorted_entries())
    _front_and_back_matter(document)
    return document, thesis


def _word_count(document):
    """Body words only, so the 8 000 budget is measured against what we actually write.

    Counted between "Uvod" and "Literatura", which is exactly the range this script owns;
    the front matter and the bibliography are outside it and are budgeted separately."""
    counting, words = False, 0
    for p in document.paragraphs:
        text = p.text.strip()
        if p.style.name == "Heading 1" and text == "Literatura":
            break
        if p.style.name == "Heading 1" and text == "Uvod":
            counting = True
        if counting:
            words += len(text.split())
    return words


def main(chapters=None):
    partial = chapters is not None
    chapters = chapters or CHAPTERS

    # Two passes: Word numbers the headings itself, so a section's number exists only as a
    # position in the finished document and a forward reference cannot resolve on the
    # first pass.
    _, first = _render(chapters)
    document, thesis = _render(chapters, sections=first.sections)

    unresolved = [p.text for p in document.paragraphs if "?.?" in p.text]
    if unresolved and not partial:
        raise ValueError(
            f"{len(unresolved)} unresolved section reference(s); the first is:\n"
            f"  {unresolved[0][:200]}\n"
            "Add label= to the heading being referred to.")

    # Always the same file, whether the build is partial or complete. A per-selection
    # filename left a trail of near-identical drafts and made it ambiguous which one was
    # current; there is exactly one short version, and this is it.
    document.save(OUTPUT)

    words = _word_count(document)
    print(f"wrote {OUTPUT.name}")
    print(f"  {thesis.chapter} chapters, {thesis._equation} numbered expressions, "
          f"{sum(thesis._figures.values())} figures, "
          f"{sum(thesis._tables.values())} tables")
    print(f"  body words: {words}  (target ~7 000; document total ~8 000, hard cap 10 000)")
    if unresolved and partial:
        print(f"  note: {len(unresolved)} forward reference(s) unresolved "
              "(expected in a partial build)")
    return thesis


if __name__ == "__main__":
    main(sys.argv[1:] or None)
