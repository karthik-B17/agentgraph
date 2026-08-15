"""
routers/agents.py
------------------
Endpoint exposing the multi-hop delegation chain query.
"""

from fastapi import APIRouter, HTTPException
from app.db import get_session
from app.queries import cypher
from app.models import DelegationChainEntry, DelegationHop

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/{agent_id}/delegation-chain", response_model=list[DelegationChainEntry])
def get_delegation_chain(agent_id: str):
    try:
        with get_session() as session:
            result = session.run(cypher.DELEGATION_CHAIN, agent_id=agent_id)
            return [
                DelegationChainEntry(
                    chain=[DelegationHop(**hop) for hop in record["chain"]],
                    hops=record["hops"],
                )
                for record in result
            ]
    except ConnectionError:
        raise HTTPException(status_code=503, detail="Database is unreachable. Please try again shortly.")
