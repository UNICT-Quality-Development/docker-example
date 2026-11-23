# The build never ends

```
docker build -t counter:broken .
```

The build reaches the last step and stays there. Stop it with Ctrl+C. Why does it hang, and what
should the last line of the `Dockerfile` be?
