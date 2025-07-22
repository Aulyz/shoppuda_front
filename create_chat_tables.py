import sqlite3
import os

# 데이터베이스 연결
db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 채팅 테이블 생성 SQL
sql_commands = [
    """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        session_number VARCHAR(20) UNIQUE,
        customer_name VARCHAR(100),
        customer_email VARCHAR(254),
        customer_phone VARCHAR(20),
        status VARCHAR(10) DEFAULT 'waiting',
        subject VARCHAR(200),
        created_at DATETIME NOT NULL,
        started_at DATETIME,
        ended_at DATETIME,
        rating INTEGER,
        feedback TEXT,
        agent_id INTEGER,
        customer_id INTEGER,
        FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE SET NULL
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        sender_type VARCHAR(10) NOT NULL,
        message_type VARCHAR(10) DEFAULT 'text',
        content TEXT NOT NULL,
        file_url VARCHAR(200),
        created_at DATETIME NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        read_at DATETIME,
        sender_id INTEGER,
        session_id TEXT NOT NULL,
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS chat_notes (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        is_important BOOLEAN DEFAULT 0,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        agent_id INTEGER NOT NULL,
        session_id TEXT NOT NULL,
        FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS chat_quick_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        category VARCHAR(50),
        usage_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        created_by_id INTEGER,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS chat_statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE UNIQUE NOT NULL,
        total_sessions INTEGER DEFAULT 0,
        completed_sessions INTEGER DEFAULT 0,
        avg_response_time REAL DEFAULT 0,
        avg_session_duration REAL DEFAULT 0,
        avg_rating REAL,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    )
    """
]

# 테이블 생성
for sql in sql_commands:
    try:
        cursor.execute(sql)
        print(f"테이블 생성 성공")
    except Exception as e:
        print(f"테이블 생성 실패: {e}")

# 마이그레이션 기록 추가
try:
    cursor.execute("""
        INSERT INTO django_migrations (app, name, applied)
        VALUES ('chat', '0001_initial', datetime('now'))
    """)
    print("마이그레이션 기록 추가 성공")
except Exception as e:
    print(f"마이그레이션 기록 추가 실패: {e}")

# 변경사항 저장
conn.commit()
conn.close()

print("채팅 테이블 생성 완료!")