# The counter cannot find Redis

```
docker compose up -d --build
```

Both services are up, but `http://localhost:8000` shows `Cannot reach localhost:6379`. Redis is
running, so why can't the app reach it?
