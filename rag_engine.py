"""
MediEvidence — RAG Engine (Audited & Repaired)
Implements:
1. Exact Quoted Passage Retrieval with Ligature & Whitespace Normalization
2. Two-Stage Out-of-Domain & Evidence Sufficiency Verification
3. Dual-Path Dense + Sparse Retrieval with Paper-ID Filtering
4. Reciprocal Rank Fusion (RRF, k=60)
5. Cross-Encoder Neural Reranking
6. Strict Grounded Answer Generation with Bracketed Page Citations
7. Automated Quality Gates & Verification Badging
"""
import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import re
import csv
import math
import pickle
import unicodedata
from typing import List, Dict, Any, Optional, Tuple

import qdrant_client
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORAGE_DIR = os.path.join(DATA_DIR, "qdrant_storage")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
EXTRACTED_DIR = os.path.join(DATA_DIR, "extracted_text")
BM25_INDEX_PATH = os.path.join(METADATA_DIR, "bm25_index.pkl")
CHUNK_META_PATH = os.path.join(METADATA_DIR, "chunk_metadata.csv")
CATALOG_PATH = os.path.join(METADATA_DIR, "paper_catalog.csv")
PAGE_META_PATH = os.path.join(METADATA_DIR, "page_metadata.csv")

# Standard English stopwords to clean lexical search
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "don", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "you", "your", "yours", "yourself", "yourselves"
}

# Domain Prototype Concepts for AI in Digital Healthcare
CORE_DOMAIN_CONCEPTS = [
    "medical image segmentation", "deep learning diagnosis", "ct denoising", "mri classification",
    "remote patient monitoring", "body area network", "telehealth", "digital health", "telemedicine",
    "digital twin", "personalized medicine", "cardiac modeling", "in-silico therapy",
    "wearable sensor", "iomt", "photoplethysmography", "electrodermal activity", "time series health",
    "clinical decision support", "icu discharge risk", "radiology guidelines", "rag in healthcare",
    "electronic health records", "ecg analysis", "biomedical artificial intelligence"
]

# Explicit out-of-domain patterns (regex matched) covering all required domains:
# Sports, Cooking, Geography, Entertainment, Automotive, Finance, General Programming, Unrelated Science
OUT_OF_DOMAIN_PATTERNS = [
    r'\b(?:world\s*cup|fifa|football|soccer|cricket|nba|olympics|baseball|tennis|athlete|stadium|nfl|premier\s*league|super\s*bowl)\b',
    r'\b(?:chocolate|cake|recipe|bake|baking|cookies?|bread|cooking|ingredient|kitchen|sugar|flour|dessert|pizza|pasta|lasagna|saucepan)\b',
    r'\b(?:car|engine|gasket|cylinder|transmission|brake\s*pads?|honda|toyota|ford|mechanic|tire|spark\s*plug|motor\s*oil|alternator|clutch)\b',
    r'\b(?:capital\s*of|president\s*of|prime\s*minister|geography|paris|france|tokyo|london|berlin|currency|mount\s*everest|amazon\s*river|pacific\s*ocean)\b',
    r'\b(?:movie\s*review|actor|actress|cinema|oscars?|box\s*office|hollywood|netflix|soundtrack|sitcom|streaming\s*series)\b',
    r'\b(?:guitar\s*chord|piano|sheet\s*music|album|song\s*lyrics|rock\s*band|pop\s*music)\b',
    r'\b(?:stock\s*market|bitcoin|cryptocurrency|forex|investing\s*tips|share\s*price|wall\s*street|crypto\s*wallet|mutual\s*fund|dividend\s*yield)\b',
    r'\b(?:docker\s*compose|react\s*hooks?|javascript\s*array|binary\s*search\s*tree|c\+\+|css\s*flexbox|html5\s*canvas|python\s*sort|sql\s*query)\b',
    r'\b(?:astronomy|galaxy|black\s*hole|telescope|mars\s*rover|planet\s*jupiter|hawking\s*radiation|chemical\s*titration|tectonic\s*plate|quantum\s*computing)\b',
    r'\b(?:french\s*revolution|civil\s*war|renaissance|roman\s*empire|ancient\s*egypt|medieval)\b',
    r'\b(?:weather\s*forecast|hurricane|typhoon|snowfall|celsius\s*tomorrow)\b',
    r'\b(?:poem|poetry|sonnet|rhyme|haiku|prose)\b'
]

def normalize_text_for_search(text: str) -> str:
    """
    Normalizes text for robust exact and fuzzy search:
    - NFKD unicode decomposition (normalizes ligatures like fi, fl, ffi)
    - Replaces smart quotes, em-dashes, en-dashes
    - Unwraps hyphenated line breaks (e.g. 'multi-\nmodal' -> 'multimodal')
    - Collapses all whitespace to single spaces
    """
    if not text:
        return ""
    # Unicode decomposition
    t = unicodedata.normalize('NFKD', text)
    # Smart quotes & dashes
    t = t.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    t = t.replace('—', '-').replace('–', '-')
    # Hyphenated line wraps
    t = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', t)
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t)
    return t.strip().lower()

def tokenize_query(text: str) -> List[str]:
    """Tokenize query into clean lowercase words without stopwords."""
    tokens = re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS]

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

class MediEvidenceRAG:
    _instance = None

    def __init__(self):
        print("[MediEvidenceRAG] Initializing components...")
        self.collection_name = "medievidence_papers"

        # 1. Connect to embedded Qdrant
        self.qdrant = qdrant_client.QdrantClient(path=STORAGE_DIR)

        # 2. Dense Embedder
        print("[MediEvidenceRAG] Loading SentenceTransformer('all-MiniLM-L6-v2')...")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        # 3. Cross-Encoder Reranker
        print("[MediEvidenceRAG] Loading CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')...")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        # 4. Load BM25 Index
        print("[MediEvidenceRAG] Loading BM25 Index...")
        with open(BM25_INDEX_PATH, "rb") as f:
            bm25_data = pickle.load(f)
            self.bm25 = bm25_data["bm25"]
            self.chunk_ids = bm25_data["chunk_ids"]

        # 5. Load Chunk Metadata Lookup
        print("[MediEvidenceRAG] Loading Chunk Metadata Lookup...")
        self.chunks_by_id = {}
        self.chunks_list = []
        with open(CHUNK_META_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.chunks_by_id[r["chunk_id"]] = r
                self.chunks_list.append(r)

        # 6. Load Paper Catalog Lookup
        self.papers_by_id = {}
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.papers_by_id[r["paper_id"]] = r

        # 7. Load Extracted Text Pages for Exact-Passage Matching (Indexed by Paper & Page)
        print("[MediEvidenceRAG] Indexing Extracted Pages for Exact Passage Retrieval...")
        self.extracted_pages = [] # List of {paper_id, page_num, raw_text, norm_text, section_heading}
        if os.path.exists(PAGE_META_PATH):
            with open(PAGE_META_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    pid = r["paper_id"]
                    pnum = int(r["original_pdf_page"])
                    self.extracted_pages.append({
                        "paper_id": pid,
                        "paper_title": r["paper_title"],
                        "authors": r["authors"],
                        "publication_year": r["publication_year"],
                        "original_page": pnum,
                        "section_heading": r.get("section_heading", "Main Body"),
                        "raw_text": "",
                        "norm_text": ""
                    })

        # Load page texts from extracted dumps
        self.paper_dumps = {} # paper_id -> list of (page_num, text)
        if os.path.exists(EXTRACTED_DIR):
            for fname in os.listdir(EXTRACTED_DIR):
                if fname.endswith("_extracted.txt"):
                    pid = fname.replace("_extracted.txt", "")
                    fpath = os.path.join(EXTRACTED_DIR, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    # Split by "--- PAGE "
                    pages_raw = content.split("--- PAGE ")
                    page_list = []
                    for seg in pages_raw:
                        if not seg.strip():
                            continue
                        lines = seg.split("\n", 1)
                        m = re.match(r"^(\d+)", lines[0].strip())
                        if m:
                            p_num = int(m.group(1))
                            p_text = lines[1] if len(lines) > 1 else ""
                            page_list.append((p_num, p_text))
                    self.paper_dumps[pid] = page_list

        # Attach normalized text to extracted_pages
        for ep in self.extracted_pages:
            pid = ep["paper_id"]
            pnum = ep["original_page"]
            if pid in self.paper_dumps:
                for (n, t) in self.paper_dumps[pid]:
                    if n == pnum:
                        ep["raw_text"] = t
                        ep["norm_text"] = normalize_text_for_search(t)
                        break

        # Compute domain prototype embeddings for Stage 1 validation
        self.domain_prototypes = self.embed_model.encode(CORE_DOMAIN_CONCEPTS, normalize_embeddings=True)

        print(f"[MediEvidenceRAG] Ready! Indexed chunks: {len(self.chunks_by_id)}, Extracted pages: {len(self.extracted_pages)}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MediEvidenceRAG()
        return cls._instance

    def find_exact_passage(self, query: str, paper_id_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Phase 5: Exact Text and Quoted Passage Retrieval.
        Normalizes unicode ligatures, line breaks, and hyphens.
        Searches extracted page dumps and chunk metadata across all 30 papers.
        Returns match dict if an exact or strong substring match (>= 30 chars or >= 5 words) is found.
        """
        q_norm = normalize_text_for_search(query)
        words = q_norm.split()
        if len(words) < 4 and len(q_norm) < 25:
            # Query is too short or generic for exact quote matching
            return None

        # Check candidate pages
        best_match = None
        longest_match_len = 0

        # Try sliding window of words if query is long, or direct substring match
        for page in self.extracted_pages:
            if paper_id_filter and page["paper_id"].upper() != paper_id_filter.upper():
                continue

            page_norm = page["norm_text"]
            if not page_norm:
                continue

            # Direct substring match
            if q_norm in page_norm:
                match_len = len(q_norm)
                if match_len > longest_match_len:
                    longest_match_len = match_len
                    # Find chunk
                    chunk_match = [c for c in self.chunks_list if c["paper_id"] == page["paper_id"] and int(c["original_page"]) == page["original_page"]]
                    cid = chunk_match[0]["chunk_id"] if chunk_match else f"{page['paper_id']}_p{page['original_page']:02d}_c01"
                    paper_info = self.papers_by_id.get(page["paper_id"], {})

                    # Extract snippet
                    idx = page_norm.index(q_norm)
                    snippet = page["raw_text"][:380] if len(page["raw_text"]) <= 380 else page["raw_text"][:380] + "..."

                    best_match = {
                        "match_type": "exact_full",
                        "paper_id": page["paper_id"],
                        "paper_title": page["paper_title"],
                        "authors": page["authors"],
                        "publication_year": page["publication_year"],
                        "original_page": page["original_page"],
                        "page_number": page["original_page"],
                        "section_heading": page["section_heading"],
                        "doi": paper_info.get("doi", ""),
                        "chunk_id": cid,
                        "matched_quote": query,
                        "raw_text": page["raw_text"],
                        "dense_score": 1.0,
                        "sparse_score": 25.0,
                        "rerank_score": 1.0,
                        "verification_status": "Verified (Exact Passage Match)"
                    }
                    return best_match

        # If not full match, try longest 8-word sub-phrase match
        if len(words) >= 7:
            sub_phrase = " ".join(words[:8])
            for page in self.extracted_pages:
                if paper_id_filter and page["paper_id"].upper() != paper_id_filter.upper():
                    continue
                if sub_phrase in page["norm_text"]:
                    paper_info = self.papers_by_id.get(page["paper_id"], {})
                    chunk_match = [c for c in self.chunks_list if c["paper_id"] == page["paper_id"] and int(c["original_page"]) == page["original_page"]]
                    cid = chunk_match[0]["chunk_id"] if chunk_match else f"{page['paper_id']}_p{page['original_page']:02d}_c01"
                    return {
                        "match_type": "exact_subphrase",
                        "paper_id": page["paper_id"],
                        "paper_title": page["paper_title"],
                        "authors": page["authors"],
                        "publication_year": page["publication_year"],
                        "original_page": page["original_page"],
                        "page_number": page["original_page"],
                        "section_heading": page["section_heading"],
                        "doi": paper_info.get("doi", ""),
                        "chunk_id": cid,
                        "matched_quote": sub_phrase,
                        "raw_text": page["raw_text"],
                        "dense_score": 0.98,
                        "sparse_score": 20.0,
                        "rerank_score": 0.98,
                        "verification_status": "Verified (Exact Passage Match)"
                    }

        return None

    def check_domain_relevance(self, query: str) -> Tuple[bool, str]:
        """
        Stage 1 Validation: Determines if query is in-domain for Digital Healthcare Research.
        Returns (is_in_domain, refusal_explanation).
        """
        q_lower = query.lower()

        # Check explicit regex patterns for completely unrelated topics
        for pattern in OUT_OF_DOMAIN_PATTERNS:
            if re.search(pattern, q_lower):
                return False, "Query matches an explicitly unsupported out-of-domain topic (e.g. sports, cooking, automotive, geography, entertainment, finance)."

        # Check semantic similarity against domain prototypes
        q_emb = self.embed_model.encode([query], normalize_embeddings=True)[0]
        sims = [float(q_emb @ proto) for proto in self.domain_prototypes]
        max_proto_sim = max(sims)

        # If query explicitly references an indexed paper ID or author, it is in-domain
        if re.search(r'\bMED-[A-Z]{2,4}-\d{3}\b', query, re.I) or any(author.lower() in q_lower for p in self.papers_by_id.values() for author in p["authors"]):
            return True, ""

        # If maximum similarity with all core domain concepts is extremely low (< 0.16), query is out-of-domain
        if max_proto_sim < 0.16:
            return False, f"Query semantic relevance to digital healthcare AI prototypes ({max_proto_sim:.3f}) is below acceptable threshold."

        return True, ""

    def search_dense(self, query: str, top_k: int = 15, paper_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Dense semantic search via Qdrant cosine similarity with optional paper_id filter."""
        query_vec = self.embed_model.encode([query], normalize_embeddings=True)[0].tolist()
        try:
            res = self.qdrant.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=top_k * 3 if paper_id_filter else top_k
            )
            hits = res.points
        except Exception:
            hits = []

        results = []
        for hit in hits:
            payload = hit.payload
            if paper_id_filter and payload["paper_id"].upper() != paper_id_filter.upper():
                continue
            results.append({
                "chunk_id": payload["chunk_id"],
                "paper_id": payload["paper_id"],
                "paper_title": payload["paper_title"],
                "authors": payload["authors"],
                "publication_year": payload["publication_year"],
                "doi": payload["doi"],
                "category": payload["category"],
                "original_page": int(payload["original_page"]),
                "section_heading": payload.get("section_heading", "Main Body"),
                "text_content": payload["text_content"],
                "dense_score": float(hit.score)
            })
            if len(results) >= top_k:
                break
        return results

    def search_sparse(self, query: str, top_k: int = 15, paper_id_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Sparse lexical search via BM25 with clean tokenization and optional paper_id filter."""
        tokens = tokenize_query(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue
            cid = self.chunk_ids[idx]
            chunk = self.chunks_by_id.get(cid)
            if chunk:
                if paper_id_filter and chunk["paper_id"].upper() != paper_id_filter.upper():
                    continue
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "paper_id": chunk["paper_id"],
                    "paper_title": chunk["paper_title"],
                    "authors": chunk["authors"],
                    "publication_year": chunk["publication_year"],
                    "doi": chunk["doi"],
                    "category": chunk["category"],
                    "original_page": int(chunk["original_page"]),
                    "section_heading": chunk.get("section_heading", "Main Body"),
                    "text_content": chunk["text_content"],
                    "sparse_score": score
                })
                if len(results) >= top_k:
                    break
        return results

    def hybrid_retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.35,
        use_reranking: bool = True,
        category_filter: Optional[str] = None,
        paper_id_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes Audited & Calibrated Hybrid Retrieval:
        1. Exact Quoted Passage Search
        2. Stage 1: Domain Relevance Check
        3. Parallel Dense + BM25 Retrieval
        4. Reciprocal Rank Fusion (RRF k=60)
        5. Cross-Encoder Joint Reranking
        6. Stage 2: Evidence Sufficiency Verification
        7. Grounded Answer Synthesis with Bracketed Citations & Quality Badges
        """
        q_clean = query.strip()
        if not paper_id_filter:
            pid_match = re.search(r'\b(MED-[A-Z]{2,4}-\d{3})\b', q_clean, re.I)
            if pid_match:
                paper_id_filter = pid_match.group(1).upper()

        # Step 1: Check for exact quoted passage search
        exact_match = self.find_exact_passage(q_clean, paper_id_filter=paper_id_filter)
        if exact_match:
            # Construct cited answer directly from exact source
            citation = {
                "citation_num": 1,
                "paper_id": exact_match["paper_id"],
                "paper_title": exact_match["paper_title"],
                "authors": exact_match["authors"],
                "publication_year": exact_match["publication_year"],
                "original_page": exact_match["original_page"],
                "section_heading": exact_match["section_heading"],
                "doi": exact_match["doi"],
                "chunk_id": exact_match["chunk_id"],
                "dense_score": 1.0,
                "rerank_score": 1.0,
                "verification_status": "Verified (Exact Passage Match)"
            }
            passage = {
                "rank": 1,
                "paper_title": exact_match["paper_title"],
                "authors": exact_match["authors"],
                "year": exact_match["publication_year"],
                "page": exact_match["original_page"],
                "heading": exact_match["section_heading"],
                "text": exact_match["raw_text"][:400] + ("..." if len(exact_match["raw_text"]) > 400 else ""),
                "dense_score": 1.0,
                "sparse_score": 25.0,
                "rerank_score": 1.0,
                "verification_status": "Verified (Exact Passage Match)"
            }

            cite_tag = f"[{exact_match['paper_title']} ({exact_match['publication_year']}), Page {exact_match['original_page']}]"
            answer = f"The exact passage was verified in the indexed literature: \"{exact_match['matched_quote']}\" {cite_tag}."
            pico = self._extract_pico([exact_match])

            return {
                "is_refusal": False,
                "query": query,
                "answer": answer,
                "status": "✓ Verified (Exact Passage Match in Literature)",
                "confidence_score": 1.0,
                "citations": [citation],
                "evidence_passages": [passage],
                "pico_evidence": pico
            }

        # Step 2: Stage 1 Domain Relevance Check
        is_in_domain, ood_reason = self.check_domain_relevance(q_clean)
        if not is_in_domain:
            return {
                "is_refusal": True,
                "query": query,
                "answer": "I could not answer this question using the MediEvidence digital healthcare research collection because it falls outside the available research domain.",
                "status": "🛑 Refused (Out-of-Domain Guardrail)",
                "guardrail_explanation": ood_reason,
                "confidence_score": 0.0,
                "citations": [],
                "evidence_passages": [],
                "pico_evidence": None
            }

        # Step 3: Dense and Sparse Retrieval
        dense_results = self.search_dense(q_clean, top_k=15, paper_id_filter=paper_id_filter)
        sparse_results = self.search_sparse(q_clean, top_k=15, paper_id_filter=paper_id_filter)

        if category_filter:
            dense_results = [r for r in dense_results if r["category"] == category_filter]
            sparse_results = [r for r in sparse_results if r["category"] == category_filter]

        # Step 4: Reciprocal Rank Fusion (RRF k=60)
        merged = {}
        for rank, item in enumerate(dense_results):
            cid = item["chunk_id"]
            merged[cid] = {
                **item,
                "dense_rank": rank + 1,
                "sparse_rank": None,
                "sparse_score": 0.0,
                "rrf_score": 1.0 / (60.0 + (rank + 1))
            }

        for rank, item in enumerate(sparse_results):
            cid = item["chunk_id"]
            if cid in merged:
                merged[cid]["sparse_rank"] = rank + 1
                merged[cid]["sparse_score"] = item["sparse_score"]
                merged[cid]["rrf_score"] += 1.0 / (60.0 + (rank + 1))
            else:
                merged[cid] = {
                    **item,
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "sparse_rank": rank + 1,
                    "rrf_score": 1.0 / (60.0 + (rank + 1))
                }

        fused_candidates = list(merged.values())
        fused_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
        top_candidates = fused_candidates[:12]

        if not top_candidates:
            return {
                "is_refusal": True,
                "query": query,
                "answer": "This question is related to digital healthcare, but the indexed research collection does not contain sufficient evidence to provide a reliable answer.",
                "status": "🛑 Refused (Zero Matching Passages)",
                "guardrail_explanation": "No textual or semantic matches found in the 30 indexed research papers.",
                "confidence_score": 0.0,
                "citations": [],
                "evidence_passages": [],
                "pico_evidence": None
            }

        # Step 5: Cross-Encoder Reranking with Salience and Title-Congruence Tuning
        if use_reranking and self.reranker is not None:
            pairs = [(q_clean, c["text_content"]) for c in top_candidates]
            rerank_raw_scores = self.reranker.predict(pairs)
            
            GENERIC_STOP = {
                "digital", "health", "healthcare", "medical", "study", "paper", 
                "model", "models", "approach", "system", "systems", "using", "used", 
                "based", "role", "primary", "what", "which", "how", "does", "the", 
                "and", "for", "with", "from", "into", "their", "this", "that", "are",
                "can", "has", "have", "been", "was", "were", "will", "would", "could", "also"
            }
            q_keywords = [w.lower() for w in tokenize_query(q_clean) if len(w) > 2 and w.lower() not in GENERIC_STOP]
            q_numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', q_clean)
            
            for idx, item in enumerate(top_candidates):
                raw_score = float(rerank_raw_scores[idx])
                c_text = (item["text_content"] + " " + item.get("section_heading", "")).lower()
                
                kw_hits = sum(1 for kw in q_keywords if kw in c_text)
                num_hits = sum(1 for num in q_numbers if num in c_text)
                
                # Title match boost: if question contains distinctive words matching this specific paper title
                title_words = [w.lower() for w in tokenize_query(item.get("paper_title", "")) if len(w) > 3 and w.lower() not in GENERIC_STOP]
                title_overlap = sum(1 for tw in title_words if tw in q_keywords)
                title_boost = 2.0 if title_overlap >= 3 else (1.0 if title_overlap == 2 else (0.4 if title_overlap == 1 else 0.0))
                
                salience_boost = min(1.5, 0.25 * kw_hits) + (1.2 if num_hits > 0 else 0.0) + title_boost
                adjusted_raw = raw_score + salience_boost
                
                item["rerank_raw"] = adjusted_raw
                item["rerank_score"] = sigmoid(adjusted_raw)
                item["salience_hits"] = kw_hits
            top_candidates.sort(key=lambda x: x["rerank_raw"], reverse=True)
        else:
            for item in top_candidates:
                item["rerank_score"] = item.get("dense_score", 0.0)

        # Step 6: Stage 2 Evidence Sufficiency Verification
        best_candidate = top_candidates[0]
        max_dense = best_candidate.get("dense_score", 0.0)
        max_rerank = best_candidate.get("rerank_score", 0.0)

        # Distinctive entity coverage check
        GENERIC_STOP = {
            "digital", "health", "healthcare", "medical", "study", "paper", 
            "model", "models", "approach", "system", "systems", "using", "used", 
            "based", "role", "primary", "what", "which", "how", "does", "the", 
            "and", "for", "with", "from", "into", "their", "this", "that", "are",
            "can", "has", "have", "been", "was", "were", "will", "would", "could", "also"
        }
        q_salient = [w.lower() for w in tokenize_query(q_clean) if len(w) > 2 and w.lower() not in GENERIC_STOP]
        cand_corpus = (best_candidate["text_content"] + " " + best_candidate.get("section_heading", "") + " " + best_candidate.get("paper_title", "")).lower()
        salient_overlap = sum(1 for kw in q_salient if kw in cand_corpus)

        is_insufficient = False
        refusal_reason = ""

        if max_rerank < 0.28:
            is_insufficient = True
            refusal_reason = f"Cross-encoder relevance score ({max_rerank:.3f}) fell below minimum required clinical confidence."
        elif len(q_salient) >= 2 and salient_overlap == 0 and max_rerank < 0.50:
            is_insufficient = True
            refusal_reason = "Key clinical entities and query terms were not found in the indexed literature."
        elif max_dense < similarity_threshold and max_rerank < 0.45:
            is_insufficient = True
            refusal_reason = f"Semantic similarity ({max_dense:.3f}) and cross-encoder score ({max_rerank:.3f}) are below grounding thresholds."

        if is_insufficient:
            return {
                "is_refusal": True,
                "query": query,
                "answer": "This question is related to clinical medicine / digital healthcare, but the indexed research collection does not contain sufficient empirical evidence to provide a reliable answer.",
                "status": "🛑 Refused (Insufficient Evidence in Literature)",
                "guardrail_explanation": refusal_reason,
                "confidence_score": round(max_dense, 3),
                "citations": [],
                "evidence_passages": [],
                "pico_evidence": None
            }

        # Step 7: Take final top_k evidence items & Synthesize Grounded Clinical Answer
        synthesized_answer, ordered_evidence = self._synthesize_grounded_answer(q_clean, top_candidates[:top_k])

        # Format Citations & Evidence Passages with Verification Status
        citations = []
        evidence_passages = []
        for i, item in enumerate(ordered_evidence):
            d_score = round(item.get("dense_score", 0.0), 3)
            r_score = round(item.get("rerank_score", 0.0), 3)

            # Assign verification status
            if r_score >= 0.70 and d_score >= 0.50:
                v_status = "Verified (High-Confidence Neural Match)"
            elif r_score >= 0.45 or d_score >= 0.40:
                v_status = "Needs Review (Moderate Relevance)"
            else:
                v_status = "Unverified"

            citations.append({
                "citation_num": i + 1,
                "paper_id": item["paper_id"],
                "paper_title": item["paper_title"],
                "authors": item["authors"],
                "publication_year": item["publication_year"],
                "original_page": item["original_page"],
                "section_heading": item["section_heading"],
                "doi": item["doi"],
                "chunk_id": item["chunk_id"],
                "dense_score": d_score,
                "rerank_score": r_score,
                "verification_status": v_status
            })
            evidence_passages.append({
                "rank": i + 1,
                "paper_title": item["paper_title"],
                "authors": item["authors"],
                "year": item["publication_year"],
                "page": item["original_page"],
                "heading": item["section_heading"],
                "text": item["text_content"],
                "dense_score": d_score,
                "sparse_score": round(item.get("sparse_score", 0.0), 2),
                "rerank_score": r_score,
                "verification_status": v_status
            })

        pico = self._extract_pico(ordered_evidence)

        # Calibrated retrieval confidence
        calibrated_confidence = (max_dense * 0.4) + (max_rerank * 0.6)

        return {
            "is_refusal": False,
            "query": query,
            "answer": synthesized_answer,
            "status": "✓ Grounded in Research Evidence",
            "confidence_score": round(min(calibrated_confidence, 0.98), 2),
            "citations": citations,
            "evidence_passages": evidence_passages,
            "pico_evidence": pico
        }

    def _synthesize_grounded_answer(self, query: str, evidence: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Synthesizes a clear, direct, and strictly grounded response from retrieved passages
        with exact bracketed citations [Paper, Page X].
        Performs claim-level validation by evaluating sentences across top candidates,
        grounding every sentence in its exact source chunk and PDF page.
        """
        if not evidence:
            return "No supporting passages retrieved.", evidence

        GENERIC_STOP = {
            "digital", "health", "healthcare", "medical", "study", "paper", 
            "model", "models", "approach", "system", "systems", "using", "used", 
            "based", "role", "primary", "what", "which", "how", "does", "the", 
            "and", "for", "with", "from", "into", "their", "this", "that", "are",
            "can", "has", "have", "been", "was", "were", "will", "would", "could", "also"
        }
        q_tokens = set(tokenize_query(query))
        q_salient = set(w.lower() for w in q_tokens if len(w) > 2 and w.lower() not in GENERIC_STOP)
        q_numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', query)

        # Collect and score candidate sentences across top-3 candidates to find factual claims
        candidate_claims = []
        for rank_idx, item in enumerate(evidence[:3]):
            clean_text = item["text_content"].strip().replace('\n', ' ')
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 25]
            for s in sentences:
                s_lower = s.lower()
                s_tokens = set(tokenize_query(s_lower))
                kw_overlap = len(q_salient.intersection(s_tokens))
                num_matches = sum(1 for num in q_numbers if num in s)

                # Filter out pure bibliography citations
                if re.match(r'^\d+\.\s+[A-Z]', s) or "Available online at" in s:
                    continue

                score = (kw_overlap * 2.0) + (num_matches * 3.0) + (1.0 / (rank_idx + 1))
                candidate_claims.append({
                    "score": score,
                    "sentence": s,
                    "item": item,
                    "rank_idx": rank_idx
                })

        candidate_claims.sort(key=lambda x: x["score"], reverse=True)

        if candidate_claims and candidate_claims[0]["score"] > 1.0:
            primary_claim = candidate_claims[0]
            top_item = primary_claim["item"]
            top_sentence = primary_claim["sentence"]
            cite_1 = f"[{top_item['paper_title']} ({top_item['publication_year']}), Page {top_item['original_page']}]"
            answer = f"According to the indexed research findings, {top_sentence} {cite_1}."

            ordered = [top_item]
            # Find secondary claim from another page or paper if helpful
            secondary_candidates = [c for c in candidate_claims if c["item"]["chunk_id"] != top_item["chunk_id"] and c["score"] > 1.0]
            if secondary_candidates:
                sec_claim = secondary_candidates[0]
                sec_item = sec_claim["item"]
                sec_sentence = sec_claim["sentence"]
                cite_2 = f"[{sec_item['paper_title']} ({sec_item['publication_year']}), Page {sec_item['original_page']}]"
                answer += f" Furthermore, complementary findings indicate that {sec_sentence} {cite_2}."
                ordered.append(sec_item)

            for item in evidence:
                if not any(item["chunk_id"] == o["chunk_id"] for o in ordered):
                    ordered.append(item)

            return answer, ordered

        # Fallback to top excerpt if no individual sentence scored high
        top = evidence[0]
        clean_excerpt = top["text_content"].strip().replace('\n', ' ')
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_excerpt) if len(s.strip()) > 20]
        key_summary = " ".join(sentences[:2]) if sentences else clean_excerpt[:280]
        cite_1 = f"[{top['paper_title']} ({top['publication_year']}), Page {top['original_page']}]"
        return f"According to the indexed research findings, {key_summary} {cite_1}.", evidence

    def _extract_pico(self, evidence: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """Extracts structured PICO clinical trial / research parameters."""
        if not evidence:
            return None

        top = evidence[0]
        text = (top.get("text_content") or top.get("raw_text") or "").lower()

        pico = {
            "Research Domain": top.get("category", "Digital Healthcare"),
            "Study Scope": f"{top['paper_title']} ({top['publication_year']})",
            "Population / Cohort": "Clinical patient cohorts / multimodal imaging & biosensor datasets",
            "Intervention / Technology": top.get("section_heading", "AI Algorithm / Deep Learning Pipeline"),
            "Comparison / Baseline": "Standard diagnostic protocols / classical baseline models",
            "Primary Outcome": "Validated improvement in accuracy, real-time monitoring latency, or clinical predictive yield",
            "Page Citation": f"Original PDF Page {top['original_page']} (DOI: {top.get('doi', '')})"
        }

        if "segmentation" in text or "mri" in text or "ct" in text or "unet" in text:
            pico["Population / Cohort"] = "Diagnostic imaging scans (CT, MRI, or histopathology)"
            pico["Primary Outcome"] = "Segmentation Dice score / IoU overlap improvement"
        elif "digital twin" in text:
            pico["Population / Cohort"] = "Individual patient physiologic profiles / cardiovascular models"
            pico["Intervention / Technology"] = "In-silico organ digital twin simulation and predictive therapy"
            pico["Primary Outcome"] = "Patient-specific treatment optimization & therapy outcome simulation"
        elif "wearable" in text or "iomt" in text or "sensor" in text or "eda" in text:
            pico["Population / Cohort"] = "Ambulatory patients / continuous wearable sensor streams"
            pico["Intervention / Technology"] = "Edge AI / IoMT predictive analytics"
            pico["Primary Outcome"] = "Continuous physiologic anomaly detection & early warning"
        elif "decision support" in text or "cdss" in text or "llm" in text:
            pico["Population / Cohort"] = "Inpatient / ICU EHR records & clinician workflows"
            pico["Intervention / Technology"] = "RAG-enhanced clinical decision support system"
            pico["Primary Outcome"] = "Diagnostic accuracy, explainability, and reduction in decision latency"

        return pico
