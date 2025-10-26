#!/usr/bin/env python3
"""
RFID-Triggered Music Playback System - Flask Web Application
Linux RFID + Web Host Component

This Flask app manages RFID-to-directory mappings and provides a web interface
for assigning RFID cards to music directories.
"""

import os
import sqlite3
import json
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import threading
import queue

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configuration
DATABASE_PATH = 'rfid_music.db'
MUSIC_BASE_PATH = os.environ.get('MUSIC_BASE_PATH', '/home/music')
MACOS_HOST = os.environ.get('MACOS_HOST', '192.168.1.100')
MACOS_PORT = os.environ.get('MACOS_PORT', '5001')

# Global queue for RFID scans
rfid_queue = queue.Queue()

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rfid_map (
                    rfid TEXT PRIMARY KEY,
                    music_dir TEXT NOT NULL,
                    album_title TEXT,
                    artist TEXT,
                    cover_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_played TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_mapping(self, rfid):
        """Get mapping for a specific RFID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM rfid_map WHERE rfid = ?', (rfid,))
            return cursor.fetchone()
    
    def get_all_mappings(self):
        """Get all RFID mappings"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM rfid_map ORDER BY created_at DESC')
            return cursor.fetchall()
    
    def create_mapping(self, rfid, music_dir, album_title=None, artist=None, cover_path=None):
        """Create new RFID mapping"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO rfid_map (rfid, music_dir, album_title, artist, cover_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (rfid, music_dir, album_title, artist, cover_path))
            conn.commit()
    
    def update_mapping(self, rfid, music_dir=None, album_title=None, artist=None, cover_path=None):
        """Update existing RFID mapping"""
        with self.get_connection() as conn:
            # Build dynamic UPDATE query
            updates = []
            params = []
            
            if music_dir is not None:
                updates.append('music_dir = ?')
                params.append(music_dir)
            if album_title is not None:
                updates.append('album_title = ?')
                params.append(album_title)
            if artist is not None:
                updates.append('artist = ?')
                params.append(artist)
            if cover_path is not None:
                updates.append('cover_path = ?')
                params.append(cover_path)
            
            if updates:
                query = f'UPDATE rfid_map SET {", ".join(updates)} WHERE rfid = ?'
                params.append(rfid)
                conn.execute(query, params)
                conn.commit()
    
    def delete_mapping(self, rfid):
        """Delete RFID mapping"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM rfid_map WHERE rfid = ?', (rfid,))
            conn.commit()
    
    def update_last_played(self, rfid):
        """Update last played timestamp"""
        with self.get_connection() as conn:
            conn.execute(
                'UPDATE rfid_map SET last_played = CURRENT_TIMESTAMP WHERE rfid = ?',
                (rfid,)
            )
            conn.commit()

# Initialize database manager
db = DatabaseManager(DATABASE_PATH)

def get_available_directories():
    """Get list of available music directories"""
    try:
        music_path = Path(MUSIC_BASE_PATH)
        if not music_path.exists():
            return []
        
        # Get all directories that contain MP3 files
        directories = []
        for item in music_path.iterdir():
            if item.is_dir():
                # Check if directory contains MP3 files
                mp3_files = list(item.glob('*.mp3'))
                if mp3_files:
                    directories.append({
                        'name': item.name,
                        'path': str(item),
                        'mp3_count': len(mp3_files)
                    })
        
        return sorted(directories, key=lambda x: x['name'])
    except Exception as e:
        print(f"Error scanning music directories: {e}")
        return []

def get_assigned_directories():
    """Get list of already assigned directories"""
    mappings = db.get_all_mappings()
    return [mapping['music_dir'] for mapping in mappings]

def trigger_playback(rfid):
    """Send playback trigger to macOS host"""
    try:
        url = f"http://{MACOS_HOST}:{MACOS_PORT}/play"
        payload = {"rfid": rfid}
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error triggering playback: {e}")
        return False

@app.route('/')
def index():
    """Home page showing all RFID mappings"""
    mappings = db.get_all_mappings()
    return render_template('index.html', mappings=mappings)

@app.route('/scan', methods=['POST'])
def handle_scan():
    """Process scanned RFID from the listener"""
    data = request.get_json()
    if not data or 'rfid' not in data:
        return jsonify({'error': 'No RFID provided'}), 400
    
    rfid = data['rfid'].strip()
    if not rfid:
        return jsonify({'error': 'Empty RFID'}), 400
    
    # Check if RFID is mapped
    mapping = db.get_mapping(rfid)
    
    if mapping:
        # Update last played timestamp
        db.update_last_played(rfid)
        
        # Trigger playback on macOS
        success = trigger_playback(rfid)
        
        return jsonify({
            'mapped': True,
            'rfid': rfid,
            'music_dir': mapping['music_dir'],
            'album_title': mapping['album_title'],
            'artist': mapping['artist'],
            'playback_triggered': success
        })
    else:
        # RFID not mapped - add to queue for web interface
        rfid_queue.put(rfid)
        
        return jsonify({
            'mapped': False,
            'rfid': rfid,
            'message': 'RFID not mapped. Please assign via web interface.'
        })

@app.route('/assign', methods=['GET', 'POST'])
def assign():
    """Assign RFID to music directory"""
    if request.method == 'GET':
        # Get pending RFID from queue or URL parameter
        pending_rfid = request.args.get('rfid')
        if not pending_rfid and not rfid_queue.empty():
            pending_rfid = rfid_queue.get()
        
        # Get available directories (not already assigned)
        all_directories = get_available_directories()
        assigned_dirs = get_assigned_directories()
        available_directories = [
            d for d in all_directories 
            if d['path'] not in assigned_dirs
        ]
        
        return render_template(
            'assign.html',
            pending_rfid=pending_rfid,
            directories=available_directories
        )
    
    elif request.method == 'POST':
        rfid = request.form.get('rfid')
        music_dir = request.form.get('music_dir')
        album_title = request.form.get('album_title', '')
        artist = request.form.get('artist', '')
        
        if not rfid or not music_dir:
            flash('RFID and music directory are required', 'error')
            return redirect(url_for('assign'))
        
        try:
            # Check if RFID already exists
            existing = db.get_mapping(rfid)
            if existing:
                flash(f'RFID {rfid} is already assigned to {existing["music_dir"]}', 'error')
                return redirect(url_for('assign'))
            
            # Create new mapping
            db.create_mapping(rfid, music_dir, album_title, artist)
            flash(f'Successfully assigned RFID {rfid} to {music_dir}', 'success')
            
            return redirect(url_for('index'))
        
        except Exception as e:
            flash(f'Error creating assignment: {str(e)}', 'error')
            return redirect(url_for('assign'))

@app.route('/edit/<rfid>', methods=['GET', 'POST'])
def edit(rfid):
    """Edit existing RFID mapping"""
    mapping = db.get_mapping(rfid)
    if not mapping:
        flash('RFID mapping not found', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('edit.html', mapping=mapping)
    
    elif request.method == 'POST':
        album_title = request.form.get('album_title', '')
        artist = request.form.get('artist', '')
        
        try:
            db.update_mapping(rfid, album_title=album_title, artist=artist)
            flash('Mapping updated successfully', 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            flash(f'Error updating mapping: {str(e)}', 'error')
            return redirect(url_for('edit', rfid=rfid))

@app.route('/unassign/<rfid>', methods=['POST'])
def unassign(rfid):
    """Remove RFID mapping"""
    try:
        mapping = db.get_mapping(rfid)
        if mapping:
            db.delete_mapping(rfid)
            flash(f'Successfully removed mapping for RFID {rfid}', 'success')
        else:
            flash('RFID mapping not found', 'error')
    
    except Exception as e:
        flash(f'Error removing mapping: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/mappings')
def api_mappings():
    """API endpoint to get all mappings as JSON"""
    mappings = db.get_all_mappings()
    return jsonify([dict(mapping) for mapping in mappings])

@app.route('/api/directories')
def api_directories():
    """API endpoint to get available directories"""
    directories = get_available_directories()
    return jsonify(directories)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print(f"Starting RFID Music Flask App")
    print(f"Database: {DATABASE_PATH}")
    print(f"Music path: {MUSIC_BASE_PATH}")
    print(f"macOS host: {MACOS_HOST}:{MACOS_PORT}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)