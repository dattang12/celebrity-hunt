"""
uvicorn main:app --reload --port 8000
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers.celebrity import router as celebrity_router
from routers.outreach import router as outreach_router

load_dotenv()

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Access Engine API",
    description="Network intelligence + leverage system for reaching high-profile individuals",
    version="1.0.0",
    docs_url="/docs",   # Swagger UI — show judges this!
    redoc_url="/redoc",
)

# CORS — allow React frontend
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← change this to "*"
    allow_credentials=False,  # ← change True to False
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────

app.include_router(celebrity_router)
app.include_router(outreach_router)


# ─────────────────────────────────────────────
# HEALTH + ROOT
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Access Engine API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "list_celebrities": "GET /celebrity/list",
            "search": "POST /celebrity/search",
            "graph": "GET /celebrity/{id}/graph",
            "score": "GET /celebrity/{id}/score",
            "nodes": "GET /celebrity/{id}/nodes",
            "generate_outreach": "POST /outreach/generate",
            "outreach_stats": "GET /outreach/stats",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    checks = {}

    # Check Supabase
    try:
        from database.supabase import get_client
        db = get_client()
        db.table("celebrities").select("id").limit(1).execute()
        checks["supabase"] = "✅ connected"
    except Exception as e:
        checks["supabase"] = f"❌ {str(e)[:50]}"

    # Check Anthropic
    checks["anthropic_key"] = "✅ set" if os.getenv("ANTHROPIC_API_KEY") else "❌ missing"
    checks["news_api_key"] = "✅ set" if os.getenv("NEWS_API_KEY") else "⚠️ missing (optional)"
    checks["serp_api_key"] = "✅ set" if os.getenv("SERP_API_KEY") else "⚠️ missing (optional)"

    all_ok = all("✅" in v for v in [checks["supabase"], checks["anthropic_key"]])

    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks,
    }


# ─────────────────────────────────────────────
# SEED COMMAND
# Run: python main.py seed
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        print("🌱 Seeding database with celebrity data...")
        from database.supabase import seed_celebrities, seed_nodes
        seed_celebrities()
        seed_nodes()
        print("✅ Done! Database is ready for the hackathon.")
    else:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

