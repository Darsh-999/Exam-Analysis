# ExamInsight — Frontend

React + Vite + Tailwind CSS frontend for ExamInsight.

## Prerequisites

- Node.js 18+ and npm
- The backend running locally (see [`../backend/README.md`](../backend/README.md)) — the frontend
  has no data of its own, every screen calls the backend API

## Setup

```
cd frontend
npm install
```

## Run the dev server

```
npm run dev
```

Opens on http://localhost:5173 (Vite picks the next free port if that one's taken). Every
`/api/...` call is proxied to the backend at `http://127.0.0.1:8000` (see `vite.config.js`) — make
sure the backend is running first, or screens will show a "couldn't load" error.

## Build for production

```
npm run build
```

Outputs static assets to `frontend/dist`. In production the backend serves this build directly
from the same origin, so no separate API base URL is needed — the app always calls relative
`/api/...` paths (see `.env.example`).

## Preview a production build locally

```
npm run preview
```

## Lint

```
npm run lint
```

## Project structure

- `src/pages/` — one folder per screen (Login, ProjectsDashboard, ProjectView, QuestionsView, TopicsView, TrendsView)
- `src/components/` — shared UI building blocks (Button, Modal, DataTable, StatCard, StatusBadge, LoadingState, ErrorState, ...)
- `src/services/` — one file per backend router; every API call goes through these
- `src/context/` — auth state (token + logged-in email, persisted to `localStorage`)
- `src/hooks/` — shared data-fetching (`useApiData`) and polling (`usePolling`) hooks
- `src/routes/` — route definitions + the protected-route guard

See [`BUILD_PLAN.md`](BUILD_PLAN.md) for the full build history and the decisions made along the way.
