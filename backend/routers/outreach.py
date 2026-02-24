"""
routers/outreach.py
Outreach message generation, saving, and tracking endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database.supabase import get_client
from services.ai import draft_outreach_message, generate_leverage

router = APIRouter(prefix="/outreach", tags=["Outreach"])


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class GenerateMessageRequest(BaseModel):
    celebrity_id: str
    node_id: str
    sender_name: str = "Dat"
    sender_background: str = "Tech founder building AI tools in San Francisco"
    user_ask: str = "3-minute FaceTime to show you something I built"


class UpdateStatusRequest(BaseModel):
    status: str  # draft, sent, replied


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/generate")
async def generate_message(req: GenerateMessageRequest):
    """
    Generate a personalized outreach message for a specific node.
    Saves to Supabase and returns the message.
    """
    db = get_client()

    # Get node details
    node_result = db.table("nodes").select("*").eq("id", req.node_id).single().execute()
    if not node_result.data:
        raise HTTPException(status_code=404, detail="Node not found")
    node = node_result.data

    # Get celebrity details
    celeb_result = db.table("celebrities").select("*").eq("id", req.celebrity_id).single().execute()
    if not celeb_result.data:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    celeb = celeb_result.data

    # Generate leverage first
    leverage = generate_leverage(
        celebrity_name=celeb["name"],
        celebrity_bio=celeb.get("bio", ""),
        recent_news=celeb.get("recent_news", []),
        user_background=req.sender_background,
        user_ask=req.user_ask,
    )

    # Generate outreach message
    message_data = draft_outreach_message(
        sender_name=req.sender_name,
        sender_background=req.sender_background,
        target_person=node["person_name"],
        target_role=node.get("role", ""),
        target_relationship_to_celebrity=node.get("relationship_type", ""),
        celebrity_name=celeb["name"],
        value_prop=leverage["value_prop"],
        why_they_would_forward=node.get("why_warm", ""),
        hop_number=node.get("hop_distance", 1),
    )

    # Save to Supabase
    saved = db.table("outreach").insert({
        "celebrity_id": req.celebrity_id,
        "node_id": req.node_id,
        "message_text": message_data["message"],
        "value_proposition": leverage["value_prop"],
        "subject_line": message_data["subject_line"],
        "status": "draft",
    }).execute()

    return {
        "outreach_id": saved.data[0]["id"] if saved.data else None,
        "message": message_data["message"],
        "subject_line": message_data["subject_line"],
        "platform_note": message_data["platform_note"],
        "tone_note": message_data["tone_note"],
        "word_count": message_data["word_count"],
        "leverage": leverage,
        "target": {
            "person_name": node["person_name"],
            "role": node["role"],
            "contact_info": node.get("contact_info"),
        },
    }


@router.get("/celebrity/{celebrity_id}")
async def get_outreach_for_celebrity(celebrity_id: str):
    """Get all outreach messages generated for a celebrity."""
    db = get_client()

    messages = (
        db.table("outreach")
        .select("*, nodes(person_name, role, contact_info)")
        .eq("celebrity_id", celebrity_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return {"messages": messages, "count": len(messages)}


@router.patch("/{outreach_id}/status")
async def update_status(outreach_id: str, req: UpdateStatusRequest):
    """Update outreach status (draft → sent → replied)."""
    valid_statuses = ["draft", "sent", "replied"]
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status must be one of: {', '.join(valid_statuses)}"
        )

    db = get_client()
    result = (
        db.table("outreach")
        .update({"status": req.status})
        .eq("id", outreach_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Outreach message not found")

    return {"message": f"Status updated to '{req.status}'", "outreach": result.data[0]}


@router.get("/stats")
async def get_outreach_stats():
    """Dashboard stats — total messages, sent, replied."""
    db = get_client()

    all_messages = db.table("outreach").select("status").execute().data

    stats = {"draft": 0, "sent": 0, "replied": 0, "total": len(all_messages)}
    for msg in all_messages:
        status = msg.get("status", "draft")
        if status in stats:
            stats[status] += 1

    reply_rate = (
        round((stats["replied"] / stats["sent"]) * 100, 1)
        if stats["sent"] > 0 else 0
    )

    return {**stats, "reply_rate_percent": reply_rate}
