### Doc 1 — Prescription: prescription.pdf
- Extracted correctly: brand names, doses, frequencies, diagnoses, follow-up, doctor name
- Issue: drug_name stored as "Glycomet (Metformin)" not just "Metformin" — 
  may break OpenFDA interaction checks
- OCR: not needed (native text PDF)
- Errors: none

### Doc 2 — Lab report: bloodtest.pdf
- Extracted correctly: 12 markers saved, diagnoses, doctor, date
- Issue: marker names inconsistent — "LDL Cholesterol" stored but 
  get_lab_trend queries for "LDL" → returns empty
- Issue: TSH stored under unknown name — subclinical hypothyroidism 
  diagnosed but TSH value not queryable
- Errors: none

### Doc 3 — Discharge summary: dischargesummary.pdf
- Extracted correctly: 4 meds, 8 labs, diagnoses, follow-up, emergency instructions
- Issue: combination drug "GLYCOMET-GP 1/500" stored as one entry — 
  active ingredients (Glimepiride, Metformin) not split out separately
- Issue: brand names dominant in drug_name field again
- Errors: none


### Doc 4 — Non-medical: nonmedical.pdf
- Correctly identified as "other" document type
- 0 medications, 0 lab results — no hallucination
- Errors: none
- Result: PASS

### Doc 5 — Scanned handwritten prescription: scanned.pdf
- Real prescription from Dr. Vivek Kumar (Neurologist)
- Medications visible: Gabapentin 300mg, Zerodol-P, Pantocid 80mg
- Extracted: 0 medications, 0 lab results, nothing
- Root cause: OCR ran but handwritten text too messy for Tesseract
  to produce clean enough text for Gemini to parse
- This is a CRITICAL failure — handwritten prescriptions are the 
  most common real-world document type in India
- Fix priority: HIGH



## Failure Patterns Found

1. CRITICAL — Handwritten/scanned prescriptions extract nothing
   OCR produces garbled text, Gemini can't parse it

2. HIGH — Marker names not normalised
   "LDL Cholesterol" stored but get_lab_trend queries "LDL" → empty

3. MEDIUM — Brand names stored in drug_name instead of generic
   "Glycomet (Metformin)" breaks OpenFDA interaction checks

4. MEDIUM — Combination drugs not split into active ingredients
   "GLYCOMET-GP 1/500" should be Glimepiride + Metformin separately

5. LOW — Duplicate ingestion not detected (not tested yet)

## Fix Priority
1. Marker name normalisation (Day 16 prompt fix)
2. Brand → generic drug name normalisation (Day 16 prompt fix)  
3. Handwritten OCR improvement (Day 16 — try Gemini Vision instead)
4. Combination drug splitting (Day 16 prompt fix)
5. Duplicate detection (Day 18)