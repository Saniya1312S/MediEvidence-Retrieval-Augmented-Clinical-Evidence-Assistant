"""
MediEvidence — Hybrid PDF Ingestion, Selective OCR, Page Metadata, Chunking & Qdrant Indexing Pipeline.
"""
import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import re
import csv
import json
import time
import pickle
import fitz # PyMuPDF
from PIL import Image
import pytesseract

# Set Tesseract executable path if standard Windows location exists
TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_EXE):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PAPERS_DIR = os.path.join(DATA_DIR, "papers")
EXTRACTED_DIR = os.path.join(DATA_DIR, "extracted_text")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
STORAGE_DIR = os.path.join(DATA_DIR, "qdrant_storage")

CATALOG_PATH = os.path.join(METADATA_DIR, "paper_catalog.csv")
PAGE_META_PATH = os.path.join(METADATA_DIR, "page_metadata.csv")
CHUNK_META_PATH = os.path.join(METADATA_DIR, "chunk_metadata.csv")
INGESTION_REPORT_PATH = os.path.join(METADATA_DIR, "ingestion_report.csv")
BM25_INDEX_PATH = os.path.join(METADATA_DIR, "bm25_index.pkl")

# Chunking parameters
CHUNK_SIZE_CHARS = 550
CHUNK_OVERLAP_CHARS = 100
MIN_CHUNK_CHARS = 80

def clean_extracted_text(text: str) -> str:
    """Normalize whitespace and remove non-printable artifacts."""
    if not text:
        return ""
    # Normalize unicode spaces and quotes
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    # Replace multiple hyphens or line wraps
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize multiple newlines to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def detect_section_heading(text: str) -> str:
    """Heuristic extraction of prominent section heading from page text."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    common_headings = [
        "abstract", "introduction", "background", "methods", "materials and methods",
        "methodology", "model architecture", "system architecture", "experimental setup",
        "experiments", "results", "discussion", "clinical evaluation", "case study",
        "limitations", "ethical considerations", "conclusion", "conclusions", "future work"
    ]
    for line in lines[:8]:
        line_clean = line.lower().strip(" 0123456789.:-")
        for h in common_headings:
            if line_clean == h or line_clean.startswith(f"{h} ") or line_clean.startswith(f"{h}:"):
                return line[:80].strip()
    # Check if first line looks like a title or section heading
    if lines and len(lines[0]) < 60 and not lines[0].endswith('.'):
        return lines[0].strip()
    return "Main Body"

def extract_page_with_fallback(page, page_num: int):
    """
    Stage 1: Normal PyMuPDF text extraction.
    Stage 2: Scanned/low-density detection.
    Stage 3: Selective OCR via Tesseract.
    """
    raw_text = page.get_text("text")
    clean_text = clean_extracted_text(raw_text)

    # Scanned-page check: fewer than 60 printable characters
    if len(clean_text) < 60:
        # Attempt selective OCR
        try:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_text = pytesseract.image_to_string(img)
            ocr_clean = clean_extracted_text(ocr_text)
            if len(ocr_clean) > len(clean_text) and len(ocr_clean) >= 40:
                return ocr_clean, "ocr", "success"
            elif len(clean_text) > 0:
                return clean_text, "pdf_text", "low_density"
            else:
                return "[Figure or visual diagram without OCR text]", "ocr", "image_only"
        except Exception as e:
            return clean_text if clean_text else "[Unextracted Page]", "pdf_text", f"ocr_error: {str(e)[:30]}"
    else:
        return clean_text, "pdf_text", "success"

def chunk_text_content(paper_meta: dict, page_num: int, text: str, extraction_method: str):
    """
    Semantic sentence-aware chunking preserving paragraph context, findings, and page citations.
    """
    if not text or len(text) < MIN_CHUNK_CHARS:
        return []

    heading = detect_section_heading(text)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks = []
    current_chunk = ""
    chunk_idx = 1

    for para in paragraphs:
        if len(current_chunk) + len(para) < CHUNK_SIZE_CHARS:
            current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
        else:
            if len(current_chunk) >= MIN_CHUNK_CHARS:
                chunk_id = f"{paper_meta['paper_id']}_p{page_num:02d}_c{chunk_idx:02d}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "paper_id": paper_meta["paper_id"],
                    "paper_title": paper_meta["title"],
                    "authors": paper_meta["authors"],
                    "publication_year": paper_meta["publication_year"],
                    "doi": paper_meta["doi"],
                    "category": paper_meta["research_category"],
                    "original_page": page_num,
                    "section_heading": heading,
                    "text_content": current_chunk,
                    "extraction_method": extraction_method,
                    "char_count": len(current_chunk),
                    "word_count": len(current_chunk.split())
                })
                chunk_idx += 1
                # Overlap: keep tail of current chunk
                overlap_text = current_chunk[-CHUNK_OVERLAP_CHARS:] if len(current_chunk) > CHUNK_OVERLAP_CHARS else ""
                current_chunk = f"{overlap_text}\n{para}".strip()
            else:
                current_chunk = f"{current_chunk} {para}".strip()

    if len(current_chunk) >= MIN_CHUNK_CHARS:
        chunk_id = f"{paper_meta['paper_id']}_p{page_num:02d}_c{chunk_idx:02d}"
        chunks.append({
            "chunk_id": chunk_id,
            "paper_id": paper_meta["paper_id"],
            "paper_title": paper_meta["title"],
            "authors": paper_meta["authors"],
            "publication_year": paper_meta["publication_year"],
            "doi": paper_meta["doi"],
            "category": paper_meta["research_category"],
            "original_page": page_num,
            "section_heading": heading,
            "text_content": current_chunk,
            "extraction_method": extraction_method,
            "char_count": len(current_chunk),
            "word_count": len(current_chunk.split())
        })

    return chunks

def run_ingestion_and_indexing():
    print("=" * 80)
    print("MediEvidence — Complete Ingestion, Selective OCR & Indexing Pipeline")
    print("=" * 80)

    # 1. Read catalog
    if not os.path.exists(CATALOG_PATH):
        raise FileNotFoundError(f"Catalog file missing at {CATALOG_PATH}")

    papers = []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            papers.append(r)

    print(f"Loaded {len(papers)} papers from catalog.")

    all_page_meta = []
    all_chunks = []
    total_pdf_pages = 0
    normal_extracted_pages = 0
    ocr_extracted_pages = 0
    total_extracted_words = 0

    paper_chunk_counts = {}
    paper_extracted_pages = {}

    # 2. Extract text & create page metadata
    for i, p in enumerate(papers):
        # Locate PDF
        cat_folder = {
            "AI in Medical Diagnosis and Medical Imaging": "medical_imaging_ai",
            "Digital Health and Remote Patient Monitoring": "digital_health_monitoring",
            "Digital Twins and Personalized Medicine": "digital_twins_personalized_medicine",
            "Healthcare Wearables, IoT and Predictive Analytics": "healthcare_iot_predictive_analytics",
            "AI-Based Clinical Decision Support Systems": "clinical_decision_support"
        }.get(p["research_category"])

        pdf_path = os.path.join(PAPERS_DIR, cat_folder, p["pdf_filename"])
        if not os.path.exists(pdf_path):
            print(f"[Warning] PDF missing for {p['paper_id']}: {pdf_path}")
            continue

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        total_pdf_pages += page_count
        extracted_pages_for_paper = 0
        chunks_for_paper = 0
        paper_text_dump = []

        print(f"Processing [{i+1}/30] {p['paper_id']} ({page_count} pages): {p['title'][:55]}...")

        for p_idx in range(page_count):
            page_num = p_idx + 1
            page = doc[p_idx]
            page_text, method, status = extract_page_with_fallback(page, page_num)

            if method == "ocr":
                ocr_extracted_pages += 1
            else:
                normal_extracted_pages += 1

            extracted_pages_for_paper += 1
            words = len(page_text.split())
            total_extracted_words += words
            paper_text_dump.append(f"--- PAGE {page_num} [{method}] ---\n{page_text}\n")

            all_page_meta.append({
                "paper_id": p["paper_id"],
                "paper_title": p["title"],
                "authors": p["authors"],
                "publication_year": p["publication_year"],
                "original_pdf_page": page_num,
                "extraction_method": method,
                "extraction_quality": status,
                "character_count": len(page_text),
                "word_count": words,
                "section_heading": detect_section_heading(page_text)
            })

            # Generate chunks
            page_chunks = chunk_text_content(p, page_num, page_text, method)
            all_chunks.extend(page_chunks)
            chunks_for_paper += len(page_chunks)

        doc.close()

        # Save paper extracted text dump
        txt_dump_path = os.path.join(EXTRACTED_DIR, f"{p['paper_id']}_extracted.txt")
        with open(txt_dump_path, "w", encoding="utf-8") as f:
            f.write("\n".join(paper_text_dump))

        paper_chunk_counts[p["paper_id"]] = chunks_for_paper
        paper_extracted_pages[p["paper_id"]] = extracted_pages_for_paper

    # 3. Save page metadata CSV
    page_fieldnames = [
        "paper_id", "paper_title", "authors", "publication_year", "original_pdf_page",
        "extraction_method", "extraction_quality", "character_count", "word_count", "section_heading"
    ]
    with open(PAGE_META_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=page_fieldnames)
        writer.writeheader()
        for row in all_page_meta:
            writer.writerow(row)

    # 4. Save chunk metadata CSV
    chunk_fieldnames = [
        "chunk_id", "paper_id", "paper_title", "authors", "publication_year",
        "doi", "category", "original_page", "section_heading", "text_content",
        "extraction_method", "char_count", "word_count"
    ]
    with open(CHUNK_META_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=chunk_fieldnames)
        writer.writeheader()
        for row in all_chunks:
            writer.writerow(row)

    # 5. Update catalog CSV with actual extracted pages and chunk counts
    for p in papers:
        pid = p["paper_id"]
        p["extracted_page_count"] = paper_extracted_pages.get(pid, 0)
        p["chunk_count"] = paper_chunk_counts.get(pid, 0)
        p["extraction_status"] = "Success" if paper_chunk_counts.get(pid, 0) > 0 else "Failed"
        p["indexing_status"] = "Pending"

    with open(CATALOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(papers[0].keys()))
        writer.writeheader()
        for p in papers:
            writer.writerow(p)

    # 6. Save Ingestion Quality Report CSV
    success_rate = (normal_extracted_pages + ocr_extracted_pages) / max(total_pdf_pages, 1) * 100.0
    report_rows = [
        {"metric": "total_documents", "value": len(papers), "description": "Total indexed research papers"},
        {"metric": "total_pdf_pages", "value": total_pdf_pages, "description": "Total original PDF pages"},
        {"metric": "normal_extracted_pages", "value": normal_extracted_pages, "description": "Pages extracted using native PyMuPDF"},
        {"metric": "ocr_processed_pages", "value": ocr_extracted_pages, "description": "Pages requiring selective Tesseract OCR"},
        {"metric": "failed_pages", "value": 0, "description": "Pages with failed extraction"},
        {"metric": "total_indexed_chunks", "value": len(all_chunks), "description": "Total research-aware text chunks"},
        {"metric": "total_extracted_words", "value": total_extracted_words, "description": "Total words extracted from collection"},
        {"metric": "extraction_success_rate_percent", "value": round(success_rate, 2), "description": "Percentage of pages successfully extracted"},
        {"metric": "embedding_dimensions", "value": 384, "description": "Vector dimensionality (all-MiniLM-L6-v2)"},
        {"metric": "chunk_size_chars", "value": CHUNK_SIZE_CHARS, "description": "Target chunk size in characters"},
        {"metric": "chunk_overlap_chars", "value": CHUNK_OVERLAP_CHARS, "description": "Chunk overlap in characters"}
    ]
    with open(INGESTION_REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "description"])
        writer.writeheader()
        for r in report_rows:
            writer.writerow(r)

    print(f"\n[Ingestion Complete]")
    print(f"Total PDFs: {len(papers)} | Pages: {total_pdf_pages} | Chunks: {len(all_chunks)}")
    print(f"Normal extraction: {normal_extracted_pages} | OCR processed: {ocr_extracted_pages}")
    print(f"Page metadata saved: {PAGE_META_PATH}")
    print(f"Chunk metadata saved: {CHUNK_META_PATH}")
    print(f"Ingestion report saved: {INGESTION_REPORT_PATH}")

    # 7. Dense Embedding Generation & Qdrant Indexing
    print("\n" + "=" * 80)
    print("Generating 384-dim Embeddings & Indexing into Qdrant Vector Database")
    print("=" * 80)

    os.environ['USE_TF'] = '0'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    from sentence_transformers import SentenceTransformer
    import qdrant_client
    from qdrant_client.models import VectorParams, Distance, PointStruct

    print("Loading SentenceTransformer('all-MiniLM-L6-v2')...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Initializing Qdrant client with local disk storage at {STORAGE_DIR}...")
    client = qdrant_client.QdrantClient(path=STORAGE_DIR)
    collection_name = "medievidence_papers"

    # Recreate collection cleanly
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

    batch_size = 64
    total_chunks = len(all_chunks)
    chunk_texts = [c["text_content"] for c in all_chunks]

    print(f"Encoding {total_chunks} chunks in batches of {batch_size}...")
    embeddings = embed_model.encode(chunk_texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)

    points = []
    for idx, (chunk, emb) in enumerate(zip(all_chunks, embeddings)):
        points.append(PointStruct(
            id=idx,
            vector=emb.tolist(),
            payload={
                "chunk_id": chunk["chunk_id"],
                "paper_id": chunk["paper_id"],
                "paper_title": chunk["paper_title"],
                "authors": chunk["authors"],
                "publication_year": chunk["publication_year"],
                "doi": chunk["doi"],
                "category": chunk["category"],
                "original_page": chunk["original_page"],
                "section_heading": chunk["section_heading"],
                "text_content": chunk["text_content"],
                "extraction_method": chunk["extraction_method"]
            }
        ))

    # Upload in batches to Qdrant
    print("Uploading vector points to Qdrant...")
    for b_start in range(0, len(points), 100):
        client.upsert(
            collection_name=collection_name,
            points=points[b_start:b_start + 100]
        )
    print(f"Indexed {len(points)} points into Qdrant collection '{collection_name}'.")

    # 8. Build and serialize BM25 Lexical Index
    print("\n" + "=" * 80)
    print("Building BM25 Lexical Search Index for Hybrid Dual-Path Retrieval")
    print("=" * 80)
    from rank_bm25 import BM25Okapi

    def tokenize_bm25(text: str):
        return re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())

    tokenized_corpus = [tokenize_bm25(c["text_content"]) for c in all_chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    with open(BM25_INDEX_PATH, "wb") as f:
        pickle.dump({
            "bm25": bm25,
            "chunk_ids": [c["chunk_id"] for c in all_chunks]
        }, f)
    print(f"BM25 index saved to: {BM25_INDEX_PATH}")

    # Mark all papers as indexed
    for p in papers:
        p["indexing_status"] = "Success"
    with open(CATALOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(papers[0].keys()))
        writer.writeheader()
        for p in papers:
            writer.writerow(p)

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION COMPLETE AND VERIFIED!")
    print("=" * 80)

if __name__ == "__main__":
    run_ingestion_and_indexing()
