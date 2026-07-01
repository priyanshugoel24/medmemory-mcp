"""First-run setup for MedMemory MCP.

Run once to create the encrypted database and write your passphrase to .env.
"""

import os
import sys
import getpass
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = ROOT / "db" / "medmemory.db"
ENV_PATH = ROOT / ".env"


def _update_env_key(passphrase: str) -> None:
    """Write MEDMEMORY_DB_KEY into .env, updating the line if it already exists."""
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    key_line = f"MEDMEMORY_DB_KEY={passphrase}"
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("MEDMEMORY_DB_KEY="):
            lines[i] = key_line
            updated = True
            break
    if not updated:
        lines.append(key_line)
    ENV_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    if DB_PATH.exists():
        print("MedMemory is already set up. Run seed_data.py to reset your database.")
        sys.exit(0)

    print("MedMemory first-run setup")
    print("=" * 40)
    print("Your health data will be stored in an encrypted SQLite database.")
    print("Choose a strong passphrase — you will need it every time the server starts.")
    print()

    while True:
        passphrase = getpass.getpass("Enter passphrase: ")
        if len(passphrase) < 8:
            print("Passphrase must be at least 8 characters. Try again.")
            continue
        confirm = getpass.getpass("Confirm passphrase: ")
        if passphrase != confirm:
            print("Passphrases do not match. Try again.")
            continue
        break

    print()
    print("Writing passphrase to .env ...")
    _update_env_key(passphrase)

    print("Initialising encrypted database ...")
    # Import after .env is written so get_connection() picks up the new key
    from dotenv import load_dotenv
    load_dotenv(override=True)
    from db.database import get_connection
    conn = get_connection()
    conn.close()

    print()
    print("=" * 40)
    print("Setup complete.")
    print()
    print("To connect to Claude Desktop, add this to your claude_desktop_config.json:")
    print()
    config_path = ROOT.resolve()
    print('  {')
    print('    "mcpServers": {')
    print('      "medmemory": {')
    print('        "command": "uv",')
    print(f'        "args": ["--directory", "{config_path}", "run", "python", "server.py"]')
    print('      }')
    print('    }')
    print('  }')
    print()
    print("Then restart Claude Desktop and ask: 'What medications am I on?'")


if __name__ == "__main__":
    main()
