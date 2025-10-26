#!/bin/bash

# Start RFID Listener Service

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
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
python rfid_listener.py