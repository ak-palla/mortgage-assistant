FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/app ./app

# Create leads.json file if it doesn't exist
RUN touch /app/leads.json

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the application (use PORT env var, default to 8000 for local)
# Railway sets PORT automatically, so we use it here
# Use exec form to ensure PORT is properly expanded
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
