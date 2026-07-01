from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import tempfile
import os
import shutil
from dotenv import load_dotenv

load_dotenv()


from db.database import (
    get_connection, get_active_medications, get_lab_trend, get_all_vaccinations, get_allergies, get_visit_history,
    insert_medications, insert_lab_result, insert_allergy, check_duplicate, save_document_hash
)
from ingestion.extractor import extract_text_or_image, extract_health_entities, compute_file_hash
from ingestion.vaccine_schedule import WHO_ADULT_SCHEDULE
from logger import get_logger

logger = get_logger("medmemory.api")
app = FastAPI(title="MedMemory API")


#Allow Next.js dev server to call this API
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=['*'], allow_headers=['*'])


#-----------Routes--------------------
@app.get("/medications")
def get_medications():
    conn = get_connection()
    try:
        return {"medications" : get_active_medications(conn)}
    finally:
        conn.close()


@app.get("/lab-trend/{marker}")
def lab_trend(marker: str):
    conn = get_connection()
    try:
        return {"marker": marker, "readings": get_lab_trend(conn, marker)}
    finally:
        conn.close()


@app.get("/vaccinations")
def vaccinations():
    conn = get_connection()
    try:
        return {"vaccinations": get_all_vaccinations(conn)}
    finally:
        conn.close()


@app.get("/allergies")
def allergies():
    conn = get_connection()
    try:
        return {"allergies": get_allergies(conn)}
    finally:
        conn.close()


@app.get("/visits")
def visits(specialty: str = None):
    conn = get_connection()
    try:
        return {"visits": get_visit_history(conn, specialty)}
    finally:
        conn.close()


def _get_vaccination_status(conn):
    records = get_all_vaccinations(conn)

    # Keep the most recent record per vaccine
    received = {}
    for r in records:
        name_lower = r["vaccine_name"].lower()
        if name_lower not in received or r["date_administered"] > received[name_lower]["date_administered"]:
            received[name_lower] = r

    today = date.today()
    overdue = []
    missing = []

    for vaccine_name, schedule in WHO_ADULT_SCHEDULE.items():
        record = received.get(vaccine_name.lower())

        if record is None:
            missing.append({"vaccine": vaccine_name, "notes": schedule["notes"]})
        elif schedule["interval_years"] is not None:
            last_date = datetime.strptime(record["date_administered"], "%Y-%m-%d").date()
            years_since = (today - last_date).days / 365.25
            if years_since > schedule["interval_years"]:
                overdue.append({
                    "vaccine": vaccine_name,
                    "last_received": record["date_administered"],
                    "overdue_by_years": round(years_since - schedule["interval_years"], 1),
                    "notes": schedule["notes"],
                })

    return {
        "vaccinations_on_record": records,
        "overdue": overdue,
        "missing": missing,
    }


@app.get("/vaccination-status")
def vaccination_status():
    conn = get_connection()
    try:
        return _get_vaccination_status(conn)
    finally:
        conn.close()


@app.get("/dashboard")
def dashboard():
    conn = get_connection()
    try:
        # 1. Medications count
        meds = get_active_medications(conn)
        medication_count = len(meds)

        # 2. Lab markers count
        cursor = conn.execute("SELECT DISTINCT marker_name FROM lab_results")
        marker_count = len(cursor.fetchall())

        # 3. Pull the most recent abnormal lab value
        cursor = conn.execute(
            """SELECT marker_name, value, unit, reference_min, reference_max, test_date
               FROM lab_results
               WHERE (reference_min IS NOT NULL AND value < reference_min)
                  OR (reference_max IS NOT NULL AND value > reference_max)
               ORDER BY test_date DESC LIMIT 1"""
        )
        row = cursor.fetchone()
        abnormal_lab = dict(row) if row else None

        # 4. Upcoming follow-ups as a list (max 3)
        visits = get_visit_history(conn)
        pending_followups = [{
            "from_visit": v["visit_date"],
            "doctor": v["doctor_name"],
            "follow_up": v["follow_up"]
        } for v in visits
            if v.get("follow_up") and v["follow_up"].lower() != "none"
        ]

        # 5. Overdue/missing vaccines
        vacc_status = _get_vaccination_status(conn)
        overdue_vaccines = vacc_status.get("overdue", [])
        missing_vaccines = vacc_status.get("missing", [])
        overdue_vaccine_count = len(overdue_vaccines)
        vaccination_gap_count = overdue_vaccine_count + len(missing_vaccines)

        # 6. Last 3 documents ingested with timestamp and what was found
        cursor = conn.execute(
            """SELECT id, file_path, ingested_at
               FROM ingested_documents
               ORDER BY datetime(ingested_at) DESC LIMIT 3"""
        )
        recent_docs = []
        for doc_row in cursor.fetchall():
            doc = dict(doc_row)
            doc_path = doc["file_path"]
            doc_name = os.path.basename(doc_path)

            # Count meds, labs, vaccinations, visits extracted from this file
            med_count = conn.execute(
                "SELECT COUNT(*) FROM medications WHERE source_document = ? OR source_document = ?",
                (doc_path, doc_name)
            ).fetchone()[0]

            lab_count = conn.execute(
                "SELECT COUNT(*) FROM lab_results WHERE source_document = ? OR source_document = ?",
                (doc_path, doc_name)
            ).fetchone()[0]

            vacc_count = conn.execute(
                "SELECT COUNT(*) FROM vaccinations WHERE source_document = ? OR source_document = ?",
                (doc_path, doc_name)
            ).fetchone()[0]

            visit_count = conn.execute(
                "SELECT COUNT(*) FROM visits WHERE source_document = ? OR source_document = ?",
                (doc_path, doc_name)
            ).fetchone()[0]

            found_items = []
            if med_count > 0:
                found_items.append(f"{med_count} medication{'s' if med_count > 1 else ''}")
            if lab_count > 0:
                found_items.append(f"{lab_count} lab result{'s' if lab_count > 1 else ''}")
            if vacc_count > 0:
                found_items.append(f"{vacc_count} vaccination{'s' if vacc_count > 1 else ''}")
            if visit_count > 0:
                found_items.append(f"{visit_count} visit record{'s' if visit_count > 1 else ''}")

            what_was_found = ", ".join(found_items) if found_items else "No health entities extracted"

            recent_docs.append({
                "id": doc["id"],
                "file_name": doc_name,
                "ingested_at": doc["ingested_at"],
                "what_was_found": what_was_found
            })

        return {
            "medication_count": medication_count,
            "marker_count": marker_count,
            "abnormal_lab": abnormal_lab,
            "pending_followups": pending_followups[:3],
            "overdue_vaccine_count": overdue_vaccine_count,
            "vaccination_gap_count": vaccination_gap_count,
            "recent_documents": recent_docs
        }
    finally:
        conn.close()


@app.get("/lab-markers")
def lab_markers():
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT DISTINCT marker_name FROM lab_results ORDER BY marker_name ASC"
        )
        return {"markers": [row["marker_name"] for row in cursor.fetchall()]}
    finally:
        conn.close()


@app.get("/summary")
def summary():
    conn = get_connection()
    try:
        medications = get_active_medications(conn)
        visits = get_visit_history(conn)
        vaccinations = get_all_vaccinations(conn)
        allergies = get_allergies(conn)

        # Get the most recent reading for common lab markers
        common_markers = ["HbA1c", "TSH", "creatinine", "hemoglobin",
                           "cholesterol", "blood pressure", "fasting glucose"]
        recent_labs = {}
        for marker in common_markers:
            trend = get_lab_trend(conn, marker)
            if trend:
                recent_labs[marker] = trend[-1]

        pending_followups = [{
            "from_visit": v["visit_date"],
            "doctor": v["doctor_name"],
            "follow_up": v["follow_up"]
        } for v in visits
            if v.get("follow_up") and v["follow_up"].lower() != "none"
        ]

        # Most recent visit per speciality
        seen_specialities = set()
        recent_visits = []
        for v in visits:
            if v["speciality"] not in seen_specialities:
                seen_specialities.add(v["speciality"])
                recent_visits.append(v)

        return {
            "generated_on": date.today().isoformat(),
            "active_medications": medications,
            "known_allergies": allergies,
            "recent_lab_results": recent_labs,
            "recent_visits_by_specialty": recent_visits,
            "vaccinations_on_record": vaccinations,
            "pending_follow_ups": pending_followups,
            "disclaimer": (
                "This summary is generated from personally stored health records. "
                "Always verify with your healthcare provider before making medical decisions."
            )
        }
    finally:
        conn.close()


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    # Save upload to temp file then process
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        content, mode, warnings = extract_text_or_image(tmp_path)
        if warnings:
            logger.warning(f"Extraction warnings: {warnings}")
        entities = extract_health_entities(content, mode)
        
        file_hash = compute_file_hash(tmp_path)
        conn = get_connection()
        try:
            existing = check_duplicate(conn, file_hash)
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"This document was already ingested on {existing['ingested_at']}."
                )
            
            meds_saved = 0
            labs_saved = 0
            for med in entities.get("medications", []):
                if med.get("drug_name"):
                    insert_medications(conn, {
                        "drug_name": med["drug_name"],
                        "dose": med.get("dose"),
                        "frequency": med.get("frequency"),
                        "condition_treated": med.get("condition_treated"),
                        "is_active": 1,
                        "start_date": entities.get("document_date"),
                        "source_document": file.filename,
                    })
                    meds_saved += 1
            for lab in entities.get("lab_results", []):
                if lab.get("marker_name") and lab.get("value") is not None:
                    insert_lab_result(conn, {
                        "marker_name": lab["marker_name"],
                        "value": lab["value"],
                        "unit": lab.get("unit"),
                        "test_date": entities.get("document_date"),
                        "source_document": file.filename,
                    })
                    labs_saved += 1
            
            allergies_saved = 0
            for allergen_entry in entities.get("allergies", []):
                if allergen_entry:
                    allergen_text = allergen_entry if isinstance(allergen_entry, str) else allergen_entry.get("allergen", "")
                    if allergen_text:
                        insert_allergy(conn, {
                            "allergen": allergen_text,
                            "reaction": allergen_entry.get("reaction") if isinstance(allergen_entry, dict) else None,
                            "severity": allergen_entry.get("severity") if isinstance(allergen_entry, dict) else None,
                            "noted_date": entities.get("document_date"),
                        })
                        allergies_saved += 1

            save_document_hash(conn, file_hash, file.filename)
            
            return {
                "success": True,
                "document_type": entities.get("document_type"),
                "medications_saved": meds_saved,
                "labs_saved": labs_saved,
                "allergies_saved": allergies_saved,
                "diagnoses": entities.get("diagnoses", []),
                "doctor_name": entities.get("doctor_name"),
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals():
            os.unlink(tmp_path)