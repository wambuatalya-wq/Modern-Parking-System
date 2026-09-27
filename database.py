import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).parent / "parking.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Vehucles (
    vehicle_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    number_plate  VARCHAR(15) NOT NULL UNIQUE,
    vehicle_type  VARCHAR(20),
    phone_number  VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS  Parking_slots(
    slot_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_no     VARCHAR(3) NOT NULL UNIQUE,
    slot_zone   VARCHAR(1) NOT NULL CHECK (slot_zone IN ('A','B','C','D')),
    slot_status VARCHAR(10) NOT NULL DEFAULT 'FREE' CHECK (slot_status IN ('FREE','OCCUPIED')) 
);

CREATE TABLE IF NOT EXIST Tickets(
    ticket_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id    INTEGER NOT NULL,
    slot_id       INTEGER NOT NULL,
    entry_time    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    exit_time     TIMESTAMP NULL,
    ticket_status VARCHAR(10) NOT NULL DEFAULT 'ACTIVE' CHECK (ticket_status IN ('ACTIVE','CLOSED')),
    FOREIGN KEY (vehicle_id) REFERENCES Vehicles(vehicle_id),
    FOREIGN KEY (slot_id) REFERENCES Parking_slots(slot_id)    
);

CREATE INDEX IF NOR EXISTS idx_active_tickets  ON Tickets(vehicle_id, ticket_status);

CREATE TABLE IF NOT EXISTS Tariffs(
    tariff_band_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    min_minutes      INTEGER NOT NULL,
    max_minutes      INTEGER NOT NULL,
    fee              DECIMAL(10,2) NOT NULL CHECK (fee >= 0),
    description      VARCHAR(100) NOT NULL,
    CHECK (min_minutes < max_minutes)
);

CREATE TABLE IF NOT EXISTS Payment(
    payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       INTEGER NOT NULL,
    tariff_band_id  INTEGER NOT NULL,
    duration_min    INTEGER NOT NULL,
    amount_due      DECIMAL(10,2) NOT NULL,
    amount_paid     DECIMAL(10,2) NOT NULL,
    payment_method  VARCHAR(10) NOT NULL DEFAULT 'CASH' CHECK (payment_method IN ('CASH','MPESA','CARD')),
    payment_status  VAARCHAR(10) NOT NULL DEFAULT 'PENDING' CHECK (payment_status IN ('PENDING','CONFIRMED','REJECTED')),
    payment_time    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id),
    FOREIGN KEY (tariff_band_id) REFERENCES Tariffs(tariff_band_id),
    CHECK (payment_status <> 'CONFIRMED' OR amount_paid >= amount_due)
);

CREATE TABLE IF NOT EXISTS Users(
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       VARCHAR(60) NOT NULL UNIQUE,
    user_password  VARCHAR(225) NOT NULL,
    user_role      VARCHAR(20) NOT NULL CHECK (user_role IN ('ADMIN','ATTENDANT'))
);

CREATE TABLE IF NOT EXISTS Audit_Log(
    log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    action    VARCHAR(100) NOT NULL,
    user_id   INTEGER NOT NULL,
    log_time  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);
"""
def get_conn():
    """Every gets its own short-lived connection (simpe and safe for SQLite, which does not like connections shared across threads)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
    
def init_db(reset=False):
    """Create tables and seeds reference/demo data if the DB is new."""
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        
    conn = get_conn()
    conn.executescript(SCHEMA)
    
    if conn.execute("SELECT COUNT(*) c FROM Tariffs").fetchone()["c"] == 0:
        conn.executemany(
            "INSERT INTO Tariffs (min_minutes, max_minutes, fee, description) VALUES (?,?,?,?)",
             [   
                (0, 30, 0.00, 'Up to 30 minutes is FREE'),   
                (31, 120, 50.00, '31 minutes to 2 hours'),
                (121, 240, 100.00, 'Over 2 hours to 4 hours'),
                (241, 360, 300.00, 'Over 4 hours to 6 hours'),
                (361, 99999, 500.00, 'Over 6 hours');
             ],
        )


    if conn.execute("SELECT  COUNT(*) c FROM Parking_slots").fetchone()["c"] == 0:
        slots = [(f"{z}{n}", z) for z in "ABCD" for n in range(1, 11)]
        conn.executemany(
            "INSERT INTO Parking_slots (slot_no, slot_zone) VALUES (?,?)", slots
        )
    
    if conn.execute("SELECT COUNT(*) c FROM Users").fetchone()["c"] == 0:
        conn.execute(
            "INSERT INTO Users (username, user_password, user_role) VALUES (?,?,?)",
            ("admin", generate_password_hash("admin123"), "ADMIN"),
        )
        conn.execute(
             "INSERT INTO Users (username, user_password, user_role) VALUES (?,?,?)",
             ("attendant", generate_password_hash("attendant1234"), "ATTENDANT"),
        )
    
    conn.commit()
    conn.close()
    
def log_action(user_id, action):
    """Writes one row to Audit_Log. Called by every state-changing route."""
    conn = get_conn()
    conn.execute("INSERT INTO Audit_Log (action, user_id) VALUES (?,?)", (action, user_id))
    conn.commit()
    conn.close()
    
    
