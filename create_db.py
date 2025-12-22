import sqlite3

# 1. Connect (creates DB file if not exists)
conn = sqlite3.connect("museum.db")
cursor = conn.cursor()

# 2. Create tables
cursor.executescript("""
CREATE TABLE IF NOT EXISTS museum (
    museum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exhibit (
    exhibit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    museum_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    acquisition_date DATE,
    FOREIGN KEY (museum_id) REFERENCES museum(museum_id)
);

CREATE TABLE IF NOT EXISTS conservation (
    conservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exhibit_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    conservation_date DATE NOT NULL,
    conservator TEXT,
    FOREIGN KEY (exhibit_id) REFERENCES exhibit(exhibit_id)
);

CREATE TABLE IF NOT EXISTS visitor (
    visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS visit (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id INTEGER NOT NULL,
    museum_id INTEGER NOT NULL,
    visit_date DATE NOT NULL,
    FOREIGN KEY (visitor_id) REFERENCES visitor(visitor_id),
    FOREIGN KEY (museum_id) REFERENCES museum(museum_id)
);
""")

# 3. Save and close
conn.commit()
conn.close()

print("Database created successfully!")
