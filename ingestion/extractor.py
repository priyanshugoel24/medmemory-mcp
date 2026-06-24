import pymupdf
import pymupdf4llm
from pathlib import Path
import json
import os
import hashlib
from google import genai
from google.genai import types
from dotenv import load_dotenv
import base64
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from logger import get_logger
extractor_logger = get_logger("medmemory.extractor")


load_dotenv()

MAX_PAGES_BEFORE_TRUNCATION = 20
TRUNCATED_PAGE_LIMIT = 10


def compute_file_hash(file_path: str) -> str:
    """Compute MD5 hash of a file for duplicate detection."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_text_or_image(file_path: str) -> tuple[str, str, list[str]]:
    """Smart extraction — returns (content, mode, warnings).
    mode is 'text' for native PDFs, 'image' for scanned/handwritten ones.
    For image mode, content is base64-encoded image data.
    warnings is a list of non-fatal issues (e.g. page truncation).
    """

    extractor_logger.debug(f"Extracting from {file_path}")
    path = Path(file_path)
    warnings: list[str] = []

    # For image files — always use vision mode
    if path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode(), "image", []

    # For PDFs — check page count first
    doc = pymupdf.open(file_path)
    total_pages = len(doc)

    pages_to_read: list[int] | None = None
    if total_pages > MAX_PAGES_BEFORE_TRUNCATION:
        pages_to_read = list(range(TRUNCATED_PAGE_LIMIT))
        msg = (
            f"Document has {total_pages} pages; only the first "
            f"{TRUNCATED_PAGE_LIMIT} pages were processed."
        )
        warnings.append(msg)
        extractor_logger.warning(f"Large PDF ({total_pages} pages): truncating to {TRUNCATED_PAGE_LIMIT} | {file_path}")

    page_indices = pages_to_read if pages_to_read is not None else list(range(total_pages))
    native_text = "".join(doc[i].get_text() for i in page_indices).strip()

    if len(native_text) > 100:
        # Good native text — use pymupdf4llm for clean markdown
        doc.close()
        md = pymupdf4llm.to_markdown(file_path, pages=page_indices)
        return md, "text", warnings
    else:
        # Scanned PDF — render first page as image for Gemini Vision
        page = doc[0]
        mat = pymupdf.Matrix(2, 2)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_bytes).decode(), "image", warnings





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
You are a medical document parser for Indian healthcare documents.
Extract all health entities and return ONLY valid JSON. No explanation, no backticks.

CRITICAL RULES:

1. drug_name must ALWAYS be the generic name, not brand name.
   Examples of brand → generic mappings:
   "Glycomet" → "Metformin", "Glycomet-GP" → split into "Glimepiride" and "Metformin"
   "Storvas" → "Atorvastatin", "Ecosprin" → "Aspirin"
   "Crocin" → "Paracetamol", "Dolo" → "Paracetamol"
   "Pantocid" → "Pantoprazole", "Pan-D" → "Pantoprazole+Domperidone"
   "Zerodol-P" → split into "Aceclofenac" and "Paracetamol"
   "Gabantin" → "Gabapentin", "Gabantin-GRS" → "Gabapentin"
   "Lantus" → "Insulin Glargine"
   For any combination drug, list each active ingredient as a SEPARATE entry.

2. marker_name must use standard names:
   "LDL Cholesterol" → "LDL", "S. Creatinine" → "creatinine"
   "Serum TSH" → "TSH", "Hb" or "Haemoglobin" → "hemoglobin"
   "T. Cholesterol" → "cholesterol", "FBS" → "fasting glucose"
   "PPBS" → "postprandial glucose", "S. Uric Acid" → "uric acid"
   "S. Bilirubin" → "bilirubin", "SGPT" → "ALT", "SGOT" → "AST"

3. If the document is non-medical, return:
   {"document_type": "non_medical", "medications": [], "lab_results": [],
    "diagnoses": [], "follow_up": null, "doctor_name": null,
    "document_date": null, "allergies": []}

EXAMPLE INPUT (prescription):
Tab Glycomet 500mg BD x 3 months - for DM
Tab Storvas 10mg HS x 3 months

EXAMPLE OUTPUT:
{
  "document_type": "prescription",
  "document_date": null,
  "doctor_name": null,
  "medications": [
    {"drug_name": "Metformin", "dose": "500mg", "frequency": "twice daily",
     "duration": "3 months", "condition_treated": "Diabetes Mellitus"},
    {"drug_name": "Atorvastatin", "dose": "10mg", "frequency": "once daily at bedtime",
     "duration": "3 months", "condition_treated": null}
  ],
  "lab_results": [],
  "diagnoses": ["Diabetes Mellitus"],
  "follow_up": null,
  "allergies": []
}

Return this exact structure for every document:
{
  "document_type": "prescription|lab_report|discharge_summary|vaccination_record|non_medical|other",
  "document_date": "YYYY-MM-DD or null",
  "doctor_name": "string or null",
  "medications": [
    {"drug_name": "generic name only", "dose": "string or null",
     "frequency": "string or null", "duration": "string or null",
     "condition_treated": "string or null"}
  ],
  "lab_results": [
    {"marker_name": "standardised name", "value": number or null,
     "unit": "string or null", "reference_range": "string or null"}
  ],
  "diagnoses": ["string"],
  "follow_up": "string or null",
  "allergies": ["string"]
}
"""


def extract_health_entities(content: str, mode: str = "text") -> dict:
    """Extract health entities via Gemini.
    mode='text': send as text prompt
    mode='image': send as inline image for vision
    Raises RuntimeError on Gemini API failure, ValueError on bad JSON.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    try:
        client = genai.Client(api_key=api_key)

        if mode == "text":
            prompt = f"{EXTRACTION_PROMPT}\n\nExtract health entities from this document:\n\n{content}"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
        else:
            # Image mode — Gemini Vision reads the image directly
            image_part = types.Part.from_bytes(
                data=base64.b64decode(content),
                mime_type="image/png"
            )
            text_part = types.Part.from_text(
                text=f"{EXTRACTION_PROMPT}\n\nExtract health entities from this medical document image:"
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[text_part, image_part]
            )

    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()

    extractor_logger.debug(f"Gemini response length: {len(raw)} chars")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {raw[:200]}")


    