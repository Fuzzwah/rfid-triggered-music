# RFID Music System Configuration

## Environment Variables

# Flask App Settings
SECRET_KEY=your-secret-key-change-in-production

# Music Directory Path (Linux host)
MUSIC_BASE_PATH=/home/music

# macOS Playback Host Configuration
MACOS_HOST=192.168.1.100
MACOS_PORT=5001

# Flask App Settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

## Directory Structure

The system expects the following directory structure on the Linux host:

```
/home/music/                    # Base music directory (configurable)
├── Album1/                     # Individual album/artist directories
│   ├── song1.mp3
│   ├── song2.mp3
│   └── cover.jpg              # Optional album art
├── Album2/
│   ├── track1.mp3
│   └── track2.mp3
└── Album3/
    ├── audio1.mp3
    ├── audio2.mp3
    └── folder.jpg
```

## Network Configuration

The Linux host should be able to reach the macOS host over the network.
Default configuration assumes both hosts are on the same local network.

## RFID Reader Setup

1. Configure RFID reader to act as keyboard input device
2. Ensure it sends a carriage return (Enter) after each scan
3. The reader should have focus when scanning (or use the RFID listener service)

## Security Notes

- This system is designed for local network use only
- Change the SECRET_KEY in production
- Consider setting up proper user authentication for the web interface
- The macOS playback host should only accept connections from trusted sources