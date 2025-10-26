#!/bin/bash

# Quick Start Script for RFID Music System using uv

echo "🎵 RFID Music System - Quick Start"
echo "=================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv not found. Please run ./setup.sh first"
    exit 1
fi

# Check if project is set up
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./setup.sh
fi

# Configuration
export MUSIC_BASE_PATH="${MUSIC_BASE_PATH:-/home/music}"
export MACOS_HOST="${MACOS_HOST:-192.168.1.100}"
export MACOS_PORT="${MACOS_PORT:-5001}"
export SECRET_KEY="${SECRET_KEY:-dev-secret-key-change-in-production}"

echo ""
echo "Configuration:"
echo "  Music directory: $MUSIC_BASE_PATH"
echo "  macOS host: $MACOS_HOST:$MACOS_PORT"
echo ""

# Function to start Flask app
start_webapp() {
    echo "Starting Flask Web Application..."
    uv run python app.py
}

# Function to start RFID listener
start_rfid_listener() {
    echo "Starting RFID Listener..."
    uv run python rfid_listener.py
}

# Check command line argument
case "${1:-}" in
    "web"|"webapp"|"flask")
        start_webapp
        ;;
    "rfid"|"listener")
        start_rfid_listener
        ;;
    "both"|"")
        echo "Starting both services..."
        echo "Web interface: http://localhost:5000"
        echo ""
        
        # Start webapp in background
        start_webapp &
        WEBAPP_PID=$!
        
        # Wait a moment for webapp to start
        sleep 2
        
        # Start RFID listener in foreground
        echo "RFID listener starting... (Ctrl+C to stop both services)"
        trap "echo 'Stopping services...'; kill $WEBAPP_PID 2>/dev/null; exit 0" INT TERM
        start_rfid_listener
        ;;
    *)
        echo "Usage: $0 [web|rfid|both]"
        echo ""
        echo "Commands:"
        echo "  web    - Start Flask web application only"
        echo "  rfid   - Start RFID listener only" 
        echo "  both   - Start both services (default)"
        echo ""
        echo "Environment variables:"
        echo "  MUSIC_BASE_PATH - Path to music directories (default: /home/music)"
        echo "  MACOS_HOST      - macOS playback host IP (default: 192.168.1.100)"
        echo "  MACOS_PORT      - macOS playback port (default: 5001)"
        exit 1
        ;;
esac