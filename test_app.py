
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
