import os
import json

os.chdir(r"C:\Users\SANIYA\.gemini\antigravity\scratch\MediEvidence-Retrieval-Augmented-Clinical-Evidence-Assistant")

from rag_engine import MediEvidenceRAG

rag = MediEvidenceRAG.get_instance()

test_queries = [
    ("Q01", "How are digital twins used in personalized medicine development?", "MED-DT-001"),
    ("Q02", "What is the primary objective of LeViT-UNet++ in medical image segmentation?", "MED-IMG-002"),
    ("Q20", "How can retrieval-grounded generative models clarify diagnostic recommendations for attending physicians?", "MED-CDS-001"),
    ("Q38", "How do IoT body area networks integrate with cloud and edge systems for elderly healthcare?", "MED-DHM-004"),
    ("Q48", "What was the Phase 3 clinical trial efficacy percentage of the Moderna mRNA-1273 COVID-19 vaccine?", "REFUSE"),
    ("Q50", "What is the standardized SUV cutoff threshold for florbetapir amyloid-beta PET imaging in Alzheimer disease diagnosis?", "REFUSE"),
    ("OOD1", "What are the rules of cricket and how many players are in each team?", "REFUSE_OOD"),
    ("OOD2", "How do I make chocolate chip cookies at home?", "REFUSE_OOD")
]

print("\n--- TESTING HYBRID RETRIEVE ---")
for qid, q, exp in test_queries:
    res = rag.hybrid_retrieve(q)
    if res["is_refusal"]:
        status = f"REFUSED: {res['status']}"
        top_info = res["guardrail_explanation"][:60]
    else:
        top_cite = res["citations"][0] if res["citations"] else {}
        status = f"ACCEPTED: {res['status']}"
        top_info = f"{top_cite.get('paper_id')} P.{top_cite.get('original_page')} - {top_cite.get('paper_title')[:35]}"
        
    print(f"[{qid}] Exp: {exp:12s} | {status:35s} | {top_info}")
    if not res["is_refusal"]:
        print(f"      Answer excerpt: {res['answer'][:120]}...")

rag.qdrant.close()
