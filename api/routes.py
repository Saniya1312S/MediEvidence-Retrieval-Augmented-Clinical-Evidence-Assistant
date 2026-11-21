"""
MediEvidence — REST API Routes
Provides endpoints for health checks, dataset stats, paper catalog,
chunk explorer, hybrid RAG querying with paper-id filtering, exact passage search,
and evaluation benchmark results with failure analysis.
"""
import os
import csv
import json
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from rag_engine import MediEvidenceRAG

router = APIRouter(prefix="/api", tags=["MediEvidence API"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
EVAL_DIR = os.path.join(DATA_DIR, "evaluation")

PAPER_CATALOG_PATH = os.path.join(METADATA_DIR, "paper_catalog.csv")
CHUNK_META_PATH = os.path.join(METADATA_DIR, "chunk_metadata.csv")
PAGE_META_PATH = os.path.join(METADATA_DIR, "page_metadata.csv")
INGESTION_REPORT_PATH = os.path.join(METADATA_DIR, "ingestion_report.csv")
EVAL_SUMMARY_PATH = os.path.join(EVAL_DIR, "evaluation_summary.json")
EVAL_QUESTIONS_PATH = os.path.join(EVAL_DIR, "evaluation_questions.json")
EVAL_FAILURES_PATH = os.path.join(EVAL_DIR, "evaluation_failures.json")

# Pydantic Schemas
class QueryRequest(BaseModel):
    query: str = Field(..., description="The clinical research question to ask", min_length=2)
    top_k: int = Field(5, description="Number of supporting passages to retrieve", ge=1, le=10)
    category_filter: Optional[str] = Field(None, description="Optional category filter")
    paper_id: Optional[str] = Field(None, description="Optional paper_id filter to restrict retrieval to a specific paper")
    similarity_threshold: float = Field(0.35, description="Threshold for refusal guardrail")
    use_reranking: bool = Field(True, description="Enable Cross-Encoder reranking")

class QueryResponse(BaseModel):
    is_refusal: bool
    query: str
    answer: str
    status: str
    confidence_score: float
    citations: List[dict]
    evidence_passages: List[dict]
    pico_evidence: Optional[dict] = None
    guardrail_explanation: Optional[str] = None

class ExactSearchRequest(BaseModel):
    quote: str = Field(..., description="The exact passage or quote to search for", min_length=5)
    paper_id: Optional[str] = Field(None, description="Optional paper_id to restrict search")


@router.get("/health")
def get_health():
    """Health check verifying model loading, Qdrant index, and chunk count."""
    rag = MediEvidenceRAG.get_instance()
    return {
        "status": "healthy",
        "service": "MediEvidence Clinical Assistant",
        "version": "2026.1.0",
        "models": {
            "dense_embedder": "all-MiniLM-L6-v2 (384-dimensional)",
            "cross_encoder": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "sparse_retrieval": "BM25Okapi"
        },
        "vector_database": {
            "type": "Qdrant Local Disk Storage",
            "collection": rag.collection_name,
            "indexed_chunks": len(rag.chunks_by_id)
        }
    }


@router.get("/stats")
def get_stats():
    """Returns dataset and ingestion metrics from ingestion_report.csv."""
    stats = {}
    if os.path.exists(INGESTION_REPORT_PATH):
        with open(INGESTION_REPORT_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats[row["metric"]] = {
                    "value": row["value"],
                    "description": row["description"]
                }
    return {
        "dataset_stats": stats,
        "categories_count": 5,
        "author_highlight": {
            "title": "Digital Twin for Personalized Medicine Development",
            "authors": "Saniya Y. Saratkar et al.",
            "journal": "Frontiers in Digital Health",
            "year": 2025,
            "doi": "10.3389/fdgth.2025.1583466",
            "paper_id": "MED-DT-001"
        }
    }


@router.get("/papers")
def list_papers(
    category: Optional[str] = Query(None, description="Filter by category slug or title"),
    search: Optional[str] = Query(None, description="Search term in title, authors, or DOI")
):
    """Returns the verified catalog of 30 research papers."""
    if not os.path.exists(PAPER_CATALOG_PATH):
        raise HTTPException(status_code=404, detail="Paper catalog not found.")

    papers = []
    with open(PAPER_CATALOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            papers.append(row)

    if category:
        cat_lower = category.lower().replace("_", " ")
        papers = [p for p in papers if cat_lower in p.get("research_category", p.get("category", "")).lower()]

    if search:
        s_lower = search.lower()
        papers = [
            p for p in papers
            if s_lower in p["title"].lower() or s_lower in p["authors"].lower() or s_lower in p["doi"].lower() or s_lower in p["paper_id"].lower()
        ]

    return {
        "total": len(papers),
        "papers": papers
    }


@router.get("/papers/{paper_id}")
def get_paper_detail(paper_id: str):
    """Returns detailed metadata and text chunks for a specific paper."""
    if not os.path.exists(PAPER_CATALOG_PATH):
        raise HTTPException(status_code=404, detail="Paper catalog not found.")

    target_paper = None
    with open(PAPER_CATALOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["paper_id"].upper() == paper_id.upper():
                target_paper = row
                break

    if not target_paper:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found.")

    # Retrieve all chunks belonging to this paper
    paper_chunks = []
    if os.path.exists(CHUNK_META_PATH):
        with open(CHUNK_META_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["paper_id"].upper() == paper_id.upper():
                    paper_chunks.append({
                        "chunk_id": row["chunk_id"],
                        "original_page": int(row["original_page"]),
                        "section_heading": row["section_heading"],
                        "char_count": int(row["char_count"]),
                        "word_count": int(row["word_count"]),
                        "text_snippet": row["text_content"][:240] + ("..." if len(row["text_content"]) > 240 else "")
                    })

    paper_chunks.sort(key=lambda x: x["original_page"])

    return {
        "paper": target_paper,
        "total_chunks": len(paper_chunks),
        "chunks": paper_chunks
    }


@router.get("/papers/{paper_id}/pdf")
def get_paper_pdf(paper_id: str):
    """Serves the original research PDF for viewing and page-level evidence verification."""
    if not os.path.exists(PAPER_CATALOG_PATH):
        raise HTTPException(status_code=404, detail="Paper catalog not found.")

    target_filename = None
    with open(PAPER_CATALOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["paper_id"].upper() == paper_id.upper():
                target_filename = row["pdf_filename"]
                break

    if not target_filename:
        raise HTTPException(status_code=404, detail=f"Paper '{paper_id}' not found.")

    papers_dir = os.path.join(DATA_DIR, "papers")
    for root, dirs, files in os.walk(papers_dir):
        if target_filename in files:
            pdf_path = os.path.join(root, target_filename)
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename={target_filename}"}
            )

    raise HTTPException(status_code=404, detail=f"PDF file '{target_filename}' not found on disk.")


@router.get("/chunks")
def list_chunks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    paper_id: Optional[str] = Query(None, description="Filter by paper_id"),
    search: Optional[str] = Query(None, description="Search text in chunk content")
):
    """Returns paginated chunk metadata with text excerpts."""
    if not os.path.exists(CHUNK_META_PATH):
        raise HTTPException(status_code=404, detail="Chunk metadata not found.")

    chunks = []
    with open(CHUNK_META_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunks.append(row)

    if paper_id:
        chunks = [c for c in chunks if c["paper_id"].upper() == paper_id.upper()]

    if search:
        s_lower = search.lower()
        chunks = [c for c in chunks if s_lower in c["text_content"].lower() or s_lower in c["section_heading"].lower()]

    total_items = len(chunks)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = chunks[start_idx:end_idx]

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": (total_items + page_size - 1) // page_size,
        "chunks": page_items
    }


@router.post("/query", response_model=QueryResponse)
def execute_query(req: QueryRequest):
    """
    Executes audited hybrid retrieval with exact quotation search,
    cross-encoder joint attention, 2-stage out-of-domain and evidence sufficiency guardrails,
    and grounded evidence synthesis.
    """
    rag = MediEvidenceRAG.get_instance()
    result = rag.hybrid_retrieve(
        query=req.query,
        top_k=req.top_k,
        similarity_threshold=req.similarity_threshold,
        use_reranking=req.use_reranking,
        category_filter=req.category_filter,
        paper_id_filter=req.paper_id
    )
    return result


@router.post("/search/exact")
def search_exact(req: ExactSearchRequest):
    """Phase 5: Exact Text and Quoted Passage Search across 30 research papers (POST)."""
    rag = MediEvidenceRAG.get_instance()
    match = rag.find_exact_passage(req.quote, paper_id_filter=req.paper_id)
    if match:
        pnum = match.get("original_page", 1)
        conf = match.get("match_confidence", match.get("rerank_score", 1.0))
        match["page_number"] = pnum
        match["match_confidence"] = conf
        return {
            "found": True,
            "paper_id": match["paper_id"],
            "page_number": pnum,
            "match_confidence": conf,
            "match": match
        }
    return {
        "found": False,
        "message": "Exact passage not found in the indexed text of the 30 papers."
    }

@router.get("/search/exact")
def search_exact_get(quote: str = Query(..., description="The exact passage or quote to search for"), paper_id: Optional[str] = Query(None, description="Optional paper_id")):
    """Phase 5: Exact Text and Quoted Passage Search across 30 research papers (GET)."""
    rag = MediEvidenceRAG.get_instance()
    match = rag.find_exact_passage(quote, paper_id_filter=paper_id)
    if match:
        pnum = match.get("original_page", 1)
        conf = match.get("match_confidence", match.get("rerank_score", 1.0))
        match["page_number"] = pnum
        match["match_confidence"] = conf
        return {
            "found": True,
            "paper_id": match["paper_id"],
            "page_number": pnum,
            "match_confidence": conf,
            "match": match
        }
    return {
        "found": False,
        "message": "Exact passage not found in the indexed text of the 30 papers."
    }


@router.get("/evaluate")
def get_evaluation():
    """Returns benchmark results, metrics (Recall@K, MRR, nDCG), and test question inventory."""
    summary = {}
    if os.path.exists(EVAL_SUMMARY_PATH):
        with open(EVAL_SUMMARY_PATH, "r", encoding="utf-8") as f:
            summary = json.load(f)

    questions = []
    if os.path.exists(EVAL_QUESTIONS_PATH):
        with open(EVAL_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            questions = json.load(f)

    return {
        "summary": summary,
        "total_questions": len(questions),
        "questions": questions
    }


@router.get("/evaluate/failures")
def get_evaluation_failures():
    """Phase 12: Returns detailed Failure Analysis dataset showing test cases, root causes, and fixes."""
    if os.path.exists(EVAL_FAILURES_PATH):
        with open(EVAL_FAILURES_PATH, "r", encoding="utf-8") as f:
            failures = json.load(f)
            return failures
    return {"total_failures": 0, "failures": []}
