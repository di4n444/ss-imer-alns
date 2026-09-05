"""Document assembly against the faculty template's rules.

The template fixes the things this module enforces so no chapter has to remember them:

  * body text is Times New Roman 12 pt with 1.5 line spacing, on A4;
  * mathematical expressions are numbered "(n)" against the right margin and referenced
    in the text as "prema izrazu (n)" - numbering is continuous through the document;
  * figures are numbered <poglavlje>.<redni broj u poglavlju> and referenced as "Sl. 2.1";
  * headings use the template's own Heading 1/2/3 styles, so Word's table of contents and
    the numbering scheme keep working.

A `Thesis` instance carries the counters, so a chapter writes `t.eq(...)` or
`t.figure(...)` without tracking numbers by hand and without them going stale when a
section moves.
"""

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

import bibliography as bib
import omml as M


class Thesis:
    """Writes chapters into an existing document, immediately before `marker_heading`.

    python-docx only appends to the end of the body, so every block is created and then
    relocated in front of the marker. Doing that per block, rather than moving a batch
    afterwards, means the document is in a valid order at every point and content can
    never be left stranded after the bibliography."""

    def __init__(self, document, marker_heading: str = "Literatura", numbering=None):
        self.d = document
        self.numbering = numbering or {}
        self.chapter = 0
        self._equation = 0
        self._figures = {}
        self.refs = {}          # label -> number, so cross-references cannot drift
        self.marker = None
        for p in document.paragraphs:
            if p.style.name == "Heading 1" and p.text.strip() == marker_heading:
                self.marker = p._p
                break
        if self.marker is None:
            raise ValueError(f"heading '{marker_heading}' not found")

    def _place(self, block):
        """Move a freshly appended block into position before the marker."""
        element = block._p if hasattr(block, "_p") else block._tbl
        self.marker.addprevious(element)
        return block

    # -- structure --------------------------------------------------------

    def _heading(self, text: str, level: int, numbered: bool):
        """Chapter numbering in this template is direct paragraph formatting, not part of
        the Heading style, so a generated heading only joins the numbering sequence if it
        carries the same `numPr` as the template's own headings. Uvod, Zaključak and
        Literatura deliberately go without."""
        from copy import deepcopy
        paragraph = self.d.add_paragraph(text, style=f"Heading {level}")
        source = self.numbering.get(level)
        if numbered and source is not None:
            paragraph._p.get_or_add_pPr().append(deepcopy(source))
        return self._place(paragraph)

    def h1(self, text: str, numbered: bool = True):
        if numbered:
            self.chapter += 1
            self._figures[self.chapter] = 0
        return self._heading(text, 1, numbered)

    def h2(self, text: str):
        return self._heading(text, 2, True)

    def h3(self, text: str):
        return self._heading(text, 3, True)

    # -- body -------------------------------------------------------------

    def p(self, *parts):
        """A paragraph of prose, optionally with inline mathematics. Strings are text -
        with "{key}" citations resolved against the bibliography - and anything else is
        an equation object."""
        return self._place(M.para(self.d, *self._cited(parts)))

    @staticmethod
    def _cited(parts):
        return [bib.expand(part) if isinstance(part, str) else part for part in parts]

    def bullets(self, items, numbered: bool = False):
        """A list. The template defines no list styles, so items are indented paragraphs
        carrying their own marker - which is also how the existing draft sets them."""
        style = "Normal Indent" if "Normal Indent" in self._style_names() else None
        for n, item in enumerate(items, start=1):
            parts = item if isinstance(item, (list, tuple)) else [item]
            marker = f"{n}. " if numbered else "– "
            self._place(M.para(self.d, marker, *self._cited(parts), style=style))

    def _style_names(self):
        return {s.name for s in self.d.styles}

    # -- numbered objects -------------------------------------------------

    def eq(self, *items, label: str = None):
        """A displayed, numbered expression. `label` records the number so the text can
        refer to it with `self.ref(label)` and never cite a stale one."""
        self._equation += 1
        if label:
            self.refs[label] = self._equation
        self._place(M.add_equation(self.d, *items, number=self._equation))
        return self._equation

    def ref(self, label: str) -> str:
        """"(3)" - for use inside a sentence: "prema izrazu " + t.ref("saa")."""
        return f"({self.refs[label]})"

    def _next_figure_number(self, label: str = None) -> str:
        """Allocate the next figure number in the current chapter, or return the one
        already reserved for `label` by a forward reference."""
        if label and label in self.refs:
            return self.refs[label]
        self._figures[self.chapter] = self._figures.get(self.chapter, 0) + 1
        number = f"{self.chapter}.{self._figures[self.chapter]}"
        if label:
            self.refs[label] = number
        return number

    def figure(self, path: str, caption: str, label: str = None, width_cm: float = 14.0):
        """A figure with a caption numbered <chapter>.<n>, per the template."""
        number = self._next_figure_number(label)

        holder = self._place(self.d.add_paragraph())
        holder.alignment = WD_ALIGN_PARAGRAPH.CENTER
        holder.add_run().add_picture(str(path), width=Cm(width_cm))

        text = self._place(
            self.d.add_paragraph(f"Sl. {number}. {bib.expand(caption)}", style="Caption"))
        text.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return number

    def figref(self, label: str) -> str:
        """"Sl. 1.2" - usable before the figure itself is placed, which is the normal
        order: a figure is announced in the text and appears just after."""
        return f"Sl. {self._next_figure_number(label)}"


def base_style(document):
    """Times New Roman 12 pt, 1.5 spacing, as the template requires."""
    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    return document


def clear_body(document, from_heading: str, to_heading: str):
    """Remove the existing body between two Heading 1 paragraphs, keeping the front
    matter (title page, sazetak, table of contents) and everything from `to_heading` on.

    Rewriting in place rather than starting a fresh document is deliberate: the template's
    styles, the table-of-contents field and the AI-usage statement all live in the
    original file and would be lost by regenerating it from scratch."""
    paragraphs = document.paragraphs
    start = end = None
    for i, p in enumerate(paragraphs):
        if p.style.name == "Heading 1" and p.text.strip() == from_heading:
            start = i
        elif p.style.name == "Heading 1" and p.text.strip() == to_heading:
            end = i
            break
    if start is None or end is None:
        raise ValueError(f"could not locate '{from_heading}' .. '{to_heading}' in the document")

    body = document.element.body
    for p in paragraphs[start:end]:
        body.remove(p._p)
    return start, end


def capture_heading_numbering(document):
    """Take the `numPr` from the first numbered heading at each level, before the body is
    cleared, so regenerated headings rejoin the same numbering sequence."""
    from docx.oxml.ns import qn
    found = {}
    for p in document.paragraphs:
        name = p.style.name
        if not name.startswith("Heading"):
            continue
        level = int(name.split()[-1])
        if level in found:
            continue
        pPr = p._p.pPr
        numPr = pPr.find(qn("w:numPr")) if pPr is not None else None
        if numPr is not None:
            found[level] = numPr
    return found
