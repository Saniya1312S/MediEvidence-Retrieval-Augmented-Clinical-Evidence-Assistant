"""
Generate data/static_data.json for GitHub Pages fallback mode.
"""
import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import csv
import json
from rag_engine import MediEvidenceRAG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
EVAL_DIR = os.path.join(DATA_DIR, "evaluation")

# 1. Load papers
papers = []
with open(os.path.join(METADATA_DIR, "paper_catalog.csv"), "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        papers.append(row)

# 2. Load stats
stats = {}
with open(os.path.join(METADATA_DIR, "ingestion_report.csv"), "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        stats[row["metric"]] = {
            "value": row["value"],
            "description": row["description"]
        }

# 3. Load evaluation summary & questions
with open(os.path.join(EVAL_DIR, "evaluation_summary.json"), "r", encoding="utf-8") as f:
    eval_summary = json.load(f)

with open(os.path.join(EVAL_DIR, "evaluation_questions.json"), "r", encoding="utf-8") as f:
    eval_questions = json.load(f)

# 4. Load chunks (first 60 for explorer)
sample_chunks = []
with open(os.path.join(METADATA_DIR, "chunk_metadata.csv"), "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        sample_chunks.append({
            "chunk_id": row["chunk_id"],
            "paper_id": row["paper_id"],
            "paper_title": row["paper_title"],
            "authors": row["authors"],
            "publication_year": row["publication_year"],
            "category": row["category"],
            "original_page": int(row["original_page"]),
            "section_heading": row["section_heading"],
            "char_count": int(row["char_count"]),
            "word_count": int(row["word_count"]),
            "text_content": row["text_content"],
            "doi": row["doi"]
        })

print(f"Loaded {len(papers)} papers, {len(sample_chunks)} chunks, eval summary.")

# 5. Run sample queries through RAG engine
rag = MediEvidenceRAG.get_instance()

sample_queries_list = [
    "How does the digital twin architecture developed by Saratkar et al. enable predictive modeling for personalized therapies?",
    "How does retrieval-augmented correction improve generalist medical AI hallucination rates?",
    "What architectural innovations are introduced in LeViT-UNet++ for medical image segmentation?",
    "What is the HAPI-EP framework for adaptive digital twins in cardiac electrophysiology?",
    "How does PocketTSLM achieve on-device predictive time-series modeling for smart healthcare wearables?",
    "How does operation-aware multimodal CDSS predict ICU discharge risks?",
    "What role does agentic robotics play in transitioning remote patient monitoring from observation to intervention?",
    "What is the best recipe for baking a chocolate cake with fudge icing?",
    "How do I replace the blown head gasket on a 2012 Honda Civic engine?"
]

sample_query_results = {}
for q in sample_queries_list:
    print(f"Indexing RAG response for: {q[:60]}...")
    res = rag.hybrid_retrieve(q, top_k=5)
    sample_query_results[q] = res

# 6. Build static data payload
static_payload = {
    "project": "MediEvidence – Retrieval-Augmented Clinical Evidence Assistant",
    "version": "2026.1.0",
    "author_highlight": {
        "title": "Digital Twin for Personalized Medicine Development",
        "authors": "Saniya Y. Saratkar et al.",
        "journal": "Frontiers in Digital Health",
        "year": 2025,
        "doi": "10.3389/fdgth.2025.1583466",
        "paper_id": "MED-DT-001"
    },
    "stats": stats,
    "papers": papers,
    "evaluation": {
        "summary": eval_summary,
        "questions": eval_questions
    },
    "sample_chunks": sample_chunks,
    "sample_queries": sample_query_results
}

out_path = os.path.join(DATA_DIR, "static_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(static_payload, f, indent=2)

print(f"Generated static data bundle at: {out_path} ({os.path.getsize(out_path):,} bytes)")
