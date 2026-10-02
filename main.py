"""
MediEvidence – Retrieval-Augmented Clinical Evidence Assistant
Main FastAPI Application Entrypoint.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import router

app = FastAPI(
    title="MediEvidence – Retrieval-Augmented Clinical Evidence Assistant",
    description="Domain-specific AI assistant to query medical research papers & generate cited answers using an end-to-end RAG pipeline with LLMs, embeddings, Qdrant, and TF-IDF evidence extraction for contextual responses.",
    version="2026.1.0"
)

# Enable CORS for web UI and integration workflows
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(router)

# Mount frontend files
static_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Serves the interactive MediEvidence Clinical Assistant Web Dashboard."""
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "project": "MediEvidence – Retrieval-Augmented Clinical Evidence Assistant",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
