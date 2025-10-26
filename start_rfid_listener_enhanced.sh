#!/bin/bash

# Enhanced RFID Listener Startup Script

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Run setup.sh first."
    exit 1
fi

echo "Starting Enhanced RFID Listener Service..."
echo "This version auto-detects your RFID reader device"
echo ""
echo "Make sure:"
echo "  1. Flask web app is running (start_webapp.sh)"
echo "  2. RFID reader is connected (detected as USB HID keyboard)"
echo "  3. You have permission to access input devices"
echo ""

# Check if user is in input group
if ! groups | grep -q input; then
    echo "WARNING: You may need input group permissions"
    echo "Run: sudo usermod -a -G input \$(whoami)"
    echo "Then log out and back in, or run: newgrp input"
    echo ""
fi

echo "Starting auto-detection and listening for RFID cards..."
echo "Press Ctrl+C to stop"
echo ""

# Start the enhanced listener
python rfid_listener_enhanced.py