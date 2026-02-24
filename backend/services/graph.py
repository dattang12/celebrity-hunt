"""
services/graph.py
Network graph builder + BFS pathfinding.
Finds shortest warm path from user to celebrity.
"""

from collections import deque
from typing import Optional
from database.supabase import get_client


# ─────────────────────────────────────────────
# ACCESS SCORE CALCULATOR
# ─────────────────────────────────────────────

def calculate_access_score(celebrity_id: str) -> int:
    """
    Calculate 0-100 access score based on:
    - Number of known warm nodes
    - Avg warm score of nodes
    - Hop distances
    - Online activity indicators
    """
    db = get_client()

    nodes = (
        db.table("nodes")
        .select("warm_score, hop_distance, relationship_type")
        .eq("celebrity_id", celebrity_id)
        .execute()
        .data
    )

    if not nodes:
        return 30  # default low score if no data

    # Base score from node warmth
    avg_warm = sum(n["warm_score"] for n in nodes) / len(nodes)

    # Bonus for having direct (1-hop) nodes
    direct_nodes = [n for n in nodes if n["hop_distance"] == 1]
    direct_bonus = min(len(direct_nodes) * 5, 20)

    # Bonus for variety of relationship types
    rel_types = set(n["relationship_type"] for n in nodes)
    variety_bonus = len(rel_types) * 3

    score = int((avg_warm * 0.6) + direct_bonus + variety_bonus)
    return min(max(score, 10), 99)  # clamp between 10-99


# ─────────────────────────────────────────────
# BEST PATH FINDER
# ─────────────────────────────────────────────

def find_best_path(celebrity_id: str, user_context: Optional[dict] = None) -> dict:
    """
    Find the best path from user to celebrity.
    Returns ordered list of nodes with reasoning.

    user_context: optional dict with user's background
    e.g. {"industry": "tech", "connections": ["YC", "Stripe"], "location": "SF"}
    """
    db = get_client()

    # Get all nodes for this celebrity
    nodes = (
        db.table("nodes")
        .select("*")
        .eq("celebrity_id", celebrity_id)
        .order("warm_score", desc=True)
        .execute()
        .data
    )

    if not nodes:
        return {"path": [], "total_hops": 0, "path_score": 0}

    # Score each node based on user context match
    scored_nodes = []
    for node in nodes:
        score = node["warm_score"]

        # Boost score based on user context match
        if user_context:
            user_industry = user_context.get("industry", "").lower()
            user_connections = [c.lower() for c in user_context.get("connections", [])]

            node_text = (
                (node.get("role") or "") + " " +
                (node.get("why_warm") or "") + " " +
                (node.get("relationship_type") or "")
            ).lower()

            # Industry match boost
            if user_industry and user_industry in node_text:
                score += 15

            # Connection overlap boost
            for conn in user_connections:
                if conn in node_text:
                    score += 10

        scored_nodes.append({**node, "final_score": score})

    # Sort by score, prioritize 1-hop nodes
    scored_nodes.sort(key=lambda x: (-x["hop_distance"] == 1, -x["final_score"]))

    # Build recommended path
    # Strategy: pick best 1-hop entry point → best 2-hop if needed
    path = []
    entry_node = scored_nodes[0]
    path.append({
        "person_name": entry_node["person_name"],
        "role": entry_node["role"],
        "relationship_type": entry_node["relationship_type"],
        "hop": entry_node["hop_distance"],
        "warm_score": entry_node["warm_score"],
        "why_warm": entry_node["why_warm"],
        "contact_info": entry_node["contact_info"],
        "node_id": entry_node["id"],
    })

    # Add intermediate nodes if entry is not direct
    if entry_node["hop_distance"] > 1:
        # Find a 1-hop node to bridge
        direct_nodes = [n for n in scored_nodes if n["hop_distance"] == 1]
        if direct_nodes:
            bridge = direct_nodes[0]
            path.append({
                "person_name": bridge["person_name"],
                "role": bridge["role"],
                "relationship_type": bridge["relationship_type"],
                "hop": bridge["hop_distance"],
                "warm_score": bridge["warm_score"],
                "why_warm": bridge["why_warm"],
                "contact_info": bridge["contact_info"],
                "node_id": bridge["id"],
            })

    total_hops = max(n["hop"] for n in path) + 1  # +1 for final hop to celebrity
    path_score = int(sum(n["warm_score"] for n in path) / len(path))

    return {
        "path": path,
        "total_hops": total_hops,
        "path_score": path_score,
        "entry_point": path[0],
        "all_nodes": [
            {
                "person_name": n["person_name"],
                "role": n["role"],
                "warm_score": n["warm_score"],
                "hop_distance": n["hop_distance"],
                "relationship_type": n["relationship_type"],
                "contact_info": n["contact_info"],
                "node_id": n["id"],
            }
            for n in scored_nodes[:8]  # top 8 nodes for graph visualization
        ],
    }


# ─────────────────────────────────────────────
# GRAPH DATA FOR VISUALIZATION
# ─────────────────────────────────────────────

def get_graph_data(celebrity_id: str, celebrity_name: str) -> dict:
    """
    Returns nodes + edges formatted for Vis.js / React Flow visualization.
    """
    db = get_client()

    nodes_data = (
        db.table("nodes")
        .select("*")
        .eq("celebrity_id", celebrity_id)
        .execute()
        .data
    )

    # Build vis.js compatible format
    vis_nodes = [
        {
            "id": "celebrity",
            "label": celebrity_name,
            "group": "celebrity",
            "size": 40,
            "color": {"background": "#FFD700", "border": "#FFA500"},
            "font": {"size": 16, "bold": True},
        }
    ]

    vis_edges = []

    for node in nodes_data:
        node_id = str(node["id"])

        # Color by relationship type
        color_map = {
            "manager": "#FF6B6B",
            "investor": "#4ECDC4",
            "collaborator": "#45B7D1",
            "media": "#96CEB4",
            "colleague": "#FFEAA7",
            "partner": "#DDA0DD",
        }
        color = color_map.get(node.get("relationship_type", ""), "#A0A0A0")

        vis_nodes.append({
            "id": node_id,
            "label": node["person_name"],
            "title": f"{node['role']}\nWarm score: {node['warm_score']}/100",
            "group": node.get("relationship_type", "other"),
            "size": 20 + (node["warm_score"] // 10),
            "color": {"background": color, "border": color},
            "hop_distance": node["hop_distance"],
            "warm_score": node["warm_score"],
            "why_warm": node["why_warm"],
            "contact_info": node["contact_info"],
        })

        vis_edges.append({
            "from": node_id,
            "to": "celebrity",
            "label": node.get("relationship_type", ""),
            "width": node["hop_distance"] == 1 and 3 or 1,
            "dashes": node["hop_distance"] > 1,
        })

    return {"nodes": vis_nodes, "edges": vis_edges}
