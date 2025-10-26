#!/usr/bin/env python3
"""
Enhanced RFID Listener Service - Auto-detects RFID reader device

This version automatically finds the RFID reader device and reads from it directly,
rather than relying on stdin focus.
"""

import os
import sys
import json
import requests
import time
import threading
import logging
import glob
import re
from datetime import datetime
import select

# Configuration
FLASK_HOST = 'localhost'
FLASK_PORT = 5000
SCAN_TIMEOUT = 2.0
MIN_RFID_LENGTH = 6
MAX_RFID_LENGTH = 20

# RFID Reader identification patterns
RFID_READER_PATTERNS = [
    r'OKE.*Electron',
    r'Chic.*Technology',
    r'05fe:1010',
    r'RFID',
    r'Card.*Reader'
]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rfid_listener_enhanced.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EnhancedRFIDListener:
    def __init__(self, flask_host=FLASK_HOST, flask_port=FLASK_PORT):
        self.flask_url = f"http://{flask_host}:{flask_port}/scan"
        self.running = False
        self.last_scan_time = 0
        self.device_path = None
        
    def find_rfid_device(self):
        """Auto-detect RFID reader input device"""
        logger.info("Searching for RFID reader device...")
        
        # Method 1: Check /proc/bus/input/devices
        try:
            with open('/proc/bus/input/devices', 'r') as f:
                content = f.read()
                
            # Split into device blocks
            devices = content.split('\n\n')
            
            for device_block in devices:
                # Check if this device matches RFID reader patterns
                for pattern in RFID_READER_PATTERNS:
                    if re.search(pattern, device_block, re.IGNORECASE):
                        # Extract the event handler
                        handlers = re.findall(r'H: Handlers=.*?(event\d+)', device_block)
                        if handlers:
                            event_device = handlers[0]
                            device_path = f'/dev/input/{event_device}'
                            if os.path.exists(device_path):
                                logger.info(f"Found RFID reader: {device_path}")
                                logger.info(f"Device info: {device_block.split()[1] if len(device_block.split()) > 1 else 'Unknown'}")
                                return device_path
        except Exception as e:
            logger.warning(f"Error reading /proc/bus/input/devices: {e}")
        
        # Method 2: Check by-id symlinks
        by_id_path = '/dev/input/by-id'
        if os.path.exists(by_id_path):
            for device_link in os.listdir(by_id_path):
                for pattern in RFID_READER_PATTERNS:
                    if re.search(pattern, device_link, re.IGNORECASE):
                        device_path = os.path.join(by_id_path, device_link)
                        if os.path.exists(device_path):
                            real_path = os.path.realpath(device_path)
                            logger.info(f"Found RFID reader via by-id: {real_path}")
                            return real_path
        
        # Method 3: Fallback - try common event devices
        logger.warning("Auto-detection failed, checking common event devices...")
        for i in range(20):  # Check event0 through event19
            device_path = f'/dev/input/event{i}'
            if os.path.exists(device_path):
                logger.info(f"Available device: {device_path}")
        
        return None
    
    def test_device_input(self, device_path, timeout=5):
        """Test if a device produces readable input"""
        logger.info(f"Testing device input: {device_path}")
        try:
            with open(device_path, 'rb') as device:
                logger.info("Device opened successfully. Scan an RFID card within 5 seconds to test...")
                
                # Use select to wait for input with timeout
                ready, _, _ = select.select([device], [], [], timeout)
                
                if ready:
                    # Read some data to confirm it's working
                    data = device.read(24)  # Read one input event (24 bytes)
                    if data:
                        logger.info("✓ Device is producing input data")
                        return True
                else:
                    logger.info("✗ No input received within timeout")
                    return False
                    
        except PermissionError:
            logger.error(f"✗ Permission denied accessing {device_path}")
            logger.info("Try running: sudo usermod -a -G input $(whoami)")
            logger.info("Then log out and back in, or run: newgrp input")
            return False
        except Exception as e:
            logger.error(f"✗ Error testing device {device_path}: {e}")
            return False
    
    def read_rfid_from_stdin(self):
        """Fallback: Read RFID from stdin (original method)"""
        logger.info("Using stdin input method (terminal must have focus)")
        scan_buffer = ""
        
        try:
            while self.running:
                char = sys.stdin.read(1)
                if char:
                    if char in ['\n', '\r']:
                        if scan_buffer.strip():
                            self.process_scan(scan_buffer.strip())
                            scan_buffer = ""
                    else:
                        scan_buffer += char
                else:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error reading from stdin: {e}")
    
    def read_rfid_from_device(self, device_path):
        """Read RFID from specific input device"""
        logger.info(f"Reading RFID input from device: {device_path}")
        
        try:
            import struct
            
            # Input event format: time_sec(8) + time_usec(8) + type(2) + code(2) + value(4) = 24 bytes
            event_format = 'llHHI'
            event_size = struct.calcsize(event_format)
            
            scan_buffer = ""
            
            with open(device_path, 'rb') as device:
                while self.running:
                    try:
                        # Read one input event
                        event_data = device.read(event_size)
                        if len(event_data) == event_size:
                            sec, usec, event_type, code, value = struct.unpack(event_format, event_data)
                            
                            # We're interested in key press events (type=1, value=1)
                            if event_type == 1 and value == 1:  # EV_KEY, key press
                                # Convert key code to character (simplified mapping)
                                char = self.keycode_to_char(code)
                                if char:
                                    if char == '\n':
                                        if scan_buffer.strip():
                                            self.process_scan(scan_buffer.strip())
                                            scan_buffer = ""
                                    else:
                                        scan_buffer += char
                        else:
                            time.sleep(0.01)
                            
                    except Exception as e:
                        logger.error(f"Error reading event: {e}")
                        time.sleep(0.1)
                        
        except PermissionError:
            logger.error(f"Permission denied accessing {device_path}")
            logger.info("Run: sudo usermod -a -G input $(whoami) && newgrp input")
            return False
        except Exception as e:
            logger.error(f"Error reading from device {device_path}: {e}")
            return False
    
    def keycode_to_char(self, keycode):
        """Convert Linux input keycode to character (simplified mapping)"""
        # Basic keycode mapping for digits and enter
        keymap = {
            2: '1', 3: '2', 4: '3', 5: '4', 6: '5',
            7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
            16: 'q', 17: 'w', 18: 'e', 19: 'r', 20: 't',
            21: 'y', 22: 'u', 23: 'i', 24: 'o', 25: 'p',
            30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g',
            35: 'h', 36: 'j', 37: 'k', 38: 'l',
            44: 'z', 45: 'x', 46: 'c', 47: 'v', 48: 'b',
            49: 'n', 50: 'm',
            28: '\n',  # Enter key
        }
        return keymap.get(keycode, '')
    
    def process_scan(self, rfid_data):
        """Process a complete RFID scan"""
        rfid = rfid_data.strip()
        
        if not self.is_valid_rfid(rfid):
            logger.warning(f"Invalid RFID format: '{rfid}'")
            return
        
        # Prevent duplicate scans
        current_time = time.time()
        if current_time - self.last_scan_time < 1.0:
            logger.debug(f"Ignoring duplicate scan: {rfid}")
            return
        
        self.last_scan_time = current_time
        logger.info(f"Processing RFID scan: {rfid}")
        
        try:
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
                    logger.info(f"✓ RFID {rfid} → {result.get('music_dir')}")
                    if result.get('playback_triggered'):
                        logger.info("♪ Playback started")
                    else:
                        logger.warning("⚠ Playback failed")
                else:
                    logger.info(f"? RFID {rfid} not mapped - assign via web interface")
            else:
                logger.error(f"Flask error {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error processing scan: {e}")
    
    def is_valid_rfid(self, rfid):
        """Validate RFID format"""
        if not rfid or len(rfid) < MIN_RFID_LENGTH or len(rfid) > MAX_RFID_LENGTH:
            return False
        # Allow alphanumeric characters
        return rfid.replace(' ', '').isalnum()
    
    def start_listening(self):
        """Start RFID listener with auto-detection"""
        self.running = True
        logger.info("Enhanced RFID Listener starting...")
        
        # Try to find RFID device automatically
        self.device_path = self.find_rfid_device()
        
        if self.device_path:
            # Test the device first
            if self.test_device_input(self.device_path):
                logger.info(f"Using device input method: {self.device_path}")
                self.read_rfid_from_device(self.device_path)
            else:
                logger.warning("Device test failed, falling back to stdin")
                self.read_rfid_from_stdin()
        else:
            logger.info("No RFID device auto-detected, using stdin method")
            logger.info("Make sure this terminal has focus when scanning")
            self.read_rfid_from_stdin()
    
    def stop_listening(self):
        """Stop the RFID listener"""
        self.running = False
        logger.info("RFID listener stopped")

def check_flask_app():
    """Check if Flask app is running"""
    try:
        response = requests.get(f"http://{FLASK_HOST}:{FLASK_PORT}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    logger.info("Enhanced RFID Listener Service starting...")
    
    # Wait for Flask app
    logger.info("Waiting for Flask app...")
    while not check_flask_app():
        logger.info(f"Flask app not available at {FLASK_HOST}:{FLASK_PORT}, retrying...")
        time.sleep(5)
    
    logger.info("✓ Flask app is available")
    
    # Create and start listener
    listener = EnhancedRFIDListener(FLASK_HOST, FLASK_PORT)
    
    try:
        listener.start_listening()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()