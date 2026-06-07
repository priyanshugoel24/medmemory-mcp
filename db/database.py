import sqlite3
from pathlib import Path

#Always store the DB next to this file
DB_PATH = Path(__file__).parent / "medmemory.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def get_connection() -> sqlite3.Connection:
    """Open a connection to the Medmemory database.
    Creates the DB and schema on first run.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row #access columns by name, not index
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn)
    return conn

def _ensure_schema(conn : sqlite3.Connection) -> None :
    """Create tables if they don't exist yet."""
    schema = SCHEMA_PATH.read_text()
    conn.executescript(schema)
    conn.commit()

#-------------Medications------------------------

def insert_medications(conn : sqlite3.Connection, data : dict) -> int:

    """Insert a medication record. Returns the new row id."""

    cursor = conn.execute(
        """
        INSERT INTO medications(drug_name,dose,frequency,condition_treated,
        prescriber,is_active,start_date,end_date,source_document)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            data.get("drug_name"),
            data.get("dose"),
            data.get("frequency"),
            data.get("condition_treated"),
            data.get("prescriber"),
            data.get("is_active"),
            data.get("start_date"),
            data.get("end_date"),
            data.get("source_document")
        )
        )

    conn.commit()
    return cursor.lastrowid

def get_active_medications(conn : sqlite3.Connection)->list[dict]:
    """Return all currently active medications as a list of dicts."""

    cursor = conn.execute(
        """SELECT drug_name, dose, frequency, condition_treated, prescriber, start_date FROM medications WHERE is_active = 1
        ORDER BY start_date DESC"""
    )
    return [dict(row) for row in cursor.fetchall()]

#----------------Lab Results-----------------
def insert_lab_result(conn : sqlite3.Connection, data : dict) -> int:
    """Insert a lab result record. Return the new row id."""

    cursor = conn.execute(
        """
        INSERT INTO lab_results(marker_name, value, unit, reference_min, reference_max, test_date, lab_name, source_document)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("marker_name"),
            data.get("value"),
            data.get("unit"),
            data.get("reference_min"),
            data.get("reference_max"),
            data.get("test_date"),
            data.get("lab_name"),
            data.get("source_document")
        )
    )
    conn.commit()
    return cursor.lastrowid

def get_lab_trend(conn: sqlite3.Connection, marker_name: str) -> list[dict]:
    """Return all readings for a lab marker, oldest first."""
    cursor = conn.execute(
    """SELECT marker_name, value, unit, reference_min,
    reference_max, test_date, lab_name
    FROM lab_results
    WHERE LOWER(marker_name) = LOWER(?)
    ORDER BY test_date ASC""",
    (marker_name,)
    )
    return [dict(row) for row in cursor.fetchall()]