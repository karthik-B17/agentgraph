# AgentGraph — Backend

The backend API for **AgentGraph**, a debugging and observability tool for multi-agent AI systems.

The backend exposes a REST API built with **FastAPI** and uses the official **Neo4j Python driver** to communicate with **CognoDB Cloud** over the Bolt protocol.

AgentGraph stores agents, tasks, runs, tool calls, outputs, dependencies, and failures as a graph, allowing the API to answer multi-hop debugging and observability questions using openCypher.

---

## Responsibilities

The backend is responsible for:

* Exposing the AgentGraph REST API
* Connecting to CognoDB Cloud
* Executing parameterised Cypher queries
* Retrieving agent and run information
* Traversing task dependency chains
* Finding root causes of failures
* Identifying shared failure patterns
* Returning structured API responses
* Handling database connectivity failures gracefully
* Providing sample graph data through the seed script

---

## Tech Stack

* **Python**
* **FastAPI** — REST API framework
* **Pydantic** — Request/response models and configuration
* **Neo4j Python Driver** — Bolt connection and query execution
* **openCypher** — Graph query language
* **CognoDB Cloud** — Managed graph database

---

## Architecture

```text
┌─────────────────────┐
│   React + Vite      │
│      Frontend       │
└──────────┬──────────┘
           │
           │ HTTP / JSON
           ▼
┌─────────────────────┐
│     FastAPI API     │
│                     │
│  Routers            │
│  Pydantic Models    │
│  Configuration      │
└──────────┬──────────┘
           │
           │ Parameterised Cypher
           │ over Bolt
           ▼
┌─────────────────────┐
│    CognoDB Cloud    │
│   Graph Database    │
└─────────────────────┘
```

The backend is the only application layer that communicates directly with CognoDB.

---

## Project Structure

```text
backend/
├── README.md
├── requirements.txt
├── .env.example
├── test_connection.py
│
├── app/
│   ├── main.py
│   │   └── FastAPI application entry point,
│   │       routers and CORS configuration
│   │
│   ├── config.py
│   │   └── Environment configuration
│   │
│   ├── db.py
│   │   └── Neo4j driver and database session handling
│   │
│   ├── models.py
│   │   └── Pydantic API response models
│   │
│   ├── queries/
│   │   └── cypher.py
│   │       └── All Cypher queries used by the API
│   │
│   └── routers/
│       ├── runs.py
│       │   └── Run and execution endpoints
│       │
│       ├── agents.py
│       │   └── Agent-related endpoints
│       │
│       └── analytics.py
│           └── Root-cause and failure analytics
│
└── seed/
    └── seed_data.py
        └── Generates and loads sample graph data
```

---

## Database

AgentGraph uses **CognoDB Cloud**, a graph database that exposes an openCypher-compatible interface over Bolt.

The application uses the official Neo4j Python driver to communicate with the database.

The backend does not require Neo4j-specific database infrastructure locally.

---

## Data Model

The graph contains five primary node types.

| Node     | Purpose                                     |
| -------- | ------------------------------------------- |
| `Agent`  | An AI agent participating in a run          |
| `Tool`   | A tool that an agent task can invoke        |
| `Task`   | A unit of work performed by an agent        |
| `Run`    | An execution containing a sequence of tasks |
| `Output` | A result or error produced by a task        |

The primary relationships are:

| Relationship    | Meaning                                        |
| --------------- | ---------------------------------------------- |
| `EXECUTED`      | Run was started by an agent                    |
| `INCLUDES`      | Run contains a task                            |
| `PERFORMED`     | Agent performed a task                         |
| `DELEGATES_TO`  | Agent delegated work to another agent          |
| `DEPENDS_ON`    | Task depends on another task                   |
| `CALLS`         | Task invoked a tool                            |
| `PRODUCED`      | Task produced an output                        |
| `FAILED_DUE_TO` | Task failed because of a specific output/error |

---

## Configuration

Create a `.env` file from the provided example:

```bash
cp .env.example .env
```

Configure the CognoDB connection details:

```env
COGNODB_URI=bolt+s://<instance-id>.databases.cognodb.cloud
COGNODB_USERNAME=cognodb
COGNODB_PASSWORD=<your-password>
```

The exact variable names should match those defined in `.env.example`.

Do not commit the `.env` file to source control.

---

## Creating a CognoDB Instance

1. Create a free CognoDB Cloud account.
2. Create a free `c0` instance.
3. Select a region.
4. Copy the generated Bolt connection URI.
5. Save the database username and password.
6. Add the credentials to the backend `.env` file.

The database credentials are required before running the seed script or API.

---

## Installation

From the `backend` directory, create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Test Database Connectivity

Before starting the API, verify that the backend can connect to CognoDB:

```bash
python test_connection.py
```

This is useful for detecting configuration, authentication, network, or TLS problems before running the application.

---

## Seed Sample Data

AgentGraph includes a standalone seed script that creates realistic simulated agent execution data.

Run:

```bash
python seed/seed_data.py
```

The generated data represents:

* Multiple agents
* Agent delegation
* Multiple runs
* Task dependencies
* Tool calls
* Task outputs
* Failed tasks
* Shared failure outputs

The data is simulated because the project does not rely on real production agent logs.

---

## Start the API

Run the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI schema can also be inspected through FastAPI's generated documentation.

---

## API Structure

The API is divided into routers based on responsibility.

### Runs

`runs.py` handles run-level operations such as retrieving executions and their associated tasks.

A run represents one complete execution of an agent system.

### Agents

`agents.py` provides information about agents and their relationships, including delegation chains.

### Analytics

`analytics.py` contains graph-based observability operations such as:

* Root-cause tracing
* Failure analysis
* Shared failure detection
* Agent delegation analysis

---

## Graph Queries

All Cypher queries are stored in:

```text
app/queries/cypher.py
```

The API executes these queries through parameterised Neo4j driver calls.

No user input is directly concatenated into Cypher queries.

---

## Example Queries

### Multi-hop Agent Delegation

```cypher
MATCH path = (start:Agent {id: $agent_id})-[:DELEGATES_TO*1..5]->(sub:Agent)
RETURN [node IN nodes(path) |
  {id: node.id, name: node.name, role: node.role}
] AS chain,
length(path) AS hops
ORDER BY hops
```

This follows an agent's delegation chain for up to five hops.

---

### Root-Cause Tracing

```cypher
MATCH (start:Task {id: $task_id})
OPTIONAL MATCH path =
  (start)-[:DEPENDS_ON*0..5]->(upstream:Task)
  -[:FAILED_DUE_TO]->(o:Output)
WITH upstream, o, path
ORDER BY length(path) DESC
RETURN upstream.id AS root_cause_task_id,
       upstream.description AS root_cause_description,
       o.summary AS error_message,
       o.type AS error_type
LIMIT 1
```

This walks backward through task dependencies to locate the earliest known upstream failure.

---

### Shared Failure Detection

```cypher
MATCH (t1:Task)-[:FAILED_DUE_TO]->(o:Output)
      <-[:FAILED_DUE_TO]-(t2:Task)
WHERE t1.id < t2.id
RETURN o.summary AS shared_error,
       o.id AS output_id,
       collect(DISTINCT t1.id) +
       collect(DISTINCT t2.id) AS affected_task_ids
```

This identifies tasks that reference the same underlying failure output, allowing failures across otherwise unrelated runs to be clustered together.

---

## Important Data Modeling Decision

Tool calls and outputs are associated with **Tasks**, rather than directly with Agents.

This distinction is important because agents are reused across many runs.

For example:

```text
Agent A
 ├── Run 1
 │    └── Task 1
 │         └── Tool Call
 │
 └── Run 2
      └── Task 2
           └── Tool Call
```

If tool relationships were attached directly to `Agent A`, queries scoped to `Run 1` could accidentally include tool activity from `Run 2`.

The model therefore uses:

```text
Run ──INCLUDES──> Task
Agent ──PERFORMED──> Task
Task ──CALLS──> Tool
Task ──PRODUCED──> Output
```

This gives every task an explicit run context and prevents unrelated execution history from leaking into run-level queries.

---

## Error Handling

The backend is designed to handle database connectivity problems gracefully.

This is particularly useful because the API and database are hosted independently.

Possible causes of failures include:

* Invalid database credentials
* Incorrect Bolt URI
* Database instance unavailable
* Network connectivity problems
* TLS inspection
* Temporary cloud/database issues

---

## Troubleshooting

### TLS / Connection Reset

If you encounter an error such as:

```text
ConnectionResetError
```

or a Windows connection reset error such as:

```text
10054
```

check whether antivirus software is inspecting encrypted connections.

During development, antivirus SSL/TLS inspection can interfere with encrypted Bolt connections to CognoDB.

Try disabling encrypted-connection inspection temporarily or adding an exclusion for the CognoDB host.

---

### Slow First Request After Deployment

The backend is deployed on the Render free tier.

The service may sleep after a period of inactivity, so the first request after sleeping can take approximately 30–60 seconds while the service starts again.

This is expected behaviour for the free hosting tier.

---

### Endpoint Returns `Cannot GET`

Verify that the request is being sent to the correct deployed backend URL.

If multiple Render services exist, check which service is currently running the AgentGraph API and verify its `/health` endpoint.

---

## Deployment

The production architecture is:

```text
React Frontend
     │
     │ HTTPS
     ▼
Render
FastAPI Backend
     │
     │ Bolt
     ▼
CognoDB Cloud
```

The backend requires the CognoDB connection variables to be configured as environment variables in the hosting environment.

---

## Development Workflow

A typical local development workflow is:

```bash
# 1. Enter backend
cd backend

# 2. Activate environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Verify database connection
python test_connection.py

# 6. Load sample data
python seed/seed_data.py

# 7. Start API
uvicorn app.main:app --reload --port 8000
```

The frontend can then be started separately and configured to point to:

```text
http://127.0.0.1:8000
```

---

## Design Principles

### Graph-first debugging

AgentGraph uses the graph structure of multi-agent systems to answer questions about relationships and dependencies rather than treating logs as isolated records.

### Parameterised queries

All database queries use parameters rather than string concatenation.

### Separation of concerns

The backend is responsible for:

* API endpoints
* Database access
* Graph traversal
* Business logic

The frontend is responsible for:

* Visualization
* Navigation
* User interaction
* Presentation

### Explicit execution context

Tasks are explicitly connected to runs using:

```text
(Run)-[:INCLUDES]->(Task)
```

This keeps run-specific queries isolated even when agents are reused across many executions.

---

## Related Documentation

See the repository root `README.md` for the complete AgentGraph overview, architecture, data model, screenshots, and setup instructions.

See `frontend/README.md` for frontend development and deployment instructions.
