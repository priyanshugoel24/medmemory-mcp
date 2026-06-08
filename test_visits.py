from db.database import get_connection, insert_visit, get_visit_history

conn = get_connection()

insert_visit(conn, {
"visit_date": "2024-08-15",
"specialty": "Endocrinology",
"doctor_name": "Dr. Priya Mehta",
"diagnosis": "Type 2 Diabetes — stable",
"follow_up": "Recheck HbA1c in 3 months"
})
insert_visit(conn, {
"visit_date": "2024-10-20",
"specialty": "Cardiology",
"doctor_name": "Dr. Ramesh Iyer",
"diagnosis": "Hypertension — borderline",
"follow_up": "Monitor BP daily, return in 6 weeks"
})
insert_visit(conn, {
"visit_date": "2024-11-05",
"specialty": "General Medicine",
"doctor_name": "Dr. Anil Sharma",
"diagnosis": "Annual checkup — all normal",
"follow_up": "None"
})

print("=== All visits ===")
all_visits = get_visit_history(conn)
for v in all_visits:
    print(f"{v['visit_date']} | {v['speciality']} | {v['doctor_name']}")
    print(f" Diagnosis: {v['diagnosis']}")

print("\n=== Cardiology only ===")
cardio = get_visit_history(conn, speciality="Cardiology")
for v in cardio:
    print(f"{v['visit_date']} | {v['doctor_name']} | {v['diagnosis']}")

conn.close()