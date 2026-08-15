"""
routers/analytics.py
---------------------
The "standout" endpoints: root-cause tracing for a single failed task,
and clustering tasks that share the same root cause across the graph.
"""

from fastapi import APIRouter, HTTPException
from app.db import get_session
from app.queries import cypher
from app.models import FailureTrace, FailureCluster

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/tasks/{task_id}/failure-trace", response_model=FailureTrace)
def trace_failure(task_id: str):
    try:
        with get_session() as session:
            result = session.run(cypher.TRACE_FAILURE_ROOT_CAUSE, task_id=task_id)
            record = result.single()
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Database is unreachable. Please try again shortly.")

    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return FailureTrace(**record.data())


@router.get("/failure-clusters", response_model=list[FailureCluster])
def failure_clusters():
    try:
        with get_session() as session:
            result = session.run(cypher.SHARED_FAILURE_CLUSTERS)
            return [FailureCluster(**record.data()) for record in result]
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Database is unreachable. Please try again shortly.")
