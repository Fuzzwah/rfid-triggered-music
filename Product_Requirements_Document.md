# RFID-Triggered Music Playback System — Product Requirements Document (PRD)

## 1. Project Overview

This system enables RFID-triggered music playback using `mpv` on a macOS machine connected to speakers. The macOS host accesses MP3 directories hosted on a Linux machine via a network share. The Linux host also runs a Flask-based web interface to manage RFID-to-directory assignments and captures RFID input via stdin from a keyboard-emulating reader.

## 2. Goals

- Trigger playback of MP3 directories on macOS when an RFID card is scanned.
- Centralize RFID-to-directory mapping and metadata management on the Linux host.
- Provide a user-friendly web interface for managing assignments.
- Ensure modularity, reproducibility, and minimal interference with other input systems.

## 3. System Architecture

### Components

- **macOS Playback Host**
  - Runs `mpv` only.
  - Connected to speakers.
  - Accesses MP3 directories via network share (e.g., NFS, SMB).
  - Accepts playback triggers via HTTP or socket from Linux host.

- **Linux RFID + Web Host**
  - Runs Flask web app for RFID mapping.
  - Accepts RFID input via stdin (keyboard-emulating reader).
  - Sends playback trigger to macOS host.
  - Hosts MP3 directories.

## 4. Functional Requirements

### 4.1 macOS Playback Host

- Run `mpv` in headless mode.
- Accept playback trigger via HTTP POST or socket.
- Play all `.mp3` files in the assigned directory.
- Shuffle playback, no video.

### 4.2 Linux RFID Listener

- Continuously read RFID input from stdin.
- On scan:
  - Check if RFID is mapped.
  - If mapped, send playback trigger to macOS host.
  - If unmapped, prompt user via web interface.

### 4.3 Flask Web Interface

- Display current RFID-to-directory mappings.
- On scan:
  - If RFID is mapped:
    - Show directory name and album art (if available).
    - Allow editing or unassignment.
  - If unmapped:
    - List unassigned directories in base music path.
    - Allow assignment to scanned RFID.
- Allow manual reassignment and metadata editing.

## 5. Data Model

### SQLite Schema

```
CREATE TABLE rfid_map (
    rfid TEXT PRIMARY KEY,
    music_dir TEXT NOT NULL,
    album_title TEXT,
    artist TEXT,
    cover_path TEXT
);
```

## 6. API Endpoints (Linux Flask App)

- `GET /` → Home page
- `POST /scan` → Process scanned RFID
- `POST /assign` → Assign RFID to directory
- `POST /edit` → Update metadata
- `POST /unassign` → Remove mapping

## 7. Playback Behavior

- Triggered via HTTP POST to macOS host:

```
POST /play
Content-Type: application/json

{
  "rfid": "1234567890"
}
```

- macOS host runs:

```
mpv /Volumes/music/card1/*.mp3 --no-video --shuffle
```

- Optionally use IPC:

```
mpv --input-ipc-server=/tmp/mpvsocket
```

## 8. Non-Functional Requirements

- **Latency**: < 1 second from scan to playback.
- **Security**: Local network only.
- **Portability**: Python 3, Flask, mpv.
- **Resilience**: Handle duplicate scans, missing directories, malformed input.

## 9. Deployment Notes

### macOS

- Install `mpv` via Homebrew.
- Mount network share to access MP3 directories.
- Run playback listener as background service.

### Linux

- Install Flask and SQLite3.
- Run Flask app with `gunicorn` or `flask run`.
- Ensure RFID reader is focused and stdin is captured.

## 10. Future Enhancements

- Add support for multiple playback zones.
- Integrate album art from ID3 tags.
- Add user authentication to web interface.
- Support FLAC, OGG formats.
- Add playback history and analytics.

## 11. Example Workflow

1. User opens web interface.
2. Scans RFID card.
3. If mapped:
   - Display album info and cover.
   - Option to edit or unassign.
4. If unmapped:
   - Show unassigned directories.
   - Assign one to RFID.
5. On future scans:
   - Linux listener sends RFID to macOS.
   - macOS triggers `mpv` to play mapped directory.
