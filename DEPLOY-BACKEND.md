# Deploying the MiroFish backend

The app is split in two:

| Part | Host | Why |
|---|---|---|
| Frontend (Vue 3 + Vite) | **Vercel** | Already live at <https://mirofish-omega.vercel.app> |
| Backend (Flask + camel-oasis) | **A container host** | Vercel Functions can't run it (see below) |

## Why the backend isn't on Vercel

- **Long-running work.** Simulations run for many rounds, with subprocess IPC
  (`backend/app/services/simulation_ipc.py`). Vercel Functions have a hard max
  duration and no persistent background processes.
- **Bundle size.** The `camel-ai` / `camel-oasis` dependency tree makes the
  250 MB unzipped function limit unlikely to fit.
- **Ephemeral filesystem.** Uploads and simulation data are written to disk.

## Required environment variables

Copy `.env.example` and fill these in:

| Variable | Required | Notes |
|---|---|---|
| `LLM_API_KEY` | ✅ | Any OpenAI-compatible provider |
| `LLM_BASE_URL` | ✅ | e.g. `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL_NAME` | ✅ | e.g. `qwen-plus` |
| `ZEP_API_KEY` | ✅ | <https://app.getzep.com/> |

`backend/run.py` calls `Config.validate()` on boot and exits if `LLM_API_KEY` or
`ZEP_API_KEY` is missing, so the service will not start without them.

## Option A — Render (Blueprint)

`render.yaml` is included.

1. Render → **New → Blueprint** → pick this repo.
2. Set `LLM_API_KEY` and `ZEP_API_KEY` when prompted.
3. Deploy. Health check: `GET /health` → `{"status":"ok"}`.

## Option B — Railway

`railway.json` is included.

```bash
railway init
railway up
railway variables --set LLM_API_KEY=... --set ZEP_API_KEY=...
```

## Option C — Fly.io

`fly.toml` is included (Singapore region, 2 GB RAM — `camel-ai` needs it).

```bash
fly launch --no-deploy --copy-config
fly secrets set LLM_API_KEY=... ZEP_API_KEY=...
fly deploy
```

## Option D — any Docker host (Cloud Run, ECS, a VPS…)

The repo's `Dockerfile` builds both runtimes. Override the default CMD
(which runs the dev frontend + backend together) so only the API serves:

```bash
docker build -t mirofish-backend .
docker run -p 5001:5001 \
  -e LLM_API_KEY=... -e ZEP_API_KEY=... \
  mirofish-backend \
  bash -lc "cd backend && uv run python run.py"
```

`run.py` listens on `$PORT` when the platform injects one, otherwise `5001`
(or an explicit `FLASK_PORT`).

## Wire the frontend to the backend

Once the backend is reachable at `https://<your-backend-host>`:

1. Vercel → project **mirofish** → **Settings → Environment Variables**
2. Add `VITE_API_BASE_URL = https://<your-backend-host>` (Production + Preview)
3. Redeploy: `vercel deploy --prod --yes` (from the repo root)

The frontend reads `VITE_API_BASE_URL` in `frontend/src/api/index.js` and falls
back to `http://localhost:5001`. CORS is already open for `/api/*`
(`backend/app/__init__.py`), so no extra origin config is needed.

## API surface

| Prefix | Blueprint |
|---|---|
| `/api/graph` | graph building |
| `/api/simulation` | simulation lifecycle |
| `/api/report` | report generation & agent chat |
| `/health` | liveness probe |
