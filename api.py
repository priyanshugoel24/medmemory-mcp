from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import shutil
from dotenv import load_dotenv

load_dotenv()


from db.database import (
    get_connection, get_active_medications, get_lab_trend, get_all_vaccinations, get_allergies, get_visit_history
)
from ingestion.extractor import extract_text_or_image, extract_health_entities
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