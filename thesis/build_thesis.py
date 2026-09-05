"""Build the thesis document.

Rewrites the body of the existing .docx in place - everything between "Uvod" and
"Literatura" - and leaves the title page, the abstract pages, the table-of-contents field
and the AI-usage statement exactly as they are. The output is written to a new file so the
current draft is never overwritten.

Run: python build_thesis.py
"""

import warnings
from pathlib import Path

import docx

import doc

warnings.filterwarnings("ignore", message="style lookup by style_id")

ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES = Path(__file__).resolve().parent.parent / "figures"
SOURCE = ROOT / "Optimizacija protoka informacije u grafovima.docx"
OUTPUT = ROOT / "Optimizacija protoka informacije u grafovima - nacrt.docx"

CHAPTERS = [
    "ch01_topologija",
]


def main():
    document = docx.Document(SOURCE)
    doc.base_style(document)
    numbering = doc.capture_heading_numbering(document)
    doc.clear_body(document, "Uvod", "Literatura")

    thesis = doc.Thesis(document, marker_heading="Literatura", numbering=numbering)
    for name in CHAPTERS:
        module = __import__(name)
        module.write(thesis, FIGURES)

    document.save(OUTPUT)

    equations = thesis._equation
    figures = sum(thesis._figures.values())
    print(f"wrote {OUTPUT.name}")
    print(f"  {thesis.chapter} chapters, {equations} numbered expressions, "
          f"{figures} figures")
    return thesis


if __name__ == "__main__":
    main()
