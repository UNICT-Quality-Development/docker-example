# The app runs but the browser cannot reach it

```
docker build -t counter:broken .
docker run --rm -p 8000:5000 counter:broken
```

The logs say the server is running on port 5000, and `-p 8000:5000` is there. Still,
`http://localhost:8000` does not answer. What is wrong?
