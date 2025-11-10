from flask import Flask, render_template, request, redirect, url_for, flash
from db_config import get_db_connection

app = Flask(__name__)
app.secret_key = 'replace_with_a_random_secret'

# Home
@app.route('/')
def index():
    return render_template('index.html')

# ==================== FACILITIES ====================
@app.route('/facilities')
def facilities():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT f.FacilityID, f.FacilityName, ft.TypeName AS FacilityType, f.Location, f.Capacity, f.Status FROM Facility f LEFT JOIN FacilityType ft ON f.FacilityTypeID=ft.FacilityTypeID;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template('facilities.html', facilities=rows)

@app.route('/facilities/add', methods=['GET','POST'])
def add_facility():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        type_id = request.form.get('type_id') or None
        location = request.form.get('location')
        capacity = request.form.get('capacity') or None
        cur.execute("INSERT INTO Facility (FacilityName, FacilityTypeID, Location, Capacity) VALUES (%s,%s,%s,%s);",
                    (name, type_id, location, capacity))
        conn.commit()
        flash('Facility added', 'success')
        cur.close(); conn.close()
        return redirect(url_for('facilities'))
    cur.execute("SELECT FacilityTypeID, TypeName FROM FacilityType;")
    types = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_facility.html', types=types)

@app.route('/facilities/edit/<int:fid>', methods=['GET','POST'])
def edit_facility(fid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        type_id = request.form.get('type_id') or None
        location = request.form.get('location')
        capacity = request.form.get('capacity') or None
        status = request.form.get('status')
        cur.execute("UPDATE Facility SET FacilityName=%s, FacilityTypeID=%s, Location=%s, Capacity=%s, Status=%s WHERE FacilityID=%s;",
                    (name, type_id, location, capacity, status, fid))
        conn.commit()
        flash('Facility updated', 'success')
        cur.close(); conn.close()
        return redirect(url_for('facilities'))
    cur.execute("SELECT * FROM Facility WHERE FacilityID=%s;", (fid,))
    facility = cur.fetchone()
    cur.execute("SELECT FacilityTypeID, TypeName FROM FacilityType;")
    types = cur.fetchall()
    cur.close(); conn.close()
    return render_template('edit_facility.html', facility=facility, types=types)

@app.route('/facilities/delete/<int:fid>')
def delete_facility(fid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Facility WHERE FacilityID=%s;", (fid,))
    conn.commit()
    cur.close(); conn.close()
    flash('Facility deleted', 'info')
    return redirect(url_for('facilities'))

# ==================== STAFF ====================
@app.route('/staff')
def staff():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT s.*, d.DepartmentName FROM Staff s LEFT JOIN Department d ON s.DepartmentID=d.DepartmentID;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template('staff.html', staff=rows)

@app.route('/staff/add', methods=['GET','POST'])
def add_staff():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        role = request.form.get('role')
        email = request.form.get('email')
        contact = request.form.get('contact')
        dept = request.form.get('department') or None
        cur.execute("INSERT INTO Staff (StaffName, Role, Email, ContactNumber, DepartmentID) VALUES (%s,%s,%s,%s,%s);",
                    (name, role, email, contact, dept))
        conn.commit()
        flash('Staff added', 'success')
        cur.close(); conn.close()
        return redirect(url_for('staff'))
    cur.execute("SELECT DepartmentID, DepartmentName FROM Department;")
    deps = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_staff.html', departments=deps)

@app.route('/staff/edit/<int:sid>', methods=['GET','POST'])
def edit_staff(sid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        role = request.form.get('role')
        email = request.form.get('email')
        contact = request.form.get('contact')
        dept = request.form.get('department') or None
        cur.execute("UPDATE Staff SET StaffName=%s, Role=%s, Email=%s, ContactNumber=%s, DepartmentID=%s WHERE StaffID=%s;",
                    (name, role, email, contact, dept, sid))
        conn.commit()
        flash('Staff updated', 'success')
        cur.close(); conn.close()
        return redirect(url_for('staff'))
    cur.execute("SELECT * FROM Staff WHERE StaffID=%s;", (sid,))
    staff_member = cur.fetchone()
    cur.execute("SELECT DepartmentID, DepartmentName FROM Department;")
    deps = cur.fetchall()
    cur.close(); conn.close()
    return render_template('edit_staff.html', staff=staff_member, departments=deps)

@app.route('/staff/delete/<int:sid>')
def delete_staff(sid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Staff WHERE StaffID=%s;", (sid,))
    conn.commit()
    cur.close(); conn.close()
    flash('Staff deleted', 'info')
    return redirect(url_for('staff'))

# ==================== RESERVATIONS ====================
@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    import mysql.connector  # make sure this line exists near the top of your file
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        facility = request.form['facility']
        staff = request.form['staff']
        purpose = request.form.get('purpose')
        start = request.form.get('start')
        end = request.form.get('end')

        try:
            # Prevent reservation overlap with maintenance (for same date)
            cur.execute("""
                SELECT COUNT(*) AS cnt FROM Maintenance
                WHERE FacilityID = %s AND DATE(MaintenanceDate) = DATE(%s);
            """, (facility, start))
            overlap = cur.fetchone()['cnt']

            if overlap > 0:
                flash('❌ This facility is under maintenance on the selected date.', 'danger')
            else:
                cur.execute("""
                    INSERT INTO Reservation (Purpose, StartTime, EndTime, FacilityID, StaffID)
                    VALUES (%s,%s,%s,%s,%s);
                """, (purpose, start, end, facility, staff))
                conn.commit()
                flash('✅ Reservation created successfully!', 'success')

        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", 'danger')

        finally:
            cur.close()
            conn.close()
            return redirect(url_for('reservations'))

    # GET request → show reservations list + form
    cur.execute("""
        SELECT r.ReservationID, r.Purpose, r.StartTime, r.EndTime,
               f.FacilityName, s.StaffName
        FROM Reservation r
        LEFT JOIN Facility f ON r.FacilityID=f.FacilityID
        LEFT JOIN Staff s ON r.StaffID=s.StaffID;
    """)
    reservations = cur.fetchall()

    cur.execute("SELECT FacilityID, FacilityName FROM Facility;")
    facilities = cur.fetchall()

    cur.execute("SELECT StaffID, StaffName FROM Staff;")
    staff = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('reservations.html', reservations=reservations, facilities=facilities, staff=staff)


@app.route('/reservations/edit/<int:rid>', methods=['GET','POST'])
def edit_reservation(rid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        facility = request.form['facility']
        staff = request.form['staff']
        purpose = request.form.get('purpose')
        start = request.form.get('start')
        end = request.form.get('end')
        cur.execute("UPDATE Reservation SET Purpose=%s, StartTime=%s, EndTime=%s, FacilityID=%s, StaffID=%s WHERE ReservationID=%s;",
                    (purpose, start, end, facility, staff, rid))
        conn.commit()
        flash('Reservation updated', 'success')
        cur.close(); conn.close()
        return redirect(url_for('reservations'))
    cur.execute("SELECT * FROM Reservation WHERE ReservationID=%s;", (rid,))
    reservation = cur.fetchone()
    cur.execute("SELECT FacilityID, FacilityName FROM Facility;")
    facilities = cur.fetchall()
    cur.execute("SELECT StaffID, StaffName FROM Staff;")
    staff = cur.fetchall()
    cur.close(); conn.close()
    return render_template('edit_reservation.html', reservation=reservation, facilities=facilities, staff=staff)

@app.route('/reservations/delete/<int:rid>')
def delete_reservation(rid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Reservation WHERE ReservationID=%s;", (rid,))
    conn.commit()
    cur.close(); conn.close()
    flash('Reservation deleted', 'info')
    return redirect(url_for('reservations'))

# ==================== EQUIPMENT ====================
@app.route('/equipment')
def equipment():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT e.*, f.FacilityName FROM Equipment e LEFT JOIN Facility f ON e.FacilityID=f.FacilityID;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template('equipment.html', equipment=rows)

@app.route('/equipment/add', methods=['GET','POST'])
def add_equipment():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        eq_type = request.form.get('type')
        quantity = request.form.get('quantity') or 1
        facility = request.form.get('facility') or None
        cur.execute("INSERT INTO Equipment (EquipmentName, EquipmentType, Quantity, FacilityID) VALUES (%s,%s,%s,%s);",
                    (name, eq_type, quantity, facility))
        conn.commit()
        flash('Equipment added', 'success')
        cur.close(); conn.close()
        return redirect(url_for('equipment'))
    cur.execute("SELECT FacilityID, FacilityName FROM Facility;")
    facilities = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_equipment.html', facilities=facilities)

@app.route('/equipment/edit/<int:eid>', methods=['GET','POST'])
def edit_equipment(eid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        eq_type = request.form.get('type')
        quantity = request.form.get('quantity') or 1
        facility = request.form.get('facility') or None
        cur.execute("UPDATE Equipment SET EquipmentName=%s, EquipmentType=%s, Quantity=%s, FacilityID=%s WHERE EquipmentID=%s;",
                    (name, eq_type, quantity, facility, eid))
        conn.commit()
        flash('Equipment updated', 'success')
        cur.close(); conn.close()
        return redirect(url_for('equipment'))
    cur.execute("SELECT * FROM Equipment WHERE EquipmentID=%s;", (eid,))
    equipment = cur.fetchone()
    cur.execute("SELECT FacilityID, FacilityName FROM Facility;")
    facilities = cur.fetchall()
    cur.close(); conn.close()
    return render_template('edit_equipment.html', equipment=equipment, facilities=facilities)

@app.route('/equipment/delete/<int:eid>')
def delete_equipment(eid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Equipment WHERE EquipmentID=%s;", (eid,))
    conn.commit()
    cur.close(); conn.close()
    flash('Equipment deleted', 'info')
    return redirect(url_for('equipment'))

# ==================== MAINTENANCE ====================
@app.route('/maintenance')
def maintenance():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT m.*, f.FacilityName FROM Maintenance m LEFT JOIN Facility f ON m.FacilityID=f.FacilityID;")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template('maintenance.html', maintenance=rows)

@app.route('/maintenance/add', methods=['GET','POST'])
def add_maintenance():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        m_type = request.form.get('type')
        m_date = request.form.get('date')
        facility = request.form.get('facility') or None
        description = request.form.get('description')
        cur.execute("INSERT INTO Maintenance (MaintenanceType, MaintenanceDate, FacilityID, Description) VALUES (%s,%s,%s,%s);",
                    (m_type, m_date, facility, description))
        conn.commit()
        flash('Maintenance added', 'success')
        cur.close(); conn.close()
        return redirect(url_for('maintenance'))
    cur.execute("SELECT FacilityID, FacilityName FROM Facility;")
    facilities = cur.fetchall()
    cur.close(); conn.close()
    return render_template('add_maintenance.html', facilities=facilities)

@app.route('/maintenance/edit/<int:mid>', methods=['GET','POST'])
def edit_maintenance(mid):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    if request.method == 'POST':
        m_type = request.form.get('type')
        m_date = request.form.get('date')
        facility = request.form.get('facility') or None
        description = request.form.get('description')
        cur.execute("UPDATE Maintenance SET MaintenanceType=%s, MaintenanceDate=%s, FacilityID=%s, Description=%s WHERE MaintenanceID=%s;",
                    (m_type, m_date, facility, description, mid))
        conn.commit()
        flash('Maintenance updated', 'success')
        cur.close(); conn.close()
        return redirect(url_for('maintenance'))
    cur.execute("SELECT * FROM Maintenance WHERE MaintenanceID=%s;", (mid,))
    maintenance = cur.fetchone()
    cur.execute("SELECT FacilityID, FacilityName FROM Facility;")
    facilities = cur.fetchall()
    cur.close(); conn.close()
    return render_template('edit_maintenance.html', maintenance=maintenance, facilities=facilities)

@app.route('/maintenance/delete/<int:mid>')
def delete_maintenance(mid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Maintenance WHERE MaintenanceID=%s;", (mid,))
    conn.commit()
    cur.close(); conn.close()
    flash('Maintenance deleted', 'info')
    return redirect(url_for('maintenance'))

if __name__ == '__main__':
    app.run(debug=True)
