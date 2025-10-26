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
