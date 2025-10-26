#!/bin/bash

# Start Flask Web Application

# Configuration - Update these for your environment
export SECRET_KEY="your-secret-key-change-in-production"
export MUSIC_BASE_PATH="/home/music"
export MACOS_HOST="192.168.1.100"
export MACOS_PORT="5001"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
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
python app.py

# For production, use gunicorn instead:
# gunicorn -w 4 -b 0.0.0.0:5000 app:app --access-logfile logs/access.log --error-logfile logs/error.log