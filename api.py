from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import tempfile
import os
import shutil
from dotenv import load_dotenv

load_dotenv()


from db.database import (
    get_connection, get_active_medications, get_lab_trend, get_all_vaccinations, get_allergies, get_visit_history
)
from ingestion.extractor import extract_text_or_image, extract_health_entities
from ingestion.vaccine_schedule import WHO_ADULT_SCHEDULE
from db.database import insert_medications, insert_lab_result
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


@app.get("/vaccination-status")
def vaccination_status():
    conn = get_connection()
    try:
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
        conn = get_connection()
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
        conn.close()
        return {
            "success": True,
            "document_type": entities.get("document_type"),
            "medications_saved": meds_saved,
            "labs_saved": labs_saved,
            "diagnoses": entities.get("diagnoses", []),
            "doctor_name": entities.get("doctor_name"),
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'tmp_path' in locals():
            os.unlink(tmp_path)