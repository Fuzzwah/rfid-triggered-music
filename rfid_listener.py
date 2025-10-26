#!/usr/bin/env python3
"""
RFID Listener Service

This service continuously reads RFID input from stdin (keyboard-emulating RFID reader)
and sends the scanned RFID to the Flask web application for processing.
"""

import sys
import json
import requests
import time
import threading
from datetime import datetime
import logging

# Configuration
FLASK_HOST = 'localhost'
FLASK_PORT = 5000
SCAN_TIMEOUT = 2.0  # Seconds to wait for complete RFID scan
MIN_RFID_LENGTH = 6  # Minimum length for valid RFID
MAX_RFID_LENGTH = 20  # Maximum length for valid RFID

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rfid_listener.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RFIDListener:
    def __init__(self, flask_host=FLASK_HOST, flask_port=FLASK_PORT):
        self.flask_url = f"http://{flask_host}:{flask_port}/scan"
        self.running = False
        self.last_scan_time = 0
        self.scan_buffer = ""
        self.scan_timer = None
        
    def process_scan(self, rfid_data):
        """Process a complete RFID scan"""
        rfid = rfid_data.strip()
        
        # Validate RFID format
        if not self.is_valid_rfid(rfid):
            logger.warning(f"Invalid RFID format: '{rfid}'")
            return
        
        # Prevent duplicate scans within short time window
        current_time = time.time()
        if current_time - self.last_scan_time < 1.0:
            logger.debug(f"Ignoring duplicate scan: {rfid}")
            return
        
        self.last_scan_time = current_time
        logger.info(f"Processing RFID scan: {rfid}")
        
        try:
            # Send RFID to Flask app
            payload = {'rfid': rfid}
            response = requests.post(
                self.flask_url, 
                json=payload, 
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('mapped'):
                    logger.info(f"RFID {rfid} mapped to: {result.get('music_dir')}")
                    if result.get('playback_triggered'):
                        logger.info("Playback triggered successfully")
                    else:
                        logger.warning("Failed to trigger playback")
                else:
                    logger.info(f"RFID {rfid} not mapped - awaiting assignment")
            else:
                logger.error(f"Flask app returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Flask app: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing scan: {e}")
    
    def is_valid_rfid(self, rfid):
        """Validate RFID format"""
        if not rfid:
            return False
        
        if len(rfid) < MIN_RFID_LENGTH or len(rfid) > MAX_RFID_LENGTH:
            return False
        
        # Check if it's alphanumeric (adjust regex as needed for your RFID format)
        if not rfid.replace(' ', '').isalnum():
            return False
        
        return True
    
    def flush_scan_buffer(self):
        """Process accumulated scan data after timeout"""
        if self.scan_buffer:
            logger.debug(f"Processing buffered scan: '{self.scan_buffer}'")
            self.process_scan(self.scan_buffer)
            self.scan_buffer = ""
        self.scan_timer = None
    
    def handle_input_char(self, char):
        """Handle individual character input from RFID reader"""
        if char == '\n' or char == '\r':
            # End of scan - process immediately
            if self.scan_timer:
                self.scan_timer.cancel()
                self.scan_timer = None
            
            if self.scan_buffer:
                self.process_scan(self.scan_buffer)
                self.scan_buffer = ""
        else:
            # Add character to buffer
            self.scan_buffer += char
            
            # Reset/start timer for scan completion
            if self.scan_timer:
                self.scan_timer.cancel()
            
            self.scan_timer = threading.Timer(SCAN_TIMEOUT, self.flush_scan_buffer)
            self.scan_timer.start()
    
    def start_listening(self):
        """Start listening for RFID input from stdin"""
        self.running = True
        logger.info("RFID listener starting...")
        logger.info("Ensure RFID reader is configured to act as keyboard input")
        logger.info("Scanning for RFID cards...")
        
        try:
            while self.running:
                try:
                    # Read character by character for better control
                    char = sys.stdin.read(1)
                    if char:
                        self.handle_input_char(char)
                    else:
                        # EOF reached
                        time.sleep(0.1)
                        
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
                    break
                except EOFError:
                    logger.info("EOF reached on stdin")
                    break
                except Exception as e:
                    logger.error(f"Error reading stdin: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"Fatal error in listener loop: {e}")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop the RFID listener"""
        self.running = False
        if self.scan_timer:
            self.scan_timer.cancel()
        logger.info("RFID listener stopped")

def check_flask_app():
    """Check if Flask app is running"""
    try:
        response = requests.get(f"http://{FLASK_HOST}:{FLASK_PORT}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    logger.info("Starting RFID Listener Service")
    
    # Wait for Flask app to be available
    logger.info("Waiting for Flask app to be available...")
    while not check_flask_app():
        logger.info(f"Flask app not available at {FLASK_HOST}:{FLASK_PORT}, retrying in 5 seconds...")
        time.sleep(5)
    
    logger.info("Flask app is available, starting RFID listener")
    
    # Create and start listener
    listener = RFIDListener(FLASK_HOST, FLASK_PORT)
    
    try:
        listener.start_listening()
    except KeyboardInterrupt:
        logger.info("Shutting down RFID listener...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()