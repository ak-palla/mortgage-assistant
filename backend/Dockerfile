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

# Use entrypoint script to handle PORT variable
ENTRYPOINT ["/app/entrypoint.sh"]
