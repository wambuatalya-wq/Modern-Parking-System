
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import date
from database import check_password

import database as db
import algorithms as algo

app = Flask(__name__) 
app.secret_key = "dev-secret-change-me"

db.init_db()

def current_user():
    return session.get("username"), session.get("role")

@app.route("/")
def home():
    """MODULE 1: Slot Availability Display."""
    data = algo.get_slot_grid()
    return render_template("index.html", **data)

@app.route("/entry", methods=["GET", "POST"])
def entry():
    """MODULE 2 AND 3: Vehicle entry and Slot allocation."""
    if request.method == "POST":
        plate = request.form["plate"]
        vtype = request.form.get("vehicle_type","Car")
        phone = request.form.get("phone","")
        result = algo.enter_vehicle(plate, vtype, phone)
        
        if result["ok"]:
            flash(f"Ticket #{result['ticket_id']} issued - slot {result['slot_no']}.","success")
        else:
            flash(result["reason"], "error")
        return redirect(url_for("home"))
    
    return render_template("entry.html")


@app.route("/exit", methods=["GET", "POST"])
def  exit_lookup():
    """MODULE 4: Duration and Fee calculation"""
    result = None
    if request.method == "POST":
        plate = request.form["plate"]
        result = algo.calc_duration_and_fee(plate)
        if not result["ok"]:
            flash(result["reason"], "error")
            result = None
    return render_template("exit.html", result=result)

@app.route("/pay", methods=["POST"])
def pay():
    """MODULE 5 AND 6: Payment Collection and Barrier control."""
    ticket_id = int(request.form["ticket_id"])
    tariff_band_id = request.form.get("tariff_band_id") or None
    duration_min = int(request.form["duration_min"])
    amount_due = float(request.form["amount_due"])
    method = request.form["method"]
    tendered = request.form.get("tendered")
    
    outcome = algo.process_payment(ticket_id, tariff_band_id, duration_min, amount_due, method, tendered)
    
    if outcome["status"] != "CONFIRMED":
        flash(f"Payment {outcome['status'].lower()} - barrier stays closed.", "error")
        return redirect(url_for("exit_lookup"))
    
    barrier = algo.open_barrier(ticket_id)
    msg = "Payment confirmed, barrier open."
    if outcome["change"] > 0:
        msg += f" Change due: Kshs. {outcome['change']:.2f}."
    if barrier.get("promoted_from_queue") and barrier["promoted_from_queue"]["ok"]:
        p = barrier["promoted_from_queue"]
        msg += f" Next in queue ({p['plate']}) allocated  slot {p['slot_no']}."
    flash(msg, "success")
    return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = db.get_conn()
        user = conn.execute("SELECT * FROM Users WHERE username=?", (username,)).fetchone()
        conn.close()
        
        if user and check_password(user["user_password"], password):
            session["username"] = user["username"]
            session["role"] = user["user_role"]
            session["user_id"] = user["user_id"]
            db.log_action(user["user_id"], "LOGIN")
            return redirect(url_for("admin_report"))
        
        flash("Invalid username or password.", "error")
    return render_template("login.html") 

@app.route("/logout") 
def admin_report():
    """MODULE 7: Admin and Reporting"""
    username, role = current_user()
    if not username:
        return redirect(url_for("login"))
    
    selected_date = request.args.get("date", date.today().isoformat())
    report = algo.daily_report(selected_date)
    return render_template("admin.html", report=report, username=username, role=role)


if __name__ == "__main__":
    app.run(debug=True)
                     
    
    
    
    