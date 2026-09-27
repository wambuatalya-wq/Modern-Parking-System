 AUTOMATED PARKING MANAGEMENT SYSTEM :
This is a web-based automated parking system built for drivers  to see live slot
availability before entry. The arrivals and exits are recorded automatically, fees
are calculated dynamically from a database andthe exit barrier only opens once
the payment is confirmed.
 
  PROJECT STRACTURE :
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
