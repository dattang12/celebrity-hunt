# WarmPath 🔥

> Find the shortest warm path to anyone.

WarmPath is an AI-powered network engine that maps the real inner circle of 140+ celebrities and generates personalized outreach messages to the right person — not the celebrity directly.

Built in 8 hours at the **Celebrity Hunt Hackathon** hosted by LSE Generate, SF.

---

## The Problem

Cold outreach to celebrities has a <1% reply rate. But a warm message to the right person in their circle? That changes everything.

Most people try to reach the celebrity directly. WarmPath finds the human door that's already open.

---

## How It Works

1. **Search** any celebrity (MrBeast, Garry Tan, Alex Hormozi...)
2. **Map** their real inner circle — managers, close friends, collaborators
3. **Score** every connection by how reachable they actually are (0-100 warm score)
4. **Generate** a personalized AI outreach message to the right node
5. **Send** with one click — Twitter DM or Gmail pre-filled

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| Database | Supabase (PostgreSQL) |
| AI | Claude (Anthropic) |
| Frontend | React / Lovable |
| Graph | SVG network visualization |
| Data | Real Twitter network exports |

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourname/warmpath
cd warmpath/backend
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the `backend/` folder:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 4. Run the backend
```bash
python main.py
```

Backend runs on `http://localhost:8000`

### 5. Expose with ngrok (for frontend connection)
```bash
ngrok http 8000
```

---

## Project Structure

```
backend/
├── database/
│   └── supabase.py        # Supabase client
├── routers/
│   └── celebrity.py       # API endpoints
├── services/
│   ├── ai.py              # Claude AI — message generation
│   ├── graph.py           # Network path finding
│   └── scraper.py         # Celebrity data scraper
├── main.py                # Flask app entry point
├── requirements.txt
└── .gitignore
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/celebrities` | List all celebrities |
| GET | `/celebrities/search?q=name` | Search celebrity |
| GET | `/celebrities/:id/nodes` | Get network nodes |
| POST | `/outreach/generate` | Generate AI outreach message |

---

## Data

- **140+ celebrities** seeded across Tech, Sports, Music, Film, Politics
- **Real Twitter network data** — connections sourced from actual Twitter following exports
- **Warm scores** — 0-100 ranking of how reachable each connection is
- **Contact info** — Twitter handles and public emails where available

---

## License
MIT
