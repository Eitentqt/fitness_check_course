import sqlite3
from datetime import date

def init_db():
    conn = sqlite3.connect('fitness.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        email TEXT,
        join_date DATE NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        type TEXT CHECK(type IN ('monthly', 'single', 'yearly')),
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        visits_left INTEGER DEFAULT 12,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired')),
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        visit_date DATE NOT NULL,
        checkin_time TEXT,
        checkout_time TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')
    c.execute('''DROP TRIGGER IF EXISTS decrease_visits''')
    c.execute('''CREATE TRIGGER decrease_visits
        AFTER INSERT ON visits
        FOR EACH ROW
        BEGIN
            UPDATE memberships 
            SET visits_left = visits_left - 1,
                status = CASE 
                    WHEN type = 'single' AND visits_left - 1 <= 0 THEN 'expired'
                    WHEN type != 'single' AND visits_left - 1 <= 0 THEN 'expired'
                    ELSE status
                END
            WHERE client_id = NEW.client_id AND status = 'active';
        END;''')
    c.executemany("""
        INSERT OR IGNORE INTO clients (name, phone, email, join_date)
        VALUES (?, ?, ?, ?)
    """, [
        ('Иванов И.И.',  '+79123456789', 'ivanov@email.com',  '2025-12-01'),
        ('Петрова А.А.', '+79223334455', 'petrova@email.com', '2025-12-01'),
        ('Сидоров С.С.', '+79334445566', None,                '2025-12-01')
    ])
    c.executemany("""
        INSERT OR IGNORE INTO memberships (client_id, type, start_date, end_date, visits_left)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (1, 'monthly',   '2025-12-01', '2025-12-31', 10),
        (2, 'quarterly', '2025-12-01', '2026-03-01', 25),
        (3, 'yearly',    '2025-12-01', '2026-12-01', 100),
    ])
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
