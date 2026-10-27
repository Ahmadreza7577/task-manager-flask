from dotenv import load_dotenv
import sqlite3
import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. Please configure it before starting the app."
    )

DATABASE = "tasks.db"

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection



def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # بررسی ستون‌های موجود برای حفظ سازگاری با دیتابیس قبلی
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
    }

    if "description" not in columns:
        connection.execute(
            "ALTER TABLE tasks ADD COLUMN description TEXT NOT NULL DEFAULT ''"
        )

    if "priority" not in columns:
        connection.execute(
            "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'"
        )

    if "due_date" not in columns:
        connection.execute(
            "ALTER TABLE tasks ADD COLUMN due_date TEXT"
        )

    if "status" not in columns:
        connection.execute(
            "ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'todo'"
        )

    connection.commit()
    connection.close()
   


@app.route("/")
def home():
    search_query = request.args.get("q", "").strip()
    state = request.args.get("state", "all")
    due_filter = request.args.get("due", "all")
    sort_by = request.args.get("sort", "newest")

    connection = get_db_connection()

    sql = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern])

    if state == "active":
        sql += " AND completed = 0"
    elif state == "completed":
        sql += " AND completed = 1"
    if due_filter == "overdue":
        sql += " AND due_date < ? AND completed = 0"
        params.append(date.today().isoformat())

    elif due_filter == "today":
        sql += " AND due_date = ? AND completed = 0"
        params.append(date.today().isoformat())

    elif due_filter == "upcoming":
        sql += " AND due_date > ? AND completed = 0"
        params.append(date.today().isoformat())

    if sort_by == "priority":
        sql += """
            ORDER BY
            CASE priority
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                ELSE 4
            END,
            id DESC
        """
    elif sort_by == "due_date":
        sql += """
            ORDER BY
            CASE WHEN due_date IS NULL OR due_date = '' THEN 1 ELSE 0 END,
            due_date ASC,
            id DESC
        """
    else:
        sql += " ORDER BY id DESC"

    tasks = connection.execute(sql, params).fetchall()

    all_tasks = connection.execute(
        "SELECT completed FROM tasks"
    ).fetchall()

    connection.close()

    total = len(all_tasks)
    completed = sum(task["completed"] for task in all_tasks)
    remaining = total - completed

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        remaining=remaining,
        today=date.today().isoformat(),
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "medium")
    due_date = request.form.get("due_date", "").strip() or None

    if not title:
        flash("Please enter a task title.", "error")
        return redirect(url_for("home"))

    if priority not in ("low", "medium", "high"):
        priority = "medium"

    connection = get_db_connection()
    connection.execute(
        """
        INSERT INTO tasks (title, description, priority, due_date)
        VALUES (?, ?, ?, ?)
        """,
        (title, description, priority, due_date)
    )
    connection.commit()
    connection.close()

    flash("Task added successfully!", "success")
    return redirect(url_for("home"))
@app.route("/toggle/<int:task_id>", methods=["POST"])    
def toggle_task(task_id):
    connection = get_db_connection()

    connection.execute("""
        UPDATE tasks
        SET completed = CASE
            WHEN completed = 0 THEN 1
            ELSE 0
        END
        WHERE id = ?
    """, (task_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    connection = get_db_connection()

    cursor = connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    connection.commit()
    deleted = cursor.rowcount

    connection.close()

    if deleted:
        flash("Task deleted successfully!", "success")
    else:
        flash("Task not found.", "error")

    return redirect(url_for("home"))


@app.route("/edit/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "medium")
    due_date = request.form.get("due_date", "").strip() or None

    if not title:
        flash("Please enter a task title.", "error")
        return redirect(url_for("home"))

    if priority not in ("low", "medium", "high"):
        priority = "medium"

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE tasks
        SET title = ?, description = ?, priority = ?, due_date = ?
        WHERE id = ?
        """,
        (title, description, priority, due_date, task_id)
    )

    connection.commit()
    connection.close()

    flash("Task updated successfully!", "success")
    return redirect(url_for("home"))



init_db()

if __name__ == "__main__":
    app.run(debug=True)
