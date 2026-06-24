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





#----------Visits--------------

def insert_visit(conn : sqlite3.Connection, data : dict) -> int:
    """Insert a doctor visit record. Returns the new row id."""
    cursor = conn.execute(
        """INSERT INTO visits(visit_date, speciality, doctor_name, diagnosis, notes, follow_up, source_document) VALUES (?, ? , ? , ? , ? , ? , ?)""",
        (
            data.get("visit_date"),
            data.get("speciality") or data.get("specialty"),
            data.get("doctor_name"),
            data.get("diagnosis"),
            data.get("notes"),
            data.get("follow_up"),
            data.get("source_document"),
        )
    )
    conn.commit()
    return cursor.lastrowid

def get_visit_history(conn : sqlite3.Connection, speciality : str | None = None) -> list[dict]:
    """Return all visits, newest first. Optionally filter by speciality (case-insensitive)."""

    if speciality:
        cursor = conn.execute(
            """SELECT visit_date, speciality, doctor_name, diagnosis, notes, follow_up FROM visits WHERE LOWER(speciality) LIKE LOWER(?) ORDER BY visit_date DESC""",
            (f"%{speciality}%",)
        )
    else :
        cursor = conn.execute(
            """SELECT visit_date, speciality, doctor_name, diagnosis, notes, follow_up FROM visits ORDER BY visit_date DESC"""
        )

    return [dict(row) for row in cursor.fetchall()]




# ── Vaccinations ─────────────────────────────────────────

def insert_vaccination(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a vaccination record. Returns the new row id."""
    cursor = conn.execute(
        """INSERT INTO vaccinations
        (vaccine_name, date_administered, dose_number,
        provider, source_document)
        VALUES (?, ?, ?, ?, ?)""",
        (
            data.get("vaccine_name"),
            data.get("date_administered"),
            data.get("dose_number", 1),
            data.get("provider"),
            data.get("source_document"),
        )
    )
    conn.commit()
    return cursor.lastrowid


def get_all_vaccinations(conn: sqlite3.Connection) -> list[dict]:
    """Return all vaccination records, newest first."""
    cursor = conn.execute(
        """SELECT vaccine_name, date_administered,
        dose_number, provider
        FROM vaccinations
        ORDER BY date_administered DESC"""
    )
    return [dict(row) for row in cursor.fetchall()]


# ── Allergies ─────────────────────────────────────────────

def insert_allergy(conn: sqlite3.Connection, data: dict) -> int:
    """Insert an allergy record. Returns the new row id."""
    cursor = conn.execute(
        """INSERT INTO allergies(allergen, reaction, severity, noted_date)
        VALUES (?, ?, ?, ?)""",
        (
            data.get("allergen"),
            data.get("reaction"),
            data.get("severity"),
            data.get("noted_date"),
        )
    )
    conn.commit()
    return cursor.lastrowid


def get_allergies(conn: sqlite3.Connection) -> list[dict]:
    """Return all allergy records."""
    cursor = conn.execute(
        """SELECT allergen, reaction, severity, noted_date
        FROM allergies
        ORDER BY noted_date DESC"""
    )
    return [dict(row) for row in cursor.fetchall()]


# ── Duplicate document detection ──────────────────────────

def check_duplicate(conn: sqlite3.Connection, file_hash: str) -> dict | None:
    """Return the existing document record if this hash was already ingested, else None."""
    cursor = conn.execute(
        "SELECT file_hash, file_path, ingested_at FROM ingested_documents WHERE file_hash = ?",
        (file_hash,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def save_document_hash(conn: sqlite3.Connection, file_hash: str, file_path: str) -> None:
    """Record a successfully ingested document hash."""
    conn.execute(
        "INSERT INTO ingested_documents(file_hash, file_path) VALUES (?, ?)",
        (file_hash, file_path)
    )
    conn.commit()
