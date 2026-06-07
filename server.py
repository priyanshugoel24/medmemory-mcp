from typing import AsyncIterator
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from mcp.server.fastmcp import FastMCP, Context
from db.database import get_connection, get_active_medications, get_lab_trend as db_get_lab_trend, insert_medications, insert_lab_result
import sqlite3
from ingestion.extractor import extract_text, extract_health_entities


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

    db = ctx.request_context.lifespan_context["db"]
    medications = get_active_medications(db)


    if not medications:
        return [{"message" : "No active medications found in the databse."}]

    return medications

@mcp.tool()
async def get_lab_trend(ctx : Context, marker_name : str) -> list[dict]:

    """Returns a list of all readings for that marker, oldest first.

    Use this when the user asks about trends, progress, changes over time, historical readings or whether something is getting better or worse for a specific lab marker.
    """
    db = ctx.request_context.lifespan_context["db"]
    lab_trends = db_get_lab_trend(db, marker_name)

    if not lab_trends:
        return [{"message" : f"No lab trend found for {marker_name} in the database."}]
    
    return lab_trends
    

@mcp.tool()
async def ingest_health_documents(file_path : str, ctx : Context) -> dict:
    """Ingest a health document (PDF for image) into the MedMemory database.

    Use this when the user wants to add a prescription, lab report, or any medical document to their health record. Extracts medications, lab results,and diagnoses automatically using AI.

    Args :
        file_path : Absolute path to the PDF or image file to ingest.
    """

    db = ctx.request_context.lifespan_context["db"]

    #Step1 : extract text from the document
    try:
        text = extract_text(file_path)
    except FileNotFoundError:
        return {"success" : False, "error" : f"File not found : {file_path}"}
    except ValueError as e:
        return {"success" : False, "error" : str(e)}

    if not text.strip():
        return {"success" : False, "error" : "Could not extract any text from the document."}

    #Step 2 : extract structured health entities via Gemini
    try:
        entities = extract_health_entities(text)
    except Exception as e:
        return {"success" : False, "error" : f"AI extraction failed : {e}"}

    #Step 3 : save medications to DB
    meds_saved = 0
    for med in entities.get("medications", []):
        if med.get("drug_name"):
            insert_medications(db, {
                "drug_name" : med["drug_name"],
                "dose" : med.get("dose"),
                "frequency" : med.get("frequency"),
                "condition_treated" : med.get("condition_treated"),
                "is_active" : 1,
                "start_date" : entities.get("document_date"),
                "source_document" : file_path,
            })
            meds_saved += 1


    #Step 4 : save lab results to DB
    labs_saved = 0
    for lab in entities.get("lab_results", []):
        if lab.get("marker_name") and lab.get("value") is not None:
            insert_lab_result(db, {
                "marker_name" : lab["marker_name"],
                "value" : lab["value"],
                "unit" : lab.get("unit"),
                "test_date" : entities.get("document_date"),
                "source_document" : file_path,
            })
            labs_saved += 1

    #Step 5 : return a summary of what was saved
    return {
        "success" : True,
        "document_tyep" : entities.get("document_type"),
        "document_date" : entities.get("document_date"),
        "doctor_name" : entities.get("doctor_name"),
        "medications_saved" : meds_saved,
        "lab_results_saved" : labs_saved,
        "diagnoses" : entities.get("diagnoses", []),
        "follow_up" : entities.get("follow_up"),
    }
    
    


if __name__ == "__main__":
    mcp.run(transport="stdio")