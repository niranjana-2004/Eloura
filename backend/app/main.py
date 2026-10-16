
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import initialize_database
from app.api.v1.router import api_router

app = FastAPI(
    title="Eloura API",
    description="AI-powered visual memory and creative-expression platform",
    version="0.1.0",
)

initialize_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

storage_dir = Path(__file__).resolve().parents[2] / "storage" / "uploads"
storage_dir.mkdir(parents=True, exist_ok=True)

app.mount(
    "/media",
    StaticFiles(directory=str(storage_dir)),
    name="media",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to Eloura API",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "eloura-backend",
    }
