PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS museum(
    museum_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL,
    city        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS item(
    item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    museum_id   INTEGER NOT NULL REFERENCES museum(museum_id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL,
    acquired    DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS guest(
    guest_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS visit(
    visit_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id    INTEGER NOT NULL REFERENCES guest(guest_id) ON DELETE CASCADE,
    museum_id   INTEGER NOT NULL REFERENCES museum(museum_id) ON DELETE CASCADE,
    visited_on  DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS upkeep(
    upkeep_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES item(item_id) ON DELETE CASCADE,
    task        TEXT NOT NULL,
    done_on     DATE NOT NULL,
    technician  TEXT NOT NULL
);
