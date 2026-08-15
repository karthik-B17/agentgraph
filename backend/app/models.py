"""
models.py
---------
Pydantic models define the *shape* of data going in/out of the API.
FastAPI uses these to auto-generate docs (at /docs) and to validate
responses. This is what makes the frontend's job predictable — it
always knows exactly what fields to expect.
"""

from pydantic import BaseModel
from typing import Optional


class RunSummary(BaseModel):
    id: str
    status: str
    started_at: str
    ended_at: Optional[str] = None
    trigger: str
    primary_agent: str


class TaskDetail(BaseModel):
    task_id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    agent: Optional[str] = None
    tool: Optional[str] = None
    output_summary: Optional[str] = None
    depends_on: Optional[str] = None


class RunDetail(BaseModel):
    run_id: str
    run_status: str
    primary_agent: str
    tasks: list[TaskDetail]


class DelegationHop(BaseModel):
    id: str
    name: str
    role: str


class DelegationChainEntry(BaseModel):
    chain: list[DelegationHop]
    hops: int


class FailureTrace(BaseModel):
    root_cause_task_id: Optional[str] = None
    root_cause_description: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class FailureCluster(BaseModel):
    shared_error: str
    output_id: str
    affected_task_ids: list[str]
