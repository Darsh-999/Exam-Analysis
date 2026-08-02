# ExamInsight — Frontend

React + Vite + Tailwind CSS frontend for ExamInsight.

## Prerequisites

- Node.js 20+ and npm — Vite 8 (via rolldown) 
- The backend running locally (see [`../backend/README.md`](../backend/README.md)) — the frontend
  has no data of its own, every screen calls the backend API

## Installing Node.js (fresh machine / RunPod pod)

Runpods default `apt` package is `nodejs 18.19.1`, which is too old for this project Install Node 22 LTS

```
curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh
sudo bash /tmp/nodesource_setup.sh
sudo apt-get install -y nodejs
node -v   # v22.x
npm -v
```

If `nodejs`/`npm` were already installed from Ubuntu's default repo, remove them first

```
sudo apt-get remove -y nodejs npm
```

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
`/api/...` call is proxied to the backend at `http://127.0.0.1:8080` (see `vite.config.js`) — make
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
