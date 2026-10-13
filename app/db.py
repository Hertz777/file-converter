import psycopg
from .config import DATABASE_URL

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    target_format TEXT NOT NULL,
    source_path TEXT NOT NULL,
    result_path TEXT,
    result_filename TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""

def get_conn():
    return psycopg.connect(DATABASE_URL)

def init_db():
    with get_conn() as conn:
        conn.execute(CREATE_TABLE)
        conn.commit()

def create_task(task_id, filename, target_format, source_path):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tasks (id, filename, target_format, source_path, status) VALUES (%s,%s,%s,%s,%s)",
            (task_id, filename, target_format, source_path, "QUEUED"),
        )
        conn.commit()

def get_task(task_id):
    with get_conn() as conn:
        row = conn.execute("SELECT id, filename, target_format, source_path, result_path, result_filename, status, error_message FROM tasks WHERE id=%s", (task_id,)).fetchone()
        return row

def update_task(task_id, status, result_path=None, result_filename=None, error_message=None):
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET status=%s, result_path=COALESCE(%s,result_path), result_filename=COALESCE(%s,result_filename), error_message=%s, updated_at=NOW() WHERE id=%s", (status, result_path, result_filename, error_message, task_id))
        conn.commit()

def get_recent_tasks(limit=20):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, filename, target_format, result_filename,
                   status, error_message, created_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()

        return rows
