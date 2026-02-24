"""
routers/celebrity.py
Celebrity search, graph data, and intelligence endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from database.supabase import get_client
from services.scraper import scrape_all
from services.graph import calculate_access_score, find_best_path, get_graph_data
from services.ai import generate_full_intelligence_package

router = APIRouter(prefix="/celebrity", tags=["Celebrity"])


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class SearchRequest(BaseModel):
    name: str
    user_background: str = "Tech founder from San Francisco"
    user_ask: str = "3-minute FaceTime"


class AddNodeRequest(BaseModel):
    celebrity_id: str
    person_name: str
    role: str
    relationship_type: str
    hop_distance: int = 1
    contact_info: Optional[str] = None
    warm_score: int = 70
    why_warm: str


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.get("/list")
async def list_celebrities():
    """Get all pre-loaded celebrities with their access scores."""
    db = get_client()
    celebs = (
        db.table("celebrities")
        .select("id, name, industry, access_score, twitter_handle, known_manager")
        .order("access_score", desc=True)
        .execute()
        .data
    )
    return {"celebrities": celebs, "count": len(celebs)}


@router.post("/search")
async def search_celebrity(req: SearchRequest, background_tasks: BackgroundTasks):
    """
    Main search endpoint — returns full intelligence package.
    1. Check if celebrity exists in DB
    2. If not, scrape and create
    3. Run pathfinding
    4. Generate AI intelligence
    """
    db = get_client()

    # Check if celebrity exists
    result = (
        db.table("celebrities")
        .select("*")
        .ilike("name", f"%{req.name}%")
        .limit(1)
        .execute()
    )

    if result.data:
        celebrity = result.data[0]
        celebrity_id = celebrity["id"]
    else:
        # Scrape and create new celebrity
        scraped = scrape_all(req.name)

        insert_result = (
            db.table("celebrities")
            .insert({
                "name": req.name,
                "bio": scraped.get("bio", ""),
                "recent_news": scraped.get("recent_news", []),
                "access_score": 50,  # default, will recalculate
            })
            .execute()
        )

        if not insert_result.data:
            raise HTTPException(status_code=500, detail="Failed to create celebrity record")

        celebrity = insert_result.data[0]
        celebrity_id = celebrity["id"]

    # Recalculate access score
    access_score = calculate_access_score(celebrity_id)
    db.table("celebrities").update({"access_score": access_score}).eq("id", celebrity_id).execute()
    celebrity["access_score"] = access_score

    # Find best path
    best_path = find_best_path(celebrity_id, user_context={
        "industry": "tech",
        "connections": [],
        "background": req.user_background,
    })

    # Get graph data for visualization
    graph = get_graph_data(celebrity_id, celebrity["name"])

    # Generate AI intelligence package
    intelligence = generate_full_intelligence_package(
        celebrity_name=celebrity["name"],
        celebrity_data=celebrity,
        best_path=best_path,
        user_background=req.user_background,
        user_ask=req.user_ask,
    )

    return {
        "celebrity": {
            "id": celebrity_id,
            "name": celebrity["name"],
            "industry": celebrity.get("industry"),
            "bio": celebrity.get("bio"),
            "access_score": access_score,
            "twitter_handle": celebrity.get("twitter_handle"),
            "known_manager": celebrity.get("known_manager"),
        },
        "graph": graph,
        "best_path": best_path,
        "intelligence": intelligence,
    }


@router.get("/{celebrity_id}/graph")
async def get_celebrity_graph(celebrity_id: str):
    """Get network graph data for visualization."""
    db = get_client()

    celeb = db.table("celebrities").select("name").eq("id", celebrity_id).single().execute()
    if not celeb.data:
        raise HTTPException(status_code=404, detail="Celebrity not found")

    graph = get_graph_data(celebrity_id, celeb.data["name"])
    return graph


@router.get("/{celebrity_id}/score")
async def get_access_score(celebrity_id: str):
    """Get current access score for a celebrity."""
    score = calculate_access_score(celebrity_id)
    return {"celebrity_id": celebrity_id, "access_score": score}


@router.get("/{celebrity_id}/nodes")
async def get_nodes(celebrity_id: str):
    """Get all network nodes for a celebrity, sorted by warm score."""
    db = get_client()
    nodes = (
        db.table("nodes")
        .select("*")
        .eq("celebrity_id", celebrity_id)
        .order("warm_score", desc=True)
        .execute()
        .data
    )
    return {"nodes": nodes, "count": len(nodes)}


@router.post("/{celebrity_id}/nodes")
async def add_node(celebrity_id: str, req: AddNodeRequest):
    """Manually add a network node (for hackathon pre-seeding)."""
    db = get_client()

    node = db.table("nodes").insert({
        "celebrity_id": celebrity_id,
        "person_name": req.person_name,
        "role": req.role,
        "relationship_type": req.relationship_type,
        "hop_distance": req.hop_distance,
        "contact_info": req.contact_info,
        "warm_score": req.warm_score,
        "why_warm": req.why_warm,
    }).execute()

    return {"node": node.data[0], "message": "Node added successfully"}
