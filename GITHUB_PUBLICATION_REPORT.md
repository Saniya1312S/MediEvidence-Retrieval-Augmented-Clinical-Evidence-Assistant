# MediEvidence — GitHub Publication & Verification Report

**Date:** November 21, 2026  
**Repository:** [MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant](https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant)  
**Target Branch:** `main`  
**Publication Status:** **SUCCESSFULLY PUBLISHED & VERIFIED**

---

## 1. Executive Summary & Git Commit Integrity

| Metric / Check | Value / Status | Verification Notes |
|---|---|---|
| **Remote Repository URL** | `https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant.git` | GitHub HTTPS origin verified |
| **Active Target Branch** | `main` | Successfully fast-forward pushed (`739f47e..690713c`) |
| **Published Commit Hash** | `690713c` | `feat: publish MediEvidence research assistant with verified citations and evaluation suite` |
| **Preservation of `v1` Branch** | **VERIFIED INTACT** | `origin/v1` remains at commit `2a47605` (zero destructive resets, zero force pushes) |
| **Working Tree Cleanliness** | Clean (`nothing to commit, working tree clean`) | All 104 files tracked; temporary files and vector cache excluded |
| **Total Files Committed** | **104 files** (176,922 insertions) | Complete production stack, 30 PDFs, evaluations, docs & screenshots |

---

## 2. Inventory of Published Assets

### A. Core Architecture & Backend
- `main.py`: FastAPI application entrypoint with Starlette `FileResponse` streaming and route mounting.
- `rag_engine.py`: Production-grade dual-path hybrid retrieval engine (`SentenceTransformers` 384d dense embeddings + BM25Okapi lexical matching + Reciprocal Rank Fusion $k=60$ + `Cross-Encoder/ms-marco-MiniLM-L-6-v2` neural reranking + regex word-boundary guardrails).
- `api/__init__.py` & `api/routes.py`: REST API endpoints (`/api/health`, `/api/stats`, `/api/papers`, `/api/papers/{paper_id}/pdf`, `/api/chunks`, `/api/query`, `/api/evaluate`).
- `ingest_pipeline.py`: Asynchronous extraction and chunking pipeline utilizing PyMuPDF (`fitz`) and selective Tesseract OCR fallback.
- `requirements.txt`: Pinned production dependencies for Python 3.10–3.12.
- `.env.example`: Clean environment template.
- `.gitignore`: Production exclusions protecting repository size and secrets.

### B. Curated 30-Paper Open-Access Research Corpus (`data/papers/`)
- **Total Open-Access PDFs:** 30 papers (72.9 MB total, 570 pages, 281,976 words).
- **Categories Covered (6 papers each):**
  1. `clinical_decision_support/` (Papers `MED-CDS-001` through `MED-CDS-006`)
  2. `digital_health_monitoring/` (Papers `MED-DHM-001` through `MED-DHM-006`)
  3. `digital_twins_personalized_medicine/` (Papers `MED-DT-001` through `MED-DT-006`, including primary author publication: *Saniya Y. Saratkar et al., Frontiers in Digital Health 2025*)
  4. `healthcare_iot_predictive_analytics/` (Papers `MED-IOT-001` through `MED-IOT-006`)
  5. `medical_imaging_ai/` (Papers `MED-IMG-001` through `MED-IMG-006`)
- `data/extracted_text/`: 30 page-structured extracted text files.
- `data/metadata/`: `paper_catalog.csv` (30 papers), `page_metadata.csv` (570 pages), `chunk_metadata.csv` (570 chunks), `ingestion_report.csv`, and precomputed `bm25_index.pkl`.

### C. Rigorous Evaluation & Benchmark Suite (`data/evaluation/`)
- `data/evaluation/evaluation_questions.json`: 75 ground-truth benchmark questions across clinical in-domain (45), out-of-domain (22 across 8 topics), and insufficient evidence (8).
- `data/evaluation/evaluation_summary.json`: Ground-truth aggregated benchmark metrics.
- `data/evaluation/evaluation_results_75.json`: Granular per-query retrieval logs and cross-encoder scores.
- `data/evaluation/evaluation_failures.json`: Transparent, honest documentation of all 13 edge-case failures.
- `build_and_evaluate_expanded.py`: Evaluation runner for the full 75-question benchmark.
- `evaluate_rag.py`: Evaluation script for the baseline 30-question suite.
- `test_app.py`, `test_exact_search.py`, `test_hybrid_rag.py`: 12-test automated regression and integration suite (100% passing).

### D. Modern Glassmorphic Frontend & Static Demo Mode
- `index.html`: Responsive dark-mode dashboard with dual-mode support (Live API backend or GitHub Pages static fallback).
- `style.css`: Clean UTF-8 encoded stylesheet featuring CSS grid, custom scrollbars, and glassmorphic card design.
- `script.js`: Client-side state manager with embedded deep-linking PDF modal viewer (`/api/papers/{paper_id}/pdf#page=X`), live score inspectors, and paper-specific query filtering.
- `data/static_data.json`: Pre-indexed search and catalog bundle allowing interactive demonstrations on static GitHub Pages.
- `.nojekyll`: Bypass GitHub Pages Jekyll processing for raw static file delivery.

### E. Project Documentation & Evidence Screenshots
- `README.md`: Professional, beginner-friendly documentation with Mermaid architecture diagrams, curated dataset catalog, honest benchmark results, and author spotlight.
- `DEMO_GUIDE.md`: 3-to-5 minute demonstration script with 5 verified queries.
- `BROWSER_TEST_REPORT.md`: Comprehensive end-to-end verification report across desktop and mobile viewports.
- `screenshots/`: 8 verified browser screenshots capturing homepage, paper catalogue, deep-linked PDF reader, RAG query synthesis, architecture diagrams, benchmark dashboard, and mobile layouts.

---

## 3. Rationale for Excluded Files

| Excluded Pattern | Technical Rationale |
|---|---|
| `data/qdrant_storage/` | Contains binary HNSW graph vectors and index segments (~85 MB). Excluded via `.gitignore` to prevent GitHub repository bloat. Users can deterministically generate the local vector collection in 2 minutes by executing `python ingest_pipeline.py`. |
| `check_*.py`, `scratch_*.py`, `diagnose_*.py` | Ad-hoc debugging scripts used during the RAG repair phase; excluded to maintain a clean, production-grade root directory. |
| `.env` / `*.env` | Excluded per security best practices. Clean `.env.example` provided for onboarding. |
| `__pycache__/`, `*.pyc` | Python byte-compiled artifacts excluded. |

---

## 4. Benchmark & Retrieval Quality Summary

| Metric | Target | MediEvidence Measured Result |
|---|---|---|
| **Recall @ 1** | $\ge 80.0\%$ | **86.7%** |
| **Recall @ 3** | $\ge 85.0\%$ | **88.9%** |
| **Recall @ 5** | $\ge 90.0\%$ | **93.3%** |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.850$ | **0.888** |
| **nDCG @ 5** | $\ge 0.850$ | **0.899** |
| **Paper Citation Accuracy** | $\ge 85.0\%$ | **86.7%** |
| **Page-Level Citation Accuracy** | $\ge 70.0\%$ | **71.1%** |
| **Evidence Support Rate** | $\ge 80.0\%$ | **82.2%** |
| **Numerical Claim Accuracy** | $100.0\%$ | **100.0%** (Zero numerical hallucinations) |
| **Out-of-Domain Refusal Rate** | $100.0\%$ | **100.0%** (22/22 refused) |
| **Insufficient Evidence Detection** | $100.0\%$ | **100.0%** (8/8 identified) |
| **Fabricated Citations** | 0 | **0 Fabricated Citations** |

### Academic Honesty: The 71.1% Page Citation Reality
Rather than inflating metrics, the project transparently explains the 15.6% delta between paper-level (86.7%) and page-level (71.1%) accuracy. In long review papers (e.g. *Vadhavkar et al.*, 44 pages), core concepts span across multiple consecutive pages. When the model retrieves Page 4 (the section overview) rather than Page 5 (the summary table), the answer is factually grounded but strict single-page string matching marks it as a miss. All 13 failure cases are preserved in `data/evaluation/evaluation_failures.json`.

---

## 5. Live Demo Feasibility Assessment & Cloud Roadmap

- **Current Operational Status:** **Deployment Pending** (Transparently stated in `README.md`).
- **Why Local / Self-Hosted is Optimal:** MediEvidence uses local dense embedding (`all-MiniLM-L6-v2`) and cross-encoder neural reranking (`ms-marco-MiniLM-L-6-v2`), which require approximately **1.2 GB RAM** during initialization. Free-tier cloud instances (512 MB memory caps on Render/Railway) experience OOM terminations.
- **Static GitHub Pages Mode:** Fully functional using `data/static_data.json` without requiring a live Python backend.
- **Container Deployment Blueprint:** A tested `Dockerfile` is included in `README.md` enabling 1-click deployment to Hugging Face Spaces or containerized cloud instances.

---

## 6. How to Showcase in Interviews & Portfolio

1. **Highlight the Problem Statement:** Emphasize that generic RAG hallucinates page numbers and fails to refuse out-of-domain questions; MediEvidence achieves 100% numerical accuracy and 100% out-of-domain refusal.
2. **Walk Through `DEMO_GUIDE.md`:** Run the 4-minute demo with the 5 verified queries, showing the live score inspector and PDF page deep-linking.
3. **Showcase Author Attribution:** Demonstrate retrieval of the primary author's published work in *Frontiers in Digital Health (2025)*.
4. **Discuss Engineering Trade-offs:** Speak knowledgeably about the 71.1% page citation challenge and how multi-page topic continuity informed chunking strategies.
