# MediEvidence — Final Professional UI Polish & GitHub Pages Live Deployment Report

**Public Live URL:** [https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/](https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/)  
**GitHub Repository:** [https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant](https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant)  
**Target Branch:** `main` (Verified clean, `v1` branch preserved untouched)  
**Date:** November 2026  

---

## 1. Executive Summary & Design Transformation

MediEvidence has been refined from an experimental dashboard into a clean, interview-ready **Academic AI Research Platform** inspired by platforms such as Google Scholar, Semantic Scholar, and ResearchGate. 

The user interface balances deep technical capability with academic restraint:
1. **Academic Visual Language:** Eliminated neon text-shadows, intense glowing accents, and promotional badge styling in favor of structured dark-navy container surfaces, crisp typography, and high-contrast clinical data tables.
2. **Elimination of Marketing Claims:** Removed repetitive promotional claims (e.g., "100% extraction", "100% success", "100% verified") across all views.
3. **Restrained Homepage Statistics:** Streamlined the statistics section to exactly **4 objective project facts**:
   - **30** Research Papers
   - **570** Indexed Chunks
   - **5** Research Categories
   - **75** Evaluation Questions
4. **Intuitive Section Hierarchy:**
   - **Hero Section:** Academic badge and research tagline.
   - **Primary Research Search (`#ask`):** Positioned immediately below the hero for instant exploratory queries, accompanied by a clear static demo disclosure.
   - **4 Project Facts:** Scannable summary of the indexed clinical corpus.
   - **Featured Paper & Research Catalogue (`#papers`):** Spotlight on *Saratkar et al., Frontiers in Digital Health 2025*, 5 research category filters, real-time metadata search, and integrated multi-page PDF modal viewer.
   - **Methodology & Grounding (`#about`):** Clinical RAG workflow and citation mechanics.
   - **Hybrid RAG Architecture (`#rag`):** Interactive visualization of the hybrid retrieval (BM25 + Dense + RRF) and neural cross-encoder reranking pipeline.
   - **Evaluation & Groundedness (`#evaluation`):** Transparent display of 5 core retrieval metrics and an expandable audit of all 13 benchmark edge cases.
   - **Footer:** Direct links to the GitHub repository, live demo, and academic licensing.

---

## 2. Transparent Evaluation & Benchmark Metrics

Rather than presenting inflated or repetitive marketing statistics, the evaluation dashboard clearly separates primary statistical information-retrieval (IR) metrics from smaller boundary stress-test sets.

### 2.1 Primary Information Retrieval & Grounding Metrics (75-Question Benchmark)

| Metric | Measured Value | Definition & Measurement Protocol |
| :--- | :---: | :--- |
| **Recall@5** | **93.3%** | Proportion of benchmark queries where the ground-truth evidence chunk appeared in top 5 retrieved results |
| **MRR (Mean Reciprocal Rank)** | **0.888** | Evaluates ranking precision of the first relevant passage (\(\frac{1}{\text{rank}}\)) |
| **nDCG@5** | **0.899** | Normalized Discounted Cumulative Gain accounting for position-discounted retrieval relevance |
| **Paper Citation Accuracy** | **86.7%** | Strict match between the cited paper identifier and the independent ground-truth paper |
| **Page-Level Citation Accuracy** | **71.1%** | Verifiable match between the cited PDF page number and the source evidence passage |

### 2.2 Boundary Guardrail Benchmarks (Reported with Explicit Sample Denominators)

| Test Category | Evaluated Ratio | Percentage | Scope Note |
| :--- | :---: | :---: | :--- |
| **Out-of-Domain Refusal** | **22 / 22** | **100.0%** | Evaluated on 22 out-of-scope non-medical queries (cooking, finance, coding, pop culture) |
| **Insufficient Evidence Detection** | **8 / 8** | **100.0%** | Evaluated on 8 clinical queries with missing or sparse corpus context |
| **Numerical Claim Accuracy** | **100.0%** | **100.0%** | Zero hallucinated numbers or statistics across all evaluated responses |

### 2.3 Transparent Edge-Case Audit (13 Analyzed Cases)

All 13 benchmark edge cases are presented in an expandable `<details>` table detailing:
- Question ID (`Q01` – `Q75`)
- Clinical Query Text
- Evaluation Category
- Expected Ground Truth Citation
- Observed Retrieval Output
- Failure Category (e.g., Top Citation Mismatch, Section Header Match)
- Root Cause Analysis (e.g., dense semantic embedding overlap across related papers)

---

## 3. End-to-End Verification Summary

Comprehensive browser verification was performed on the deployed GitHub Pages site ([https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/](https://saniya1312s.github.io/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant/)):

1. **Academic Styling & Hero:**
   - Academic badge renders cleanly: `⚡ Static Portfolio Demo · Pre-Indexed Evidence & Benchmarks · 30 Papers`.
   - Title matches `MediEvidence: Clinical Evidence Assistant`.
   - Exactly 4 project fact cards render with balanced spacing and typography.
2. **Main Search Interface (`#ask`):**
   - Notice displayed: *"Static Portfolio Demo — Explore pre-indexed research evidence and benchmark examples. Live RAG inference is available in the locally hosted application."*
   - Sample query (`"How are digital twins used in personalized medicine?"`) returns grounded evidence with confidence score `0.78`, citation `[1]`, and chunk source `MED-DHM-001_p01_c01`.
   - Out-of-Domain query (`"What is the recipe for chocolate cake?"`) triggers strict refusal: *"I cannot answer this query as it falls outside digital healthcare, clinical AI, and biomedical research."*
3. **Research Papers Catalogue (`#papers`):**
   - Featured publication spotlight for *Saratkar et al., Frontiers in Digital Health 2025* displayed prominently.
   - Category filter cards tested: selecting *"Medical Imaging & AI"* filtered table to exactly 6 papers; clearing filter restored all 30 papers.
   - Text search tested: searching *"Saratkar"* filtered the catalogue to the matching publication.
   - Integrated PDF modal viewer opened with clean page navigation controls (`◀ Prev`, `Next ▶`, `↗ New Tab`, `✕`).
4. **Evaluation & Audit Tables (`#evaluation`):**
   - Core 5 metrics displayed in clean, non-glowing cards.
   - Secondary metrics rendered with explicit sample size notes.
   - 13 failure cases expandable with full root-cause audit.
   - 75 benchmark questions expandable with category and ground-truth tags.
5. **Mobile Responsiveness (375 × 812 viewport):**
   - Navigation collapses to an accessible hamburger menu (`.nav-hamburger`).
   - Cards and search container wrap cleanly within 360px container without horizontal scroll or clipping.

---

## 4. Local Execution for Full AI Inference

To run live neural inference with FastAPI, Qdrant vector retrieval, and Cross-Encoder neural reranking:

```bash
# Clone the repository
git clone https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant.git
cd MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant

# Install dependencies
pip install -r requirements.txt

# Start the local FastAPI server
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Once running, navigate to `http://127.0.0.1:8000` to interact with live sentence embeddings, BM25 retrieval, and neural cross-encoder reranking.
