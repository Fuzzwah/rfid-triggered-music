#!/usr/bin/env python3
"""
RFID Music System - macOS Playback Host

This script runs on the macOS machine and handles music playback requests
from the Linux RFID host. It uses mpv to play MP3 files from network-mounted
music directories.
"""

import os
import json
import subprocess
import threading
from pathlib import Path
from flask import Flask, request, jsonify
import glob

app = Flask(__name__)

# Configuration
MUSIC_MOUNT_PATH = os.environ.get('MUSIC_MOUNT_PATH', '/Volumes/music')
MPV_COMMAND = 'mpv'
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 5001

class MusicPlayer:
    def __init__(self):
        self.current_process = None
        self.is_playing = False
    
    def stop_current_playback(self):
        """Stop any currently playing music"""
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
        self.is_playing = False
    
    def play_directory(self, music_dir):
        """Play all MP3 files in the specified directory"""
        try:
            # Stop any current playback
            self.stop_current_playback()
            
            # Find MP3 files in the directory
            mp3_pattern = os.path.join(music_dir, '*.mp3')
            mp3_files = glob.glob(mp3_pattern)
            
            if not mp3_files:
                print(f"No MP3 files found in {music_dir}")
                return False
            
            print(f"Playing {len(mp3_files)} MP3 files from {music_dir}")
            
            # Build mpv command
            mpv_args = [
                MPV_COMMAND,
                '--no-video',           # Audio only
                '--shuffle',            # Shuffle playback
                '--loop-playlist=inf',  # Loop the playlist
                '--volume=80'           # Set volume to 80%
            ] + mp3_files
            
            # Start mpv in a separate thread
            def run_mpv():
                try:
                    self.current_process = subprocess.Popen(
                        mpv_args,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.is_playing = True
                    self.current_process.wait()
                    self.is_playing = False
                except Exception as e:
                    print(f"Error running mpv: {e}")
                    self.is_playing = False
            
            playback_thread = threading.Thread(target=run_mpv, daemon=True)
            playback_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Error starting playback: {e}")
            return False

# Initialize player
player = MusicPlayer()

def get_database_mapping(rfid):
    """
    In a full implementation, this would query the Linux host's database
    For now, we'll implement a simple mapping lookup via HTTP
    """
    # This could make an HTTP request to the Linux host to get the mapping
    # For simplicity, we'll expect the directory to be passed directly
    return None

@app.route('/play', methods=['POST'])
def play_music():
    """Handle music playback request from Linux host"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        rfid = data.get('rfid')
        music_dir = data.get('music_dir')  # Direct directory path
        
        if not rfid:
            return jsonify({'error': 'No RFID provided'}), 400
        
        # If music_dir is provided directly, use it
        if music_dir:
            full_path = music_dir
        else:
            # Otherwise, we'd need to look up the mapping
            # For now, assume the directory name matches the RFID
            full_path = os.path.join(MUSIC_MOUNT_PATH, rfid)
        
        # Verify the directory exists and is accessible
        if not os.path.exists(full_path):
            return jsonify({
                'error': f'Music directory not found: {full_path}',
                'rfid': rfid
            }), 404
        
        if not os.path.isdir(full_path):
            return jsonify({
                'error': f'Path is not a directory: {full_path}',
                'rfid': rfid
            }), 400
        
        # Start playback
        success = player.play_directory(full_path)
        
        if success:
            return jsonify({
                'success': True,
                'rfid': rfid,
                'music_dir': full_path,
                'message': 'Playback started'
            })
        else:
            return jsonify({
                'error': 'Failed to start playback',
                'rfid': rfid,
                'music_dir': full_path
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/stop', methods=['POST'])
def stop_music():
    """Stop current music playback"""
    try:
        player.stop_current_playback()
        return jsonify({
            'success': True,
            'message': 'Playback stopped'
        })
    except Exception as e:
        return jsonify({'error': f'Error stopping playback: {str(e)}'}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current playback status"""
    return jsonify({
        'is_playing': player.is_playing,
        'music_mount_path': MUSIC_MOUNT_PATH,
        'mpv_available': check_mpv_available()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mpv_available': check_mpv_available(),
        'music_mount_accessible': os.path.exists(MUSIC_MOUNT_PATH)
    })

def check_mpv_available():
    """Check if mpv is available in PATH"""
    try:
        result = subprocess.run(['which', MPV_COMMAND], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def check_music_mount():
    """Check if music mount point is accessible"""
    if not os.path.exists(MUSIC_MOUNT_PATH):
        print(f"Warning: Music mount path {MUSIC_MOUNT_PATH} does not exist")
        print("Make sure to mount the network share with music files")
        return False
    return True

if __name__ == '__main__':
    print("RFID Music System - macOS Playback Host")
    print("=====================================")
    print(f"Music mount path: {MUSIC_MOUNT_PATH}")
    print(f"Listening on: {LISTEN_HOST}:{LISTEN_PORT}")
    
    # Check dependencies
    if not check_mpv_available():
        print("ERROR: mpv not found. Install with: brew install mpv")
        exit(1)
    
    if not check_music_mount():
        print("WARNING: Music mount not accessible")
    
    print("\nStarting playback service...")
    print("Ready to receive playback requests from Linux host")
    
    app.run(host=LISTEN_HOST, port=LISTEN_PORT, debug=False)