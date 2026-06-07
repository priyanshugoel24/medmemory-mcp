from typing import AsyncIterator
from contextlib import asynccontextmanager
from collections.abc import AsyncIterable
from mcp.server.fastmcp import FastMCP, Context
from db.database import get_connection, get_active_medications, get_lab_trend as db_get_lab_trend
import sqlite3


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
    

    


if __name__ == "__main__":
    mcp.run(transport="stdio")