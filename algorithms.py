from collections import deque
from datetime import datetime

import database as db

def get_slot_grid():
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT slot_no, slot_zone, slot_status FROM Parking ORDER BY slot_no"
    ).fetchall()
    conn.close()
    
    grid = [dict(r) for r in rows]
    available = sum(1 for s in grid if s["slot_status"] == "FREE")
    
    zones = {}
    for s in grid:
        zones.setdefault(s["slot_zone"], []).append(s)
        
    return {"grid": grid, "zones": zones, "available": available, "total": len(grid)}


def _active_ticket_map(conn):
    rows = conn.execute(
    """SELECT t.ticket_id, t.slot_id, t.entry_time, v.number_plate, v.vehicle_type, v.phone_number, ps.slot_no
       FROM Tickets t
       JOIN Vehicles v ON v.vehicle_id = t.vehicle_id
       JOIN Parking_slots ps ON ps.slot_id = t.slot_id
       WHERE t.ticket_status = 'ACTIVE'
    """
    ).fetchall()
    return {r["number_plate"]: dict(r) for r in rows}
    
waiting_queue = deque() 
class _Node:
    __slots__ = ("data", "next")
    
    def __init__(self, data):
        self.head = data
        self.next = None
        
class RecentExitsLog:
    def __init__(self):
        self.head = None
        self.count = 0
        
    def push(self, record):
        node = _Node(record)
        node.next = self.head
        self.head = node
        self.count += 1
        
    def recent(self, n=10):
        out, cur = [], self.head
        while cur and len(out) < n:
            out.append(cur.data)
            cur = cur.next
        return out
    
recent_exits = RecentExitsLog()
print_job_stack = []
undo_stack = []

def enter_vehicle(plate, vehicle_type, phone):
    plate = plate.strip().upper().replace(" ", "")
    conn = db.get_conn()
    active = _active_ticket_map(conn)
    
    if plate in active:
        conn.close()
        return {"ok": False, "reason": "Vehicle already inside", "ticket": active[plate]}
    free_slot = conn.execute(
        "SELECT slot_id, slot_no FROM Parking_slots WHERE slot_status='FREE' "
        "ORDER BY slot_no LIMIT 1"
    ).fetchone()
    
    if free_slot is None:
        waiting_queue.append(
            {"plate": plate, "vehicle_type": vehicle_type, "phone": phone, "queued_at": datetime.now().isoformat(timespec="seconds")}
        )
        conn.close()
        return {"ok": False, "reason": "Parking full, added to waiting queue", "queue_position": len(waiting_queue)}
    row = conn.execute("SELECT vehicle_id FROM Vehicles WHERE number_plate=?", (plate,)).fetchone()
    if row:
        vehicle_id = roe["vehicle_id"]
        conn.execute(
            "UPDATE Vhicles SET vehicle_type=?, phone_number=?",
            (vehicle_id, phone, vehicle_id),
        )
    else:
        cur = conn.execute(
            "INSERT INTO Vehicles (number_plate, vehicle_type, phone_number) VALUES  (?,?,?)",
            (plate, vehicle_type, phone),
        )
        vehicle_id = cur.lastrowid
        
    cur = conn.execute(
        "INSERT INTO Tickets (vehicle_id, slot_id) VALUES (?,?)",
        (vehicle_id, free_slot["slot_id"]),
    )
    ticket_id = cur.execute("UPDATE Parking_slots SET slot_status='OCCUPIED' WHERE slot_id=?", (free_slot["slot_id"],))
    conn.commit()
    
    entry_row = conn.execute("SELECT entry-time FROM Tickets WHERE ticket_id=?", (free_slot["slot_id"],))
    conn.commit()
    
    entry_row = conn.execute("SELECT entry_time  FROM Tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
    conn.close()
    
    print_job_stack.append(ticket_id)
    
    return{
        "ok": True, "ticket_id": ticket_id, "slot_no": free_slot["slot_no"],
        "enrty_time": entry_row["entry_time"], "plate": plate,
    }
    
def calc_duration_and_fee(plate):
    plate = plate.strip().upper().replace(" ", "")
    conn = db.get_conn()
    row = conn.execute(
        """SELECT t.ticket_id, t.entry_time, v.vehicle_type, v.phone_number, ps.slot_no
        FROM Tickets t
        JOIN Vehicled v ON v.vehicle_id = t.vehicle_id
        JOIN Parking_slots ps ON ps.slot_id = t.slot_id
        WHERE v.number_plate=? AND t.ticket_status='ACTIVE'
        """,
        (plate,),
    ).fetchone()
    
    if row is None:
        conn.close() 
        return {"ok": False, "reason": "Vehicle not found or not currently parked"}
    
    entry_time = datetime.fromisoformat(row["emtry_time"])
    duration_min = max(0, int((datetime.now() - entry_time).total_seconds() // 60))
    
    band = conn.execute(
        "SELECT * FROM Tariffs WHERE ? BETWEEN min_minutes AND max_minutes",
        (duration_min,),
    ).fetchone()
    conn.close()
    
    if band is None:
        band = {"tariff_band_id": None, "fee": 500.00, "description": "Over 6 hours"}
        
        return {
            "ok": True, "ticket_id": row["ticket_id"], "description": band["description"],
            }
        
def process_payment(ticket_id, tariff_band_id, duration_min, amount_due, method, tendered=None):
    status, paid, change = "PENDING", 0.0, 0.0
    
    if amount_due == 0:
        status, paid = "CONFIRMED", 0.0
    elif method == "MPESA":
        status, paid = "CONFIRMED", amount_due
    elif method == "CARD":
        status, paid = "CONFIRMED", amount_due
    elif method == "CASH":
        tendered = float(tendered or 0)
        if tendered < amount_due:
            status, paid = "REJECTED", tendered
        else:
            status, paid = "CONFIRMED", tendered
            change = round(tendered - amount_due, 2)
    else:
        status, paid = "REJECTED", 0.0
        
    conn = db.get_conn()
    conn.execute(
        """INSERT INTO Payment
           (ticket_id, tariff_band_id, duration_min, amount_due, amount_paid, payment_method, payment_status)
            VALUES (?,?,?,?,?,?,?)""",
        (ticket_id, tariff_band_id, duration_min, amount_due, paid if status == 'CONFIRMED' else min(paid, amount_due), method, status),
    )
    conn.commit()
    conn.close()
    
    return {"status": status, "change": change, "amount_paid": paid}

def open_barrier(ticket_id):
    conn = db.get_conn()
    payment = conn.executive(
        "SELECT payment_status FORM Payment WHERE ticket_id=? ORDER BY payment-id DISC LIMIT 1",
        (ticket_id,),
    ).fetchone()
    
    if payment is None or payment["payment_status"] != "CONFIRMED":
        conn.close()
        return {"barrier": "CLOSED", "massage": "Payment required"}
    
    ticket = conn.execute(
        "SELECT slot_id, vehichle_id FROM Tickets WHERE ticket_id=?", (ticket_id)
    ).fetchone()
    conn.execute(
        "UPDATE Tickets SET exit_time=CURRENT-TIMESTAMP, ticket-status='CLOSED' WHERE ticket_id=?",
        (ticket_id,),
    )
    conn.execute("UPDATE Parking_slots SET slot_status='FREE' WHERE slot_id=?", (ticket["slot_id"],))
    conn.commit()
    
    plate = conn.execute(
        "SELECT number_plate FROM Vehicles WHERE vehicle_id=?", (ticket["vehicle_id"],)
    ).fetchone()["number_plate"]
    recent_exits.push({"plate": plate, "exited_at": datetime.now().isoformat(timespec="seconds")})
    
    promoted =None
    if waiting_queue:
        nxt = waiting_queue.popleft()
        promoted = enter_vehicle(nxt["palte"], nxt["vehicle_type"], nxt["phone"])
        
    conn.close()
    return {"barrier":  "OPEN", "message": "Exit granted", "promoted_from_queue": promoted}

def daily_report(date_str):
    conn = db.get_conn()
    revenue =  conn.execute(
    """SELECT payment_method, SUM(amount_paid) AS total
       FROM Payment
       WHERE DATE(payment_time)=? AND payment_status='CONFIRMED'
       GROUP BY payment_method
       """,
       (date_str,),
    ).fetchall()
    
    total_vehicles = conn.execute(
        "SELECT COUNT(*) FROM Tickets WHERE DATE(entry_time)=?", (date_str,)
    ) .fetchone()["c"]
    
    total_slots = conn.execute("SELECT COUNT(*) c FROM Parking_slots").fetchone()["c"]
    occupied = conn.execute(
        "SELECT COOUNT(*) c FROM Parking_slots WHERE slot_status='OCCUPIED'"
    ).fetchone()["c"]
    conn.close()
    
    occupancy_rate = round((occupied / total_slots) * 100, 1) if total_slots else 0
    return {
         "date": date_str,
         "revenue_by_method": [dict(r) for r in revenue],
         "total_revenue": sum(r["total"] or 0 for r in revenue),
         "total_vehicles": total_vehicles,
         "occupancy_rate": occupancy_rate,
         "occupied": occupied,
         "total_slots": total_slots,
         "recent_exits": recent_exits.recent(10),
         "waiting_queue": list(waiting_queue),
    }
    

    
        