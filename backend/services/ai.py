"""
services/ai.py
Claude-powered intelligence layer:
- Leverage Generator (why FaceTime benefits THEM)
- Outreach Message Drafter (per hop, personalized)
- Value Proposition Builder
- Access Strategy Advisor
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-opus-4-6"


# ─────────────────────────────────────────────
# LEVERAGE GENERATOR
# Creates compelling reason why celebrity benefits
# ─────────────────────────────────────────────

def generate_leverage(
    celebrity_name: str,
    celebrity_bio: str,
    recent_news: list[dict],
    user_background: str,
    user_ask: str = "3-minute FaceTime",
) -> dict:
    """
    Generate a custom value proposition — why FaceTime benefits THEM.
    Returns: {value_prop, ego_hook, curiosity_hook, subject_line}
    """

    news_summary = "\n".join(
        f"- {a['title']}" for a in (recent_news or [])[:3]
    )

    prompt = f"""You are a world-class relationship strategist helping someone get a FaceTime with {celebrity_name}.

ABOUT {celebrity_name.upper()}:
{celebrity_bio}

RECENT NEWS ABOUT THEM:
{news_summary or "No recent news available"}

THE PERSON REQUESTING ACCESS:
{user_background}

WHAT THEY WANT:
{user_ask}

Generate a compelling leverage package with these 4 components:

1. VALUE_PROP: A 2-sentence explanation of why meeting this person genuinely benefits {celebrity_name}. 
   Must be specific to their current situation/goals. NOT generic flattery.
   
2. EGO_HOOK: A 1-sentence observation about {celebrity_name} that shows deep understanding of their work.
   Something that makes them feel truly seen, not just famous.
   
3. CURIOSITY_HOOK: A 1-sentence teaser that makes them curious enough to respond.
   Should feel like an incomplete story they need to hear the end of.
   
4. SUBJECT_LINE: A 6-word email/DM subject line that gets opened. Not clickbait. Genuinely intriguing.

Format your response EXACTLY like this:
VALUE_PROP: [your text]
EGO_HOOK: [your text]
CURIOSITY_HOOK: [your text]
SUBJECT_LINE: [your text]"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    result = {}

    for line in text.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            result[key] = value.strip()

    return {
        "value_prop": result.get("value_prop", ""),
        "ego_hook": result.get("ego_hook", ""),
        "curiosity_hook": result.get("curiosity_hook", ""),
        "subject_line": result.get("subject_line", ""),
    }


# ─────────────────────────────────────────────
# OUTREACH MESSAGE DRAFTER
# Writes message for each hop in the chain
# ─────────────────────────────────────────────

def draft_outreach_message(
    sender_name: str,
    sender_background: str,
    target_person: str,
    target_role: str,
    target_relationship_to_celebrity: str,
    celebrity_name: str,
    value_prop: str,
    why_they_would_forward: str,
    hop_number: int = 1,
) -> dict:
    """
    Draft a personalized outreach message for a specific hop.
    Returns: {message, subject_line, platform_note, word_count}
    """

    prompt = f"""You are writing a {_hop_label(hop_number)} outreach message.

SENDER: {sender_name}
SENDER BACKGROUND: {sender_background}

TARGET: {target_person} ({target_role})
TARGET'S CONNECTION TO {celebrity_name.upper()}: {target_relationship_to_celebrity}
WHY THEY WOULD FORWARD: {why_they_would_forward}

ULTIMATE GOAL: Get a FaceTime with {celebrity_name}
VALUE PROPOSITION: {value_prop}


CRITICAL: This message is to {target_person} who has a connection to {celebrity_name}.
You are asking {target_person} to forward or intro you to {celebrity_name}.

Write a message that sounds like a real text or DM from a smart person:
✓ Start with "Hi," — no specific name, just "Hi, my name is {sender_name}. I am {sender_background} at San Jose State University."
✓ First line acknowledges {target_person}'s connection to {celebrity_name} naturally
✓ NO hyphens anywhere — not em dashes, not " — ", not " - "
✓ Write like a friendly founder texting another founder. Warm, grateful, human
✓ Warm and grateful tone — like you genuinely appreciate them taking the time
✓ NO aggressive language like "knock on", "pitch", "close", "deal"
✓ One sentence of what you built
✓ One sentence why it's relevant to {celebrity_name}'s world
✓ Phrase the ask softly — "Would you be open to passing this along?" or "If it feels right, would you intro me?"
✓ Under 70 words. Short = confident. Long = desperate
✓ NO "I wanted to reach out", "Hope this finds you well", "I know you're busy"
✓ NO "I'd love to", NO "Would love to"
✓ Read it back — if it sounds like ChatGPT wrote it, rewrite it

Also provide:
- SUBJECT_LINE: if this is an email (6 words max)
- PLATFORM_NOTE: best platform to send this (email / Twitter DM / LinkedIn / text)
- TONE_NOTE: one-word tone description

Format EXACTLY:
MESSAGE: [your message]
SUBJECT_LINE: [subject]
PLATFORM_NOTE: [platform]
TONE_NOTE: [tone]"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text
    result = {}

    for line in text.strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().lower().replace(" ", "_")
            result[key] = value.strip()

    message = result.get("message", "")
    return {
        "message": message,
        "subject_line": result.get("subject_line", ""),
        "platform_note": result.get("platform_note", "Twitter DM or Email"),
        "tone_note": result.get("tone_note", "warm"),
        "word_count": len(message.split()),
        "hop_number": hop_number,
        "target_person": target_person,
    }


def _hop_label(hop: int) -> str:
    labels = {1: "FIRST (you sending directly)", 2: "SECOND (forwarded intro)", 3: "THIRD (near the celebrity)"}
    return labels.get(hop, f"HOP {hop}")


# ─────────────────────────────────────────────
# ACCESS STRATEGY ADVISOR
# Gives overall strategic advice for this target
# ─────────────────────────────────────────────

def generate_access_strategy(
    celebrity_name: str,
    celebrity_bio: str,
    access_score: int,
    best_nodes: list[dict],
    user_background: str,
) -> str:
    """
    Generate a short strategic brief: best approach for this specific celebrity.
    Returns a 3-paragraph strategy note.
    """

    nodes_summary = "\n".join(
        f"- {n['person_name']} ({n.get('role', '')}) — warm score: {n.get('warm_score', 0)}"
        for n in (best_nodes or [])[:4]
    )

    prompt = f"""You are a strategic advisor helping someone access {celebrity_name}.

CELEBRITY PROFILE:
{celebrity_bio[:300]}

ACCESS SCORE: {access_score}/100
({'Hard to reach directly — use warm paths' if access_score < 60 else 'Moderately reachable — direct + warm paths both viable' if access_score < 80 else 'Highly reachable — multiple strong entry points'})

BEST ENTRY POINTS FOUND:
{nodes_summary}

USER BACKGROUND:
{user_background}

Write a 3-paragraph strategic brief (plain text, no headers, no bullet points):
1. Why this celebrity is or isn't reachable and what their main access pattern is
2. The single best entry point and exactly why it works for this user specifically  
3. One unconventional tactic that most people wouldn't think of for THIS specific celebrity

Keep it sharp, specific, and under 200 words total. Write like a well-connected advisor who actually knows this world."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()


# ─────────────────────────────────────────────
# FULL PIPELINE — generate everything at once
# ─────────────────────────────────────────────

def generate_full_intelligence_package(
    celebrity_name: str,
    celebrity_data: dict,
    best_path: dict,
    user_background: str,
    user_ask: str = "3-minute FaceTime",
) -> dict:
    """
    Master function — generates complete intelligence package.
    Called after celebrity search + path finding.
    Returns everything needed for the dashboard.
    """

    print(f"🧠 Generating AI intelligence for {celebrity_name}...")

    # 1. Generate leverage
    leverage = generate_leverage(
        celebrity_name=celebrity_name,
        celebrity_bio=celebrity_data.get("bio", ""),
        recent_news=celebrity_data.get("recent_news", []),
        user_background=user_background,
        user_ask=user_ask,
    )

    # 2. Generate outreach for best entry point
    outreach_messages = []
    path_nodes = best_path.get("path", [])

    for i, node in enumerate(path_nodes[:2]):  # max 2 hops for now
        msg = draft_outreach_message(
            sender_name="Dat",  # can be made dynamic
            sender_background=user_background,
            target_person=node["person_name"],
            target_role=node.get("role", ""),
            target_relationship_to_celebrity=node.get("relationship_type", ""),
            celebrity_name=celebrity_name,
            value_prop=leverage["value_prop"],
            why_they_would_forward=node.get("why_warm", ""),
            hop_number=i + 1,
        )
        outreach_messages.append(msg)

    # 3. Generate access strategy
    strategy = generate_access_strategy(
        celebrity_name=celebrity_name,
        celebrity_bio=celebrity_data.get("bio", ""),
        access_score=celebrity_data.get("access_score", 50),
        best_nodes=best_path.get("all_nodes", []),
        user_background=user_background,
    )

    return {
        "leverage": leverage,
        "outreach_messages": outreach_messages,
        "strategy": strategy,
    }
