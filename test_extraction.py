from ingestion.extractor import extract_text, extract_health_entities
import json

text = extract_text("HODReport.pdf")
print("=== EXTRACTED TEXT ===")
print(text)
print(f"\nCharacter count: {len(text)}")

print("\n=== EXTRACTED HEALTH ENTITIES ===")
entities = extract_health_entities(text)
print(json.dumps(entities, indent=2))