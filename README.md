                  AUTOMATED PARKING MANAGEMENT SYSYTEM
This a web-based automated parking system built to allow drivers to see live slot availability
before entry, arrivals and exits are recorded automatically, fees are calculated dynamically
from a database and the exit barrier only opens once payment is confirmed

Client requirements are covered in modules:
Module 1 — Slot availability display
     Drivers see a visual display of available slots before entry
Modules 2 & 3 — Vehicle entry & slot allocation
    System records vehicles on arrival
Module 4 — Duration & fee calculation
    System automatically calculates time spent and amount to pay on exit
Modules 5 & 6 — Payment collection & barrier control
    Barrier opens on payment of fees

Two additional models are added to manage certain aspects of the system:
Module 7 — Admin & reporting
    Management needs visibility into revenue, occupancy and traffic — implicit in "automate
    their operations"

PROJECT STRACTURE:
 parking_system/
├── app.py             # Flask routes — the web front end
├── algorithms.py       # Modules 1-7 + the five data structures
├── database.py         # SQLite schema + seeding (mirrors schema.sql)
├── schema.sql           # Corrected MySQL DDL — the formal database design (Task 1c)
├── requirements.txt
├── .gitignore
├── templates/
│   ├── base.html        # Shared layout, nav, flash messages
│   ├── index.html        # Module 1 — slot grid
│   ├── entry.html         # Modules 2/3 — entry form
│   ├── exit.html           # Modules 4/5 — fee lookup + payment
│   ├── login.html           # Staff login
│   └── admin.html            # Module 7 — daily report
└── static/style.css 
