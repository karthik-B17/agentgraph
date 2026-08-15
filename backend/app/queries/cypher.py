"""
queries/cypher.py
------------------
Every Cypher query the API uses lives here, in one place. Routers call
these — they never write raw Cypher inline. This makes queries easy to
find, test, and explain in the interview (and is generally good practice:
keep query logic separate from HTTP/routing logic).

All queries use $parameters — never string formatting — per the
assignment's "no string-concatenated Cypher" requirement.
"""

# ---------------------------------------------------------------------
# Basic listing / detail queries
# ---------------------------------------------------------------------

LIST_RUNS = """
MATCH (r:Run)-[:EXECUTED]->(a:Agent)
RETURN r.id AS id, r.status AS status, r.started_at AS started_at,
       r.ended_at AS ended_at, r.trigger AS trigger,
       a.name AS primary_agent
ORDER BY r.started_at DESC
"""

GET_RUN_DETAIL = """
MATCH (r:Run {id: $run_id})-[:EXECUTED]->(primary:Agent)
MATCH (r)-[:INCLUDES]->(task:Task)
OPTIONAL MATCH (agent:Agent)-[:PERFORMED]->(task)
OPTIONAL MATCH (task)-[:DEPENDS_ON]->(prevTask:Task)
OPTIONAL MATCH (task)-[:CALLS]->(tool:Tool)
OPTIONAL MATCH (task)-[:PRODUCED]->(output:Output)
RETURN r.id AS run_id, r.status AS run_status, primary.name AS primary_agent,
       collect(DISTINCT {
         task_id: task.id,
         description: task.description,
         status: task.status,
         agent: agent.name,
         tool: tool.name,
         output_summary: output.summary,
         depends_on: prevTask.id
       }) AS tasks
"""

# ---------------------------------------------------------------------
# Multi-hop traversal: delegation chain (2+ hops)
# ---------------------------------------------------------------------
# Follows DELEGATES_TO relationships outward from a starting agent,
# 1 to 5 hops deep, to reveal the full chain of hand-offs.

DELEGATION_CHAIN = """
MATCH path = (start:Agent {id: $agent_id})-[:DELEGATES_TO*1..5]->(sub:Agent)
RETURN [node IN nodes(path) | {id: node.id, name: node.name, role: node.role}] AS chain,
       length(path) AS hops
ORDER BY hops
"""

# ---------------------------------------------------------------------
# Root-cause tracing: the "SQL would find this awkward" query
# ---------------------------------------------------------------------
# Starting from a failed task, walk backward through its DEPENDS_ON
# chain to find the EARLIEST upstream task that also failed and has
# a recorded error output. That earliest failure is the "root cause."

TRACE_FAILURE_ROOT_CAUSE = """
MATCH (start:Task {id: $task_id})
OPTIONAL MATCH path = (start)-[:DEPENDS_ON*0..5]->(upstream:Task)-[:FAILED_DUE_TO]->(o:Output)
WITH upstream, o, path
ORDER BY length(path) DESC
RETURN upstream.id AS root_cause_task_id,
       upstream.description AS root_cause_description,
       o.summary AS error_message,
       o.type AS error_type
LIMIT 1
"""

# ---------------------------------------------------------------------
# Shared root-cause clustering: tasks that failed for the SAME reason
# ---------------------------------------------------------------------
# In SQL this needs a recursive self-join; in Cypher it's one pattern.

SHARED_FAILURE_CLUSTERS = """
MATCH (t1:Task)-[:FAILED_DUE_TO]->(o:Output)<-[:FAILED_DUE_TO]-(t2:Task)
WHERE t1.id < t2.id
RETURN o.summary AS shared_error, o.id AS output_id,
       collect(DISTINCT t1.id) + collect(DISTINCT t2.id) AS affected_task_ids
"""

# ---------------------------------------------------------------------
# Health / debug
# ---------------------------------------------------------------------

COUNT_NODES_BY_LABEL = """
MATCH (n)
RETURN labels(n)[0] AS label, count(n) AS count
"""