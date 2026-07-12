# Obelisk

Obelisk is a backend service for managing a physical library catalog. It provides APIs for books, authors, genres, languages, publishers, library branches, readers, librarians, shelf placement, loans, and audit events.

## Features

- Manage books and their copies
- Track authors, genres, languages, and publishers
- Organize libraries, shelves, and book locations
- Register readers and handle loans
- Store audit logs for important actions
- Expose a REST API with automatic OpenAPI documentation

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLModel-1F6FEB?style=for-the-badge&logo=databricks&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![AsyncPG](https://img.shields.io/badge/AsyncPG-336791?style=for-the-badge)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=for-the-badge)

## Project Structure

- src/main.py — FastAPI application entry point
- src/api/ — route handlers for each domain
- src/models/ — SQLModel database models
- src/services/ — business logic services
- src/schemas/ — Pydantic request and response schemas
- src/utils/ — database initialization and helpers

## Prerequisites

- Docker and Docker Compose
- Python 3.12 (optional, if you want to run locally without Docker)

## Environment Variables

Create a .env file in the project root with at least the following values:

```env
DATABASE_URL=postgresql+asyncpg://librarian:LibPass_2026@postgres:5432/library_catalog
SECRET_KEY=replace-this-with-a-secure-secret
ALGORITHM=HS256
```

If you run the app with Docker Compose, the database credentials and URL are already configured in compose.yaml.

## Running with Docker Compose

From the project root:

```bash
docker compose up --build
```

The API will be available at:

- http://localhost:8001/docs
- http://localhost:8001/redoc

PostgreSQL Admin UI is also available at:

- http://localhost:5151

## Running Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the application:

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

On startup, the database tables are created automatically.

## API Documentation

FastAPI generates interactive documentation automatically:

- Swagger UI: /docs
- ReDoc: /redoc

## Notes

- The project uses async database access.
- Authentication is based on JWT bearer tokens.
- Audit logging is enabled for key create, update, delete, issue, and return actions.
