# Coin API
> **IMPORTANT:**
> 
> In a real-world scenario, I would never include actual passwords or secrets in the repository. I would only include an `.env.example` file with placeholders. However, under the current circumstances, the `.env` file is included for convenience.
>
> **If the .env file is not present, the build process will fail.**

The application consists of the following components:
* **FastAPI Webserver**: The core backend API.
* **Nginx Reverse Proxy**: Handles incoming traffic and load balancing.
* **Redis**: Used for data caching.

## Prerequisites
Before running the project, ensure you have the following installed:
* **Docker** (Tested on version `28.2.2`, build `e6534b4`)
* **Docker Compose** (Tested on version `v5.0.0-desktop.1`)
* **Make** (Tested on version `4.4.1`)
  
For local testing (optional):
* **Python** (Tested on version `3.13.3`)
* **uv** (Tested on version `0.9.26`)

## How to use

The build, teardown and testing processes are fully automated via the `Makefile`:

**Start the infrastructure**:
```bash
make dev-run
```
**Access the application**:
```
http://localhost
```
**Access the application Swagger UI**:
```
http://localhost/docs
```
**Make an exchange request**:
```
http://localhost/exchange?coin=<selected coin>&amount=<selected amount>`
```
**Shut down**:
```bash
make dev-clean
```
**Cleanup**:
```bash
make dev-prune
```

For more options run simple `make`.

## Scalability
The web server can be scaled to multiple replicas using docker-compose.yaml.
All replicas will be served behind the Nginx.

## Extra

### Tests
In addition to the core requirements, the project includes unit and integration tests.
The test suite is flexible and can be executed in 2 ways:

**Dockerized Environment**:
```bash
make test-run
```

**Local virtual Environment**:
```bash
make local-test
```
### Logging
Each server replica has its own log file. For convenience, the log folder from the container is mounted to the host's `/log` folder so you can easily inspect logs while the app is running.

### Cache failure
Because avoiding spam to the external API is mentioned as a critical requirement, I also considered the scenario where the Redis cache goes down and becomes inaccessible. In this case, I implemented a simple form of rate limiting at the level of each web server replica. Example:

1. A user makes a request to convert a certain amount of BTC.

    - The server cannot access the cache to check for an existing entry, so it attempts to call the external API directly.

2. The user then makes a request to convert a certain amount of ETH.

    - This request will reach the external API because it is a different currency.

3. The user makes another request to convert BTC within 2 minutes of the first request.

    - The server refuses to make the request.
    The replica will only be able to make the request to the external API after the 2-minute timeout expires (similar to what happens when the Redis cache is up and running).
