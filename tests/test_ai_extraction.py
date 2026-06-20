from ingestion.extractor import extract_text, extract_health_entities
import json


print("Step 1: Extracting text from PDF...")
text = extract_text("sample_prescription.pdf")
print(f"Extracted {len(text)} characters")

print("\nStep 2: Sending to Claude API...")
entities = extract_health_entities(text)

print("\n=== EXTRACTED ENTITIES ===")
print(json.dumps(entities, indent=2))

print(f"\n=== SUMMARY ===")
print(f"Document type: {entities.get('document_type')}")
print(f"Medications found: {len(entities.get('medications', []))}")
print(f"Lab results found: {len(entities.get('lab_results', []))}")
print(f"Diagnoses: {entities.get('diagnoses', [])}")