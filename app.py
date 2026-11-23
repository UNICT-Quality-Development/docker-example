import os
from urllib.parse import urlparse

import pymysql
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index() -> str:
    return "Hello from Docker!"


@app.route("/visits")
def visits() -> tuple[str, int]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return "DATABASE_URL is not set, start the app with docker compose up", 503

    url = urlparse(database_url)
    try:
        connection = pymysql.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path.lstrip("/"),
            connect_timeout=2,
            autocommit=True,
        )
        with connection, connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS visits ("
                "id INT AUTO_INCREMENT PRIMARY KEY, "
                "visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            )
            cursor.execute("INSERT INTO visits () VALUES ()")
            cursor.execute("SELECT COUNT(*) FROM visits")
            (count,) = cursor.fetchone()
        return f"Visits: {count}", 200
    except pymysql.MySQLError as error:
        return f"Cannot reach {url.hostname}:{url.port}: {error}", 503


if __name__ == "__main__":
    # 0.0.0.0, not the default 127.0.0.1: otherwise `docker run -p` cannot reach the server
    app.run(host="0.0.0.0", port=5000)
