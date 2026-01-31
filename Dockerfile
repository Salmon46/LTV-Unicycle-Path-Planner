FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend ./backend
COPY frontend ./frontend

# Set working directory to backend for correct import resolution
WORKDIR /app/backend

# Expose port
EXPOSE 8001

# Run commands
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
