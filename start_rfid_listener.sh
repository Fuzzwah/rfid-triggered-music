#!/bin/bash

# Start RFID Listener Service

# Check if uv is available and use it, otherwise fall back to traditional venv
if command -v uv &> /dev/null && [ -d ".venv" ]; then
    echo "Using uv virtual environment..."
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

echo "Starting RFID Listener Service..."
echo "Make sure:"
echo "  1. Flask web app is running (start_webapp.sh)"
echo "  2. RFID reader is connected and configured as keyboard input"
echo "  3. This terminal has focus to receive RFID input"
echo ""
echo "Scan RFID cards to trigger music playback..."
echo "Press Ctrl+C to stop"
echo ""

# Start the listener
${UV_RUN} python rfid_listener.py