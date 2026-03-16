"""
tests/test_modules.py
Run from project root: python -m pytest tests/ -v
or:                     python tests/test_modules.py
"""

import sys
import os
import tempfile
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.document_processor import DocumentProcessor


def _make_temp_docx(text: str) -> str:
    """Create a temp DOCX file with given text, return path."""
    try:
        from docx import Document
        doc = Document()
        for para in text.split("\n"):
            doc.add_paragraph(para)
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        doc.save(tmp.name)
        tmp.close()
        return tmp.name
    except ImportError:
        return None


def test_sentence_splitter():
    dp = DocumentProcessor()
    sentences = dp._split_sentences(
        "The quick brown fox jumps. "
        "It was a sunny day! "
        "Was it really? Yes, it was."
    )
    assert len(sentences) == 4, f"Expected 4, got {len(sentences)}"
    print(f"  ✓ sentence splitter: {len(sentences)} sentences")


def test_sliding_window():
    dp = DocumentProcessor()
    sents = [f"Sentence {i}." for i in range(10)]
    chunks = dp._sliding_window(sents)
    assert len(chunks) > 0
    assert all(len(c) <= dp.CHUNK_SIZE for c in chunks)
    print(f"  ✓ sliding window: {len(chunks)} chunks from 10 sentences")


def test_docx_processing():
    dp = DocumentProcessor()
    text = textwrap.dedent("""
        Artificial intelligence is transforming industries.
        Machine learning models now power many applications.
        Natural language processing enables human-like text understanding.
        Deep learning has revolutionised computer vision tasks.
        Retrieval-augmented generation combines search with generation.
    """).strip()

    path = _make_temp_docx(text)
    if path is None:
        print("  ⚠ python-docx not installed, skipping DOCX test")
        return

    try:
        chunks = dp.process(path)
        assert len(chunks) > 0, "Expected at least one chunk"
        assert "text" in chunks[0]
        assert "sentences" in chunks[0]
        print(f"  ✓ DOCX processing: {len(chunks)} chunks extracted")
    finally:
        os.unlink(path)


def test_embedding_search():
    from modules.embedding_search import EmbeddingSearch
    es = EmbeddingSearch()

    chunks = [
        {"text": "Python is a programming language.", "page": 1,
         "sentences": ["Python is a programming language."], "bbox": None,
         "source_sentences": []},
        {"text": "Kivy is a framework for building mobile apps.", "page": 1,
         "sentences": ["Kivy is a framework for building mobile apps."], "bbox": None,
         "source_sentences": []},
        {"text": "PyMuPDF renders and annotates PDF documents.", "page": 2,
         "sentences": ["PyMuPDF renders and annotates PDF documents."], "bbox": None,
         "source_sentences": []},
        {"text": "Scikit-learn provides machine learning tools.", "page": 3,
         "sentences": ["Scikit-learn provides machine learning tools."], "bbox": None,
         "source_sentences": []},
    ]

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        dummy_path = f.name

    try:
        es.build_index(chunks, dummy_path)
        assert es.is_ready, "Index should be ready after build"

        results = es.search("mobile application framework", top_k=2)
        assert len(results) > 0, "Should return results"
        assert results[0]["score"] >= 0, "Score should be non-negative"

        top_text = results[0]["text"]
        print(f"  ✓ sklearn search: top result = '{top_text[:55]}…'")
        print(f"                    score = {results[0]['score']:.4f}")

        # Verify scores are descending
        if len(results) > 1:
            assert results[0]["score"] >= results[1]["score"], \
                "Results should be sorted by score descending"
            print(f"  ✓ results correctly sorted by score")
    finally:
        os.unlink(dummy_path)


def test_hybrid_scoring():
    """Verify word + char hybrid scoring boosts partial matches."""
    from modules.embedding_search import EmbeddingSearch, ALPHA
    import numpy as np

    es = EmbeddingSearch()
    chunks = [
        {"text": "retrieval augmented generation pipeline", "page": 1,
         "sentences": [], "bbox": None, "source_sentences": []},
        {"text": "convolutional neural network image classification", "page": 2,
         "sentences": [], "bbox": None, "source_sentences": []},
    ]
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        dummy = f.name

    try:
        es.build_index(chunks, dummy)
        results = es.search("RAG retrieval generation", top_k=2)
        assert results[0]["page"] == 1, \
            f"Expected RAG chunk first, got page={results[0]['page']}"
        assert 0.0 <= ALPHA <= 1.0
        print(f"  ✓ hybrid scoring: correct chunk ranked first "
              f"(score={results[0]['score']:.4f})")
    finally:
        os.unlink(dummy)


if __name__ == "__main__":
    print("\n=== DocAssist Module Tests ===\n")
    tests = [
        test_sentence_splitter,
        test_sliding_window,
        test_hybrid_scoring,
        test_docx_processing,
        test_embedding_search,
    ]
    passed = 0
    for t in tests:
        try:
            print(f"Running {t.__name__}…")
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")

    print(f"\n{passed}/{len(tests)} tests passed\n")
