from datetime import date, timedelta
import sqlite3
import tempfile

import app as taskflow


def setup_test_database(database_path):
    connection = sqlite3.connect(database_path)
    connection.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            description TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT 'medium',
            due_date TEXT,
            status TEXT NOT NULL DEFAULT 'todo'
        )
    """)
    connection.commit()
    connection.close()


def test_home_page_loads():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        client = taskflow.app.test_client()
        response = client.get("/")

        assert response.status_code == 200


def test_add_task():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        client = taskflow.app.test_client()

        response = client.post("/add", data={
            "title": "Learn Flask testing",
            "description": "Write automated tests",
            "priority": "high",
            "due_date": "2026-11-15",
        })

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        task = connection.execute("""
            SELECT title, description, priority, due_date
            FROM tasks
        """).fetchone()
        connection.close()

        assert task == (
            "Learn Flask testing",
            "Write automated tests",
            "high",
            "2026-11-15",
        )

def test_add_task_without_title():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        client = taskflow.app.test_client()

        response = client.post("/add", data={
            "title": "   ",
            "description": "This task should not be saved",
            "priority": "medium",
        })

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        task_count = connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]
        connection.close()

        assert task_count == 0

def test_add_task_with_invalid_priority():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        client = taskflow.app.test_client()

        response = client.post("/add", data={
            "title": "Test invalid priority",
            "priority": "urgent",
        })

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        task = connection.execute(
            "SELECT priority FROM tasks"
        ).fetchone()
        connection.close()

        assert task == ("medium",)
        
def test_toggle_task_completion():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            ("Test task completion",),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.post("/toggle/1")

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        completed = connection.execute(
            "SELECT completed FROM tasks WHERE id = 1"
        ).fetchone()[0]
        connection.close()

        assert completed == 1

def test_delete_task():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            ("Task to delete",),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.post("/delete/1")

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        task_count = connection.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]
        connection.close()

        assert task_count == 0

def test_edit_task():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            ("Old title",),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.post("/edit/1", data={
            "title": "Updated title",
            "description": "Updated description",
            "priority": "high",
            "due_date": "2026-11-20",
        })

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        task = connection.execute("""
            SELECT title, description, priority, due_date
            FROM tasks
            WHERE id = 1
        """).fetchone()
        connection.close()

        assert task == (
            "Updated title",
            "Updated description",
            "high",
            "2026-11-20",
        )

def test_search_tasks_by_description():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            """
            INSERT INTO tasks (title, description)
            VALUES (?, ?)
            """,
            ("Prepare portfolio", "Practice Python testing"),
        )
        connection.execute(
            """
            INSERT INTO tasks (title, description)
            VALUES (?, ?)
            """,
            ("Buy groceries", "Get milk and bread"),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?q=Python")

        assert response.status_code == 200
        assert b"Prepare portfolio" in response.data
        assert b"Buy groceries" not in response.data

def test_filter_completed_tasks():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, completed) VALUES (?, ?)",
            ("Completed task", 1),
        )
        connection.execute(
            "INSERT INTO tasks (title, completed) VALUES (?, ?)",
            ("Active task", 0),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?state=completed")

        assert response.status_code == 200
        assert b"Completed task" in response.data
        assert b"Active task" not in response.data

def test_sort_tasks_by_priority():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)",
            ("Low priority task", "low"),
        )
        connection.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)",
            ("High priority task", "high"),
        )
        connection.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)",
            ("Medium priority task", "medium"),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?sort=priority")

        assert response.status_code == 200

        high_position = response.data.index(b"High priority task")
        medium_position = response.data.index(b"Medium priority task")
        low_position = response.data.index(b"Low priority task")

        assert high_position < medium_position < low_position

def test_filter_overdue_tasks():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Overdue task", yesterday),
        )
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Upcoming task", tomorrow),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?due=overdue")

        assert response.status_code == 200
        assert b"Overdue task" in response.data
        assert b"Upcoming task" not in response.data

def test_filter_tasks_due_today():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Due today task", today),
        )
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Due tomorrow task", tomorrow),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?due=today")

        assert response.status_code == 200
        assert b"Due today task" in response.data
        assert b"Due tomorrow task" not in response.data

def test_filter_upcoming_tasks():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Overdue task", yesterday),
        )
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Upcoming task", tomorrow),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?due=upcoming")

        assert response.status_code == 200
        assert b"Upcoming task" in response.data
        assert b"Overdue task" not in response.data

def test_init_db_migrates_old_database():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/old_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        connection = sqlite3.connect(test_database)
        connection.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            )
        """)
        connection.execute(
            "INSERT INTO tasks (title, completed) VALUES (?, ?)",
            ("Old task", 0),
        )
        connection.commit()
        connection.close()

        taskflow.init_db()
        taskflow.init_db()

        connection = sqlite3.connect(test_database)
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(tasks)"
            ).fetchall()
        }
        task = connection.execute(
            "SELECT title, description, priority, due_date, status "
            "FROM tasks WHERE title = ?",
            ("Old task",),
        ).fetchone()
        connection.close()

        assert {
            "description",
            "priority",
            "due_date",
            "status",
        }.issubset(columns)

        assert task == ("Old task", "", "medium", None, "todo")
        
def test_sort_tasks_by_due_date():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Later task", "2099-12-31"),
        )
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("Earlier task", "2099-01-01"),
        )
        connection.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)",
            ("No due date", None),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?sort=due_date")

        assert response.status_code == 200

        html = response.data.decode()
        earlier_position = html.index("Earlier task")
        later_position = html.index("Later task")
        no_date_position = html.index("No due date")

        assert earlier_position < later_position < no_date_position

def test_filter_active_tasks():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title, completed) VALUES (?, ?)",
            ("Active task", 0),
        )
        connection.execute(
            "INSERT INTO tasks (title, completed) VALUES (?, ?)",
            ("Completed task", 1),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.get("/?state=active")

        assert response.status_code == 200
        assert b"Active task" in response.data
        assert b"Completed task" not in response.data

def test_delete_nonexistent_task():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        client = taskflow.app.test_client()
        response = client.post("/delete/999")

        assert response.status_code == 302
        assert response.location == "/"

        with client.session_transaction() as session:
            flashes = session.get("_flashes", [])
            assert any(
                "Task not found." in message
                for category, message in flashes
            )

def test_edit_task_without_title():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            ("Original task",),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.post(
            "/edit/1",
            data={"title": ""},
        )

        assert response.status_code == 302
        assert response.location == "/"

        with client.session_transaction() as session:
            flashes = session.get("_flashes", [])
            assert any(
                "Please enter a task title." in message
                for category, message in flashes
            )

        connection = sqlite3.connect(test_database)
        task = connection.execute(
            "SELECT title FROM tasks WHERE id = 1"
        ).fetchone()
        connection.close()

        assert task == ("Original task",)

def test_edit_task_with_invalid_priority():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        setup_test_database(test_database)

        connection = sqlite3.connect(test_database)
        connection.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            ("Original task",),
        )
        connection.commit()
        connection.close()

        client = taskflow.app.test_client()
        response = client.post(
            "/edit/1",
            data={
                "title": "Updated task",
                "priority": "urgent",
            },
        )

        assert response.status_code == 302

        connection = sqlite3.connect(test_database)
        task = connection.execute(
            "SELECT title, priority FROM tasks WHERE id = 1"
        ).fetchone()
        connection.close()

        assert task == ("Updated task", "medium")

