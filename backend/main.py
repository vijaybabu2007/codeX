import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.database import init_db

# Initialize database schema immediately on import
init_db()

from backend.api.routes_source import router as source_router
from backend.api.routes_contract import router as contract_router
from backend.api.routes_pack import router as pack_router
from backend.api.routes_decision import router as decision_router
from backend.api.routes_student import router as student_router
from backend.api.routes_presets import router as presets_router
from backend.api.routes_question import router as question_router
from backend.api.routes_auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LessonFoundry – Constraint-Aware Learning Asset Generation Studio (Milestone 0)",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(source_router, prefix=settings.API_V1_STR)
app.include_router(contract_router, prefix=settings.API_V1_STR)
app.include_router(pack_router, prefix=settings.API_V1_STR)
app.include_router(decision_router, prefix=settings.API_V1_STR)
app.include_router(student_router, prefix=settings.API_V1_STR)
app.include_router(presets_router, prefix=settings.API_V1_STR)
app.include_router(question_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)

from backend.config import get_effective_llm_provider, get_effective_groq_model, get_effective_gemini_model

@app.get("/health")
def healthcheck():
    active_provider = get_effective_llm_provider()
    active_model = get_effective_groq_model() if active_provider == "groq" else get_effective_gemini_model()
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "provider": active_provider,
        "model_configured": active_model,
        "sqlite_wal": True
    }

# Mount static frontend build if present
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
