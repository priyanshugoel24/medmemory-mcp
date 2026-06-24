from datetime import date
from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from mcp.server.fastmcp import FastMCP, Context
from db.database import (
    get_connection,
    get_active_medications,
    get_lab_trend as db_get_lab_trend,
    insert_medications,
    insert_lab_result,
    insert_visit,
    get_visit_history as db_get_visit_history,
    insert_vaccination,
    get_all_vaccinations,
    insert_allergy,
    get_allergies as db_get_allergies,
    check_duplicate,
    save_document_hash,
)
from ingestion.extractor import extract_text_or_image, extract_health_entities, compute_file_hash
from ingestion.vaccine_schedule import WHO_ADULT_SCHEDULE
import httpx
import os
from logger import get_logger

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}



logger = get_logger("medmemory.server")


@asynccontextmanager
async def app_lifespan(server : FastMCP) -> AsyncIterator[dict]:
    """Open DB on startup, close on shutdown."""
    
    conn = get_connection()
    try:
        yield{"db" : conn}
    finally:
        conn.close()


mcp = FastMCP("MedMemory", lifespan = app_lifespan)

@mcp.tool()
async def get_current_medications(ctx : Context) -> list[dict]:
    """Returns all currently active medications for the patient.

    Use this when the user asks what medications they are taking, what drugs they are currently on, or what their current prescriptions are. Filters out completed medication courses automatically."""

    logger.info("get_current_medications called")
    db = ctx.request_context.lifespan_context["db"]
    medications = get_active_medications(db)


    if not medications:
        return [{"message" : "No active medications found in the database."}]


    logger.info(f"get_current_medications → {len(medications)} active medications")
    return medications

@mcp.tool()
async def get_lab_trend(ctx : Context, marker_name : str) -> list[dict]:

    """Returns a list of all readings for that marker, oldest first.

    Use this when the user asks about trends, progress, changes over time, historical readings or whether something is getting better or worse for a specific lab marker.
    """

    logger.info(f"get_lab_trend called | marker={marker_name}")
    db = ctx.request_context.lifespan_context["db"]
    lab_trends = db_get_lab_trend(db, marker_name)

    if not lab_trends:
        return [{"message" : f"No lab trend found for {marker_name} in the database."}]
    logger.info(f"get_lab_trend → {len(lab_trends)} readings found")

    return lab_trends
    

@mcp.tool()
async def ingest_health_documents(file_path: str, ctx: Context) -> dict:
    """Ingest a health document (PDF or image) into the MedMemory database.

    Use this when the user wants to add a prescription, lab report, or any medical document to their health record. Extracts medications, lab results, diagnoses, and allergies automatically using AI.

    Args:
        file_path: Absolute path to the PDF or image file to ingest.
    """

    logger.info(f"ingest_health_document called | file={file_path}")
    db = ctx.request_context.lifespan_context["db"]

    # Day 19 — validate file exists
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return {"success": False, "error": f"File not found: {file_path}"}

    # Day 19 — validate file type
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {path.suffix} | file={file_path}")
        return {
            "success": False,
            "error": (
                f"Unsupported file type '{path.suffix}'. "
                f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        }

    # Day 18 — duplicate detection
    try:
        file_hash = compute_file_hash(file_path)
    except OSError as e:
        logger.error(f"Could not read file for hashing: {e}")
        return {"success": False, "error": f"Could not read file: {e}"}

    existing = check_duplicate(db, file_hash)
    if existing:
        logger.info(f"Duplicate document detected | hash={file_hash} | original={existing['file_path']}")
        return {
            "success": False,
            "already_ingested": True,
            "message": (
                f"This document was already ingested on {existing['ingested_at']} "
                f"(original path: {existing['file_path']})."
            ),
        }

    # Step 1 — extract text / image content
    try:
        content, mode, extraction_warnings = extract_text_or_image(file_path)
        logger.debug(f"Extraction mode={mode} | content_length={len(content)}")
    except Exception as e:
        logger.error(f"File extraction failed: {e}")
        return {"success": False, "error": f"File extraction failed: {e}"}

    # Day 19 — blank / corrupted document
    if mode == "text" and not content.strip():
        logger.error(f"No text extracted from document | file={file_path}")
        return {
            "success": False,
            "error": "Could not extract any text from the document. It may be blank or corrupted.",
        }

    # Step 2 — extract structured health entities via Gemini
    try:
        entities = extract_health_entities(content, mode)
        logger.info(
            f"Entities extracted | type={entities.get('document_type')} | "
            f"meds={len(entities.get('medications', []))} | "
            f"labs={len(entities.get('lab_results', []))}"
        )
    except RuntimeError as e:
        # Gemini API-level failure (network, auth, quota, etc.)
        logger.error(f"Gemini API failure: {e}")
        return {
            "success": False,
            "error": f"AI extraction failed: {e}. Please try again in a moment.",
        }
    except ValueError as e:
        # Bad JSON response from Gemini
        logger.error(f"Gemini returned unparseable response: {e}")
        return {
            "success": False,
            "error": f"AI extraction returned an invalid response: {e}. Please try again.",
        }
    except Exception as e:
        logger.error(f"Unexpected AI extraction error: {e}")
        return {"success": False, "error": f"AI extraction failed: {e}"}

    # Day 19 — non-medical document
    if entities.get("document_type") == "non_medical":
        logger.warning(f"Non-medical document detected | file={file_path}")
        return {
            "success": False,
            "non_medical": True,
            "message": (
                "This document does not appear to be a medical record "
                "(prescription, lab report, discharge summary, or vaccination record). "
                "No data was saved."
            ),
        }

    # Step 3 — save medications
    meds_saved = 0
    for med in entities.get("medications", []):
        if med.get("drug_name"):
            insert_medications(db, {
                "drug_name": med["drug_name"],
                "dose": med.get("dose"),
                "frequency": med.get("frequency"),
                "condition_treated": med.get("condition_treated"),
                "is_active": 1,
                "start_date": entities.get("document_date"),
                "source_document": file_path,
            })
            meds_saved += 1

    # Step 4 — save lab results
    labs_saved = 0
    for lab in entities.get("lab_results", []):
        if lab.get("marker_name") and lab.get("value") is not None:
            insert_lab_result(db, {
                "marker_name": lab["marker_name"],
                "value": lab["value"],
                "unit": lab.get("unit"),
                "test_date": entities.get("document_date"),
                "source_document": file_path,
            })
            labs_saved += 1

    # Day 20 — save allergies
    allergies_saved = 0
    for allergen_entry in entities.get("allergies", []):
        if allergen_entry:
            allergen_text = allergen_entry if isinstance(allergen_entry, str) else allergen_entry.get("allergen", "")
            if allergen_text:
                insert_allergy(db, {
                    "allergen": allergen_text,
                    "reaction": allergen_entry.get("reaction") if isinstance(allergen_entry, dict) else None,
                    "severity": allergen_entry.get("severity") if isinstance(allergen_entry, dict) else None,
                    "noted_date": entities.get("document_date"),
                })
                allergies_saved += 1

    # Day 18 — record this document so future ingestions are detected as duplicates
    save_document_hash(db, file_hash, file_path)

    logger.info(
        f"Ingestion complete | meds={meds_saved} | labs={labs_saved} | "
        f"allergies={allergies_saved} | file={file_path}"
    )

    response: dict = {
        "success": True,
        "document_type": entities.get("document_type"),
        "document_date": entities.get("document_date"),
        "doctor_name": entities.get("doctor_name"),
        "medications_saved": meds_saved,
        "lab_results_saved": labs_saved,
        "allergies_saved": allergies_saved,
        "diagnoses": entities.get("diagnoses", []),
        "follow_up": entities.get("follow_up"),
    }
    if extraction_warnings:
        response["warnings"] = extraction_warnings
    return response

@mcp.tool()
async def get_allergies(ctx: Context) -> list[dict]:
    """Returns all recorded allergies for the patient.

    Call this when the user asks about:
    - known allergies or drug allergies
    - whether they are allergic to anything
    - what medications or substances to avoid
    Always call this before performing a drug interaction check so allergy context is available.
    """

    logger.info("get_allergies called")
    db = ctx.request_context.lifespan_context["db"]
    allergies = db_get_allergies(db)

    if not allergies:
        return [{"message": "No allergies on record."}]

    logger.info(f"get_allergies → {len(allergies)} allergies found")
    return allergies


@mcp.tool()
async def get_visit_history(ctx : Context, speciality : str | None = None) -> list[dict] :
    """Use this tool when asked about:
     
     1. Doctor visits, appointments, consultations
     2. what a specific specialist said
     3. medical history by speciality
     4. preparing for a new doctor appointment
     """

    logger.info(f"get_visit_history called | specialty={speciality}")
    db = ctx.request_context.lifespan_context["db"]

    history = db_get_visit_history(db, speciality)

    if not history :
        return [{"message" : "No visitation history found in the database."}]

    return history

     

@mcp.tool()
async def get_vaccination_status(ctx: Context) -> dict:
    """Returns all recorded vaccinations and flags overdue or missing ones.

    Use this when the user asks about:
    - their vaccination history or immunisation records
    - whether they are up to date on vaccines
    - what vaccines they are missing or overdue for
    - travel vaccine recommendations
    """
    from datetime import date, datetime

    logger.info("get_vaccination_status called")
    db = ctx.request_context.lifespan_context["db"]
    records = get_all_vaccinations(db)

    # Build a set of vaccine names already on record (lowercase for matching)
    received = {}
    for r in records:
        name_lower = r["vaccine_name"].lower()
        if name_lower not in received:
            received[name_lower] = r
    # keep the most recent record per vaccine
        elif r["date_administered"] > received[name_lower]["date_administered"]:
            received[name_lower] = r

    today = date.today()
    overdue = []
    missing = []

    for vaccine_name, schedule in WHO_ADULT_SCHEDULE.items():
        name_lower = vaccine_name.lower()
        record = received.get(name_lower)

        if record is None:
            # Never received this vaccine
            missing.append({
                "vaccine": vaccine_name,
                "notes": schedule["notes"]
            })
        elif schedule["interval_years"] is not None:
            # Check if booster is overdue
            last_date = datetime.strptime(
                record["date_administered"], "%Y-%m-%d"
            ).date()
            years_since = (today - last_date).days / 365.25
            if years_since > schedule["interval_years"]:
                overdue.append({
                    "vaccine": vaccine_name,
                    "last_received": record["date_administered"],
                    "overdue_by_years": round(years_since - schedule["interval_years"], 1),
                    "notes": schedule["notes"]
                })

    return {
        "vaccinations_on_record": records,
        "overdue": overdue,
        "missing": missing,
        "disclaimer": "Consult your doctor before making vaccination decisions."
    }

@mcp.tool()
async def check_drug_interaction(new_drug: str, ctx: Context) -> dict:
    """Check if a newly prescribed drug interacts with current medications.

    Use this when the user:
    - has been prescribed a new medication and wants to check safety
    - asks 'is X safe to take with my current medications'
    - wants to know about drug interactions before starting a new drug

    Args:
        new_drug: Name of the newly prescribed drug to check (generic or brand name)
    """

    logger.info(f"check_drug_interaction called | new_drug={new_drug}")
    db = ctx.request_context.lifespan_context["db"]
    api_key = os.getenv("OPENFDA_API_KEY", "")

    # Step 1: get current medications from DB
    current_meds = get_active_medications(db)
    if not current_meds:
        return {
            "new_drug": new_drug,
            "current_medications": [],
            "interaction_data": None,
            "message": "No current medications on record to check against."
        }

    current_med_names = [m["drug_name"] for m in current_meds]

    # Step 2: query OpenFDA for the new drug's interaction data
    interaction_text = None
    drug_found = False

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                "https://api.fda.gov/drug/label.json",
                params={
                    "search": f"openfda.generic_name:{new_drug.lower()}",
                    "limit": 5,
                    "api_key": api_key
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    drug_found = True
                    # Try each result until we find one with interaction data
                    for result in data["results"]:
                        for field in ["drug_interactions", "warnings_and_cautions",
                                      "warnings", "precautions"]:
                            content = result.get(field, [])
                            if content:
                                interaction_text = content[0][:1000]
                                break
                        if interaction_text:
                            break

            elif response.status_code == 404:
                drug_found = False

        except httpx.TimeoutException:
            return {
                "new_drug": new_drug,
                "error": "OpenFDA API timed out. Try again in a moment."
            }
        except Exception as e:
            return {
                "new_drug": new_drug,
                "error": f"API call failed: {str(e)}"
            }


    logger.info(f"check_drug_interaction → drug_found={drug_found} | has_interaction_data={interaction_text is not None}")
    # Step 3: return structured result
    return {
        "new_drug": new_drug,
        "current_medications": current_med_names,
        "drug_found_in_fda_database": drug_found,
        "interaction_data": interaction_text,
        "disclaimer": (
            "This is FDA label data for informational purposes only. "
            "Always confirm with your doctor or pharmacist before "
            "starting any new medication."
        )
    }

@mcp.tool()
async def generate_health_summary(ctx : Context) -> dict :
    """Generate a complete health summary suitable for sharing with a new doctor.

    Use this when the user asks for :
    - a health summary or medical summary
    - a document to bring to a new doctor or a specialist
    - an overview of their complete health records
    - a printable health report
    - a summary of everything in their health record

    No inputs needed - pulls all data from the health record automatically.
    """
    
    logger.info("generate_health_summary called")
    db = ctx.request_context.lifespan_context["db"]

    # Pull data from every table
    medications = get_active_medications(db)
    visits = db_get_visit_history(db)
    vaccinations = get_all_vaccinations(db)
    allergies = db_get_allergies(db)


    #Get the most recent reading for common lab markers
    common_markers = ["HbA1c", "TSH", "creatinine", "hemoglobin",
"cholesterol", "blood pressure", "fasting glucose"]
    recent_labs = {}
    for marker in common_markers :
        trend = db_get_lab_trend(db, marker)
        if trend:
            recent_labs[marker] = trend[-1]

    pending_followups = [{
        "from_visit": v["visit_date"],
        "doctor": v["doctor_name"],
        "follow_up": v["follow_up"]
    } for v in visits
    if v.get("follow_up") and v["follow_up"].lower() != "none"
    ]

    #Most recent visit per speciality
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
    






if __name__ == "__main__":
    mcp.run(transport="stdio")