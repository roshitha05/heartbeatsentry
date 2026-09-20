# HeartbeatSentry

HeartbeatSentry is a backend API project I built to explore API development, endpoint monitoring, database integration, automated testing and deployment using Python.

The application allows web endpoints to be registered and checked for availability. Each check records the HTTP status, response time and health status, while previous results are stored and used to calculate basic uptime statistics.

## Live Demo

**API:** https://heartbeatsentry.onrender.com  
**Swagger Documentation:** https://heartbeatsentry.onrender.com/docs

> The API is hosted on Render's free tier, so the first request may take longer if the service has been inactive.

## What I Built

HeartbeatSentry can:

- Register endpoints to monitor
- Send real HTTP requests to registered endpoints
- Detect healthy and unhealthy responses
- Measure response times
- Store monitoring results in PostgreSQL
- Retrieve previous health checks
- Calculate uptime and average response time
- Validate URLs and prevent duplicate endpoints
- Handle failed connections and HTTP errors
- Expose the API through automatically generated Swagger documentation

## Tech Stack

| Technology | Usage |
| --- | --- |
| Python | Backend development |
| FastAPI | REST API |
| Pydantic | Request and URL validation |
| HTTPX | Endpoint health checks |
| SQLAlchemy | Database access |
| PostgreSQL | Production database |
| Neon | PostgreSQL hosting |
| Pytest | Automated testing |
| GitHub Actions | Continuous integration |
| Render | API deployment |

## How It Works

```text
Client / Swagger
       |
       v
HeartbeatSentry API
     (FastAPI)
       |
       +------------------+
       |                  |
       v                  v
     HTTPX            SQLAlchemy
       |                  |
       v                  v
Monitored Website    PostgreSQL
                       (Neon)
```

When a health check is requested, HeartbeatSentry sends an HTTP request to the registered URL using HTTPX. The response status and response time are recorded and stored in PostgreSQL.

Stored results are then used to calculate statistics such as uptime percentage, successful and failed checks, average response time and latest status.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | API information |
| GET | `/health` | Check HeartbeatSentry's health |
| POST | `/endpoints` | Register an endpoint |
| GET | `/endpoints` | View registered endpoints |
| POST | `/endpoints/{endpoint_id}/check` | Run an endpoint health check |
| GET | `/endpoints/{endpoint_id}/checks` | View previous checks |
| GET | `/endpoints/{endpoint_id}/stats` | View uptime statistics |

Interactive documentation for these endpoints is available through Swagger at `/docs`.

## Example

A health check returns information such as:

```json
{
  "endpoint_id": 1,
  "status": "healthy",
  "status_code": 200,
  "response_time_ms": 576.08,
  "error": null
}
```

HeartbeatSentry currently treats HTTP `2xx` and `3xx` responses as healthy. Connection failures and unsuccessful responses are recorded as unhealthy.

## Testing

I created a Pytest test suite covering the main API and monitoring behaviour.

The current suite contains **12 automated tests**, including:

- Endpoint creation and retrieval
- URL validation
- Duplicate endpoint handling
- Missing endpoints
- Successful health checks
- Unhealthy HTTP responses
- Connection failures
- Check history
- Uptime calculations

HTTP requests are mocked during testing so the test suite does not depend on external websites being available.

Run the tests with:

```bash
pytest -v
```

## CI/CD and Deployment

A GitHub Actions workflow automatically installs the project dependencies and runs the Pytest suite whenever changes are pushed to `main` or submitted through a pull request.

The API is deployed on Render and uses a PostgreSQL database hosted on Neon.

Production database credentials are provided through the `DATABASE_URL` environment variable rather than being stored in the repository.

## Local Setup

Clone the repository:

```bash
git clone https://github.com/roshitha05/heartbeatsentry.git
cd heartbeatsentry
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Swagger documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

By default, local development uses SQLite. A PostgreSQL connection can be supplied through the `DATABASE_URL` environment variable.

## Project Structure

```text
heartbeatsentry/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── routers/
│   │   └── endpoints.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── monitor.py
│   └── schemas.py
├── tests/
│   └── test_health.py
├── README.md
└── requirements.txt
```

## What I Learned

This project gave me practical experience with:

- Designing and implementing REST API endpoints
- Integrating an application with PostgreSQL
- Working with an ORM using SQLAlchemy
- Making and handling external HTTP requests
- Validating API input and handling errors
- Writing automated backend tests
- Mocking external dependencies during testing
- Managing development and production database configurations
- Setting up continuous integration with GitHub Actions
- Deploying a Python API and managing environment variables

## Future Improvements

Possible improvements include scheduled health checks, configurable monitoring intervals, downtime alerts, authentication, endpoint management and Docker containerisation.

## License

MIT License