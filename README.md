## Docker example

This repository contains the examples for the Docker section of the Software Quality and Project Development course at the University of Catania: a small Flask app with its `Dockerfile`, a `compose.yaml` that adds a MySQL database and Adminer, the GitHub Actions workflow that builds and publishes the image, and a one-hour lab.

| File                                   | What it is                                                         |
| -------------------------------------- | ------------------------------------------------------------------ |
| `app.py`, `requirements.txt`           | The app: `/` says hello, `/visits` counts visits in MySQL           |
| `Dockerfile`                           | Recipe to build the app image                                      |
| `.dockerignore`                        | Files kept out of the build context                                |
| `layers-cache/`                        | The same image written badly and well for the layer cache          |
| `compose.yaml`                         | The app, a MySQL database and Adminer on one network               |
| `.github/workflows/docker-publish.yml` | Builds the image and pushes it to ghcr.io on every push to `main`  |
| `LAB.md`, `lab/`                       | The lab: tasks, the counter app, and broken setups to fix          |

You need [Docker](https://docs.docker.com/get-started/get-docker/) installed and running.

```bash
git clone https://github.com/UNICT-Quality-Development/docker-example
cd docker-example
docker --version
docker compose version
```

### Hello World

```bash
docker run hello-world
```

Docker pulls the image, creates the container, runs it, prints the message and exits. Run it again: the image is already there, so there is no pull.

### docker run

```bash
docker run -d -p 8080:80 --name web nginx
docker ps
curl localhost:8080
docker logs web
docker exec -it web bash
docker stop web && docker rm web
```

| Flag                | Meaning                            |
| ------------------- | ---------------------------------- |
| `-d`                | detached, run in background        |
| `-p HOST:CONTAINER` | publish a port                     |
| `--name`            | give the container a name          |
| `--rm`              | remove the container when it exits |
| `-e KEY=VALUE`      | set an environment variable        |

Without `-p` the container runs but `curl localhost:8080` fails: nothing on the host listens on that port.

### Build and run the app

```bash
docker build -t my-app .
docker images my-app
docker run --rm -p 8000:5000 my-app
```

Open http://localhost:8000. The app listens on port 5000 inside the container; host port 8000 avoids port 5000, which macOS uses for AirPlay Receiver. `-t` sets the image name (`name:tag`), `.` is the build context: the folder sent to Docker, minus what `.dockerignore` excludes.

`/visits` answers `DATABASE_URL is not set` here: the database comes later.

### Layers and cache

Each instruction is a cached layer: when a file changes, every layer after it is rebuilt. Build both images, change a string in `app.py`, then build them again:

```bash
docker build -f layers-cache/Dockerfile.bad -t my-app:bad .
docker build -f layers-cache/Dockerfile.good -t my-app:good .
```

On the second build `Dockerfile.bad` reinstalls every package, `Dockerfile.good` shows the `pip install` step as `CACHED` and only copies the new code. The cache also remembers older versions of `app.py`: type a string you haven't used before, or every step shows `CACHED`.

### Push to ghcr.io

Create a personal access token (classic) with only the `write:packages` scope and a short expiry ([new token](https://github.com/settings/tokens/new?scopes=write:packages)), then:

```bash
export TOKEN=YOUR_TOKEN
echo $TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker tag my-app ghcr.io/USERNAME/my-app:1.0
docker push ghcr.io/USERNAME/my-app:1.0
docker logout ghcr.io
```

Image names are lowercase: type your username in lowercase. A new package is private: open it from the Packages tab of your GitHub profile, then Package settings, Danger Zone, Change visibility.

To push one image that runs on both x86 and ARM laptops:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/USERNAME/my-app:1.0 --push .
```

### Volumes

Containers are ephemeral: when removed, their data is lost.

```bash
docker run -d -p 8080:80 --name web nginx
docker exec web sh -c 'echo "<h1>Changed inside the container</h1>" > /usr/share/nginx/html/index.html'
curl localhost:8080
docker rm -f web
docker run -d -p 8080:80 --name web nginx
curl localhost:8080
docker rm -f web
```

The second `curl` shows the default nginx page again. A named volume keeps data after the container is removed (MySQL below uses one). A bind mount shares a host folder, useful in development:

```bash
docker run -v $(pwd):/app -p 8000:5000 my-app
```

### Two containers on a network, by hand

Start clean, in case an earlier try left something behind:

```bash
docker rm -f web db adminer
docker volume rm -f db-data
docker network rm -f app-net
```

On the default network containers cannot find each other by name:

```bash
docker run -d --name db -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=app \
    -e MYSQL_USER=user -e MYSQL_PASSWORD=pass -v db-data:/var/lib/mysql mysql:8.4
docker run -d --name web -p 8000:5000 \
    -e DATABASE_URL=mysql://user:pass@db:3306/app my-app
curl localhost:8000/visits
```

```
Cannot reach db:3306: (2003, "Can't connect to MySQL server on 'db' ([Errno -2] Name or service not known)")
```

On a network you create, Docker runs a DNS and the container name is the hostname. Wait until MySQL's first start is over before removing `db`: `docker logs db` must show `ready for connections` with `port: 3306` (the `port: 0` line is not enough). Removing it earlier leaves a broken `db-data` volume.

```bash
docker network create app-net
docker rm -f web db
docker run -d --name db --network app-net -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=app \
    -e MYSQL_USER=user -e MYSQL_PASSWORD=pass -v db-data:/var/lib/mysql mysql:8.4
docker run -d --name web --network app-net -p 8000:5000 \
    -e DATABASE_URL=mysql://user:pass@db:3306/app my-app
curl localhost:8000/visits
```

```
Visits: 1
```

Add Adminer, a web UI for the database, on the same network:

```bash
docker run -d --name adminer --network app-net -p 8081:8080 adminer:6.3.0
```

Open http://localhost:8081 and log in with server `db`, user `user`, password `pass`, database `app`: the `visits` table is there.

### Docker Compose

`compose.yaml` is the commands above written down once. Remove the containers you started by hand first, they hold ports 8000 and 8081:

```bash
docker rm -f web db adminer
docker compose up -d
docker compose ps
curl localhost:8000/visits
```

Compose creates one network for the project (`app-net` here) and connects every service to it, so services reach each other by name: `web` connects to `db:3306`. The `networks:` section is optional: without it Compose creates a default network. `depends_on` with `condition: service_healthy` makes `web` wait until the `db` healthcheck passes, not just until the container starts. Adminer is on http://localhost:8081.

| Command                | Containers | Network | Volumes (data) |
| ---------------------- | ---------- | ------- | -------------- |
| `docker compose stop`  | stopped    | kept    | kept           |
| `docker compose down`  | removed    | removed | kept           |
| `docker compose down -v` | removed  | removed | removed        |

The visit count survives `down` and `up`, and starts again from 1 after `down -v`.

| Command                         | Description                           |
| ------------------------------- | ------------------------------------- |
| `docker compose up (-d)`        | build, create and start all services  |
| `docker compose up -d --build`  | rebuild after a code change           |
| `docker compose ps`             | list the services                     |
| `docker compose logs -f web`    | follow the logs of a service          |
| `docker compose exec web bash`  | shell inside a service                |
| `docker compose down (-v)`      | stop and remove (also volumes)        |
| `docker compose build`          | rebuild the images                    |

### Docker in CI/CD

`.github/workflows/docker-publish.yml` logs in to the GitHub Container Registry with `GITHUB_TOKEN`, builds the image and pushes it as `ghcr.io/<owner>/<repo>:latest` on every push to `main`. `docker/metadata-action` builds the image name in lowercase, so an owner or repository name with capitals still works.

The same job also exists as a reusable workflow:

- [UNICT-DMI/reusable-workflows](https://github.com/UNICT-DMI/reusable-workflows/blob/main/.github/workflows/docker.yml) publishes it (`on: workflow_call`).
- [UNICT-DMI/unict-telegram-hub](https://github.com/UNICT-DMI/unict-telegram-hub/blob/main/.github/workflows/docker.yaml) is a repository that calls it.

### Useful commands

| Command                     | Description                             |
| --------------------------- | --------------------------------------- |
| `docker pull IMAGE`         | download an image from a registry       |
| `docker images`             | list local images                       |
| `docker run IMAGE`          | create and start a container            |
| `docker ps (-a)`            | list running (all) containers           |
| `docker stop NAME`          | stop a container                        |
| `docker rm NAME`            | remove a container                      |
| `docker rmi IMAGE`          | remove an image                         |
| `docker logs (-f) NAME`     | show (follow) the output of a container |
| `docker exec -it NAME bash` | open a shell inside a container         |
| `docker top NAME`           | list the processes of a container       |

### Lab

The one-hour lab is in [LAB.md](LAB.md).
