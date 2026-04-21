"""
app.py — FastAPI entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .upload_audio import router as upload_router
from .routers import router as main_router

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FluentAI Backend",
    description="Audio fluency capture and analysis API",
    version="1.0.0"
)

# ── CORS — allow the React frontend ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(upload_router)
app.include_router(main_router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "message": "FluentAI Backend Running"}