import sqlite3
import hashlib
import bcrypt
import os

DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            plan_active BOOLEAN NOT NULL,
            onboarded BOOLEAN NOT NULL DEFAULT 0,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarded BOOLEAN NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Coluna já existe
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN renda_mensal REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE users ADD COLUMN gastos_fixos REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE users ADD COLUMN objetivo_fin TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS improvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
        )
    ''')
    try:
        cursor.execute("ALTER TABLE chat_messages ADD COLUMN session_id INTEGER")
        cursor.execute("SELECT DISTINCT user_id FROM chat_messages WHERE session_id IS NULL")
        orphans = cursor.fetchall()
        for orph in orphans:
            uid = orph[0]
            cursor.execute("INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)", (uid, "Papo Original"))
            new_sess = cursor.lastrowid
            cursor.execute("UPDATE chat_messages SET session_id = ? WHERE user_id = ? AND session_id IS NULL", (new_sess, uid))
    except sqlite3.OperationalError:
        pass
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def _hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_user(name, email, password, phone="", address="", username=""):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if username:
            base_username = username
            counter = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    username = f"{base_username}{counter}"
                    counter += 1
                else:
                    break
        
        # Atribuir como admin automaticamente se for o email de env
        admin_auth_mail = os.environ.get("ADMIN_EMAIL", "rodrigo@agfinance.com")
        is_admin = True if email.lower().strip() == admin_auth_mail.lower().strip() else False

        cursor.execute(
            "INSERT INTO users (name, email, password, plan_active, onboarded, is_admin, phone, address, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, email, _hash_password(password), True, False, is_admin, phone, address, username)
        )
        conn.commit()
        conn.close()
        return True, "Usuário criado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Este email já está cadastrado."
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def verify_login(identifier, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, password, plan_active, onboarded, is_admin, email, last_login_at, renda_mensal, gastos_fixos, objetivo_fin FROM users WHERE email = ? OR username = ?", (identifier, identifier))
    user = cursor.fetchone()
    
    if user:
        stored_hash = user[2]
        
        # Check privileges
        admin_status = user[5]
        admin_mail = os.environ.get("ADMIN_EMAIL", "rodrigo@agfinance.com")
        if user[6].lower().strip() == admin_mail.lower().strip() and not admin_status:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user[0],))
            conn.commit()
            admin_status = 1
            
        is_valid = False
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                is_valid = True
        except ValueError:
            old_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if old_hash == stored_hash:
                is_valid = True
                
        if is_valid:
            last_dt = user[7] if len(user) > 7 else None
            renda = user[8] if len(user) > 8 else 0.0
            gastos = user[9] if len(user) > 9 else 0.0
            objetivo = user[10] if len(user) > 10 else ""
            cursor.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?", (user[0],))
            conn.commit()
            conn.close()
            return True, {
                "id": user[0], "name": user[1], "plan_active": user[3], "onboarded": user[4], 
                "is_admin": admin_status, "last_login": last_dt,
                "renda_mensal": renda, "gastos_fixos": gastos, "objetivo_fin": objetivo
            }
            
    conn.close()
    return False, None

def marcar_como_onboarded(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET onboarded = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_onboarding_data(user_id, renda, gastos, objetivo):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET onboarded = 1, renda_mensal = ?, gastos_fixos = ?, objetivo_fin = ? WHERE id = ?", (renda, gastos, objetivo, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# METODOS DE GESTAO ADMIN
def get_dashboard_metrics():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE onboarded = 1")
    onboarded_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT id, name, email, plan_active, onboarded, is_admin, phone, address, username FROM users ORDER BY id DESC")
    all_users = cursor.fetchall()
    conn.close()
    return total_users, onboarded_users, all_users

def add_improvement(title):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO improvements (title, status) VALUES (?, 'Pendente')", (title,))
    conn.commit()
    conn.close()

def get_improvements():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, status FROM improvements ORDER BY id DESC")
    items = cursor.fetchall()
    conn.close()
    return items

def delete_improvement(imp_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM improvements WHERE id = ?", (imp_id,))
    conn.commit()
    conn.close()

def toggle_improvement_status(imp_id, current_status):
    new_status = 'Concluído' if current_status == 'Pendente' else 'Pendente'
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE improvements SET status = ? WHERE id = ?", (new_status, imp_id))
    conn.commit()
    conn.close()

# METODOS DE MEMÓRIA (HISTÓRICO DO CHAT)
def create_session(user_id, title):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_sessions (user_id, title) VALUES (?, ?)", (user_id, title))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid

def get_user_sessions(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM chat_sessions WHERE user_id = ? ORDER BY id DESC", (user_id,))
    s = cursor.fetchall()
    conn.close()
    return s

def get_onboarding_profile(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Busca qualquer texto longo (onde o usuário explicou finanças) ou uploads de extrato
    cursor.execute("""
        SELECT content FROM chat_messages 
        WHERE user_id = ? AND role = 'user' 
        AND (content LIKE '%panorama inicial%' OR content LIKE '%extrato financeiro%' OR length(content) > 100)
        ORDER BY id ASC LIMIT 3
    """, (user_id,))
    recs = cursor.fetchall()
    conn.close()
    
    if recs:
        textos = [r[0] for r in recs]
        return "MEMÓRIA GLOBAL DO USUÁRIO (Contexto de Gastos e Faturas Anteriores):\n\n" + "\n\n---\n\n".join(textos)
    return ""

def add_message(session_id, user_id, role, content):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_messages (session_id, user_id, role, content) VALUES (?, ?, ?, ?)", (session_id, user_id, role, content))
    conn.commit()
    conn.close()

def get_session_messages(session_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    registros = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in registros]

# METODOS DE MONITORAMENTO DA PLATAFORMA
def log_activity(user_id, activity_type):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usage_logs (user_id, activity_type) VALUES (?, ?)", (user_id, activity_type))
    conn.commit()
    conn.close()

def get_top_activities():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT activity_type, COUNT(*) as count 
        FROM usage_logs 
        GROUP BY activity_type 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    results = cursor.fetchall()
    conn.close()
    return results

# Force reload
