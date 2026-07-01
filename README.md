# MedMemory MCP

A personal health records server for Claude Desktop. Store and query your medications, lab results, visit history, vaccinations, and allergies — all encrypted locally on your machine.

## Quick start

```bash
# Install dependencies
uv sync

# First-run setup (creates the encrypted database)
python setup.py
```

Follow the on-screen instructions to choose a passphrase and connect to Claude Desktop.

## What you can ask Claude

- "What medications am I on?"
- "Show me my HbA1c trend over the past year."
- "When was my last cardiology visit?"
- "Do I have any drug allergies?"
- "Am I up to date on my vaccines?"

## Ingesting documents

Pass a PDF or image path to the `ingest_document` tool, or ask Claude:

> "Ingest this prescription: /path/to/prescription.pdf"

Supported formats: PDF, JPG, PNG (including handwritten documents via Gemini Vision).

## Privacy

Your health data never leaves your machine. The database is encrypted with SQLCipher using the passphrase you set during setup.

See [PRIVACY.md](PRIVACY.md) for the full breakdown of what goes where.

**Encryption proof** — run this in the project directory:

```
xxd db/medmemory.db | head -3
```

An encrypted database shows random bytes. An unencrypted SQLite file would start with `SQLite format 3`. You should see something like:

```
00000000: b88d 0a2e 4f93 7c21 d301 9a55 f02b 3e1c  ....O.|!...U.+>.
00000010: 8a74 c2d8 3f51 0b66 e9a2 4c37 1d84 5f20  .t..?Q.f..L7.._ 
00000020: 29fc 6b38 e047 02da 5571 93bc 7e1a 0d84  ).k8.G..Uq..~...
```

No recognisable text. That is what encryption looks like.
