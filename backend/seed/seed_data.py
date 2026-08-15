"""
seed_data.py
------------
Generates realistic fake data for the AgentGraph data model and loads
it into CognoDB using parameterised Cypher (no string concatenation).

Run with (from inside backend/, venv active):
    python seed/seed_data.py
"""

import random
import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from faker import Faker
from app.db import get_session, verify_connection, close_driver

fake = Faker()

NUM_RUNS = 40
AGENT_ROLES = ["manager", "researcher", "coder", "reviewer", "planner"]
TOOL_DEFS = [
    ("web_search", "search"),
    ("code_exec", "execution"),
    ("db_query", "data"),
    ("file_read", "data"),
    ("calculator", "execution"),
    ("email_send", "communication"),
]
MODELS = ["claude-sonnet-5", "claude-haiku-4-5", "claude-opus-4-8"]

FAILURE_MESSAGES = [
    "Tool timed out after 30s",
    "Rate limit exceeded",
    "Invalid arguments passed to tool",
    "Upstream API returned 500",
    "Permission denied accessing resource",
]


def new_id():
    return str(uuid.uuid4())


def _create_constraints_tx(tx):
    constraints = [
        "CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT tool_id IF NOT EXISTS FOR (t:Tool) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT task_id IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT run_id IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT output_id IF NOT EXISTS FOR (o:Output) REQUIRE o.id IS UNIQUE",
    ]
    for c in constraints:
        tx.run(c)
    return len(constraints)


def _clear_existing_data_tx(tx):
    tx.run("MATCH (n) WHERE n:Agent OR n:Tool OR n:Task OR n:Run OR n:Output DETACH DELETE n")


def _seed_agents_and_tools_tx(tx, agents, tools):
    tx.run(
        "UNWIND $agents AS a "
        "CREATE (:Agent {id: a.id, name: a.name, role: a.role, model: a.model})",
        agents=agents,
    )
    tx.run(
        "UNWIND $tools AS t "
        "CREATE (:Tool {id: t.id, name: t.name, category: t.category})",
        tools=tools,
    )


def _seed_run_tx(tx, agents, tools, run_index, tool_failure_outputs):
    run_id = new_id()
    started_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))
    primary_agent = random.choice(agents)

    tx.run(
        "CREATE (r:Run {id: $id, started_at: $started_at, status: 'pending', "
        "trigger: $trigger})",
        id=run_id,
        started_at=started_at.isoformat(),
        trigger=random.choice(["user", "scheduled"]),
    )
    tx.run(
        "MATCH (r:Run {id: $run_id}), (a:Agent {id: $agent_id}) "
        "CREATE (r)-[:EXECUTED]->(a)",
        run_id=run_id,
        agent_id=primary_agent["id"],
    )

    num_tasks = random.randint(2, 4)
    prev_task_id = None
    run_has_failure = False
    current_agent = primary_agent

    for t in range(num_tasks):
        if t > 0 and random.random() < 0.4:
            next_agent = random.choice(agents)
            tx.run(
                "MATCH (a1:Agent {id: $a1}), (a2:Agent {id: $a2}) "
                "CREATE (a1)-[:DELEGATES_TO]->(a2)",
                a1=current_agent["id"],
                a2=next_agent["id"],
            )
            current_agent = next_agent

        task_id = new_id()
        will_fail = random.random() < 0.2
        status = "failed" if will_fail else "success"

        tx.run(
            "CREATE (task:Task {id: $id, description: $desc, status: $status})",
            id=task_id,
            desc=fake.sentence(nb_words=6),
            status=status,
        )
        # Explicitly scope this task to its run — without this, tasks are
        # only reachable via the shared Agent nodes, which causes queries
        # scoped to "one run" to accidentally pull in that agent's tasks
        # from EVERY run it's ever been part of.
        tx.run(
            "MATCH (r:Run {id: $run_id}), (task:Task {id: $task_id}) "
            "CREATE (r)-[:INCLUDES]->(task)",
            run_id=run_id,
            task_id=task_id,
        )
        tx.run(
            "MATCH (a:Agent {id: $agent_id}), (task:Task {id: $task_id}) "
            "CREATE (a)-[:PERFORMED]->(task)",
            agent_id=current_agent["id"],
            task_id=task_id,
        )

        if prev_task_id:
            tx.run(
                "MATCH (t1:Task {id: $t1}), (t2:Task {id: $t2}) "
                "CREATE (t1)-[:DEPENDS_ON]->(t2)",
                t1=task_id,
                t2=prev_task_id,
            )

        tool = random.choice(tools)
        # CALLS lives on the Task, not the Agent — a specific tool call
        # belongs to a specific task, not generically to "this agent,
        # sometime, somewhere."
        tx.run(
            "MATCH (task:Task {id: $task_id}), (tool:Tool {id: $tool_id}) "
            "CREATE (task)-[:CALLS]->(tool)",
            task_id=task_id,
            tool_id=tool["id"],
        )

        if will_fail:
            run_has_failure = True
            existing = tool_failure_outputs.get(tool["id"], [])
            if existing and random.random() < 0.5:
                output_id = random.choice(existing)
            else:
                output_id = new_id()
                output_summary = random.choice(FAILURE_MESSAGES)
                tx.run(
                    "CREATE (o:Output {id: $id, type: 'error', summary: $summary})",
                    id=output_id,
                    summary=output_summary,
                )
                tool_failure_outputs.setdefault(tool["id"], []).append(output_id)

            tx.run(
                "MATCH (task:Task {id: $task_id}), (o:Output {id: $output_id}) "
                "CREATE (task)-[:PRODUCED]->(o)",
                task_id=task_id,
                output_id=output_id,
            )
            tx.run(
                "MATCH (task:Task {id: $task_id}), (o:Output {id: $output_id}) "
                "CREATE (task)-[:FAILED_DUE_TO]->(o)",
                task_id=task_id,
                output_id=output_id,
            )
        else:
            output_id = new_id()
            tx.run(
                "CREATE (o:Output {id: $id, type: 'text', summary: $summary})",
                id=output_id,
                summary=fake.sentence(nb_words=8),
            )
            tx.run(
                "MATCH (task:Task {id: $task_id}), (o:Output {id: $output_id}) "
                "CREATE (task)-[:PRODUCED]->(o)",
                task_id=task_id,
                output_id=output_id,
            )

        prev_task_id = task_id

    final_status = "failed" if run_has_failure else "success"
    tx.run(
        "MATCH (r:Run {id: $run_id}) SET r.status = $status, r.ended_at = $ended_at",
        run_id=run_id,
        status=final_status,
        ended_at=(started_at + timedelta(minutes=random.randint(1, 45))).isoformat(),
    )


def main():
    print("Checking CognoDB connectivity...")
    if not verify_connection():
        print("❌ Cannot reach CognoDB. Check your .env values before seeding.")
        sys.exit(1)

    agents = [
        {
            "id": new_id(),
            "name": f"{random.choice(AGENT_ROLES).capitalize()}Agent-{i+1}",
            "role": random.choice(AGENT_ROLES),
            "model": random.choice(MODELS),
        }
        for i in range(8)
    ]
    tools = [{"id": new_id(), "name": name, "category": category} for name, category in TOOL_DEFS]

    with get_session() as session:
        n = session.execute_write(_create_constraints_tx)
        print(f"✅ Created/verified {n} constraints")

        session.execute_write(_clear_existing_data_tx)
        print("🧹 Cleared existing data")

        session.execute_write(_seed_agents_and_tools_tx, agents, tools)
        print(f"✅ Created {len(agents)} agents and {len(tools)} tools")

        seeded = 0
        tool_failure_outputs = {}
        for i in range(NUM_RUNS):
            try:
                session.execute_write(_seed_run_tx, agents, tools, i, tool_failure_outputs)
                seeded += 1
            except Exception as e:
                print(f"⚠️  Run {i} failed even after retries: {e}")
            if (i + 1) % 10 == 0:
                print(f"  ...processed {i + 1}/{NUM_RUNS} runs ({seeded} succeeded so far)")

    print(f"✅ Done. Successfully seeded {seeded}/{NUM_RUNS} runs.")
    close_driver()


if __name__ == "__main__":
    main()