"""
NeuroDetect backend entrypoint.

Scope for this milestone: the Memory Recall game only. Other cognitive
games, PHQ-9/GAD-7, PROCESS-2 speech, and fusion/ML are intentionally not
wired in yet.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.assessments.router import router as assessments_router
from app.games.nback.router import router as nback_router
from app.games.mmse.router import router as mmse_router
from app.games.memory.router import router as memory_router

app = FastAPI(
    title="NeuroDetect API",
    description="Cognitive assessment backend. Prototype — not a diagnostic system.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessments_router)
app.include_router(memory_router)
app.include_router(mmse_router)
app.include_router(nback_router)


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}
