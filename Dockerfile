FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables to prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (needed for compiling some python packages like asyncpg if wheels are missing)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml
COPY pyproject.toml ./

# Install project and dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
