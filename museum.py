"""
HeritagePlus Museum Group - Multi-Tiered Application
Demonstrates complete architecture with presentation, business, and data layers.
"""
import sys
from pathlib import Path
from backend.connection import DB_FILE
from backend.security import AuthenticationManager
from frontend.cli_interface import CLIInterface

def initialize_database():
    """Initialize the database with schema and sample data."""
    import sqlite3

    SCHEMA_FILE = Path(__file__).with_name("backend") / "schema.sql"

    print("Initializing database...")

    # Create fresh database
    if DB_FILE.exists():
        DB_FILE.unlink()
    DB_FILE.touch()

    # Apply schema
    with open(SCHEMA_FILE, encoding="utf-8") as f:
        sqlite3.connect(DB_FILE).executescript(f.read())

    print("✓ Database schema created")

    # Create default admin user for initial access
    try:
        AuthenticationManager.create_user(
            username="admin",
            password="admin123",
            email="admin@heritageplus.com",
            role="admin"
        )
        print("✓ Default admin user created (username: admin, password: admin123)")
    except Exception as e:
        print(f"Note: {e}")

    print("✓ Database initialization complete\n")

def seed_sample_data():
    """Seed sample data for demonstration (requires authenticated user)."""
    from backend import repositories as repos

    print("Seeding sample data...")

    # Museums
    museums = [
        ("British Museum", "London"),
        ("National Museum of Scotland", "Edinburgh"),
        ("Imperial War Museum", "London"),
        ("Science Museum", "London"),
        ("Tate Britain", "London"),
        ("V&A Museum", "London"),
        ("Museum of London", "London"),
    ]

    for name, city in museums:
        repos.MuseumRepository.create(name, city)

    # Exhibits
    exhibits = [
        (1, "Rosetta Stone", "Ancient", "1802-03-11"),
        (1, "Parthenon Marbles", "Classical", "1816-01-01"),
        (2, "Lewis Chessmen", "Medieval", "1831-04-01"),
        (3, "Spitfire Mk IX", "Aviation", "1946-07-10"),
        (4, "Stephenson's Rocket", "Engineering", "1829-10-08"),
        (5, "Ophelia Painting", "Fine Art", "1852-01-01"),
        (6, "Cast Court Plaster", "Sculpture", "1873-04-21"),
        (2, "Pictish Stones", "Early Medieval", "1855-05-10"),
        (3, "Enigma Machine", "Military", "1945-09-03"),
        (4, "Apollo 10 Capsule", "Space", "1969-05-18"),
    ]

    for museum_id, title, category, acquired in exhibits:
        repos.ExhibitRepository.add(museum_id, title, category, acquired)

    # Visitors
    visitors = [
        ("James Thornton", "j.thornton@example.co.uk"),
        ("Emily Watson", "emily.watson@example.co.uk"),
        ("Oliver Brown", "oliver.brown@example.co.uk"),
        ("Charlotte Green", "charlotte.green@example.co.uk"),
        ("Mohammed Rahman", "m.rahman@example.co.uk"),
        ("Ayesha Hussain", "ayesha.hussain@example.co.uk"),
    ]

    for name, email in visitors:
        repos.VisitorRepository.register(name, email)

    # Maintenance records
    maintenance = [
        (1, "Surface Cleaning", "2023-01-15", "Dr Carter"),
        (1, "Stone Preservation", "2024-02-10", "Dr Wilson"),
        (3, "Avionics Check", "2023-06-05", "RAF Team"),
        (4, "Engine Calibration", "2024-03-12", "Engineering Team"),
        (2, "Restoration", "2024-01-20", "Ms Johnson"),
    ]

    for item_id, task, done_on, technician in maintenance:
        repos.MaintenanceRepository.schedule(item_id, task, done_on, technician)

    # Visits
    visits = [
        (1, 1, "2024-01-10"),
        (2, 3, "2024-02-15"),
        (3, 4, "2024-03-01"),
        (4, 5, "2024-03-10"),
        (5, 2, "2024-03-15"),
        (1, 2, "2024-03-20"),
        (2, 1, "2024-04-01"),
    ]

    for guest_id, museum_id, visited_on in visits:
        repos.VisitorRepository.record_visit(guest_id, museum_id, visited_on)

    print("✓ Sample data seeded\n")

def run_demo_queries():
    """Run demonstration queries to show system capabilities."""
    from backend import repositories as repos
    from backend.business_logic import ReportingService, MaintenanceService

    print("\n" + "="*60)
    print("DEMONSTRATION QUERIES - System Capabilities")
    print("="*60)

    print("\n1. TOP EXHIBITS BY MAINTENANCE ACTIVITY")
    print("-" * 50)
    for title, count in repos.ExhibitRepository.top_by_maintenance()[:5]:
        print(f"  {title}: {count} maintenance actions")

    print("\n2. VISITOR ACTIVITY SUMMARY")
    print("-" * 50)
    for name, count in repos.VisitorRepository.activity_summary()[:5]:
        print(f"  {name}: visited {count} different museums")

    print("\n3. MAINTENANCE SUMMARY BY EXHIBIT")
    print("-" * 50)
    for title, total in repos.MaintenanceRepository.summary()[:5]:
        print(f"  {title}: {total} total maintenance actions")

    print("\n4. ITEMS NEEDING MAINTENANCE (6+ months)")
    print("-" * 50)
    items = MaintenanceService.get_items_needing_maintenance(6)
    for item in items[:5]:
        last = item['last_maintenance'] or "Never"
        print(f"  {item['title']}: Last maintenance {last}")

    print("\n5. EXECUTIVE SUMMARY")
    print("-" * 50)
    summary = ReportingService.generate_executive_summary()
    print(f"  Total Museums: {summary['summary'].get('total_museums', 0)}")
    print(f"  Total Exhibits: {summary['summary'].get('total_items', 0)}")
    print(f"  Total Visitors: {summary['summary'].get('total_visitors', 0)}")
    print(f"  Recent Visits: {summary['recent_activity'].get('visits_last_month', 0)}")

    print("\n" + "="*60)

def main():
    """Main entry point for the application."""
    print("\n" + "="*60)
    print("  HeritagePlus Museum Group Management System")
    print("  Multi-Tiered Architecture Demonstration")
    print("="*60 + "\n")

    # Check if database exists
    if not DB_FILE.exists():
        print("Database not found. Initializing...\n")
        initialize_database()
        seed_sample_data()
        run_demo_queries()

    # Provide options
    print("\nApplication Modes:")
    print("  1. Interactive CLI Interface (Full multi-tier demonstration)")
    print("  2. Run Demo Queries Only")
    print("  3. Reset Database")
    print("  0. Exit")

    choice = input("\nSelect mode: ").strip()

    if choice == '1':
        # Run interactive CLI
        print("\nStarting interactive interface...\n")
        print("Default credentials - username: admin, password: admin123\n")
        cli = CLIInterface()
        cli.run()

    elif choice == '2':
        # Run demo queries
        if not DB_FILE.exists():
            print("Database not found. Please initialize first.")
            return
        run_demo_queries()

    elif choice == '3':
        # Reset database
        if input("Are you sure you want to reset the database? (yes/no): ").lower() == 'yes':
            initialize_database()
            seed_sample_data()
            run_demo_queries()
        else:
            print("Reset cancelled.")

    elif choice == '0':
        print("\nThank you for using HeritagePlus Museum System!")
        sys.exit(0)

    else:
        print("Invalid option. Please try again.")
        main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


