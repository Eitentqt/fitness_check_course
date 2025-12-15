from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'fitness_key'

def get_db():
    conn = sqlite3.connect('fitness.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    conn = get_db()

    if request.method == 'POST':
        client_id = int(request.form['client_id'])
        now = datetime.now()
        conn.execute(
            "INSERT INTO visits (client_id, visit_date, checkin_time) VALUES (?, ?, ?)",
            (client_id, now.date(), now.strftime("%H:%M:%S"))
        )
        conn.commit()
        conn.close()
        flash('✅ Посещение зарегистрировано!')
        return redirect(url_for('checkin'))
    clients = conn.execute("""
        SELECT id, name, phone
        FROM clients
        ORDER BY name
    """).fetchall()
    conn.close()
    return render_template('checkin.html', clients=clients)

@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    membership_type = request.form['membership_type']

    if not name or not phone or not membership_type:
        flash('❌ Заполните ФИО, телефон и тип абонемента!')
        return redirect(url_for('checkin'))

    conn = get_db()
    try:
        cur = conn.execute("SELECT id FROM clients WHERE phone = ?", (phone,))
        row = cur.fetchone()
        if row:
            client_id = row['id']
        else:
            cur = conn.execute(
                "INSERT INTO clients (name, phone, join_date) VALUES (?, ?, ?)",
                (name, phone, date.today())
            )
            client_id = cur.lastrowid
        if membership_type == 'monthly':
            start_date = date.today()
            end_date = date(start_date.year, start_date.month, 28)
            visits_left = 12
        elif membership_type == 'yearly':
            start_date = date.today()
            end_date = date(start_date.year + 1, start_date.month, start_date.day)
            visits_left = 120
        else:
            start_date = date.today()
            end_date = start_date
            visits_left = 1
        conn.execute("""
            INSERT INTO memberships (client_id, type, start_date, end_date, visits_left, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        """, (client_id, membership_type, start_date, end_date, visits_left))
        conn.commit()
        flash('✅ Клиент и абонемент добавлены/обновлены.')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Ошибка: {e}')
    finally:
        conn.close()
    return redirect(url_for('checkin'))
@app.route('/reports')
def reports():
    conn = get_db()
    visits = conn.execute("""
        SELECT v.id,
               c.name,
               v.visit_date,
               v.checkin_time
        FROM visits v
        JOIN clients c ON v.client_id = c.id
        ORDER BY v.visit_date DESC, v.checkin_time DESC
        LIMIT 50
    """).fetchall()
    memberships = conn.execute("""
    SELECT c.id AS client_id,
           c.name,
           m.type,
           m.start_date,
           m.end_date,
           m.visits_left,
           m.status
    FROM memberships m
    JOIN clients c ON m.client_id = c.id
    WHERE m.id IN (
        SELECT MAX(id) FROM memberships GROUP BY client_id
    )
    ORDER BY m.end_date
""").fetchall()
    olap_data = conn.execute("""
        SELECT DATE(visit_date) AS visit_date,
               COUNT(*) AS visits_count
        FROM visits
        GROUP BY DATE(visit_date)
        ORDER BY visit_date DESC
        LIMIT 30
    """).fetchall()
    top_clients = conn.execute("""
        SELECT c.name,
               COUNT(v.id) AS visits
        FROM visits v
        JOIN clients c ON v.client_id = c.id
        GROUP BY v.client_id
        ORDER BY visits DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return render_template(
        'reports.html',
        visits=visits,
        memberships=memberships,
        olap_data=olap_data,
        top_clients=top_clients
    )
@app.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM visits WHERE client_id = ?", (client_id,))
        conn.execute("DELETE FROM memberships WHERE client_id = ?", (client_id,))
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        flash('✅ Клиент и все его данные удалены.')
    except Exception as e:
        conn.rollback()
        flash(f'❌ Ошибка удаления: {e}')
    finally:
        conn.close()
    return redirect(url_for('reports'))
if __name__ == '__main__':
    from db_init import init_db
    init_db()
    app.run(debug=True, port=5000)
