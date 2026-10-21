import sqlite3
from datetime import datetime
import bcrypt

DB_NAME = "csol3_agenda.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            is_active INTEGER DEFAULT 1,
            must_change_password INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            title TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            date TEXT,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed_default_pwd = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "INSERT INTO users (username, password, full_name, is_active, must_change_password) VALUES (?, ?, ?, ?, ?)",
            ("admin", hashed_default_pwd, "Administrador CSOL-3", 1, 0)
        )
        
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT password, full_name, is_active, must_change_password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        stored_password_hash, full_name, is_active, must_change_password = user
        if is_active == 0:
            return None, "Conta inativada. Contate o administrador."
        
        if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return {"full_name": full_name, "must_change_password": must_change_password}, None
            
    return None, "Usuário ou senha inválidos."

def add_user_by_admin(username, password, full_name):
    try:
        hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name, is_active, must_change_password) VALUES (?, ?, ?, 1, 1)", 
            (username, hashed_pwd, full_name)
        )
        conn.commit()
        conn.close()
        return True, "Usuário cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Este nome de usuário já existe."

def update_password(username, new_password):
    hashed_pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ?, must_change_password = 0 WHERE username = ?", (hashed_pwd, username))
    conn.commit()
    conn.close()

def toggle_user_status(username, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE username = ?", (status, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, is_active, must_change_password FROM users")
    data = cursor.fetchall()
    conn.close()
    return data

def get_all_bookings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.id, b.username, u.full_name, b.title, b.date, b.start_time, b.end_time 
        FROM bookings b 
        JOIN users u ON b.username = u.username 
        ORDER BY b.date ASC, b.start_time ASC
    ''')
    data = cursor.fetchall()
    conn.close()
    return data

def get_bookings_by_period(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.id, b.username, u.full_name, b.title, b.date, b.start_time, b.end_time 
        FROM bookings b 
        JOIN users u ON b.username = u.username 
        WHERE b.date BETWEEN ? AND ?
        ORDER BY b.date ASC, b.start_time ASC
    ''', (start_date, end_date))
    data = cursor.fetchall()
    conn.close()
    return data

def get_calendar_events():
    bookings = get_all_bookings()
    events = []
    for b in bookings:
        event_id, username, full_name, title, date_str, start_time, end_time = b
        events.append({
            "title": f"{title} ({full_name})",
            "start": f"{date_str}T{start_time}",
            "end": f"{date_str}T{end_time}",
            "id": str(event_id),
            "backgroundColor": "#0078d4",
            "borderColor": "#005a9e"
        })
    return events

def add_notification(username, message, date_str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notifications (username, message, date) VALUES (?, ?, ?)", (username, message, date_str))
    conn.commit()
    conn.close()

def get_user_notifications(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, message, date, is_read FROM notifications WHERE username = ? ORDER BY id DESC", (username,))
    data = cursor.fetchall()
    conn.close()
    return data

def mark_notifications_as_read(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def add_booking(username, title, date_str, start_time, end_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT start_time, end_time FROM bookings 
        WHERE date = ? AND NOT (end_time <= ? OR start_time >= ?)
    ''', (date_str, start_time, end_time))
    
    if cursor.fetchall():
        conn.close()
        return False, "Já existe uma reserva na sala CSOL-3 que conflita com este horário!"
    
    cursor.execute('''
        INSERT INTO bookings (username, title, date, start_time, end_time) 
        VALUES (?, ?, ?, ?, ?)
    ''', (username, title, date_str, start_time, end_time))
    conn.commit()
    conn.close()
    
    msg = f"Reserva confirmada: '{title}' em {date_str} das {start_time} às {end_time}."
    add_notification(username, msg, date_str)
    if username != "admin":
        add_notification("admin", f"Nova reserva de {username}: '{title}' em {date_str} ({start_time}-{end_time}).", date_str)
        
    return True, "Reserva realizada com sucesso!"

def update_booking(booking_id, username, title, date_str, start_time, end_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM bookings WHERE id = ?", (booking_id,))
    res = cursor.fetchone()
    if not res or (res[0] != username and username != "admin"):
        conn.close()
        return False, "Você não tem permissão para alterar esta reserva."
        
    cursor.execute('''
        SELECT start_time, end_time FROM bookings 
        WHERE date = ? AND id != ? AND NOT (end_time <= ? OR start_time >= ?)
    ''', (date_str, booking_id, start_time, end_time))
    
    if cursor.fetchall():
        conn.close()
        return False, "Conflito de horário com outra reserva existente!"
        
    cursor.execute('''
        UPDATE bookings SET title = ?, date = ?, start_time = ?, end_time = ? WHERE id = ?
    ''', (title, date_str, start_time, end_time, booking_id))
    conn.commit()
    conn.close()
    return True, "Reserva alterada com sucesso!"

def delete_booking(booking_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM bookings WHERE id = ?", (booking_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "Reserva não encontrada."
        
    owner = res[0]
    if username == "admin" or username == owner:
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()
        return True, "Reserva cancelada com sucesso!"
    else:
        conn.close()
        return False, "Você só pode cancelar suas próprias reservas."
