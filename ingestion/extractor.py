import pymupdf
import pymupdf4llm
from pathlib import Path
import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()



def extract_text(file_path : str) -> str:
    """Extract text from a PDF or image file.


    Strategy:
    1. Try native text extraction first ( fast, works on digital PDFs)
    2. If result is too short, fall back to OCR ( for scanned documents)
    3. Use pymupdf4llm for clean Markdown output - better for LLMs
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"No file found at {file_path}")
    
    if path.suffix.lower() not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise ValueError(f"Unsupported file type : {path.suffix}")

    doc = pymupdf.open(file_path)

    #Try native text extraction first
    native_text = "".join(page.get_text() for page in doc).strip()

    if len(native_text) > 100:
        doc.close()
        return pymupdf4llm.to_markdown(file_path)

    else:
        ocr_text = ""
        for page in doc:
            tp = page.get_textpage_ocr(language = "eng")
            ocr_text += tp.extractText() + "\n\n"
        doc.close()
        return ocr_text.strip()


EXTRACTION_PROMPT = """
You are a medical document parser. Extract all health entities from the document below and return only a valid JSON object. No explanation, no preamble, no markdown backticks - just raw JSON.

Return this exact structure (use null for missing fields):

{
  "document_type": "prescription|lab_report|discharge_summary|vaccination_record|other",
  "document_date": "YYYY-MM-DD or null",
  "doctor_name": "string or null",
  "medications": [
    {
      "drug_name": "string",
      "dose": "string or null",
      "frequency": "string or null",
      "duration": "string or null",
      "condition_treated": "string or null"
    }
  ],
  "lab_results": [
    {
      "marker_name": "string",
      "value": number or null,
      "unit": "string or null",
      "reference_range": "string or null"
    }
  ],
  "diagnoses": ["string"],
  "follow_up": "string or null",
  "allergies": ["string"]
}
"""


def extract_health_entities(text: str) -> dict:
    """Send extracted PDF text to Gemini API and get structured health entities."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"{EXTRACTION_PROMPT}\n\nExtract health entities from this document:\n\n{text}"
    )

    raw = response.text.strip()

    # Strip markdown backticks if Gemini wraps response in them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw response: {raw[:200]}")


    