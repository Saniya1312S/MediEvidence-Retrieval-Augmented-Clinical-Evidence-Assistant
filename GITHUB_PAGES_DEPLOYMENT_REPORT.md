# MediEvidence — GitHub Pages Live Portfolio Demo Deployment Report

**Date:** November 21, 2026  
**Repository:** [https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant](https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant)  
**Public Live Demo URL:** [https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/](https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/)  
**Deployment Status:** **SUCCESSFULLY DEPLOYED & LIVE (HTTP 200 OK)**

---

## 1. Public Access & Verification Summary

| Check / Metric | Status / Value | Verification Details |
|---|---|---|
| **Public Live URL** | `https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/` | Verified live; HTTP 200 OK |
| **Deployment Mechanism** | GitHub Actions (`deploy-pages.yml`) | Automated static artifact deployment (`actions/deploy-pages@v4`) |
| **Branch Deployed** | `main` (commit `97b6044`) | Latest production code and static bundle |
| **Asset Delivery** | Clean relative URLs | `style.css` (200), `script.js` (200), `static_data.json` (200), `404.html` (200) |
| **Console Errors** | **0 Console Errors** | No 404 network errors or failed API probes |
| **PDF Serving** | **Active on GitHub Pages** | All 30 open-access PDFs load directly via relative paths |
| **Target Viewports** | Desktop (1280x800) & Mobile (375x812) | 100% verified responsive layout |

---

## 2. End-to-End Live Browser Testing Results

A comprehensive browser verification was conducted directly against the live public URL (`https://saniya1312s.github.io/...`). All 8 test phases passed:

| Journey Step / Feature | User Action / Element | Live Result | Evidence |
|---|---|:---:|---|
| **1. Homepage & Hero** | Loaded root URL | **PASS** | Dark glassmorphic design system rendered with hero gradient; hero badge displays: `⚡ Static Portfolio Demo · Pre-Indexed Evidence & Benchmarks · 30 Papers`. |
| **2. Section Navigation** | Clicked `#papers`, `#ask`, `#rag`, `#evaluation` | **PASS** | Smooth scroll to anchors with dynamic active navigation pill highlighting. |
| **3. Papers Catalogue** | Inspected `#papersTable` | **PASS** | Rendered all 30 research papers with title, journal, year, category, page count, and chunk count. |
| **4. Metadata & Search Filter** | Typed `"Saratkar"` in search bar | **PASS** | Filtered table to exactly 1 paper: `MED-DT-001: Digital Twin for Personalized Medicine Development` (*Frontiers in Digital Health*, 2025). |
| **5. Paper Details Modal** | Clicked `"🔍 Inspect Paper & Chunks"` | **PASS** | Modal opened showing verified metadata, DOI link, and indexed chunk excerpts (`c001` through `c023`). |
| **6. Interactive PDF Reader** | Clicked `"📄 View PDF"` on `MED-DT-001` | **PASS** | Embedded PDF viewer modal opened with Page controls (`Prev`, `Page 1 / 23`, `Next`) and `"↗ New Tab"` direct link to the static PDF file. |
| **7. Grounded Ask Demo** | Queried: *"How are digital twins used in personalized medicine development?"* | **PASS** | Retrieved grounded answer with confidence score `0.78` and bracketed citation `[Digital Twin for Personalized Medicine Development (2025), Page 2]`. Displayed `⚡ STATIC PORTFOLIO DEMONSTRATION` badge. |
| **8. Strict Guardrail Refusal** | Queried: *"What is the recipe for pasta carbonara?"* | **PASS** | Immediate refusal triggered. Displayed `🛡️ Out-of-Domain Guardrail — Refusal` explaining non-medical queries are rejected. |
| **9. RAG Architecture** | Scrolled to `#rag` | **PASS** | Rendered offline ingestion pipeline (5 stages) and online query pipeline (6 stages) with model specifications. |
| **10. Evaluation Dashboard** | Scrolled to `#evaluation` | **PASS** | Rendered exact measured metrics (Recall@1: 86.7%, Recall@3: 88.9%, Recall@5: 93.3%, MRR: 0.888, nDCG@5: 0.899). Question Inventory displays all 75 questions; Failure Analysis Dashboard displays all 13 edge cases. |
| **11. Mobile Responsiveness** | Resized to 375x812 | **PASS** | Hamburger navigation toggles cleanly; cards, query input, and tables wrap without horizontal overflow. |

---

## 3. Important Architectural Distinction: Static Demo vs. Full Live Backend

### What the GitHub Pages Static Demo Delivers:
- **Zero-Dependency Exploration:** Portfolio visitors, recruiters, and hiring managers can explore the entire project without cloning, installing Python, or running servers.
- **Pre-Indexed Evidence Lookup:** Demonstrates verified retrieval responses, bracketed citations, PICO tables, and out-of-domain refusals using client-side pre-indexed data (`data/static_data.json`).
- **Full Catalog & Document Access:** Visitors can search all 30 research papers, filter by domain, inspect chunks, and view original PDFs directly in the browser.
- **Full Evaluation Transparency:** Interactive inspection of all 75 benchmark questions and the 13 failure cases.

### What Requires the Local FastAPI Backend:
- **Arbitrary Live Semantic Retrieval:** Encoding new, unindexed questions through `SentenceTransformers` (`all-MiniLM-L6-v2`, 384d).
- **HNSW Cosine Vector Search:** Running embedded local vector database queries via `qdrant-client`.
- **Lexical Token Scoring:** Dynamic BM25Okapi inverted index ranking with custom acronym tokenization.
- **Neural Cross-Attention Reranking:** Real-time inference through `cross-encoder/ms-marco-MiniLM-L-6-v2` over top candidates.

---

## 4. How to Run the Full AI Application Locally

For recruiters or engineers who wish to test live neural question-answering on arbitrary queries:

```bash
# 1. Clone the repository
git clone https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant.git
cd MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant

# 2. Set up virtual environment
python -m venv venv
# On Windows PowerShell: .\venv\Scripts\Activate.ps1
# On Linux / macOS: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Build local vector database & inverted index (Processes 30 PDFs in ~2 minutes)
python ingest_pipeline.py

# 5. Start the FastAPI server
python main.py
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** for the live AI interface or **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** for the interactive Swagger API docs.

---

## 5. Live Demo Screenshot Evidence

The live site verification screenshot is preserved at:
- `screenshots/live_github_pages_demo.png`
- Host origin verified: `https://saniya1312s.github.io`
- Zero HTTP errors, zero layout breakages.
