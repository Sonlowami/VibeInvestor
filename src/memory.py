from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import sqlite3
import json
from datetime import datetime

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

DB_PATH = "faiss_investment_db"

def populate_memory(documents, metadatas):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.create_documents(documents, metadatas=metadatas)

    vector_db = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )
    vector_db.save_local(DB_PATH)

    return len(chunks)


def retrieve_top_k(query, k=5):
    vector_db = FAISS.load_local(
        DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_db.similarity_search(query, k=k)

def init_persistent_store():
    conn = sqlite3.connect("memory_log.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_query TEXT,
            selected_tickers TEXT,
            financial_summary TEXT,
            metrics TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

    print("[MEMORY INIT] Persistent store initialized")

def write_session_memory(session_id, user_query, selected_tickers, financial_summary, metrics):
    conn = sqlite3.connect("memory_log.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO sessions (session_id, user_query, selected_tickers, financial_summary, metrics, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        user_query,
        json.dumps(selected_tickers),
        json.dumps(financial_summary),
        json.dumps(metrics),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

    print(f"[MEMORY WRITE] Session {session_id} memory written to persistent store")


def read_recent_sessions(limit=5):
    conn = sqlite3.connect("memory_log.db")
    c = conn.cursor()
    c.execute('''
        SELECT session_id, user_query, selected_tickers, financial_summary, metrics, timestamp
        FROM sessions
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()

    sessions = []
    for row in rows:
        sessions.append({
            "session_id": row[0],
            "user_query": row[1],
            "selected_tickers": json.loads(row[2]),
            "financial_summary": json.loads(row[3]),
            "metrics": json.loads(row[4]),
            "timestamp": row[5]
        })
    
    print(f"[MEMORY READ] Retrieved {len(sessions)} recent sessions from persistent store")
    return sessions

def prune_memory(max_sessions=100):
    conn = sqlite3.connect("memory_log.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sessions")
    count = c.fetchone()[0]

    if count > max_sessions:
        delete_count = count - max_sessions
        c.execute('''
            DELETE FROM sessions
            WHERE id NOT IN (
                SELECT id FROM sessions
                ORDER BY id DESC
                LIMIT ?
            )
        ''', (delete_count,))
        conn.commit()
        conn.close()

        print(f"[MEMORY PRUNE] Pruned memory to keep only the most recent {max_sessions} sessions")
    else:
        conn.close()
        print(f"[MEMORY PRUNE] No pruning needed. Current session count: {count}")