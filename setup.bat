@echo off
REM ═══════════════════════════════════════════════════════════
REM  MediEvidence — Windows 1-Click Setup Script
REM ═══════════════════════════════════════════════════════════
echo.
echo ==========================================================
echo   MediEvidence Clinical Assistant — Automated Setup
echo ==========================================================
echo.

REM Step 1: Create directories
echo [1/5] Creating directories...
if not exist "data\qdrant_storage" mkdir data\qdrant_storage
if not exist "data\n8n_data" mkdir data\n8n_data
if not exist "uploads" mkdir uploads
echo       Done.

REM Step 2: Install dependencies
echo.
echo [2/5] Installing Python dependencies...
pip install -r requirements.txt
echo       Done.

REM Step 3: Copy environment config
echo.
echo [3/5] Setting up environment configuration...
if not exist ".env" copy .env.example .env
echo       Done.

REM Step 4: Check or pull Ollama models (if Ollama installed)
echo.
echo [4/5] Checking Ollama models...
where ollama >nul 2>nul
if %errorlevel% equ 0 (
    echo       Pulling nomic-embed-text...
    ollama pull nomic-embed-text
    echo       Pulling gemma3:4b...
    ollama pull gemma3:4b
) else (
    echo       Ollama not detected in PATH. Using local fallback embeddings.
)
echo       Done.

REM Step 5: Start server
echo.
echo [5/5] Launching MediEvidence FastAPI Server...
echo.
echo Access the Interactive Dashboard at: http://localhost:8000
echo Access Swagger API Documentation at:  http://localhost:8000/docs
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
