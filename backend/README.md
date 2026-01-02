# HeritagePlus Museum Group Management System

## Multi-Tiered Architecture Implementation

A comprehensive museum management system demonstrating a complete multi-tiered architecture with presentation, business logic, and data access layers, plus robust security and performance optimization.

---

## Project Structure

```
museum-system/
├── backend/
│   ├── __init__.py
│   ├── connection.py           # Data Access - Connection management
│   ├── repositories.py         # Data Access - Repository pattern
│   ├── business_logic.py       # Business Layer - Business rules
│   ├── security.py             # Business Layer - Authentication & Authorization
│   ├── schema.sql              # Database schema with constraints & triggers
│   └── museum.db               # SQLite database (generated)
├── frontend/
│   ├── __init__.py
│   └── cli_interface.py        # Presentation Layer - CLI interface
├── museum.py                    # Main application entry point
└── README.md                    # This file
```

---

## Architecture Overview

### 1. **Presentation Layer** (`frontend/cli_interface.py`)
- Interactive command-line interface
- User input validation and formatting
- Menu-driven navigation
- Error handling and user feedback
- Role-based interface adaptation

### 2. **Business Logic Layer** (`backend/business_logic.py` & `backend/security.py`)
- **Business Services:**
  - MuseumService: Museum operations and capacity management
  - ExhibitService: Exhibit management with status tracking
  - VisitorService: Visitor registration and recommendations
  - MaintenanceService: Maintenance scheduling and cost analysis
  - ReportingService: Analytics and executive summaries

- **Security Services:**
  - Authentication: User login, password hashing, session management
  - Authorization: Role-based access control (RBAC)
  - Input Validation: Comprehensive input sanitization
  - Audit Logging: Security event tracking

### 3. **Data Access Layer** (`backend/repositories.py` & `backend/connection.py`)
- Repository pattern for data abstraction
- Connection pooling and optimization
- Transaction management
- Error handling and retry logic
- Query optimization with prepared statements

---

## Usage

### Initial Setup

When you first run the application:
1. Database is automatically initialized with schema
2. Sample data is seeded
3. Default admin account is created
   - Username: `admin`
   - Password: `admin123`

### Running the Application

```bash
python museum.py
```

You'll see three options:
1. **Interactive CLI Interface** - Full multi-tier demonstration
2. **Run Demo Queries Only** - See advanced queries in action
3. **Reset Database** - Reinitialize with fresh data

### User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **admin** | Full access: create, read, update, delete, manage users |
| **curator** | Create, read, update exhibits; manage exhibits |
| **staff** | Read, update, create visits |
| **viewer** | Read-only access |

### Example Workflows

#### 1. Adding a New Museum
```
Login → Museum Management → Add New Museum
→ Enter name and city
→ Success message displayed
```

#### 2. Registering a Visitor and Recording Visit
```
Login → Visitor Management → Register New Visitor
→ Enter details
→ Record Museum Visit
→ Enter visitor ID, museum ID, date
```

#### 3. Scheduling Maintenance
```
Login → Maintenance Management → Schedule Maintenance
→ Enter exhibit ID, task, date, technician
→ Optionally enter cost
```

#### 4. Viewing Reports
```
Login → Reports & Analytics → Executive Summary
→ View organization-wide statistics
```

---

## Advanced Queries Demonstrated

### 1. Top Exhibits by Maintenance
```sql
SELECT title, COUNT(upkeep_id) AS maintenance_count
FROM item
LEFT JOIN upkeep USING(item_id)
GROUP BY item_id
ORDER BY maintenance_count DESC, title
```

### 2. Visitor Activity Summary
```sql
SELECT full_name, COUNT(DISTINCT museum_id) AS museums_visited
FROM guest
JOIN visit USING(guest_id)
GROUP BY guest_id
ORDER BY museums_visited DESC
```

### 3. Maintenance Cost Analysis
```sql
SELECT
    COUNT(*) as total_tasks,
    SUM(COALESCE(cost, 0)) as total_cost,
    AVG(COALESCE(cost, 0)) as avg_cost
FROM upkeep
WHERE done_on BETWEEN ? AND ?
```

### 4. Items Needing Maintenance
```sql
SELECT i.item_id, i.title, MAX(u.done_on) as last_maintenance
FROM item i
LEFT JOIN upkeep u ON i.item_id = u.item_id
WHERE i.status = 'active'
GROUP BY i.item_id
HAVING last_maintenance IS NULL OR last_maintenance < ?
```

### 5. Museum Performance Report
- Combines multiple queries
- Joins across museum, item, visit tables
- Temporal analysis (visitor trends)
- Category distribution

---

## Security Features

### Authentication
- Password hashing using SHA-256 with random salt
- Session management with last login tracking
- Account activation/deactivation
- Password change functionality

### Authorization
- Role-based access control (RBAC)
- Permission checks on every operation
- Hierarchical role system
- Granular permissions per role

### Input Validation
- Email format validation
- Date validation (no future dates for historical records)
- Positive integer validation
- SQL injection prevention through parameterized queries
- String sanitization

### Audit Trail
- All user actions logged
- Change tracking (old/new values)
- Timestamp and user ID for every action
- IP address logging capability

---

## Performance Optimizations

### Database Level
- **Indexes**: 14 strategic indexes on high-traffic columns and joins
- **Views**: Pre-computed aggregations for common queries
- **WAL Mode**: Write-Ahead Logging for concurrent access
- **Cache**: 64MB cache size for in-memory operations
- **ANALYZE**: Statistics for query optimizer

### Application Level
- **Connection Pooling**: Reuse connections efficiently
- **Prepared Statements**: Pre-compiled queries
- **Transaction Management**: Batch operations
- **Retry Logic**: Handle database locks gracefully
- **Resource Cleanup**: Proper connection closure

### Query Optimization
- Selective column retrieval (avoid SELECT *)
- Efficient JOINs with proper indexes
- LIMIT clauses for large result sets
- Composite indexes for multi-column queries

---

## Testing

### Manual Testing
Run the demo queries to see system capabilities:
```bash
python museum.py
# Select option 2: Run Demo Queries Only
```

### Test User Accounts
Create test accounts with different roles to verify authorization:
```python
# In CLI:
# Create Account → Enter details with different roles
# Test access to different features
```

---

## How This Meets Distinction Requirements

### ✅ Multi-Tiered Architecture
- **Presentation Layer**: `frontend/cli_interface.py` provides complete user interaction
- **Business Layer**: `backend/business_logic.py` and `backend/security.py` implement all business rules
- **Data Access Layer**: `backend/repositories.py` and `backend/connection.py` abstract database operations
- **Clear Separation**: Each layer has distinct responsibilities, communicates through well-defined interfaces

### ✅ Data Integrity
- **Constraints**: 15+ CHECK constraints, UNIQUE constraints, NOT NULL, Foreign Keys
- **Triggers**: 6 triggers for automatic updates, validation, and audit logging
- **Relationships**: Proper CASCADE on all foreign keys
- **Views**: 3 views for complex aggregations

### ✅ Security
- **Authentication**: Password hashing, session management, role-based login
- **Authorization**: 4-tier role system with granular permissions
- **Input Validation**: Comprehensive validation for all user inputs
- **Audit Log**: Complete tracking of security-relevant actions

### ✅ Performance
- **14 Indexes**: Strategic indexing on all frequently queried columns
- **Connection Management**: Pooling, retry logic, timeout handling
- **Query Optimization**: Prepared statements, efficient JOINs, LIMIT clauses
- **Database Tuning**: WAL mode, 64MB cache, ANALYZE statistics

### ✅ Functional Application
- **Complete System**: Fully functional museum management system
- **Interactive**: Menu-driven CLI with real-time feedback
- **Robust**: Error handling, validation, and user guidance
- **Demonstrable**: Easy to show all features through the interface

---


