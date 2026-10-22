import sqlite3
from datetime import datetime
import bcrypt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DB_NAME = "csol3_agenda.db"

# --- CONFIGURAÇÕES DE EMAIL / GMAIL (SENHA DE APP) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "saladereuniao.csol3@gmail.com"
SENDER_PASSWORD = "qzhllawezztjzfmd"  # Senha de aplicativo gerada

def enviar_email_convite_ics(email_destino, nome_usuario, titulo_reuniao, data_str, hora_inicio, hora_fim):
    try:
        # Estrutura MIME 'alternative' com cabeçalhos específicos para integração com Outlook/Teams
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = email_destino
        msg['Subject'] = f"🗓️ Convite de Reunião: {titulo_reuniao} (Sala CSOL-3)"
        msg['Content-Class'] = "urn:content-classes:calendarmessage"

        dt_obj = datetime.strptime(data_str, "%Y-%m-%d")
        data_formatada = dt_obj.strftime("%d/%m/%Y")

        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #0078d4;">Convite de Agendamento — Sala CSOL-3</h2>
                <p>Olá!</p>
                <p>Você foi convidado(a) para a reunião agendada por <b>{nome_usuario}</b> na Sala de Reunião CSOL-3.</p>
                <ul style="background-color: #f3f2f1; padding: 15px; border-radius: 5px; list-style: none;">
                    <li>📌 <b>Assunto:</b> {titulo_reuniao}</li>
                    <li>📅 <b>Data:</b> {data_formatada}</li>
                    <li>⏰ <b>Horário:</b> {hora_inicio} às {hora_fim}</li>
                </ul>
                <p><i>💡 Utilize os botões de resposta no cabeçalho do seu e-mail para <b>Aceitar</b> ou <b>Recusar</b> este convite no seu calendário.</i></p>
            </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, "html"))

        dt_start = f"{data_str.replace('-', '')}T{hora_inicio.replace(':', '')}00"
        dt_end = f"{data_str.replace('-', '')}T{hora_fim.replace(':', '')}00"

        # iCalendar com formato de REQUEST nativo e organizador/participantes
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CSOL3 Agenda//PT
METHOD:REQUEST
BEGIN:VEVENT
SUMMARY:Reserva CSOL-3: {titulo_reuniao}
LOCATION:Sala de Reunião CSOL-3
DESCRIPTION:Reunião agendada via Sistema CSOL-3 por {nome_usuario}.
DTSTART:{dt_start}
DTEND:{dt_end}
STATUS:CONFIRMED
ORGANIZER;CN="Sala CSOL-3":mailto:{SENDER_EMAIL}
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN="{email_destino}":mailto:{email_destino}
END:VEVENT
END:VCALENDAR"""

        # Inserção direta como 'text/calendar; method=REQUEST' inline para ativação de botões nativos
        part_ics = MIMEText(ics_content, 'calendar; method=REQUEST; charset=utf-8', 'utf-8')
        part_ics.add_header('Content-Disposition', 'inline; filename="invite.ics"')
        msg.attach(part_ics)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email_destino, msg.as_string())
        server.quit()
        return True, "E-mail enviado com sucesso!"
    except Exception as e:
        return False, f"Falha ao enviar e-mail: {str(e)}"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            full_name TEXT,
            email TEXT,
            is_active INTEGER DEFAULT 1,
            must_change_password INTEGER DEFAULT 0
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
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
            "INSERT INTO users (username, password, full_name, email, is_active, must_change_password) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", hashed_default_pwd, "Administrador CSOL-3", "saladereuniao.csol3@gmail.com", 1, 0)
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

def add_user_by_admin(username, password, full_name, email):
    try:
        hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name, email, is_active, must_change_password) VALUES (?, ?, ?, ?, 1, 1)", 
            (username, hashed_pwd, full_name, email)
        )
        conn.commit()
        conn.close()
        return True, "Usuário cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Este nome de usuário já existe."

def update_user_by_admin(username, full_name, email, new_password=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        if new_password and new_password.strip():
            hashed_pwd = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "UPDATE users SET full_name = ?, email = ?, password = ?, must_change_password = 1 WHERE username = ?",
                (full_name, email, hashed_pwd, username)
            )
        else:
            cursor.execute(
                "UPDATE users SET full_name = ?, email = ? WHERE username = ?",
                (full_name, email, username)
            )
        conn.commit()
        conn.close()
        return True, "Cadastro atualizado com sucesso!"
    except Exception as e:
        conn.close()
        return False, f"Erro ao atualizar: {str(e)}"

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
    cursor.execute("SELECT username, full_name, email, is_active, must_change_password FROM users")
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
            "id": str
