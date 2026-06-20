from db.database import get_connection, insert_medications, get_active_medications, insert_lab_result, get_lab_trend

conn = get_connection()
print("✓ Database connected and schema created")

# Insert 3 fake medications
insert_medications(conn, {
"drug_name": "Metformin",
"dose": "500mg",
"frequency": "twice daily",
"condition_treated": "Type 2 Diabetes",
"is_active": 1,
"start_date": "2024-01-15"
})
insert_medications(conn, {
"drug_name": "Levothyroxine",
"dose": "50mcg",
"frequency": "once daily",
"condition_treated": "Hypothyroidism",
"is_active": 1,
"start_date": "2023-06-01"
})
insert_medications(conn, {
"drug_name": "Amoxicillin",
"dose": "250mg",
"frequency": "three times daily",
"condition_treated": "Throat infection",
"is_active": 0, # completed course
"start_date": "2024-09-01",
"end_date": "2024-09-07"
})
print("✓ 3 medications inserted")


# Query active medications — should return only 2
active = get_active_medications(conn)
print(f"✓ Active medications ({len(active)} found):")
for med in active:
    print(f" - {med['drug_name']} {med['dose']} — {med['frequency']}")


# Insert 2 HbA1c readings
insert_lab_result(conn, {
"marker_name": "HbA1c",
"value": 7.2,
"unit": "%",
"reference_min": 4.0,
"reference_max": 5.6,
"test_date": "2024-03-01"
})
insert_lab_result(conn, {
"marker_name": "HbA1c",
"value": 6.8,
"unit": "%",
"reference_min": 4.0,
"reference_max": 5.6,
"test_date": "2024-09-01"
})
print("✓ 2 HbA1c readings inserted")



# Query the trend
trend = get_lab_trend(conn, "HbA1c")
print(f"✓ HbA1c trend ({len(trend)} readings):")
for r in trend:
    flag = "⚠ HIGH" if r['value'] > r['reference_max'] else "✓"
    print(f" {r['test_date']}: {r['value']}{r['unit']} {flag}")

conn.close()
print("✓ All done")