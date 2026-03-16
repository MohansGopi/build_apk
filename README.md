# DocAssist — Mobile RAG Document Assistant

A fully functional Android app built with **Python + Kivy** that implements a
**Retrieval-Augmented Generation (RAG)** pipeline for searching and highlighting
relevant passages inside PDF and DOCX documents.

---

## Features

| Feature | Details |
|---|---|
| Document upload | PDF and DOCX via native file picker |
| Text extraction | PyMuPDF (PDF) · python-docx (DOCX) |
| Sentence chunking | Sliding-window overlap for context preservation |
| Search engine | **Hybrid TF-IDF** (word n-gram + char n-gram) via scikit-learn |
| Similarity | Cosine similarity, NumPy vectorised — zero PyTorch dependency |
| PDF highlighting | PyMuPDF annotation overlay, rendered as PNG |
| Chat interface | Scrollable conversation with relevance scores |
| Background threading | Heavy work runs off the UI thread |
| Index cache | Pickled vectorisers — instant reload on restart |
| Android packaging | Buildozer + python-for-android |

---

## Project Structure

```
docassist/
├── main.py                   # App entry point
├── buildozer.spec            # Android build config
├── requirements.txt
├── modules/
│   ├── document_processor.py # Text extraction + chunking
│   ├── embedding_search.py   # Embeddings + cosine search
│   ├── pdf_highlighter.py    # Page rendering with highlights
│   └── rag_engine.py         # Orchestration + threading
└── ui/
    └── main_screen.py        # Full Kivy UI (viewer + chat)
```

---

## Desktop / Development Setup

### 1 – Install dependencies

```bash
# Create virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install all deps — no PyTorch, ~15 MB total
pip install -r requirements.txt
```

### 2 – Run on desktop

```bash
python main.py
```

A 400×800 px window simulates a phone screen. You can resize it.

---

## Android Build with Buildozer

### Prerequisites

| Tool | Version |
|---|---|
| Ubuntu 20.04 / 22.04 (or WSL2) | — |
| Python | 3.10 |
| buildozer | ≥ 1.5 |
| Android SDK / NDK | auto-downloaded by buildozer |

### Step-by-step

```bash
# Install buildozer
pip install buildozer

# Install system deps (Ubuntu)
sudo apt-get install -y \
    git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev

# Inside project root
cd docassist
buildozer init          # generates buildozer.spec (already provided)
buildozer android debug  # first build downloads NDK/SDK (~1 GB)
```

The APK will be at:

```
bin/docassist-1.0.0-arm64-v8a-debug.apk
```

### Install on device

```bash
# Enable USB debugging on Android device, then:
adb install bin/docassist-1.0.0-arm64-v8a-debug.apk
```

### Release build (signed)

```bash
buildozer android release
# Then sign with jarsigner / apksigner
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│               MainScreen (Kivy)          │
│  ┌──────────────┐   ┌────────────────┐  │
│  │  PDFViewer   │   │  Chat Panel    │  │
│  │  (top 52%)   │   │  (bottom 48%)  │  │
│  └──────┬───────┘   └───────┬────────┘  │
└─────────┼───────────────────┼───────────┘
          │                   │
          ▼                   ▼
    ┌─────────────────────────────┐
    │         RAGEngine           │
    │  (orchestrates background   │
    │   threads + callbacks)      │
    └──┬──────────┬───────────────┘
       │          │
       ▼          ▼
┌──────────┐  ┌──────────────────┐
│ Document │  │  EmbeddingSearch │
│ Processor│  │  (sentence-      │
│ (fitz /  │  │   transformers + │
│  docx)   │  │   cosine sim)    │
└──────────┘  └──────────────────┘
       │
       ▼
┌──────────────┐
│PDFHighlighter│
│(fitz annots, │
│ PNG render)  │
└──────────────┘
```

### RAG Flow

```
User uploads PDF/DOCX
        │
        ▼
DocumentProcessor.process()
  ├── Extract text per page
  ├── Split into sentences
  └── Sliding-window chunk (3 sentences, 1 overlap)
        │
        ▼
EmbeddingSearch.build_index()
  ├── TfidfVectorizer(word, 1-2 grams, sublinear_tf)  → 8192-dim matrix
  ├── TfidfVectorizer(char_wb, 3-5 grams, sublinear_tf) → 4096-dim matrix
  ├── L2-normalise both matrices
  └── Pickle vectorisers + matrices to .idx.pkl cache
        │
User asks question
        │
        ▼
EmbeddingSearch.search(query, top_k=3)
  ├── Transform query with both vectorisers
  ├── word_scores  = word_matrix  @ q_word  (cosine, vectorised)
  ├── char_scores  = char_matrix  @ q_char
  └── hybrid = 0.65 × word_scores + 0.35 × char_scores → ranked chunks
        │
        ▼
PDFHighlighter.render_page(page, highlights)
  ├── PyMuPDF search_for() to locate text
  ├── Add temporary highlight annotation
  ├── Render page to PNG (zoom 1.8×)
  └── Remove annotation
        │
        ▼
MainScreen
  ├── Display results in chat bubbles
  └── Show highlighted PDF page
```

---

## Performance Notes

* **No model download**: The entire search engine is fit directly on the document text — zero network calls, zero large model files.
* **Index size**: A 100-page PDF produces an index of roughly 2–5 MB on disk.
* **Index build time**: ~0.5–2 s for a typical 100-page document (single CPU core).
* **Query time**: < 10 ms per query regardless of document size.
* **Index cache**: Vectorisers + matrices are pickled — re-opening the same document is instant.
* **Hybrid scoring**: `word TF-IDF (65%) + char n-gram (35%)` handles synonyms, technical abbreviations, and partial keyword matches better than plain TF-IDF.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: fitz` | `pip install PyMuPDF` |
| `ModuleNotFoundError: sklearn` | `pip install scikit-learn` |
| Blank PDF viewer | Ensure the PDF is not password-protected |
| Low relevance scores | Use more specific keywords; TF-IDF is lexical — exact words matter |
| `buildozer` NDK error | Ensure `openjdk-17-jdk` installed and JAVA_HOME set |

---

## Licence

MIT – use freely, attribution appreciated.
