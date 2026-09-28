# Deployment Guide (Vercel frontend + separate backend)

## Why the deployed site felt slow (or hung) on PDF upload

Two independent problems:

1. **`POST /api/graph/ontology/generate` used to be fully synchronous.**
   PDF text extraction plus a single large LLM call (up to ~50k chars of
   document context) ran inside the HTTP request. The frontend waited with a
   5-minute axios timeout and showed only a static "analyzing..." message.

   **Fixed:** the endpoint now persists the uploaded files, queues an ontology
   task, and returns immediately with `project_id` + `task_id`. The frontend
   polls `/api/graph/task/<task_id>` (2s interval) and shows live progress;
   when the ontology completes, the graph build starts automatically exactly
   as before.

2. **The production bundle called `http://localhost:5001` directly.**
   `frontend/src/api/index.js` hardcoded the dev backend as the default base
   URL, so the deployed frontend could only work while a local backend was
   running on your machine.

   **Fixed:** the axios client now defaults to same-origin (`''`). Local
   development keeps working because the Vite dev server proxies `/api` to
   `localhost:5001` (see `frontend/vite.config.js`). For production, point the
   frontend at your backend with an env var (below).

## Environment variables

### Frontend (Vercel project settings)

| Variable            | Required | Example                          |
|---------------------|----------|----------------------------------|
| `VITE_API_BASE_URL` | yes (prod) | `https://your-backend.example.com` |

- Local dev: leave unset. Vite's `/api` proxy handles it.
- Production: set it to the public HTTPS URL of your Flask backend
  (e.g. a VM, Fly.io, Render, Railway...). The backend enables CORS for all
  origins on `/api/*`, so cross-origin calls work out of the box.
- Direct calls (instead of a Vercel rewrite) also avoid Vercel's ~4.5 MB
  serverless request-body limit; the backend accepts uploads up to 50 MB.

### Backend (wherever you run it)

Same variables as documented in the root `README.md` / `.env.example`:
`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL_NAME`, `ZEP_API_KEY`, and optionally
`FLASK_HOST` / `FLASK_PORT`.

## Running locally

```bash
# terminal 1 - backend
cd backend
uv sync                      # or: pip install -r requirements.txt
uv run python run.py         # serves http://localhost:5001 (activates .venv)

# terminal 2 - frontend
cd frontend
npm ci
npm run dev                  # serves http://localhost:3000, proxies /api
```

## Verifying the async flow

```bash
# 1. Upload (returns immediately with a task_id)
curl -s -X POST https://your-backend/api/graph/ontology/generate \
  -F files=@report.pdf \
  -F simulation_requirement="Simulate public opinion" | jq

# 2. Poll the task until status is "completed"
curl -s https://your-backend/api/graph/task/task_xxxx | jq '.data.status,.data.progress,.data.message'
```

Expected timings: upload + text extraction return in a few seconds; the
ontology task typically completes in 1–3 minutes depending on your LLM
provider; the graph build stage was already async and unchanged.

## Troubleshooting "slow PDF" after deploying

- **Requests fail instantly with 404 / Network Error on the Vercel domain:**
  `VITE_API_BASE_URL` is not set (or the frontend was built before setting
  it). Redeploy after adding it.
- **CORS errors in the browser console:** the backend must be reachable over
  HTTPS from the browser. `zep-cloud`/Flask only on `http://localhost` will
  not work from a public site.
- **Task stuck at "processing" or poll returns 404:** the ontology task state
  lives in backend process memory. If the backend restarts or you run multiple
  workers, a queued task can be lost. Re-submitting the same documents +
  simulation requirement on `/process/new` detects the orphaned pending
  project, marks it failed, and lets you retry cleanly. For production, run a
  single backend worker or add persistent task storage.
- **Scanned/image-only PDFs:** PyMuPDF extracts embedded text only; scanned
  image PDFs yield no text and are rejected at upload with "No documents were
  processed successfully". Run OCR before uploading.
