# Docker lab (1 hour)

Work on your own laptop, at your own pace. Each part ends with a **Done when** check: when it
passes, move on. Parts 5 and 6 can be finished at home.

The counter app in `lab/counter/` is ready: you write only the `Dockerfile` and the
`compose.yaml`. It greets with the `AUTHOR` environment variable and, when `REDIS_HOST` is set,
counts visits in Redis.

**A host port is taken?** If Docker says `port is already allocated`, or the port is used by
another program on your laptop, change the left number of `-p` (or of `ports:` in Compose):
`-p 8001:5000` instead of `-p 8000:5000`, then open `localhost:8001`. The right number is the
port inside the container and stays the same.

| Part | Minutes | Topic |
| ---- | ------- | ----- |
| 0 | 5 | Setup |
| 1 | 8 | Containers |
| 2 | 12 | Images |
| 3 | 10 | Registry |
| 4 | 8 | Network by hand |
| 5 | 15 | Compose |
| 6 | extra | Fix it |

## Part 0: Setup (5 min)

Install Docker if you don't have it yet (steps from Docker's documentation, not tested here):

- **Windows**: install WSL 2 (`wsl --install` in an administrator PowerShell, then reboot), then
  Docker Desktop from <https://docs.docker.com/desktop/setup/install/windows-install/>.
- **macOS**: Docker Desktop from <https://docs.docker.com/desktop/setup/install/mac-install/>.
  Pick the Apple silicon download on Macs with an M chip (M1, M2, ...), Intel otherwise. The
  chip is shown in Apple menu > About This Mac.
- **Linux**: Docker Desktop from <https://docs.docker.com/desktop/setup/install/linux/>, or
  Docker Engine from <https://docs.docker.com/engine/install/> and then
  `sudo usermod -aG docker $USER` (log out and in again).

Start Docker Desktop, then:

```
docker --version
docker compose version
docker run hello-world
```

Pull the images the lab needs, so you don't wait later:

```
docker pull nginx
docker pull python:3.12-slim
docker pull redis:8-alpine
```

**Done when** `docker run hello-world` prints `Hello from Docker!`.

## Part 1: Containers (8 min)

1. Run nginx in the background on host port 8080, named `site`, and open `localhost:8080`.
2. Change its page from inside the container: `docker exec` a command that writes a new
   `/usr/share/nginx/html/index.html`. Reload the browser.
3. Remove the container and run it again. Is your change still there?
4. Make a folder `site` with an `index.html` in it. Remove the `site` container, then run nginx
   again with that folder mounted on `/usr/share/nginx/html` (`-v`, with an absolute path to your
   folder).

Commands you need: `docker run` (`-d`, `-p`, `--name`, `-v`), `docker exec`, `docker rm -f`.

Bind-mount path per system: Linux and macOS `"$(pwd)/site"`; Windows PowerShell `"${PWD}\site"`
(not tested); Windows cmd `"%cd%\site"` (not tested). Docker Desktop only shares your home folder
by default on Linux: keep the `site` folder somewhere under it, or you get `mounts denied`.

**Done when** editing your local `index.html` changes the page on reload, with no restart.

## Part 2: Images (12 min)

1. In `lab/counter/` write a `Dockerfile` for the app: base image `python:3.12-slim`, install
   `requirements.txt`, copy the code, start `python app.py`. The app listens on port 5000.
2. Set `ENV AUTHOR` to your name in the `Dockerfile`.
3. Build it as `counter:1.0` and run it with host port 8000.
4. Change a string in `app.py` (a new one, not one you used before) and build again.

Commands you need: `docker build -t`, `docker run --rm -p`.

**Done when** `localhost:8000` greets with your name, and the second build shows the
`pip install` step as `CACHED`. If it isn't, look at the order of the `COPY` lines.

## Part 3: Registry (10 min)

1. Create a GitHub personal access token (classic) with only the `write:packages` scope and a
   short expiry: <https://github.com/settings/tokens/new?scopes=write:packages>. Fine-grained
   tokens don't work with ghcr.io. Never paste the token in a file or a chat.
2. Log in to `ghcr.io` with your GitHub username, passing the token on standard input:

   ```
   export TOKEN=YOUR_TOKEN
   echo $TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

   Windows PowerShell (not tested): `$env:TOKEN="YOUR_TOKEN"`, then
   `$env:TOKEN | docker login ghcr.io -u USERNAME --password-stdin`.
3. Build for both CPU types and push it as `ghcr.io/USERNAME/counter:1.0`, with
   `docker buildx build --platform linux/amd64,linux/arm64 ... --push`.

   Type `USERNAME` in lowercase even if your GitHub name has capitals: Docker rejects
   `ghcr.io/SomeUser/counter:1.0` with `repository name (SomeUser/counter) must be lowercase`.

   Why both platforms: an image built on an Apple Silicon Mac is arm64 only, and an x86 laptop
   can't run it (`exec format error`). Docker Desktop builds both with no setup. On Docker Engine
   for Linux without Docker Desktop, if the build fails, run these two commands once and try again
   (not tested):

   ```
   docker run --privileged --rm tonistiigi/binfmt --install all
   docker buildx create --name multi --driver docker-container --use
   ```

   If that doesn't work either, or Docker Desktop says the multi-platform build is not supported,
   push with `--platform linux/amd64` only: it runs on Windows and
   Linux laptops, and Docker Desktop on Apple Silicon Macs runs it through emulation.
4. On GitHub, open your profile, the **Packages** tab, then `counter`. A new package is private:
   open **Package settings**, and under **Danger Zone** use **Change visibility** to make it
   public.
5. `docker logout ghcr.io`.

**Done when** a classmate runs `docker run --rm -p 8000:5000 ghcr.io/USERNAME/counter:1.0` and
sees your name.

## Part 4: Network by hand (8 min)

1. Create a network called `lab-net`.
2. Run Redis (`redis:8-alpine`) on it, named `cache`. Don't publish its port.
3. Run `counter:1.0` on the same network, host port 8000, with `REDIS_HOST=cache`.
4. Remove the counter and run it again with `REDIS_HOST=localhost`. Read the error on the page:
   what does `localhost` mean inside a container?

Commands you need: `docker network create`, `docker run --network ... -e ...`.

**Done when** the counter increments on every refresh with `REDIS_HOST=cache`.

## Part 5: Compose (15 min)

Clean up part 4 first (`docker rm -f` the two containers): they hold host port 8000.

Write `lab/counter/compose.yaml` with two services:

- `web`: built from the `Dockerfile`, host port 8000, `REDIS_HOST` pointing at the other service.
  It is the only service with a published port.
- `cache`: `redis:8-alpine`, its data (`/data`) in a named volume `cache-data`, and a
  `healthcheck` (`redis-cli ping`). `web` waits until `cache` is healthy.

Commands you need: `docker compose up -d --build`, `docker compose ps`, `docker compose down`,
`docker compose down -v`.

**Done when** the count survives `docker compose down` and `up` again, and is back to 1 after
`docker compose down -v`.

**The result.** Once your image is public on ghcr.io, anyone can run your app without the code:
a `compose.yaml` whose `web` service says `image: ghcr.io/USERNAME/counter:1.0` instead of
`build: .`, then:

```
docker compose pull
docker compose up -d
curl localhost:8000
```

## Part 6: Fix it (extra)

Each folder in `lab/broken/` is a small setup that fails. Its `README.md` says what you see. Make
it work, and say in one sentence what was wrong.

- `1-build-hangs`
- `2-unreachable`
- `3-localhost`
- `4-port-taken`

**Done when** each one runs, and you can explain the cause.

## Extra tasks and homework

- Delete your `counter` package on GitHub (Package settings, Danger Zone, Delete this package).
- Dockerize your own project, and check it against criterion 18 of the project review:
  - a `Dockerfile` that builds and runs;
  - dependencies installed before the code is copied;
  - a `.dockerignore` that excludes `.git`, `.venv` and `.env`;
  - no secrets in the image;
  - a `compose.yaml` when there is more than one service.
- Add a GitHub Action to your project that builds the image on every pull request.
- Move the passwords of `compose.yaml` to a `.env` file (`${MYSQL_PASSWORD}` in `compose.yaml`),
  keep `.env` out of git and of the image, and commit a `.env.example`.
- Split the services of the example over two networks, and show that a name stops resolving when
  two services share no network.
