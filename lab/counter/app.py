import os

import redis
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index() -> tuple[str, int]:
    greeting = f"Hello from {os.environ.get('AUTHOR', 'nobody')}!"
    host = os.environ.get("REDIS_HOST")
    if not host:
        return f"{greeting}\nCounter is off: REDIS_HOST is not set\n", 200

    try:
        client = redis.Redis(host=host, port=6379, socket_connect_timeout=2)
        visits = client.incr("visits")
    except redis.RedisError as error:
        return f"{greeting}\nCannot reach {host}:6379: {error}\n", 503
    return f"{greeting}\nVisits: {visits}\n", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
