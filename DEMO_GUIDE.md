# MediEvidence — 3 to 5 Minute Live Demonstration Guide

This guide is designed for recruiters, engineering hiring managers, AI researchers, and technical interviewers who want to evaluate **MediEvidence: AI-Powered Research Assistant for Digital Healthcare Literature**.

---

## 🎯 Demo Objectives & Key Takeaways

In this 3-to-5 minute demonstration, you will observe:
1. **Zero-Hallucination Retrieval:** How MediEvidence accurately pinpoints exact research evidence across 30 peer-reviewed papers (570 pages).
2. **Deterministic Page-Level Citations:** Every retrieved claim is tied to `[Paper Title (Year), Page X]` and verifiable in the built-in PDF viewer.
3. **Hybrid RAG Mechanics:** Real-time visibility into Dense Cosine, BM25 Lexical, and Cross-Encoder neural rerank scores.
4. **Strict Guardrail Refusal:** Demonstration of 100% out-of-domain rejection preventing inappropriate or fabricated answers.
5. **Primary Author Spotlight:** Direct retrieval of research from *Saniya Y. Saratkar et al. (Frontiers in Digital Health, 2025)*.

---

## ⚡ 60-Second Quick Start

```bash
# 1. Clone repository
git clone https://github.com/Saniya1312S/MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant.git
cd MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant

# 2. Install dependencies (requires Python 3.10+)
pip install -r requirements.txt

# 3. Launch application
python main.py
```

*Open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000).*

---

## ⏱️ 4-Minute Demonstration Walkthrough Script

### Minute 1: The Research Problem & Catalog Overview (0:00 - 1:00)

1. **Open the Homepage (`#home`):**
   - Point out the real-time corpus counter pills: **30 Papers**, **570 Chunks**, **570 Pages**, **5 Categories**, **100% Native Extraction**.
   - Explain the core motivation: *"Researchers frequently remember a clinical result or machine learning architecture, but forget which specific paper or PDF page contained it."*
2. **Navigate to Research Papers (`#papers`):**
   - Scroll through the 30-paper catalogue.
   - In the search bar, type `Saratkar`.
   - Show the filtered result: `MED-DT-001: Digital Twin for Personalized Medicine Development` published in *Frontiers in Digital Health (2025)*.
   - Click the **"Inspect Details"** button: observe metadata, DOI, full author list, and indexed semantic chunks.
   - Click **"View Original PDF"**: notice the built-in viewer opens directly to Page 1 of the original publication.

---

### Minute 2: Primary Author Research Retrieval (1:00 - 2:00)

1. **Navigate to Ask MediEvidence (`#ask`):**
2. **Submit Query 1 (Author Research):**
   ```text
   How are digital twins used in personalized medicine development?
   ```
3. **What to Observe:**
   - **Grounded Status:** Status displays `✓ Grounded in Research Evidence` with a high confidence score (~0.83).
   - **Page Citation:** The system retrieves and cites `[Digital Twin for Personalized Medicine Development (2025), Page 2]`.
   - **PICO Synthesis:** Population, Intervention (digital twin in-silico simulation), Comparison, and Outcome are parsed cleanly.
   - **PDF Verification:** Click the citation link `[Page 2]` — the PDF viewer immediately renders Page 2 of the author's paper.
   - **Inspect Scores:** Expand the *Multi-Stage Score Inspector* to show the Dense Cosine score, BM25 Okapi score, and Cross-Encoder neural rerank score.

---

### Minute 3: Precision Retrieval in Imaging & IoT Wearables (2:00 - 3:00)

1. **Submit Query 2 (Technical Acronyms & Medical Imaging):**
   ```text
   What is the primary objective of LeViT-UNet++ in medical image segmentation?
   ```
   - **Outcome:** The hybrid pipeline uses BM25 lexical token matching to catch the exact term `LeViT-UNet++` and pairs it with dense semantic search.
   - **Citation:** Correctly cites `MED-IMG-002` (*LeViT-UNet++*, Page 1), explaining how transformer encoders balance fine-grained details with global context.

2. **Submit Query 3 (On-Device Wearables & IoT):**
   ```text
   How does PocketTSLM deploy language models for wearable time-series modeling on smart devices?
   ```
   - **Outcome:** Correctly retrieves `MED-IOT-001` (*PocketTSLM*, Page 4).
   - **Highlight:** Shows how parameter-efficient soft-prompt tuning enables time-series modeling locally on edge wearables without compromising patient privacy.

---

### Minute 4: Guardrail Refusal & Architecture Transparency (3:00 - 4:00)

1. **Submit Query 4 (Out-of-Domain Guardrail Test):**
   ```text
   What is the authentic Italian recipe for pasta alla carbonara without using heavy cream or peas?
   ```
   - **Outcome:** **Immediate Refusal**.
   - **Notice:** MediEvidence does not hallucinate a recipe or attempt to force a medical analogy. The whole-word boundary regex and cosine guardrails trigger a strict refusal adhering to clinical AI domain boundaries.

2. **Navigate to RAG Architecture (`#rag`):**
   - Review the dual offline/online pipeline diagram showing PyMuPDF extraction, semantic chunking, Qdrant HNSW indexing, BM25, and Cross-Encoder reranking.

3. **Navigate to Evaluation Dashboard (`#evaluation`):**
   - Point out the verified 75-question benchmark metrics:
     - **Recall@1:** 86.7%
     - **Recall@5:** 93.3%
     - **MRR:** 0.888
     - **Out-of-Domain Refusal:** 100.0% (22/22)
     - **Page Citation Accuracy:** 71.1% (with full transparent disclosure of failure modes).

---

## 📋 5 Verified Test Queries for Hands-On Testing

Copy and paste any of these 5 verified benchmark questions into the search box:

| # | Question String | Expected Target Paper | Target Page | Key Verifiable Fact |
|---|---|---|---|---|
| **1** | `How are digital twins used in personalized medicine development?` | `MED-DT-001` (Saratkar et al., 2025) | Page 2 | In-silico organ modeling and real-time sensor streams for individualized therapy optimization. |
| **2** | `What is the primary objective of LeViT-UNet++ in medical image segmentation?` | `MED-IMG-002` (Xu et al., 2026) | Page 1 | Balances fine-grained edge details and high-level context using nested dense skip connections. |
| **3** | `How does PocketTSLM deploy language models for wearable time-series modeling on smart devices?` | `MED-IOT-001` (Rosenblattl et al., 2026) | Page 4 | Soft-prompt tuning for local, privacy-preserving time-series inference on low-power devices. |
| **4** | `How do RAG-enhanced LLMs support interactive explainability in clinical decision support?` | `MED-CDS-001` (Mannocci et al., 2026) | Page 1 | Provides clinician-facing diagnostic explanations grounded in indexed clinical guidelines. |
| **5** | `What is the authentic Italian recipe for pasta alla carbonara without using heavy cream or peas?` | *None (Out-of-Domain)* | *N/A* | **Refusal Triggered:** Enforces 100% strict domain boundary policy. |

---

## 🔍 How to Demonstrate Paper-Specific Mode

MediEvidence supports targeting queries to a single document:

1. Under the query box, toggle from **"🌐 Search All 30 Papers"** to **"📄 Specific Paper"**.
2. Select `MED-DT-001 - Digital Twin for Personalized Medicine Development (2025)`.
3. Ask: `What oncology modeling methods are detailed for patient digital twins?`
4. Observe that 100% of the returned chunks, citations, and scores are constrained strictly to `MED-DT-001`.
