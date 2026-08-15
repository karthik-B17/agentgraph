"""
routers/runs.py
----------------
Endpoints for listing runs and viewing one run's full detail.
"""

from fastapi import APIRouter, HTTPException
from app.db import get_session
from app.queries import cypher
from app.models import RunSummary, RunDetail, TaskDetail

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunSummary])
def list_runs():
    try:
        with get_session() as session:
            result = session.run(cypher.LIST_RUNS)
            return [RunSummary(**record.data()) for record in result]
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Database is unreachable. Please try again shortly.")


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    try:
        with get_session() as session:
            result = session.run(cypher.GET_RUN_DETAIL, run_id=run_id)
            record = result.single()
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Database is unreachable. Please try again shortly.")

    if record is None or record["run_id"] is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    return RunDetail(
        run_id=record["run_id"],
        run_status=record["run_status"],
        primary_agent=record["primary_agent"],
        tasks=[TaskDetail(**t) for t in record["tasks"] if t.get("task_id")],
    )
