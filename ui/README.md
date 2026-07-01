# MedMemory Web UI

A Next.js companion app for [MedMemory](../README.md), for people without Claude Desktop / MCP access. It talks to the FastAPI bridge (`api.py`) over HTTP; the bridge handles the encrypted SQLCipher database transparently.

## Running locally

You need two processes running at the same time: the FastAPI bridge and the Next.js dev server.

**1. Start the FastAPI bridge** (from the project root, not `ui/`):

```bash
uv run uvicorn api:app --reload --port 8000
```

**2. Start the Next.js dev server** (from `ui/`):

```bash
npm install   # first time only
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

`ui/.env.local` points the frontend at the bridge:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Pages

- `/` — dashboard with record summary counts and quick links
- `/upload` — drag-and-drop document ingestion (PDF, PNG, JPG)
- `/medications` — active medications table
- `/labs` — lab marker trend chart with reference range and readings table
- `/summary` — printable health summary for sharing with a doctor

## Notes

- All styling is Tailwind CSS v4, no component library.
- Charts use Recharts.
- The UI never talks to the encrypted database directly — everything goes through `api.py`.
