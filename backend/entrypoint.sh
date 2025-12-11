#!/bin/bash
set -e

# Use PORT from environment or default to 8000
# Remove any $ signs that might be in the PORT variable
PORT=${PORT:-8000}
PORT=$(echo "$PORT" | sed 's/\$//g')

# Ensure PORT is a valid integer
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Warning: PORT is not a valid integer, using default 8000"
    PORT=8000
fi

echo "Starting uvicorn on port: $PORT"

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
