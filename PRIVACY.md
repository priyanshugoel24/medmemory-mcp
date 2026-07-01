# Privacy & Data Storage

MedMemory stores your health records locally on your machine. This document explains exactly what stays private, what leaves your device, and how you can verify each claim yourself.

---

## What stays on your machine

Everything. Your health records — medications, lab results, visit notes, vaccinations, allergies — are stored only in the encrypted database file at `db/medmemory.db`. This file never leaves your computer unless you copy it yourself.

## What goes to the Gemini API

When you **ingest a document** (a prescription, lab report, discharge summary), the text extracted from that document is sent to Google's Gemini API so it can be understood and structured. Gemini does not receive your existing health history — only the raw text of the document you are currently importing.

Once ingestion is complete, the extracted data is saved to your local database and nothing further is sent to Gemini.

## What never leaves your machine

- **Your encryption passphrase** — stored only in the `.env` file on your machine. It is never transmitted anywhere.
- **Your database file** (`db/medmemory.db`) — encrypted at rest with SQLCipher. Without the passphrase, the file is unreadable.

## What Anthropic sees

When you ask Claude Desktop questions like "What medications am I on?", Claude calls MedMemory's tools to fetch data from your local database and includes the results in your conversation. Anthropic can see these tool calls and responses in the same way it can see any other message in a Claude Desktop conversation — no more, no less.

## How to verify the database is encrypted

Run this command in your terminal from the project directory:

```
xxd db/medmemory.db | head -3
```

You should see random-looking bytes — **not** the string `SQLite format 3` that an unencrypted SQLite file would show. That confirms the file is encrypted and unreadable without the passphrase.

## How to verify Gemini only receives document text

Open [`ingestion/extractor.py`](ingestion/extractor.py) and search for the Gemini API call. You will see that only the extracted document content is passed to the model — no database rows, no existing health history, no personal identifiers beyond what is already in the document you uploaded.
