# UrjaSarathi frontend

The frontend uses the FastAPI backend by default.

## Local run

Start the backend from the repository root:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

Then start the interface in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite proxy forwards `/api` to
`http://127.0.0.1:8000`.

## Configuration

- `VITE_API_URL=/api` uses the local Vite proxy.
- `VITE_MOCK_MODE=false` uses real backend data and is the default.
- `VITE_MOCK_MODE=true` enables the explicit frontend-only demonstration mode.

Copy `.env.example` to `.env` only when an override is needed.

## Validation

```powershell
npm run typecheck
npm run build
```

The interface is a simulated decision-support prototype and does not control real
devices or a live electricity grid.
