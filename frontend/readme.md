# AgentGraph — Frontend

The frontend for **AgentGraph**, a debugging and observability dashboard for multi-agent AI systems.

It provides a visual interface for exploring agent runs, tracing task dependencies, identifying root causes, and discovering recurring failure patterns across runs.

The frontend is built with **React + Vite** and communicates with the AgentGraph backend through a REST API.

---

## Features

### Dashboard

Provides a high-level overview of the agent system, including:

* Total runs
* Successful and failed runs
* Agent activity
* Recent executions
* Failure statistics

### Run Explorer

Explore an individual agent run and its execution flow.

The run explorer shows:

* The agents involved in the run
* Tasks performed by each agent
* Agent delegation chains
* Task dependencies
* Tool calls
* Generated outputs
* Failed tasks
* Root-cause information

The dependency chain makes it possible to trace a downstream failure back to the upstream task that originally caused it.

### Failure Patterns

Groups failures that share the same underlying output/error.

This makes it possible to identify situations such as:

> Multiple unrelated runs failing because the same external tool or service was unavailable.

---

## Tech Stack

* **React** — UI framework
* **Vite** — Development server and build tooling
* **React Router** — Client-side routing
* **Axios** — HTTP client
* **CSS** — Application styling

---

## Project Structure

```text
frontend/
├── README.md
├── package.json
├── .env.example
├── index.html
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    │
    ├── api/
    │   └── client.js
    │       └── Centralised backend API requests
    │
    ├── styles/
    │   └── global.css
    │       └── Design tokens, layout and global styles
    │
    ├── components/
    │   ├── Layout
    │   ├── StatusPill
    │   ├── LoadingState
    │   ├── EmptyState
    │   └── ErrorState
    │
    └── pages/
        ├── Dashboard.jsx
        ├── RunExplorer.jsx
        └── FailurePatterns.jsx
```

---

## Architecture

The frontend is intentionally kept separate from the database.

```text
┌──────────────────────┐
│      React App       │
│                      │
│  Dashboard           │
│  Run Explorer        │
│  Failure Patterns    │
└──────────┬───────────┘
           │
           │ HTTP / JSON
           ▼
┌──────────────────────┐
│    AgentGraph API    │
│   FastAPI Backend    │
└──────────────────────┘
```

The frontend does not communicate directly with CognoDB. All database access happens through the backend API.

---

## Configuration

Create a `.env` file from the provided example:

```bash
cp .env.example .env
```

Set the backend API URL:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For a deployed application, replace this with the deployed backend URL.

For example:

```env
VITE_API_BASE_URL=https://your-agentgraph-api.example.com
```

---

## Local Development

### 1. Install dependencies

From the `frontend` directory:

```bash
npm install
```

### 2. Configure the backend URL

```bash
cp .env.example .env
```

Then configure:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Make sure the backend is running before opening the application.

### 3. Start the development server

```bash
npm run dev
```

Vite will print the local development URL, typically:

```text
http://localhost:5173
```

---

## Production Build

Create an optimized production build:

```bash
npm run build
```

The generated files are placed in the Vite `dist/` directory.

To preview the production build locally:

```bash
npm run preview
```

---

## API Communication

All backend communication is centralised in:

```text
src/api/client.js
```

This keeps API requests separate from UI components and pages.

The frontend expects the backend to expose endpoints for areas such as:

* Runs
* Agents
* Analytics
* Root-cause analysis
* Failure patterns

The exact API implementation lives in the `backend` directory.

---

## Pages

### `/`

The main dashboard providing a system-level overview.

### `/runs/:id`

The Run Explorer for investigating a specific execution.

It provides the detailed context needed to understand how an agent run progressed and where a failure originated.

### `/failures`

The Failure Patterns view for identifying shared root causes across multiple tasks and runs.

---

## Error Handling

The frontend includes reusable states for:

* Loading data
* Empty results
* API failures
* Missing resources

This allows the application to remain usable even when the backend or database is temporarily unavailable.

---

## Deployment

The frontend can be deployed as a static Vite application.

The production architecture used by AgentGraph is:

```text
React + Vite
      │
      ▼
   Netlify
      │
      │ HTTPS / JSON
      ▼
FastAPI Backend
```

Before deploying, configure:

```env
VITE_API_BASE_URL=<deployed-backend-url>
```

Then build the application:

```bash
npm run build
```

---

## Development Notes

The frontend intentionally treats the backend API as the source of truth.

It does not contain database queries or CognoDB-specific logic. This separation allows the UI to focus on:

* Data presentation
* Navigation
* Visualization
* User interaction
* Loading and error states

while the backend handles graph traversal and data access.

---

## Related Documentation

See the repository root `README.md` for the complete AgentGraph architecture, data model, graph queries, and deployment overview.

See `backend/README.md` for backend setup and API documentation.
