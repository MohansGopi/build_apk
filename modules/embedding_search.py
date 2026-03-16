"""
modules/embedding_search.py
Retrieval engine using scikit-learn only — no PyTorch, no transformers.

Strategy
--------
Two complementary sklearn vectorisers are combined into a hybrid score:

1. TF-IDF (TfidfVectorizer)
   Fast lexical matching.  Great for exact keyword queries.
   Vocabulary: up to MAX_FEATURES unigrams + bigrams from the document corpus.

2. BM25-style re-ranking via sublinear TF + IDF (same vectoriser flag)
   sklearn's sublinear_tf=True approximates BM25 term saturation.

3. Character n-gram vectoriser (analyzer='char_wb', ngram_range=(3,5))
   Catches partial matches, morphological variants, typos.
   Especially helpful for technical terms and proper nouns.

Final score = alpha * tfidf_cosine  +  (1 - alpha) * char_cosine
where alpha=0.65 gives a good lexical / morphological balance.

Persistence: the fitted vectorisers + matrix are pickled alongside
the source document so re-indexing is instant on app restart.
"""

import os
import logging
import pickle
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Tunable constants ──────────────────────────────────────────────────────
MAX_FEATURES_WORD  = 8192   # word-level TF-IDF vocabulary size
MAX_FEATURES_CHAR  = 4096   # char n-gram vocabulary size
NGRAM_WORD         = (1, 2)  # unigrams + bigrams
NGRAM_CHAR         = (3, 5)  # char 3–5-grams
ALPHA              = 0.65    # blend weight: word TF-IDF vs char n-gram


class EmbeddingSearch:
    """
    Scikit-learn–only semantic search index.

    All heavy work (fit_transform) runs on the background thread supplied
    by RAGEngine; only lightweight query transforms happen on the search path.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or self._default_cache_dir()

        # Vectorisers (fitted during build_index)
        self._word_vec:  Optional[TfidfVectorizer] = None
        self._char_vec:  Optional[TfidfVectorizer] = None

        # Normalised dense matrices  (N_chunks × vocab)
        self._word_matrix: Optional[np.ndarray] = None
        self._char_matrix: Optional[np.ndarray] = None

        self._chunks:       List[Dict] = []
        self._current_doc:  Optional[str] = None

    # ------------------------------------------------------------------
    # Cache dir
    # ------------------------------------------------------------------

    def _default_cache_dir(self) -> str:
        try:
            from kivy.utils import platform
            if platform == "android":
                from android.storage import app_storage_path  # type: ignore
                return os.path.join(app_storage_path(), "index_cache")
        except Exception:
            pass
        return os.path.join(Path.home(), ".docassist", "index_cache")

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_index(self, chunks: List[Dict], doc_path: str,
                    progress_callback=None):
        """
        Fit vectorisers on all chunk texts and build normalised matrices.
        Tries to load a previously cached index first.

        progress_callback(float 0..1) is called at key steps.
        """
        self._chunks = chunks
        self._current_doc = doc_path

        cache_path = self._cache_path(doc_path)

        # ── Try disk cache ────────────────────────────────────────────
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    cached = pickle.load(f)
                if (cached.get("doc_path") == doc_path
                        and cached.get("n_chunks") == len(chunks)):
                    self._word_vec    = cached["word_vec"]
                    self._char_vec    = cached["char_vec"]
                    self._word_matrix = cached["word_matrix"]
                    self._char_matrix = cached["char_matrix"]
                    logger.info(f"Index loaded from cache ({len(chunks)} chunks)")
                    if progress_callback:
                        progress_callback(1.0)
                    return
            except Exception as e:
                logger.warning(f"Cache load failed, rebuilding: {e}")

        # ── Build fresh index ─────────────────────────────────────────
        texts = [c["text"] for c in chunks]

        if progress_callback:
            progress_callback(0.1)

        # Word-level TF-IDF
        self._word_vec = TfidfVectorizer(
            max_features=MAX_FEATURES_WORD,
            ngram_range=NGRAM_WORD,
            sublinear_tf=True,          # log(1+tf) — BM25-like saturation
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
            min_df=1,
        )
        word_sparse = self._word_vec.fit_transform(texts)
        self._word_matrix = self._normalise(word_sparse.toarray())

        if progress_callback:
            progress_callback(0.55)

        # Char n-gram TF-IDF
        self._char_vec = TfidfVectorizer(
            max_features=MAX_FEATURES_CHAR,
            ngram_range=NGRAM_CHAR,
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="char_wb",
        )
        char_sparse = self._char_vec.fit_transform(texts)
        self._char_matrix = self._normalise(char_sparse.toarray())

        if progress_callback:
            progress_callback(0.9)

        # ── Persist to disk ───────────────────────────────────────────
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "wb") as f:
                pickle.dump({
                    "doc_path":    doc_path,
                    "n_chunks":    len(chunks),
                    "word_vec":    self._word_vec,
                    "char_vec":    self._char_vec,
                    "word_matrix": self._word_matrix,
                    "char_matrix": self._char_matrix,
                }, f)
            logger.info(f"Index cached → {cache_path}")
        except Exception as e:
            logger.warning(f"Could not cache index: {e}")

        if progress_callback:
            progress_callback(1.0)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Return top_k chunks ranked by hybrid TF-IDF + char-ngram similarity.
        Each result dict contains the original chunk fields plus 'score'.
        """
        if not self.is_ready:
            return []

        # Word scores
        q_word = self._normalise(
            self._word_vec.transform([query]).toarray()
        )
        word_scores = (self._word_matrix @ q_word.T).flatten()

        # Char scores
        q_char = self._normalise(
            self._char_vec.transform([query]).toarray()
        )
        char_scores = (self._char_matrix @ q_char.T).flatten()

        # Hybrid blend
        scores = ALPHA * word_scores + (1.0 - ALPHA) * char_scores

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = dict(self._chunks[int(idx)])
            chunk["score"] = float(scores[idx])
            results.append(chunk)

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(matrix: np.ndarray) -> np.ndarray:
        """L2-normalise rows; safe against zero vectors."""
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return (matrix / norms).astype(np.float32)

    def _cache_path(self, doc_path: str) -> str:
        name = Path(doc_path).stem
        cache_base = os.path.join(self.cache_dir, "indexes")
        os.makedirs(cache_base, exist_ok=True)
        return os.path.join(cache_base, f"{name}.idx.pkl")

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        return (self._word_matrix is not None
                and self._char_matrix is not None
                and len(self._chunks) > 0)

    def clear(self):
        self._word_vec    = None
        self._char_vec    = None
        self._word_matrix = None
        self._char_matrix = None
        self._chunks      = []
        self._current_doc = None
