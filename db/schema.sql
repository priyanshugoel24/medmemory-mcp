CREATE TABLE IF NOT EXISTS medications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_name TEXT NOT NULL,
    dose TEXT,
    frequency TEXT,
    condition_treated TEXT,
    prescriber TEXT,
    is_active INTEGER DEFAULT 1,
    start_date TEXT,
    end_date TEXT,
    source_document TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lab_results(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marker_name TEXT NOT NULL,
    value REAL,
    unit TEXT,
    reference_min REAL,
    reference_max REAL,
    test_date TEXT,
    lab_name TEXT,
    source_document TEXT,
    created_at TEXT DEFAULT(datetime('now'))
);

CREATE TABLE IF NOT EXISTS vaccinations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vaccine_name TEXT NOT NULL,
    date_administered TEXT,
    dose_number INTEGER DEFAULT 1,
    provider TEXT,
    source_document TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS visits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_date TEXT,
    speciality TEXT,
    doctor_name TEXT,
    diagnosis TEXT,
    notes TEXT,
    follow_up TEXT,
    source_document TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS allergies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allergen TEXT NOT NULL,
    reaction TEXT,
    severity TEXT,
    noted_date TEXT,
    created_at TEXT DEFAULT(datetime('now'))
);