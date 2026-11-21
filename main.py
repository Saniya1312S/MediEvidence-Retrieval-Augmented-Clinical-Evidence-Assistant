"""
MediEvidence – Retrieval-Augmented Clinical Evidence Assistant
Main FastAPI Application Entrypoint.
"""
import os
os.environ['USE_TF'] = '0'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, Response

from api.routes import router

app = FastAPI(
    title="MediEvidence – Retrieval-Augmented Clinical Evidence Assistant",
    description="Domain-specific AI assistant to query medical research papers & generate cited answers using an end-to-end RAG pipeline with Qdrant vector search, BM25 sparse search, cross-encoder reranking, and grounded evidence extraction.",
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static asset directories
if os.path.exists(os.path.join(BASE_DIR, "data")):
    app.mount("/data", StaticFiles(directory=os.path.join(BASE_DIR, "data")), name="data")

@app.get("/", response_class=HTMLResponse)
def root():
    """Serves the interactive MediEvidence Clinical Assistant Web Dashboard."""
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>MediEvidence – Retrieval-Augmented Clinical Evidence Assistant</h1><p><a href='/docs'>API Docs</a> | <a href='/api/health'>API Health</a></p>")

@app.get("/style.css")
def get_style():
    style_path = os.path.join(BASE_DIR, "style.css")
    if os.path.exists(style_path):
        return FileResponse(style_path, media_type="text/css")
    alt_style = os.path.join(BASE_DIR, "frontend", "style.css")
    if os.path.exists(alt_style):
        return FileResponse(alt_style, media_type="text/css")
    return Response(content="", media_type="text/css")

@app.get("/script.js")
def get_script():
    script_path = os.path.join(BASE_DIR, "script.js")
    if os.path.exists(script_path):
        return FileResponse(script_path, media_type="application/javascript")
    alt_script = os.path.join(BASE_DIR, "frontend", "script.js")
    if os.path.exists(alt_script):
        return FileResponse(alt_script, media_type="application/javascript")
    return Response(content="", media_type="application/javascript")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
