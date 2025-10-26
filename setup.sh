#!/bin/bash

# RFID Music System - Linux Host Setup Script
# This script sets up the Linux RFID + Web Host environment

echo "Setting up RFID Music System - Linux Host"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p logs
mkdir -p static/covers

# Set environment variables (you may want to customize these)
export SECRET_KEY="your-secret-key-change-in-production"
export MUSIC_BASE_PATH="/home/music"  # Change to your music directory
export MACOS_HOST="192.168.1.100"    # Change to your macOS host IP
export MACOS_PORT="5001"

echo ""
echo "Setup complete!"
echo ""
echo "Configuration:"
echo "  Music directory: $MUSIC_BASE_PATH"
echo "  macOS host: $MACOS_HOST:$MACOS_PORT"
echo ""
echo "To start the system:"
echo "  1. Start the Flask app: ./start_webapp.sh"
echo "  2. Start the RFID listener: ./start_rfid_listener.sh"
echo ""
echo "Make sure to:"
echo "  1. Update environment variables in the scripts as needed"
echo "  2. Ensure your music directory exists and contains subdirectories with MP3 files"
echo "  3. Configure your RFID reader to act as a keyboard input device"
echo "  4. Set up the macOS playback host"