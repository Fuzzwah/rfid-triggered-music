# RFID-Triggered Music Playback System

A simple, modular system that plays music albums using RFID cards. Scan a card, and your chosen album starts playing on your speakers—perfect for physical music collections, kids' music players, or anyone who loves the tactile experience of choosing music.

## Overview

This system uses two machines working together:

- **macOS (Playback Host)**: Connected to speakers, runs `mpv` media player
- **Linux (RFID & Web Host)**: Handles RFID scanning and provides a web interface for managing card-to-album assignments

When you scan an RFID card on the Linux machine, it triggers playback of the assigned music directory on the macOS machine. A Flask web interface lets you easily assign albums to cards and manage metadata.

## Features

- 🎵 **Instant Playback**: Scan an RFID card to start playing an album
- 🖥️ **Web Interface**: Easy-to-use interface for managing card assignments
- 🎨 **Album Art Support**: Display cover images for your music
- 🔀 **Shuffle Mode**: Randomized playback of tracks
- 🗂️ **Centralized Management**: All metadata and mappings stored in SQLite database
- 🔌 **Modular Design**: Separate RFID handling from playback for flexibility

## System Requirements

### macOS (Playback Host)
- macOS (any recent version)
- `mpv` media player
- Network share access (NFS or SMB)
- Python 3.x

### Linux (RFID & Web Host)
- Linux distribution (tested on Ubuntu/Debian)
- Python 3.x
- Flask
- SQLite3
- USB RFID reader (keyboard emulation mode)

## Installation

### macOS Setup

First, install `mpv` using Homebrew:

```
brew install mpv
```

Mount the network share where your music is stored. For NFS, you can mount it with:

```
sudo mount -t nfs linux-host:/path/to/music /Volumes/music
```

For SMB, use:

```
mount -t smbfs //linux-host/music /Volumes/music
```

Clone this repository and install Python dependencies:

```
git clone https://github.com/Fuzzwah/rfid-triggered-music.git
cd rfid-triggered-music
pip3 install -r requirements.txt
```

### Linux Setup

Clone the repository:

```
git clone https://github.com/Fuzzwah/rfid-triggered-music.git
cd rfid-triggered-music
```

Install Python dependencies:

```
pip3 install -r requirements.txt
```

Create the SQLite database:

```
python3 init_db.py
```

Configure your music directory path in `config.py`.

## Configuration

Create a `config.py` file with your settings:

```
# Linux host settings
MUSIC_BASE_PATH = "/path/to/music/directories"
MACOS_HOST = "192.168.1.100"  # IP address of macOS playback host
MACOS_PORT = 5001

# Flask settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DEBUG = False

# Database
DATABASE_PATH = "rfid_mappings.db"
```

## Usage

### Starting the System

On the Linux host, start the Flask web interface:

```
python3 app.py
```

In another terminal on the Linux host, start the RFID listener:

```
python3 rfid_listener.py
```

On the macOS host, start the playback service:

```
python3 playback_service.py
```

### Managing RFID Cards

Open your web browser and navigate to the Linux host's IP address on port 5000:

```
http://linux-host-ip:5000
```

To assign a new card, scan it with the RFID reader. If it's not already assigned, you'll see a list of available music directories. Select one to assign it to the card.

To edit or unassign an existing card, scan it and use the web interface options.

### Playing Music

Simply scan an RFID card that's been assigned to a music directory. The macOS host will automatically start playing the album.

## Project Structure

```
rfid-triggered-music/
├── README.md
├── Product_Requirements_Document.md
├── requirements.txt
├── config.py
├── init_db.py                 # Database initialization
├── app.py                     # Flask web application
├── rfid_listener.py           # RFID scanning service (Linux)
├── playback_service.py        # Music playback service (macOS)
├── templates/
│   └── index.html            # Web interface template
└── static/
    └── style.css             # Web interface styling
```

## How It Works

The RFID reader connects to the Linux machine and emulates a keyboard. When you scan a card, it types the RFID code followed by Enter.

The RFID listener on Linux captures this input, looks up the RFID in the SQLite database, and sends a playback request to the macOS host.

The macOS playback service receives the request, looks up the corresponding music directory, and starts `mpv` to play all MP3 files in that directory.

## Troubleshooting

If playback doesn't start, check that the network share is mounted on macOS:

```
ls /Volumes/music
```

To verify the playback service is running, check for the process:

```
ps aux | grep playback_service
```

To test RFID reader input, run the listener in debug mode:

```
python3 rfid_listener.py --debug
```

## Future Enhancements

See the [Product Requirements Document](Product_Requirements_Document.md) for planned features including:

- Multiple playback zones
- ID3 tag integration for automatic metadata
- User authentication
- Support for FLAC and OGG formats
- Playback history and analytics

## License

MIT License - feel free to use and modify for your own projects.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

Built with:
- [mpv](https://mpv.io/) - Media player
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [SQLite](https://www.sqlite.org/) - Database
