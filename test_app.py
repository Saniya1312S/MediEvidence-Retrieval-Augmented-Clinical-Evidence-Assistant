"""
Local End-to-End Verification of FastAPI Application & MediEvidence Endpoints
"""
import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import requests

SERVER_URL = "http://127.0.0.1:8000"
use_live = False
try:
    print("[Client] Checking live server at http://127.0.0.1:8000/ ...", flush=True)
    res = requests.get(f"{SERVER_URL}/", timeout=10.0)
    if res.status_code == 200:
        use_live = True
        print(f"[Client] Connected to live running FastAPI server at {SERVER_URL}!", flush=True)
except Exception as e:
    print(f"[Client] Live server check failed: {e}", flush=True)
    pass

if use_live:
    class LiveClient:
        def get(self, path, **kwargs):
            return requests.get(f"{SERVER_URL}{path}", **kwargs)
        def post(self, path, **kwargs):
            return requests.post(f"{SERVER_URL}{path}", **kwargs)
    client = LiveClient()
else:
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)

print("=" * 80)
print("MediEvidence — Automated End-to-End Test Suite (12 Comprehensive Tests)")
print("=" * 80)

# 1. Test Root
print("\n[Test 1] GET / (Root HTML)")
r = client.get("/")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
assert "MediEvidence" in r.text
print("✓ Root endpoint serves MediEvidence dashboard HTML successfully.")

# 2. Test Health
print("\n[Test 2] GET /api/health")
r = client.get("/api/health")
assert r.status_code == 200
data = r.json()
assert data["status"] == "healthy"
assert data["vector_database"]["indexed_chunks"] == 570
print(f"✓ Health check: healthy | Indexed chunks: {data['vector_database']['indexed_chunks']}")

# 3. Test Stats
print("\n[Test 3] GET /api/stats")
r = client.get("/api/stats")
assert r.status_code == 200
stats = r.json()
assert stats["author_highlight"]["doi"] == "10.3389/fdgth.2025.1583466"
print(f"✓ Dataset stats loaded. Author highlight: {stats['author_highlight']['title']}")

# 4. Test Papers
print("\n[Test 4] GET /api/papers")
r = client.get("/api/papers")
assert r.status_code == 200
papers_data = r.json()
assert papers_data["total"] == 30, f"Expected 30 papers, got {papers_data['total']}"
print(f"✓ Paper catalog contains all {papers_data['total']} verified research papers.")

# 5. Test Author Paper Detail
print("\n[Test 5] GET /api/papers/MED-DT-001 (Saniya Y. Saratkar et al.)")
r = client.get("/api/papers/MED-DT-001")
assert r.status_code == 200
p = r.json()
assert "Saratkar" in p["paper"]["authors"]
assert p["total_chunks"] == 23
print(f"✓ Paper MED-DT-001 verified: '{p['paper']['title']}' ({p['total_chunks']} chunks).")

# 6. Test Chunks Pagination
print("\n[Test 6] GET /api/chunks?page=1&page_size=5")
r = client.get("/api/chunks?page=1&page_size=5")
assert r.status_code == 200
chunks_data = r.json()
assert len(chunks_data["chunks"]) == 5
assert chunks_data["total_items"] == 570
print(f"✓ Chunk explorer verified: {chunks_data['total_items']} total chunks across {chunks_data['total_pages']} pages.")

# 7. Test Query Endpoint (Clinical Domain)
print("\n[Test 7] POST /api/query (Clinical Query: Saratkar et al. Digital Twin)")
clinical_q = "How does the digital twin architecture developed by Saratkar et al. enable predictive modeling for personalized therapies?"
r = client.post("/api/query", json={"query": clinical_q, "top_k": 5})
assert r.status_code == 200
ans = r.json()
assert ans["is_refusal"] is False
assert ans["confidence_score"] >= 0.6
assert len(ans["citations"]) > 0
top_cite = ans["citations"][0]
print(f"✓ Grounded Answer: {ans['answer'][:120]}...")
print(f"  Confidence: {ans['confidence_score']} | Status: {ans['status']}")
print(f"  Top Citation: [{top_cite['paper_title']} ({top_cite['publication_year']}), Page {top_cite['original_page']}]")
print(f"  PICO Domain: {ans['pico_evidence']['Research Domain']}")

# 8. Test Query Endpoint (Out-of-Domain Refusal)
print("\n[Test 8] POST /api/query (Out-of-Domain Refusal Guardrail)")
ood_q = "What is the best recipe for baking a chocolate cake with fudge icing?"
r = client.post("/api/query", json={"query": ood_q, "top_k": 5})
assert r.status_code == 200
ans = r.json()
assert ans["is_refusal"] is True
assert ans["confidence_score"] == 0.0
assert "Refused" in ans["status"]
print(f"✓ Guardrail triggered correctly: {ans['status']}")
print(f"  Explanation: {ans['guardrail_explanation']}")

# 9. Test Evaluation Endpoint
print("\n[Test 9] GET /api/evaluate")
r = client.get("/api/evaluate")
assert r.status_code == 200
eval_data = r.json()
assert eval_data["summary"]["total_questions_tested"] in [50, 75]
assert eval_data["summary"]["recall_at_1_percent"] >= 80.0
assert eval_data["summary"]["mrr"] >= 0.85
print(f"✓ Evaluation summary: Total = {eval_data['summary']['total_questions_tested']} | Recall@1 = {eval_data['summary']['recall_at_1_percent']}% | MRR = {eval_data['summary']['mrr']}")

# 10. Test Failure Analysis Endpoint
print("\n[Test 10] GET /api/evaluate/failures")
r = client.get("/api/evaluate/failures")
assert r.status_code == 200
fail_data = r.json()
assert fail_data["total_evaluated"] in [50, 75]
assert "failures" in fail_data
print(f"✓ Failure analysis verified: {fail_data['total_failures']} logged failures across {fail_data['total_evaluated']} questions ({fail_data['failure_rate_percent']}% failure rate).")

# 11. Test Exact Quote Search Endpoint
print("\n[Test 11] GET /api/search/exact (Unicode NFKD & Ligature search)")
quote_text = "In contrast, the use of DTs enables a shift toward precision"
r = client.get(f"/api/search/exact?quote={quote_text}")
assert r.status_code == 200
exact_res = r.json()
assert exact_res["found"] is True
assert exact_res["paper_id"] == "MED-DT-001"
assert exact_res["page_number"] == 2
print(f"✓ Exact quote resolved: Paper {exact_res['paper_id']} Page {exact_res['page_number']} (Match confidence: {exact_res['match_confidence']})")

# 12. Test Paper-Specific Filtered Query
print("\n[Test 12] POST /api/query with paper_id filter")
r = client.post("/api/query", json={
    "query": "What specific personalized oncology modeling methods are detailed for patient digital twins in Saratkar et al.?",
    "paper_id": "MED-DT-001",
    "top_k": 3
})
assert r.status_code == 200
paper_query = r.json()
assert paper_query["is_refusal"] is False
assert len(paper_query["citations"]) > 0
assert all(c["paper_id"] == "MED-DT-001" for c in paper_query["citations"])
print(f"✓ Paper-specific query verified: All citations strictly constrained to MED-DT-001 (Page {paper_query['citations'][0]['original_page']}).")

print("\n" + "=" * 80)
print("ALL 12 LOCAL END-TO-END TESTS PASSED WITH 100% SUCCESS!")
print("=" * 80)
# Gracefully shutdown Qdrant client if running in-memory
if not use_live:
    from rag_engine import MediEvidenceRAG
    MediEvidenceRAG.get_instance().qdrant.close()
