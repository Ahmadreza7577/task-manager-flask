import sqlite3
import tempfile

import app as taskflow


def test_home_page_loads():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_database = f"{temp_dir}/test_tasks.db"

        taskflow.app.config.update(
            TESTING=True,
            DATABASE=test_database,
        )

        connection = sqlite3.connect(test_database)
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

        client = taskflow.app.test_client()
        response = client.get("/")

        assert response.status_code == 200