#!/bin/bash

# Start Flask Web Application

# Configuration - Update these for your environment
export SECRET_KEY="your-secret-key-change-in-production"
export MUSIC_BASE_PATH="/home/music"
export MACOS_HOST="192.168.1.100"
export MACOS_PORT="5001"

# Check if uv is available and use it, otherwise fall back to traditional venv
if command -v uv &> /dev/null && [ -d ".venv" ]; then
    echo "Using uv virtual environment..."
    # uv run automatically activates the virtual environment
    UV_RUN="uv run"
elif [ -d ".venv" ]; then
    echo "Activating .venv virtual environment..."
    source .venv/bin/activate
    UV_RUN=""
elif [ -d "venv" ]; then
    echo "Activating venv virtual environment..."
    source venv/bin/activate
    UV_RUN=""
else
    echo "Virtual environment not found. Run setup.sh first."
    exit 1
fi

echo "Starting Flask Web Application..."
echo "Web interface will be available at: http://localhost:5000"
echo "Music directory: $MUSIC_BASE_PATH"
echo "macOS host: $MACOS_HOST:$MACOS_PORT"
echo ""

# For development
${UV_RUN} python app.py

# For production, use gunicorn instead:
# ${UV_RUN} gunicorn -w 4 -b 0.0.0.0:5000 app:app --access-logfile logs/access.log --error-logfile logs/error.log