"""
modules/document_processor.py
Handles text extraction from PDF and DOCX files.
Splits text into semantic chunks for embedding.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Extracts and chunks text from PDF and DOCX documents.
    Each chunk carries metadata: page number, bbox (for PDF highlighting).
    """

    CHUNK_SIZE = 3          # sentences per chunk (overlap sliding window)
    CHUNK_OVERLAP = 1       # sentences overlap between consecutive chunks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, filepath: str) -> List[Dict]:
        """
        Main entry point.
        Returns a list of chunk dicts:
        {
            'text': str,
            'page': int,          # 1-based (PDF) or 0 for DOCX
            'sentences': List[str],
            'bbox': Optional[list],   # PDF: [x0,y0,x1,y1] of first match
            'source_sentences': List[dict]  # per-sentence bbox data (PDF)
        }
        """
        ext = Path(filepath).suffix.lower()
        if ext == ".pdf":
            return self._process_pdf(filepath)
        elif ext in (".docx", ".doc"):
            return self._process_docx(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------

    def _process_pdf(self, filepath: str) -> List[Dict]:
        import fitz  # PyMuPDF

        chunks: List[Dict] = []
        doc = fitz.open(filepath)

        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if not page_text.strip():
                continue

            sentences = self._split_sentences(page_text)
            page_chunks = self._sliding_window(sentences)

            for chunk_sentences in page_chunks:
                chunk_text = " ".join(chunk_sentences)
                # Find bbox of the first sentence for scroll targeting
                bbox = self._find_sentence_bbox(page, chunk_sentences[0])
                source_sentences = []
                for s in chunk_sentences:
                    b = self._find_sentence_bbox(page, s)
                    source_sentences.append({"text": s, "page": page_num, "bbox": b})

                chunks.append({
                    "text": chunk_text,
                    "page": page_num,
                    "sentences": chunk_sentences,
                    "bbox": bbox,
                    "source_sentences": source_sentences,
                })

        doc.close()
        logger.info(f"PDF processed: {len(chunks)} chunks from {filepath}")
        return chunks

    def _find_sentence_bbox(self, page, sentence: str) -> Optional[list]:
        """Search for sentence text on a PDF page and return bbox."""
        try:
            import fitz
            # Try exact search first
            rects = page.search_for(sentence[:60])  # limit search string length
            if rects:
                r = rects[0]
                return [r.x0, r.y0, r.x1, r.y1]
        except Exception as e:
            logger.debug(f"bbox search failed: {e}")
        return None

    # ------------------------------------------------------------------
    # DOCX
    # ------------------------------------------------------------------

    def _process_docx(self, filepath: str) -> List[Dict]:
        from docx import Document

        doc = Document(filepath)
        full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        sentences = self._split_sentences(full_text)
        page_chunks = self._sliding_window(sentences)

        chunks = []
        for chunk_sentences in page_chunks:
            chunk_text = " ".join(chunk_sentences)
            chunks.append({
                "text": chunk_text,
                "page": 0,
                "sentences": chunk_sentences,
                "bbox": None,
                "source_sentences": [{"text": s, "page": 0, "bbox": None}
                                       for s in chunk_sentences],
            })

        logger.info(f"DOCX processed: {len(chunks)} chunks from {filepath}")
        return chunks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _split_sentences(self, text: str) -> List[str]:
        """Basic sentence splitter (no NLTK dependency)."""
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Split on sentence-ending punctuation
        raw = re.split(r"(?<=[.!?])\s+", text)
        # Filter very short fragments
        return [s.strip() for s in raw if len(s.strip()) > 10]

    def _sliding_window(self, sentences: List[str]) -> List[List[str]]:
        """Create overlapping sentence windows (chunks)."""
        if not sentences:
            return []

        chunks = []
        step = max(1, self.CHUNK_SIZE - self.CHUNK_OVERLAP)

        for i in range(0, len(sentences), step):
            window = sentences[i: i + self.CHUNK_SIZE]
            if window:
                chunks.append(window)

        return chunks

    # ------------------------------------------------------------------
    # Utility – extract raw page images for viewer (PDF)
    # ------------------------------------------------------------------

    @staticmethod
    def render_page_to_image(filepath: str, page_num: int,
                              zoom: float = 1.5) -> Optional[bytes]:
        """
        Render a PDF page to PNG bytes (for display in Kivy).
        page_num is 0-based.
        """
        try:
            import fitz
            doc = fitz.open(filepath)
            if page_num >= len(doc):
                return None
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            doc.close()
            return img_bytes
        except Exception as e:
            logger.error(f"render_page_to_image error: {e}")
            return None

    @staticmethod
    def get_page_count(filepath: str) -> int:
        try:
            import fitz
            doc = fitz.open(filepath)
            n = len(doc)
            doc.close()
            return n
        except Exception:
            return 0
