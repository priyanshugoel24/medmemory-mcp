from db.database import get_connection, insert_vaccination

conn = get_connection()

# Insert some vaccinations — leave most missing to test the gap detection
insert_vaccination(conn, {
"vaccine_name": "Influenza",
"date_administered": "2022-10-01", # overdue — more than 1 year ago
"dose_number": 1,
"provider": "City Health Clinic"
})
insert_vaccination(conn, {
"vaccine_name": "Hepatitis B",
"date_administered": "2015-03-15",
"dose_number": 3,
"provider": "Apollo Hospital"
})
insert_vaccination(conn, {
"vaccine_name": "Typhoid",
"date_administered": "2023-06-20", # not yet overdue
"dose_number": 1,
"provider": "Travel Clinic"
})

print("Vaccination records inserted")
conn.close()