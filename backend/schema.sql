-- Enhanced Schema with Integrity Constraints, Triggers, and Indexes
PRAGMA foreign_keys = ON;

-- Museum table with enhanced constraints
CREATE TABLE IF NOT EXISTS museum(
    museum_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT UNIQUE NOT NULL CHECK(length(trim(name)) > 0),
    city        TEXT NOT NULL CHECK(length(trim(city)) > 0),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Item/Exhibit table with enhanced constraints
CREATE TABLE IF NOT EXISTS item(
    item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    museum_id   INTEGER NOT NULL REFERENCES museum(museum_id) ON DELETE CASCADE,
    title       TEXT NOT NULL CHECK(length(trim(title)) > 0),
    category    TEXT NOT NULL CHECK(length(trim(category)) > 0),
    acquired    DATE NOT NULL CHECK(acquired <= date('2026-01-01')),
    status      TEXT DEFAULT 'active' CHECK(status IN ('active', 'on_loan', 'in_restoration', 'retired')),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(museum_id, title)
);

-- Guest/Visitor table with enhanced constraints
CREATE TABLE IF NOT EXISTS guest(
    guest_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL CHECK(length(trim(full_name)) > 0),
    email       TEXT UNIQUE NOT NULL CHECK(email LIKE '%_@_%._%'),
    phone       TEXT CHECK(phone IS NULL OR length(phone) >= 10),
    member_since DATE DEFAULT (datetime('now')),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Visit table with enhanced constraints
CREATE TABLE IF NOT EXISTS visit(
    visit_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id    INTEGER NOT NULL REFERENCES guest(guest_id) ON DELETE CASCADE,
    museum_id   INTEGER NOT NULL REFERENCES museum(museum_id) ON DELETE CASCADE,
    visited_on  DATE NOT NULL CHECK(visited_on <= date('2026-01-01')),
    duration_minutes INTEGER CHECK(duration_minutes IS NULL OR duration_minutes > 0),
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Upkeep/Maintenance table with enhanced constraints
CREATE TABLE IF NOT EXISTS upkeep(
    upkeep_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES item(item_id) ON DELETE CASCADE,
    task        TEXT NOT NULL CHECK(length(trim(task)) > 0),
    done_on     DATE NOT NULL CHECK(done_on <= date('done_on')),
    technician  TEXT NOT NULL CHECK(length(trim(technician)) > 0),
    cost        DECIMAL(10,2) CHECK(cost IS NULL OR cost >= 0),
    notes       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User authentication table for security
CREATE TABLE IF NOT EXISTS user(
    user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL CHECK(length(username) >= 3),
    password_hash TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('admin', 'curator', 'staff', 'viewer')),
    email       TEXT UNIQUE NOT NULL CHECK(email LIKE '%_@_%._%'),
    is_active   INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    last_login  DATETIME,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for security tracking
CREATE TABLE IF NOT EXISTS audit_log(
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES user(user_id),
    action      TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    record_id   INTEGER,
    old_values  TEXT,
    new_values  TEXT,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address  TEXT
);

-- ==================== TRIGGERS FOR DATA INTEGRITY ====================

-- Trigger: Update timestamp on museum modification
CREATE TRIGGER IF NOT EXISTS museum_update_timestamp
AFTER UPDATE ON museum
FOR EACH ROW
BEGIN
    UPDATE museum SET updated_at = CURRENT_TIMESTAMP WHERE museum_id = NEW.museum_id;
END;

-- Trigger: Update timestamp on item modification
CREATE TRIGGER IF NOT EXISTS item_update_timestamp
AFTER UPDATE ON item
FOR EACH ROW
BEGIN
    UPDATE item SET updated_at = CURRENT_TIMESTAMP WHERE item_id = NEW.item_id;
END;

-- Trigger: Update timestamp on guest modification
CREATE TRIGGER IF NOT EXISTS guest_update_timestamp
AFTER UPDATE ON guest
FOR EACH ROW
BEGIN
    UPDATE guest SET updated_at = CURRENT_TIMESTAMP WHERE guest_id = NEW.guest_id;
END;

-- Trigger: Prevent deletion of museums with active items
CREATE TRIGGER IF NOT EXISTS prevent_museum_deletion_with_items
BEFORE DELETE ON museum
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM item WHERE museum_id = OLD.museum_id AND status = 'active') > 0
BEGIN
    SELECT RAISE(ABORT, 'Cannot delete museum with active items');
END;

-- Trigger: Validate visit date is not in future
CREATE TRIGGER IF NOT EXISTS validate_visit_date
BEFORE INSERT ON visit
FOR EACH ROW
WHEN NEW.visited_on > datetime('now')
BEGIN
    SELECT RAISE(ABORT, 'Visit date cannot be in the future');
END;

-- Trigger: Audit log for user changes
CREATE TRIGGER IF NOT EXISTS audit_user_update
AFTER UPDATE ON user
FOR EACH ROW
BEGIN
    INSERT INTO audit_log(user_id, action, table_name, record_id, old_values, new_values)
    VALUES (OLD.user_id, 'UPDATE', 'user', OLD.user_id,
            json_object('username', OLD.username, 'role', OLD.role),
            json_object('username', NEW.username, 'role', NEW.role));
END;

-- ==================== INDEXES FOR PERFORMANCE ====================

-- Index on museum name for fast lookups
CREATE INDEX IF NOT EXISTS idx_museum_name ON museum(name);
CREATE INDEX IF NOT EXISTS idx_museum_city ON museum(city);

-- Indexes on item for common queries
CREATE INDEX IF NOT EXISTS idx_item_museum ON item(museum_id);
CREATE INDEX IF NOT EXISTS idx_item_category ON item(category);
CREATE INDEX IF NOT EXISTS idx_item_status ON item(status);
CREATE INDEX IF NOT EXISTS idx_item_acquired ON item(acquired);

-- Indexes on guest for email searches
CREATE INDEX IF NOT EXISTS idx_guest_email ON guest(email);
CREATE INDEX IF NOT EXISTS idx_guest_name ON guest(full_name);

-- Composite index for visit queries
CREATE INDEX IF NOT EXISTS idx_visit_guest_museum ON visit(guest_id, museum_id);
CREATE INDEX IF NOT EXISTS idx_visit_date ON visit(visited_on);
CREATE INDEX IF NOT EXISTS idx_visit_museum_date ON visit(museum_id, visited_on);

-- Index on upkeep for maintenance tracking
CREATE INDEX IF NOT EXISTS idx_upkeep_item ON upkeep(item_id);
CREATE INDEX IF NOT EXISTS idx_upkeep_date ON upkeep(done_on);

-- Index on user for authentication
CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- Index on audit log for security analysis
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name, record_id);

-- ==================== VIEWS FOR COMMON QUERIES ====================

-- View: Museum statistics
CREATE VIEW IF NOT EXISTS museum_stats AS
SELECT
    m.museum_id,
    m.name,
    m.city,
    COUNT(DISTINCT i.item_id) as total_items,
    COUNT(DISTINCT v.visit_id) as total_visits,
    COUNT(DISTINCT u.upkeep_id) as total_maintenance
FROM museum m
LEFT JOIN item i ON m.museum_id = i.museum_id
LEFT JOIN visit v ON m.museum_id = v.museum_id
LEFT JOIN upkeep u ON i.item_id = u.item_id
GROUP BY m.museum_id;

-- View: Item maintenance history
CREATE VIEW IF NOT EXISTS item_maintenance_view AS
SELECT
    i.item_id,
    i.title,
    i.category,
    m.name as museum_name,
    u.task,
    u.done_on,
    u.technician,
    u.cost
FROM item i
JOIN museum m ON i.museum_id = m.museum_id
LEFT JOIN upkeep u ON i.item_id = u.item_id
ORDER BY u.done_on DESC;

-- View: Visitor activity summary
CREATE VIEW IF NOT EXISTS visitor_activity AS
SELECT
    g.guest_id,
    g.full_name,
    g.email,
    COUNT(DISTINCT v.museum_id) as museums_visited,
    COUNT(v.visit_id) as total_visits,
    MIN(v.visited_on) as first_visit,
    MAX(v.visited_on) as last_visit
FROM guest g
LEFT JOIN visit v ON g.guest_id = v.guest_id
GROUP BY g.guest_id;

