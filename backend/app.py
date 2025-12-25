import sqlite3

DB_NAME = "museum.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_museum(name, location):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO museum (name, location) VALUES (?, ?)",
            (name, location)
        )


def get_museums():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM museum").fetchall()


def update_museum(museum_id, name, location):
    with get_connection() as conn:
        conn.execute(
            "UPDATE museum SET name=?, location=? WHERE museum_id=?",
            (name, location, museum_id)
        )


def delete_museum(museum_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM museum WHERE museum_id=?", (museum_id,))


def create_exhibit(museum_id, title, category, acquisition_date):
    with get_connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO exhibit (museum_id, title, category, acquisition_date)
               VALUES (?, ?, ?, ?)""",
            (museum_id, title, category, acquisition_date)
        )


def get_exhibits():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM exhibit").fetchall()


def update_exhibit(exhibit_id, title):
    with get_connection() as conn:
        conn.execute(
            "UPDATE exhibit SET title=? WHERE exhibit_id=?",
            (title, exhibit_id)
        )


def delete_exhibit(exhibit_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM exhibit WHERE exhibit_id=?", (exhibit_id,))


def create_conservation(exhibit_id, action, date, conservator):
    with get_connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO conservation (exhibit_id, action, conservation_date, conservator)
               VALUES (?, ?, ?, ?)""",
            (exhibit_id, action, date, conservator)
        )


def get_conservations():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM conservation").fetchall()


def update_conservation(conservation_id, action):
    with get_connection() as conn:
        conn.execute(
            "UPDATE conservation SET action=? WHERE conservation_id=?",
            (action, conservation_id)
        )


def delete_conservation(conservation_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM conservation WHERE conservation_id=?", (conservation_id,))


def create_visitor(name, email):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO visitor (full_name, email) VALUES (?, ?)",
            (name, email)
        )


def get_visitors():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM visitor").fetchall()


def update_visitor(visitor_id, email):
    with get_connection() as conn:
        conn.execute(
            "UPDATE visitor SET email=? WHERE visitor_id=?",
            (email, visitor_id)
        )


def delete_visitor(visitor_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM visitor WHERE visitor_id=?", (visitor_id,))


def create_visit(visitor_id, museum_id, date):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO visit (visitor_id, museum_id, visit_date) VALUES (?, ?, ?)",
            (visitor_id, museum_id, date)
        )


def get_visits():
    with get_connection() as conn:
        return conn.execute("SELECT * FROM visit").fetchall()


def update_visit(visit_id, date):
    with get_connection() as conn:
        conn.execute(
            "UPDATE visit SET visit_date=? WHERE visit_id=?",
            (date, visit_id)
        )


def delete_visit(visit_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM visit WHERE visit_id=?", (visit_id,))


# -------------------- QUERIES (JOIN / ORDER / GROUP) --------------------

# 1. JOIN: Exhibits with their Museum name
def get_exhibits_with_museum():
    with get_connection() as conn:
        return conn.execute("""
            SELECT e.title, e.category, m.name AS museum_name
            FROM exhibit e
            JOIN museum m ON e.museum_id = m.museum_id
        """).fetchall()


# 2. JOIN + ORDER BY: Conservation history ordered by date (latest first)
def get_conservation_history_ordered():
    with get_connection() as conn:
        return conn.execute("""
            SELECT e.title, c.action, c.conservation_date, c.conservator
            FROM conservation c
            JOIN exhibit e ON c.exhibit_id = e.exhibit_id
            ORDER BY c.conservation_date DESC
        """).fetchall()


# 3. GROUP BY: Count exhibits per museum
def get_exhibit_count_per_museum():
    with get_connection() as conn:
        return conn.execute("""
            SELECT m.name, COUNT(e.exhibit_id) AS total_exhibits
            FROM museum m
            LEFT JOIN exhibit e ON m.museum_id = e.museum_id
            GROUP BY m.museum_id
        """).fetchall()


# 4. GROUP BY: Number of visits per museum
def get_visit_count_per_museum():
    with get_connection() as conn:
        return conn.execute("""
            SELECT m.name, COUNT(v.visit_id) AS total_visits
            FROM visit v
            JOIN museum m ON v.museum_id = m.museum_id
            GROUP BY m.museum_id
        """).fetchall()


# 5. JOIN + ORDER BY: Visitor visit history
def get_visitor_visit_history():
    with get_connection() as conn:
        return conn.execute("""
            SELECT vis.full_name, m.name AS museum, v.visit_date
            FROM visit v
            JOIN visitor vis ON v.visitor_id = vis.visitor_id
            JOIN museum m ON v.museum_id = m.museum_id
            ORDER BY v.visit_date ASC
        """).fetchall()



if __name__ == "__main__":

    # ---- CREATE ----
    create_museum("HeritagePlus Central Museum", "Karachi")

    create_exhibit(1, "Ancient Vase", "Archaeology", "2021-01-01")
    create_exhibit(1, "Medieval Sword", "Weapons", "2022-03-15")
    create_exhibit(1, "Historic Painting", "Art", "2023-05-10")

    create_visitor("Ali Khan", "ali@example.com")
    create_visitor("Sara Ahmed", "sara@example.com")
    create_visitor("Usman Raza", "usman@example.com")

    create_conservation(1, "Cleaning", "2024-01-01", "Dr. Ahmed")
    create_conservation(2, "Rust Removal", "2024-02-01", "Ms. Fatima")
    create_conservation(3, "Frame Repair", "2024-03-01", "Mr. Hassan")

    create_visit(1, 1, "2024-04-01")
    create_visit(2, 1, "2024-04-02")
    create_visit(3, 1, "2024-04-03")

    print("Museums:", get_museums())
    print("Exhibits:", get_exhibits())

    update_exhibit(1, "Ancient Greek Vase")
    update_visitor(1, "ali.khan@example.com")

    delete_visit(3)
    delete_conservation(2)

    print("Updated Exhibits:", get_exhibits())
    print("Remaining Visits:", get_visits())

    # -------------- Queries demonstration -------------------
    print("\n--- Exhibits with Museum (JOIN) ---")
    for row in get_exhibits_with_museum():
        print(row)

    print("\n--- Conservation History (JOIN + ORDER BY) ---")
    for row in get_conservation_history_ordered():
        print(row)

    print("\n--- Exhibit Count per Museum (GROUP BY) ---")
    for row in get_exhibit_count_per_museum():
        print(row)

    print("\n--- Visit Count per Museum (GROUP BY) ---")
    for row in get_visit_count_per_museum():
        print(row)

    print("\n--- Visitor Visit History (JOIN + ORDER BY) ---")
    for row in get_visitor_visit_history():
        print(row)

