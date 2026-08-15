# AgentGraph

A debugging and observability tool for multi-agent AI systems, backed by **CognoDB** (a graph database speaking the Bolt/openCypher protocol).

When a chain of AI agents delegates work, calls tools, and depends on each other's output, a single failure deep in that chain can be hard to trace back to its root cause. AgentGraph models an agent system's execution history as a graph — agents, tasks, tool calls, and outputs, all connected — so that tracing *why* something failed is a graph traversal instead of a manual log hunt.

**Live demo:** [https://agentgraph.netlify.app/]


---

## Screenshots

**Dashboard**

 <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/8e99e4b7-6f28-4b4d-8646-826dddf5e05a" />


**Run Explorer — task trace with root-cause highlighting**

 <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/61ad6e38-664a-462f-97c1-4a69409647cf" />


**Failure Patterns — shared root-cause clustering**

 <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/51377c00-bbfb-44b5-98bb-1e8cf51181ec" />


---

## Why a graph database?

Multi-agent AI systems are, structurally, graphs: agents delegate to other agents, tasks depend on earlier tasks, and tool calls produce outputs that later steps rely on. The questions worth asking about a failing system are almost always about *connections*, not individual records:

- "Which upstream failure actually caused this task to break, three steps back?"
- "What's the full delegation chain this run went through?"
- "Do these five failures across unrelated runs share the same root cause?"

In a relational database, each of these needs a recursive self-join or a chain of application-level queries that gets uglier as the chain gets deeper. In CognoDB, they're single, readable Cypher queries using variable-length path traversal (`[:DEPENDS_ON*1..5]`) — the database itself understands "follow this connection, however many hops it takes."

This mirrors a real, current problem: as companies deploy multi-agent AI systems in production, understanding *why* a chain of delegations and tool calls failed is an active pain point — it's the same class of problem observability platforms like LangSmith and Langfuse exist to solve. AgentGraph is a small, from-scratch demonstration of that idea using a purpose-built graph data model.

---

## Data model

**Nodes**

| Label | Key properties |
|---|---|
| `Agent` | `id`, `name`, `role`, `model` |
| `Tool` | `id`, `name`, `category` |
| `Task` | `id`, `description`, `status` |
| `Run` | `id`, `status`, `started_at`, `ended_at`, `trigger` |
| `Output` | `id`, `type`, `summary` |

**Relationships**

| Relationship | Meaning |
|---|---|
| `(Run)-[:EXECUTED]->(Agent)` | The primary agent that started this run |
| `(Run)-[:INCLUDES]->(Task)` | Explicitly scopes a task to its run |
| `(Agent)-[:PERFORMED]->(Task)` | Which agent carried out a task |
| `(Agent)-[:DELEGATES_TO]->(Agent)` | One agent handing work off to another |
| `(Task)-[:DEPENDS_ON]->(Task)` | Task ordering — a task can't start until the one it depends on finishes |
| `(Task)-[:CALLS]->(Tool)` | The specific tool this task invoked |
| `(Task)-[:PRODUCED]->(Output)` | The result this task's tool call produced |
| `(Task)-[:FAILED_DUE_TO]->(Output)` | Links a failed task to the specific error output that caused it — multiple tasks can point to the *same* Output node, representing a shared root cause (e.g. one tool outage breaking several unrelated runs) |

**Diagram (one run, simplified):**

```
(Run) --EXECUTED--> (Agent A) --PERFORMED--> (Task 1) --CALLS--> (Tool) --PRODUCED--> (Output)
   |                    |                        |
   |                DELEGATES_TO             DEPENDS_ON
   |                    v                        v
   |--INCLUDES-->   (Agent B) --PERFORMED--> (Task 2) --FAILED_DUE_TO--> (Output: error)
```

A key modeling decision worth calling out: `CALLS` and `PRODUCED` live on the **Task**, not the Agent. Agents are shared across many runs (only 8 agents total, reused 40+ times), so an early version of this model that attached tool-calls to the Agent caused queries scoped to "one run" to accidentally pull in that agent's history from every other run it had ever been part of. Moving these relationships to the Task — and adding an explicit `Run -[:INCLUDES]-> Task` relationship — fixed this by giving every task an unambiguous owner.

---

## Main queries

All queries live in `backend/app/queries/cypher.py` and are called through parameterised Neo4j driver calls — no string-concatenated Cypher anywhere in the codebase.

### 1. Multi-hop delegation chain (2+ hops)
```cypher
MATCH path = (start:Agent {id: $agent_id})-[:DELEGATES_TO*1..5]->(sub:Agent)
RETURN [node IN nodes(path) | {id: node.id, name: node.name, role: node.role}] AS chain,
       length(path) AS hops
ORDER BY hops
```
Follows agent-to-agent hand-offs as deep as they go, using variable-length path matching (`*1..5`).

### 2. Root-cause tracing
```cypher
MATCH (start:Task {id: $task_id})
OPTIONAL MATCH path = (start)-[:DEPENDS_ON*0..5]->(upstream:Task)-[:FAILED_DUE_TO]->(o:Output)
WITH upstream, o, path
ORDER BY length(path) DESC
RETURN upstream.id AS root_cause_task_id, upstream.description AS root_cause_description,
       o.summary AS error_message, o.type AS error_type
LIMIT 1
```
Starting from one failed task, walks backward through its dependency chain to find the *earliest* upstream failure — the true root cause, not just a downstream symptom.

### 3. Shared failure clustering — the query a relational database finds awkward
```cypher
MATCH (t1:Task)-[:FAILED_DUE_TO]->(o:Output)<-[:FAILED_DUE_TO]-(t2:Task)
WHERE t1.id < t2.id
RETURN o.summary AS shared_error, o.id AS output_id,
       collect(DISTINCT t1.id) + collect(DISTINCT t2.id) AS affected_task_ids
```
Finds tasks — potentially from completely unrelated runs — that failed for the exact same underlying reason (they point to the same `Output` node). In SQL this needs a recursive self-join across a join table plus de-duplication of pairs; here it's one pattern match.

---

## Architecture

```
┌──────────────────┐        ┌────────────────────┐        ┌───────────────────┐
│   Frontend       │  HTTP  │   Backend API      │  Bolt  │   CognoDB Cloud   │
│   React + Vite   │◄──────►│  FastAPI +         │◄──────►│  (graph database) │
│   (Netlify)      │        │  Neo4j driver      │        │                   │
└──────────────────┘        │  (Render)          │        └───────────────────┘
                            └────────────────────┘
                                        ▲
                                        │
                               ┌────────────────────┐
                               │  seed_data.py       │
                               │  generates realistic│
                               │  agent/run data     │
                               └────────────────────┘
```

- **Frontend** — React + Vite, deployed on Netlify. Talks to the backend over plain HTTP/JSON.
- **Backend** — FastAPI, deployed on Render. Wraps parameterised Cypher queries behind a REST API, with graceful error handling if CognoDB is unreachable.
- **Database** — CognoDB Cloud (free tier), a managed graph database speaking openCypher over Bolt, accessed via the official Neo4j Python driver.
- **Seed script** — a standalone Python script that populates the graph with realistic (simulated) agent-run data, since no real production agent logs were available to pull from.

---

## Project structure

```
agentgraph/
├── README.md                  ← you are here
├── .gitignore
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   ├── .env.example
│   ├── test_connection.py
│   ├── app/
│   │   ├── main.py             FastAPI entry point, routers, CORS
│   │   ├── config.py           reads env vars
│   │   ├── db.py                Neo4j driver + session handling
│   │   ├── models.py            Pydantic response models
│   │   ├── queries/
│   │   │   └── cypher.py        every Cypher query used by the API
│   │   └── routers/
│   │       ├── runs.py
│   │       ├── agents.py
│   │       └── analytics.py
│   └── seed/
│       └── seed_data.py         generates and loads sample data
└── frontend/
    ├── README.md
    ├── package.json
    ├── .env.example
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx / App.jsx
        ├── api/client.js         all backend calls in one place
        ├── styles/global.css     design tokens + layout
        ├── components/           Layout, StatusPill, Loading/Empty/ErrorState
        └── pages/
            ├── Dashboard.jsx
            ├── RunExplorer.jsx
            └── FailurePatterns.jsx
```

---

## Setup and run instructions

### 1. Create a CognoDB Cloud instance
1. Sign up at [console.cognodb.com/signup](https://console.cognodb.com/signup) (free tier, no credit card).
2. From the console, create a free (`c0`) instance and pick a region — provisions in under a minute.
3. Save your connection URI (`bolt+s://<instance-id>.databases.cognodb.cloud`), username (`cognodb`), and the password — it's shown only once.

### 2. Run the backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your real CognoDB values
python test_connection.py       # confirms connectivity before continuing
```

Load the sample data:
```bash
python seed/seed_data.py
```

Start the API:
```bash
uvicorn app.main:app --reload --port 8000
```
Visit `http://127.0.0.1:8000/docs` for interactive API docs.

### 3. Run the frontend
```bash
cd frontend
npm install
cp .env.example .env            # set VITE_API_BASE_URL to your backend URL
npm run dev
```
Visit the URL Vite prints (usually `http://localhost:5173`).

See `backend/README.md` and `frontend/README.md` for more detail on each half.

---

## Troubleshooting

- **TLS/connection-reset error connecting to CognoDB** (`ConnectionResetError`, Windows error 10054): this was traced to antivirus software (Kaspersky, in development) performing SSL/TLS inspection on non-standard encrypted ports. Check for antivirus "scan encrypted connections" features and add an exclusion for your CognoDB host, or temporarily disable it while developing.
- **Backend is slow to respond on first request after deploy**: the Render free tier sleeps after 15 minutes of inactivity and takes 30–60 seconds to wake on the next request. This is expected — refresh after a moment.
- **`Cannot GET /...` on a deployed endpoint**: double-check you're hitting the correct Render service URL — if multiple services were created during setup, confirm which one is actually live via its `/health` endpoint.

---

## Tech stack

- **Database:** CognoDB Cloud (openCypher over Bolt)
- **Backend:** Python, FastAPI, official `neo4j` driver, Pydantic
- **Frontend:** React, Vite, React Router, Axios
- **Hosting:** Render (backend), Netlify (frontend)
