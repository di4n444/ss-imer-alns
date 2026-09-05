"""Build the thesis document.

Rewrites the body of the existing .docx in place - everything between "Uvod" and
"Literatura" - and leaves the title page, the abstract pages, the table-of-contents field
and the AI-usage statement exactly as they are. The output is written to a new file so the
current draft is never overwritten.

Run: python build_thesis.py
"""

import warnings
from pathlib import Path

import bibliography as bib
import docx

import bibliography as bib
import doc

warnings.filterwarnings("ignore", message="style lookup by style_id")

ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES = Path(__file__).resolve().parent.parent / "figures"
SOURCE = ROOT / "Optimizacija protoka informacije u grafovima.docx"
OUTPUT = ROOT / "Optimizacija protoka informacije u grafovima - nacrt.docx"

CHAPTERS = [
    "ch01_topologija",
    "ch02_bitcoin_alpha",
    "ch03_formulacija",
    "ch04_kriteriji",
    "ch05_metode",
    "ch06_implementacija",
]


def _render(sections=None):
    """Write every chapter into a fresh copy of the source document.

    Returns the assembled document and its `Thesis`, whose `sections` maps each labelled
    heading to the number it ended up with."""
    document = docx.Document(SOURCE)
    doc.base_style(document)
    numbering = doc.capture_heading_numbering(document)
    doc.clear_body(document, "Uvod", "Literatura")

    doc.numbering_into_heading_styles(
        document, numbering,
        unnumbered=("Sažetak", "Summary", "Sadržaj", "Uvod", "Zaključak", "Literatura",
                    "Izjava o korištenju umjetne inteligencije"))

    thesis = doc.Thesis(document, marker_heading="Literatura", numbering=numbering,
                        sections=sections)
    for name in CHAPTERS:
        module = __import__(name)
        module.write(thesis, FIGURES)

    doc.write_bibliography(document, bib.sorted_entries())
    return document, thesis


def main():
    # Two passes. Word numbers headings itself, so a section's number exists only as a
    # position in the finished document; the first pass is what discovers it. A chapter
    # may point forward - chapter 3 refers to 5.2.4 - which no single pass can resolve.
    _, first = _render()
    document, thesis = _render(sections=first.sections)

    unresolved = [p.text for p in document.paragraphs if "?.?" in p.text]
    if unresolved:
        raise ValueError(
            f"{len(unresolved)} unresolved section reference(s); the first is:\n"
            f"  {unresolved[0][:200]}\n"
            "Add label= to the heading being referred to.")

    document.save(OUTPUT)

    equations = thesis._equation
    figures = sum(thesis._figures.values())
    print(f"wrote {OUTPUT.name}")
    print(f"  {thesis.chapter} chapters, {equations} numbered expressions, "
          f"{figures} figures, {len(thesis.sections)} labelled sections")
    return thesis


if __name__ == "__main__":
    main()
