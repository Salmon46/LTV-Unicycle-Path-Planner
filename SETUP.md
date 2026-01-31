# Setup & Installation Guide

## Prerequisites

- **Python 3.10** or higher
- **Docker** & **Docker Compose** (Optional, for containerized run)
- A modern web browser (Chrome, Firefox, Edge)

## Option 1: Docker (Recommended)

This is the easiest way to run the application as it handles all dependencies automatically.

1. Open a terminal in the project root.
2. Build and run the container:

    ```bash
    docker-compose up --build
    ```

3. The application will be available at `http://localhost:8001`.
4. To stop the server, press `Ctrl+C`.

## Option 2: Manual Local Setup

### 1. Backend Setup

1. Navigate to the backend directory:

    ```bash
    cd backend
    ```

2. (Optional) Create and activate a virtual environment:

    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Start the server:

    ```bash
    uvicorn main:app --reload --port 8001
    ```

### 2. Frontend Access

Since the backend is configured to serve the static frontend files, you simply need to access the backend URL:

- Go to `http://localhost:8001` in your browser.

## Troubleshooting

- **Port Conflicts**: If port 8001 is in use, modify `docker-compose.yml` and the `uvicorn` command to use a different port.
- **Missing Modules**: Ensure you have installed `requirements.txt` if running locally without Docker.
