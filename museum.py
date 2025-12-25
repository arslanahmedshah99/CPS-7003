#!/usr/bin/env python3
"""
Executable demo for HeritagePlus Museum Group.
- Initializes the database using schema.sql
- Seeds sample museums, exhibits, visitors, visits, and maintenance tasks
- Runs advanced queries: top exhibits, visitor activity, upkeep summary
"""

import sqlite3
from pathlib import Path
from backend import repositories as repos
from backend.connection import DB_FILE

# Path to the schema SQL file
SCHEMA_FILE = Path(__file__).with_name("backend") / "schema.sql"


def initialize_database():
    """Create a fresh database and populate tables using the schema."""
    if DB_FILE.exists():
        DB_FILE.unlink()
    DB_FILE.touch()

    with open(SCHEMA_FILE, encoding="utf-8") as f:
        sqlite3.connect(DB_FILE).executescript(f.read())
    print("Database initialized.")


def seed_data():
    """Seed museums, exhibits, visitors, visits, and maintenance tasks."""
        # --- 1. Museums (7) ------------------------------------------
    for name, city in [
        ("British Museum", "London"),
        ("National Museum of Scotland", "Edinburgh"),
        ("Imperial War Museum", "London"),
        ("Science Museum", "London"),
        ("Tate Britain", "London"),
        ("V&A", "London"),
        ("Museum of London", "London"),
    ]:
        repos.MuseumRepository.create(name, city)

    # --- 2. Exhibits (10) ----------------------------------------
    for m, title, cat, acq in [
        (1, "Rosetta Stone", "Ancient", "1802-03-11"),
        (1, "Parthenon Marbles", "Classical", "1816-01-01"),
        (2, "Lewis Chessmen", "Medieval", "1831-04-01"),
        (3, "Spitfire Mk IX", "Aviation", "1946-07-10"),
        (4, "Stephenson's Rocket", "Engineering", "1829-10-08"),
        (5, "Ophelia", "Fine Art", "1852-01-01"),
        (6, "Cast Court Plaster", "Sculpture", "1873-04-21"),
        (2, "Pictish Stones", "Early Medieval", "1855-05-10"),
        (3, "Enigma Machine", "Military", "1945-09-03"),
        (4, "Apollo 10 Capsule", "Space", "1969-05-18"),
    ]:
        repos.ExhibitRepository.add(m, title, cat, acq)

    # --- 3. Visitors (6) -----------------------------------------
    for name, email in [
        ("James Thornton", "j.thornton@example.co.uk"),
        ("Emily Watson", "emily.watson@example.co.uk"),
        ("Oliver Brown", "oliver.brown@example.co.uk"),
        ("Charlotte Green", "charlotte.green@example.co.uk"),
        ("Mohammed Rahman", "m.rahman@example.co.uk"),
        ("Ayesha Hussain", "ayesha.hussain@example.co.uk"),
    ]:
        repos.VisitorRepository.register(name, email)

    # --- 4. Maintenance (4) --------------------------------------
    repos.MaintenanceRepository.schedule(1, "Surface Cleaning", "2023-01-15", "Dr Carter")
    repos.MaintenanceRepository.schedule(1, "Stone Preservation", "2024-02-10", "Dr Wilson")
    repos.MaintenanceRepository.schedule(3, "Avionics Check", "2023-06-05", "RAF Team")
    repos.MaintenanceRepository.schedule(4, "Engine Calibration", "2024-03-12", "Eng Team")

    # --- 5. Visits (5) -------------------------------------------
    repos.VisitorRepository.record_visit(1, 1, "2024-01-10")
    repos.VisitorRepository.record_visit(2, 3, "2024-02-15")
    repos.VisitorRepository.record_visit(3, 4, "2024-03-01")
    repos.VisitorRepository.record_visit(4, 5, "2024-03-10")
    repos.VisitorRepository.record_visit(5, 2, "2024-03-15")

    print("Small data set loaded.")

def show_reports():
    """Print advanced query reports."""
    print("\n=== Top Exhibits by Maintenance ===")
    for title, count in repos.ExhibitRepository.top_by_maintenance():
        print(f"{title}: {count}")

    print("\n=== Visitor Activity (Museums Visited) ===")
    for name, visited_count in repos.VisitorRepository.activity_summary():
        print(f"{name}: {visited_count}")

    print("\n=== Maintenance Summary ===")
    for title, total in repos.MaintenanceRepository.summary():
        print(f"{title}: {total}")


if __name__ == "__main__":
    initialize_database()

    # run to seed sample data
    seed_data()

    show_reports()
