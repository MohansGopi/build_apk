"""
modules/pdf_highlighter.py
Renders PDF pages with highlighted search results using PyMuPDF.
Returns PNG bytes suitable for display in a Kivy Image widget.
"""

import logging
from typing import List, Optional, Tuple, Dict
from io import BytesIO

logger = logging.getLogger(__name__)

# Highlight colour: semi-transparent yellow (R,G,B) in 0-1 range
HIGHLIGHT_COLOR = (1.0, 0.95, 0.0)   # yellow
HIGHLIGHT_ALPHA = 0.4


class PDFHighlighter:
    """
    Wraps PyMuPDF to render pages with optional highlights.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._doc = None
        self._open()

    # ------------------------------------------------------------------
    # Document lifecycle
    # ------------------------------------------------------------------

    def _open(self):
        try:
            import fitz
            self._doc = fitz.open(self.filepath)
            logger.info(f"PDFHighlighter opened: {self.filepath} "
                        f"({len(self._doc)} pages)")
        except Exception as e:
            logger.error(f"Could not open PDF: {e}")
            self._doc = None

    def close(self):
        if self._doc:
            self._doc.close()
            self._doc = None

    @property
    def page_count(self) -> int:
        return len(self._doc) if self._doc else 0

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_page(self, page_num: int,
                    zoom: float = 1.5,
                    highlights: Optional[List[Dict]] = None) -> Optional[bytes]:
        """
        Render page_num (0-based) to PNG bytes.
        highlights: list of dicts with keys 'text' and optional 'bbox'.
        Returns PNG bytes or None on error.
        """
        if not self._doc:
            return None
        if page_num < 0 or page_num >= len(self._doc):
            return None

        try:
            import fitz

            page = self._doc[page_num]
            highlights = highlights or []

            # Apply highlights
            added_annots = []
            for hl in highlights:
                text = hl.get("text", "")
                if not text:
                    continue

                # Try to find text on this specific page
                rects = page.search_for(text[:80])
                if not rects:
                    # Try first 40 chars
                    rects = page.search_for(text[:40])

                for rect in rects:
                    annot = page.add_highlight_annot(rect)
                    annot.set_colors(stroke=HIGHLIGHT_COLOR)
                    annot.set_opacity(HIGHLIGHT_ALPHA)
                    annot.update()
                    added_annots.append(annot)

            # Render
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")

            # Remove temporary annotations so they don't persist
            for annot in added_annots:
                page.delete_annot(annot)

            return img_bytes

        except Exception as e:
            logger.error(f"render_page error on page {page_num}: {e}")
            return None

    # ------------------------------------------------------------------
    # Utility: find page containing a text snippet
    # ------------------------------------------------------------------

    def find_text_page(self, text: str) -> Optional[int]:
        """Return 0-based page number where text first appears, or None."""
        if not self._doc:
            return None

        search = text[:60]
        for i, page in enumerate(self._doc):
            if page.search_for(search):
                return i
        return None

    def get_text_bbox(self, page_num: int, text: str) -> Optional[List[float]]:
        """Return bbox [x0,y0,x1,y1] of first occurrence of text on page."""
        if not self._doc or page_num >= len(self._doc):
            return None
        try:
            rects = self._doc[page_num].search_for(text[:80])
            if rects:
                r = rects[0]
                return [r.x0, r.y0, r.x1, r.y1]
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Page dimensions (in points, before zoom)
    # ------------------------------------------------------------------

    def get_page_size(self, page_num: int) -> Tuple[float, float]:
        """Return (width, height) of page in points."""
        if not self._doc or page_num >= len(self._doc):
            return (612, 792)
        rect = self._doc[page_num].rect
        return (rect.width, rect.height)
