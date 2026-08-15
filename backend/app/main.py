"""
main.py
-------
FastAPI entry point. Wires together all routers and exposes a health
check. Also enables CORS so the React frontend (running on a different
port/domain) is allowed to call this API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import verify_connection
from app.routers import runs, agents, analytics

app = FastAPI(title="AgentGraph API")

# Allow the frontend (dev server or deployed site) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router)
app.include_router(agents.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "AgentGraph API is running"}


@app.get("/health")
def health():
    db_ok = verify_connection()
    return {"status": "ok" if db_ok else "degraded", "cognodb_connected": db_ok}


@app.get("/debug/count")
def debug_count():
    from app.db import get_session
    with get_session() as session:
        result = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count")
        return {record["label"]: record["count"] for record in result}


@app.get("/debug/failures")
def debug_failures():
    from app.db import get_session
    with get_session() as session:
        result = session.run(
            "MATCH (t:Task {status: 'failed'})-[:FAILED_DUE_TO]->(o:Output) "
            "RETURN count(t) AS failed_task_count"
        )
        return {"failed_tasks": result.single()["failed_task_count"]}


@app.get("/debug/sample-ids")
def debug_sample_ids():
    from app.db import get_session
    with get_session() as session:
        run_id = session.run("MATCH (r:Run) RETURN r.id AS id LIMIT 1").single()["id"]
        agent_id = session.run(
            "MATCH (a:Agent)-[:DELEGATES_TO]->() RETURN a.id AS id LIMIT 1"
        ).single()
        agent_id = agent_id["id"] if agent_id else None
        failed_task = session.run(
            "MATCH (t:Task {status: 'failed'}) RETURN t.id AS id LIMIT 1"
        ).single()["id"]
        return {
            "sample_run_id": run_id,
            "sample_agent_id_with_delegation": agent_id,
            "sample_failed_task_id": failed_task,
        }


@app.get("/debug/check-includes")
def debug_check_includes():
    from app.db import get_session
    with get_session() as session:
        includes = session.run("MATCH ()-[rel:INCLUDES]->() RETURN count(rel) AS total").single()["total"]
        runs = session.run("MATCH (r:Run) RETURN count(r) AS total").single()["total"]
        tasks = session.run("MATCH (t:Task) RETURN count(t) AS total").single()["total"]
        return {"includes_relationship_count": includes, "run_count": runs, "task_count": tasks}