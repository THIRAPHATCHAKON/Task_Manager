import sqlite3
import hashlib
import sys
from pathlib import Path
from datetime import datetime

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "tasks.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def initialize():
    with connect() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                detail TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo',
                priority TEXT NOT NULL DEFAULT 'Medium',
                category_id INTEGER,
                due_date TEXT,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(category_id)
                REFERENCES categories(id)
            )
        """)

        user = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            ("admin",)
        ).fetchone()

        if user is None:
            conn.execute(
                "INSERT INTO users(username, password) VALUES (?, ?)",
                ("admin", hash_password("1234"))
            )

        default_categories = [
            "ทั่วไป",
            "เรียน",
            "งาน",
            "ส่วนตัว"
        ]

        for category in default_categories:
            conn.execute(
                "INSERT OR IGNORE INTO categories(name) VALUES (?)",
                (category,)
            )

def login(username, password):
    with connect() as conn:
        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ? AND password = ?
            """,
            (
                username.strip(),
                hash_password(password)
            )
        ).fetchone()

        return user is not None

def list_categories():
    with connect() as conn:
        return conn.execute(
            "SELECT id, name FROM categories ORDER BY name"
        ).fetchall()

def add_category(name):
    name = name.strip()

    if not name:
        return False

    try:
        with connect() as conn:
            conn.execute(
                "INSERT INTO categories(name) VALUES (?)",
                (name,)
            )

        return True

    except sqlite3.IntegrityError:
        return False


def update_category(category_id, name):
    name = name.strip()

    if not name:
        return False

    try:
        with connect() as conn:
            conn.execute(
                """
                UPDATE categories
                SET name = ?
                WHERE id = ?
                """,
                (name, category_id)
            )

        return True

    except sqlite3.IntegrityError:
        return False


def delete_category(category_id):
    with connect() as conn:

        conn.execute(
            """
            UPDATE tasks
            SET category_id = NULL
            WHERE category_id = ?
            """,
            (category_id,)
        )

        conn.execute(
            "DELETE FROM categories WHERE id = ?",
            (category_id,)
        )

def add_task(
    title,
    detail,
    due_date,
    priority="Medium",
    category_id=None
):
    title = title.strip()

    if not title:
        return False

    with connect() as conn:

        conn.execute(
            """
            INSERT INTO tasks(
                title,
                detail,
                due_date,
                priority,
                category_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                detail.strip(),
                due_date or None,
                priority,
                category_id
            )
        )

    return True

def list_tasks(
    keyword="",
    status="All",
    priority="All",
    category_id=None
):
    sql = """
        SELECT
            tasks.id,
            tasks.title,
            tasks.detail,
            tasks.status,
            tasks.priority,
            tasks.category_id,
            categories.name AS category,
            tasks.due_date,
            tasks.completed_at,
            tasks.created_at

        FROM tasks

        LEFT JOIN categories
        ON tasks.category_id = categories.id

        WHERE tasks.title LIKE ?
    """
    params = [f"%{keyword}%"]

    if status != "All":
        sql += " AND tasks.status = ?"
        params.append(status)

    if priority != "All":
        sql += " AND tasks.priority = ?"
        params.append(priority)

    if category_id is not None:
        sql += " AND tasks.category_id = ?"
        params.append(category_id)

    sql += """
        ORDER BY
            CASE tasks.priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END,
            tasks.due_date,
            tasks.id DESC
    """

    with connect() as conn:
        return conn.execute(
            sql,
            params
        ).fetchall()


def get_task(task_id):
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

def update_task(
    task_id,
    title,
    detail,
    due_date,
    priority,
    category_id
):
    with connect() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET
                title = ?,
                detail = ?,
                due_date = ?,
                priority = ?,
                category_id = ?

            WHERE id = ?
            """,
            (
                title.strip(),
                detail.strip(),
                due_date or None,
                priority,
                category_id,
                task_id
            )
        )


def update_status(task_id, status):
    completed_at = None

    if status == "done":
        completed_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    with connect() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET
                status = ?,
                completed_at = ?

            WHERE id = ?
            """,
            (
                status,
                completed_at,
                task_id
            )
        )


def delete_task(task_id):
    with connect() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )


def duplicate_task(task_id):
    task = get_task(task_id)

    if task is None:
        return

    add_task(
        title=task["title"] + " (Copy)",
        detail=task["detail"],
        due_date=task["due_date"],
        priority=task["priority"],
        category_id=task["category_id"]
    )

def dashboard_counts():
    with connect() as conn:

        total = conn.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

        done = conn.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE status = 'done'
            """
        ).fetchone()[0]

        todo = conn.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE status = 'todo'
            """
        ).fetchone()[0]

        overdue = conn.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE
                status != 'done'
                AND due_date IS NOT NULL
                AND due_date < date('now')
            """
        ).fetchone()[0]

        near_due = conn.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE
                status != 'done'
                AND due_date IS NOT NULL
                AND due_date BETWEEN
                    date('now')
                    AND date('now', '+3 day')
            """
        ).fetchone()[0]

        return {
            "total": total,
            "done": done,
            "todo": todo,
            "overdue": overdue,
            "near_due": near_due
        }


def count_by_category():
    with connect() as conn:
        return conn.execute(
            """
            SELECT
                COALESCE(categories.name, 'ไม่มีหมวดหมู่'),
                COUNT(tasks.id)

            FROM tasks

            LEFT JOIN categories
            ON tasks.category_id = categories.id

            GROUP BY categories.name
            ORDER BY COUNT(tasks.id) DESC
            """
        ).fetchall()


def count_by_priority():
    with connect() as conn:
        return conn.execute(
            """
            SELECT priority, COUNT(*)
            FROM tasks
            GROUP BY priority
            """
        ).fetchall()

def get_due_alerts():
    with connect() as conn:
        return conn.execute(
            """
            SELECT id, title, due_date

            FROM tasks

            WHERE
                status != 'done'
                AND due_date IS NOT NULL
                AND due_date <= date('now', '+3 day')

            ORDER BY due_date
            """
        ).fetchall()

if __name__ == "__main__":
    initialize()
    print("Database initialized.")