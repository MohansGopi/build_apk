"""
modules/rag_engine.py
Orchestrates document processing, embedding, and retrieval.
All heavy operations run on background threads to keep UI responsive.
"""

import threading
import logging
from typing import List, Dict, Callable, Optional
from pathlib import Path

from modules.document_processor import DocumentProcessor
from modules.embedding_search import EmbeddingSearch
from modules.pdf_highlighter import PDFHighlighter

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    High-level RAG engine.

    Usage:
        engine = RAGEngine()
        engine.load_document(path, on_progress, on_complete, on_error)
        engine.query(question, on_result)
    """

    TOP_K = 3   # number of chunks to retrieve per query

    def __init__(self):
        self.processor = DocumentProcessor()
        self.searcher = EmbeddingSearch()
        self.highlighter: Optional[PDFHighlighter] = None
        self._doc_path: Optional[str] = None
        self._is_loading = False

    # ------------------------------------------------------------------
    # Document loading (background thread)
    # ------------------------------------------------------------------

    def load_document(self,
                      filepath: str,
                      on_progress: Callable[[str, float], None],
                      on_complete: Callable[[], None],
                      on_error: Callable[[str], None]):
        """
        Asynchronously process and index a document.
        Callbacks are invoked on the calling thread (schedule_once on UI).
        """
        if self._is_loading:
            on_error("Already processing a document. Please wait.")
            return

        self._is_loading = True
        t = threading.Thread(
            target=self._load_worker,
            args=(filepath, on_progress, on_complete, on_error),
            daemon=True
        )
        t.start()

    def _load_worker(self, filepath, on_progress, on_complete, on_error):
        try:
            # Step 1 – extract text
            on_progress("Extracting text…", 0.1)
            chunks = self.processor.process(filepath)
            if not chunks:
                on_error("No text could be extracted from the document.")
                return

            on_progress(f"Found {len(chunks)} text chunks. Building index…", 0.3)

            # Step 2 – build TF-IDF index (no model download needed)
            self.searcher.clear()

            def _prog(ratio):
                on_progress(f"Building search index… {int(ratio*100)}%",
                            0.3 + ratio * 0.65)

            self.searcher.build_index(chunks, filepath, _prog)

            # Step 3 – open PDF highlighter
            if filepath.lower().endswith(".pdf"):
                if self.highlighter:
                    self.highlighter.close()
                self.highlighter = PDFHighlighter(filepath)

            self._doc_path = filepath
            on_progress("Ready!", 1.0)
            on_complete()

        except Exception as e:
            logger.exception("load_worker error")
            on_error(str(e))
        finally:
            self._is_loading = False

    # ------------------------------------------------------------------
    # Query (background thread)
    # ------------------------------------------------------------------

    def query(self,
              question: str,
              on_result: Callable[[List[Dict]], None],
              on_error: Callable[[str], None]):
        """
        Asynchronously search for relevant chunks.
        on_result receives a list of result dicts (with highlight info).
        """
        if not self.searcher.is_ready:
            on_error("No document indexed. Please upload a document first.")
            return

        t = threading.Thread(
            target=self._query_worker,
            args=(question, on_result, on_error),
            daemon=True
        )
        t.start()

    def _query_worker(self, question, on_result, on_error):
        try:
            results = self.searcher.search(question, top_k=self.TOP_K)

            # Enrich each result with rendered page image (with highlight)
            for res in results:
                page_0based = res.get("page", 1) - 1  # convert 1-based → 0-based
                page_0based = max(0, page_0based)
                res["page_0based"] = page_0based

                if self.highlighter and self._doc_path.endswith(".pdf"):
                    # Build highlight list: top sentence of this chunk
                    hl_texts = [s for s in res.get("sentences", [])[:2] if s]
                    img_bytes = self.highlighter.render_page(
                        page_0based,
                        zoom=1.8,
                        highlights=[{"text": t} for t in hl_texts]
                    )
                    res["page_image"] = img_bytes
                else:
                    res["page_image"] = None

            on_result(results)

        except Exception as e:
            logger.exception("query_worker error")
            on_error(str(e))

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def doc_path(self) -> Optional[str]:
        return self._doc_path

    @property
    def is_pdf(self) -> bool:
        return self._doc_path is not None and self._doc_path.lower().endswith(".pdf")

    @property
    def page_count(self) -> int:
        if self.highlighter:
            return self.highlighter.page_count
        return 0

    def render_page(self, page_num: int, zoom: float = 1.8) -> Optional[bytes]:
        """Plain page render without highlight (for PDF browsing)."""
        if self.highlighter:
            return self.highlighter.render_page(page_num, zoom=zoom)
        return None

    def close(self):
        if self.highlighter:
            self.highlighter.close()
            self.highlighter = None
