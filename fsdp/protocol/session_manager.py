"""
FSDP Session Manager
Handles session persistence, reconnection, and state management
Supports multiple isolated terminals per session
"""

import json
import os
import time
import logging
from typing import Dict, Optional, List
import pickle
import threading

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class SessionState:
    """Persistent session state"""
    
    def __init__(self, session_id: str, admin_id: str, target_id: str):
        self.session_id = session_id
        self.admin_id = admin_id
        self.target_id = target_id
        self.created_at = time.time()
        self.last_active = time.time()
        self.reconnect_count = 0
        self.is_connected = True
        self.terminals: Dict[str, 'TerminalState'] = {}
        
    def to_dict(self) -> Dict:
        return {
            'session_id': self.session_id,
            'admin_id': self.admin_id,
            'target_id': self.target_id,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'reconnect_count': self.reconnect_count,
            'is_connected': self.is_connected,
            'terminals': {tid: t.to_dict() for tid, t in self.terminals.items()}
        }


class TerminalState:
    """State of an isolated terminal"""
    
    def __init__(self, terminal_id: str, session_id: str):
        self.terminal_id = terminal_id
        self.session_id = session_id
        self.created_at = time.time()
        self.is_active = True
        self.command_history: List[str] = []
        self.output_buffer: List[str] = []
        self.current_directory = os.path.expanduser("~")
        self.environment_vars: Dict[str, str] = {}
        self.process_id: Optional[int] = None
        
    def add_command(self, command: str):
        """Add command to history"""
        self.command_history.append(command)
        
    def add_output(self, output: str):
        """Add output to buffer"""
        self.output_buffer.append(output)
        # Keep only last 1000 lines
        if len(self.output_buffer) > 1000:
            self.output_buffer = self.output_buffer[-1000:]
            
    def to_dict(self) -> Dict:
        return {
            'terminal_id': self.terminal_id,
            'session_id': self.session_id,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'command_count': len(self.command_history),
            'current_directory': self.current_directory,
            'process_id': self.process_id
        }


class SessionManager:
    """
    Manages persistent sessions with reconnection support
    Handles multiple isolated terminals per session
    """
    
    def __init__(self, storage_dir: str = "./fsdp_sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, SessionState] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger("SessionManager")
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
        
        # Start background persistence thread
        self.running = True
        self.persist_thread = threading.Thread(target=self._auto_persist, daemon=True)
        self.persist_thread.start()
        
        self.logger.info(f"Session Manager initialized with storage: {storage_dir}")
        
    def _load_sessions(self):
        """Load persisted sessions from disk"""
        try:
            session_files = [f for f in os.listdir(self.storage_dir) if f.endswith('.session')]
            for session_file in session_files:
                file_path = os.path.join(self.storage_dir, session_file)
                try:
                    with open(file_path, 'rb') as f:
                        session_state = pickle.load(f)
                        self.sessions[session_state.session_id] = session_state
                        self.logger.info(f"Loaded session: {session_state.session_id}")
                except Exception as e:
                    self.logger.error(f"Failed to load session {session_file}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load sessions: {e}")
            
    def _save_session(self, session_id: str):
        """Save a session to disk"""
        if session_id not in self.sessions:
            return
            
        try:
            session_state = self.sessions[session_id]
            file_path = os.path.join(self.storage_dir, f"{session_id}.session")
            with open(file_path, 'wb') as f:
                pickle.dump(session_state, f)
            self.logger.debug(f"Session saved: {session_id}")
        except Exception as e:
            self.logger.error(f"Failed to save session {session_id}: {e}")
            
    def _auto_persist(self):
        """Automatically persist sessions every 10 seconds"""
        while self.running:
            try:
                with self.lock:
                    for session_id in list(self.sessions.keys()):
                        self._save_session(session_id)
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"Error in auto-persist: {e}")
                
    def create_session(self, session_id: str, admin_id: str, target_id: str) -> SessionState:
        """Create a new session"""
        with self.lock:
            session_state = SessionState(session_id, admin_id, target_id)
            self.sessions[session_id] = session_state
            self._save_session(session_id)
            self.logger.info(f"Session created: {session_id}")
            return session_state
            
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
        
    def update_session_activity(self, session_id: str):
        """Update last activity timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id].last_active = time.time()
            
    def reconnect_session(self, session_id: str) -> bool:
        """
        Reconnect to an existing session
        Returns True if session exists and can be reconnected
        """
        with self.lock:
            if session_id not in self.sessions:
                self.logger.warning(f"Session not found for reconnection: {session_id}")
                return False
                
            session = self.sessions[session_id]
            session.is_connected = True
            session.reconnect_count += 1
            session.last_active = time.time()
            self._save_session(session_id)
            
            self.logger.info(f"Session reconnected: {session_id} (reconnect count: {session.reconnect_count})")
            return True
            
    def disconnect_session(self, session_id: str):
        """Mark session as disconnected (but keep it for reconnection)"""
        if session_id in self.sessions:
            self.sessions[session_id].is_connected = False
            self._save_session(session_id)
            self.logger.info(f"Session disconnected: {session_id}")
            
    def delete_session(self, session_id: str):
        """Permanently delete a session"""
        with self.lock:
            if session_id in self.sessions:
                # Close all terminals
                session = self.sessions[session_id]
                for terminal_id in list(session.terminals.keys()):
                    self.close_terminal(session_id, terminal_id)
                    
                # Delete from memory and disk
                del self.sessions[session_id]
                file_path = os.path.join(self.storage_dir, f"{session_id}.session")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                self.logger.info(f"Session deleted: {session_id}")
                
    def create_terminal(self, session_id: str, terminal_id: str) -> Optional[TerminalState]:
        """Create a new isolated terminal in a session"""
        with self.lock:
            if session_id not in self.sessions:
                self.logger.error(f"Session not found: {session_id}")
                return None
                
            terminal_state = TerminalState(terminal_id, session_id)
            self.sessions[session_id].terminals[terminal_id] = terminal_state
            self._save_session(session_id)
            
            self.logger.info(f"Terminal created: {terminal_id} in session {session_id}")
            return terminal_state
            
    def get_terminal(self, session_id: str, terminal_id: str) -> Optional[TerminalState]:
        """Get a terminal by ID"""
        session = self.sessions.get(session_id)
        if session:
            return session.terminals.get(terminal_id)
        return None
        
    def close_terminal(self, session_id: str, terminal_id: str):
        """Close a terminal"""
        with self.lock:
            session = self.sessions.get(session_id)
            if session and terminal_id in session.terminals:
                session.terminals[terminal_id].is_active = False
                del session.terminals[terminal_id]
                self._save_session(session_id)
                self.logger.info(f"Terminal closed: {terminal_id}")
                
    def get_session_terminals(self, session_id: str) -> List[TerminalState]:
        """Get all terminals in a session"""
        session = self.sessions.get(session_id)
        if session:
            return list(session.terminals.values())
        return []
        
    def get_active_sessions(self) -> List[SessionState]:
        """Get all active (connected) sessions"""
        return [s for s in self.sessions.values() if s.is_connected]
        
    def get_all_sessions(self) -> List[SessionState]:
        """Get all sessions (including disconnected)"""
        return list(self.sessions.values())
        
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than max_age_hours"""
        with self.lock:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            sessions_to_delete = []
            for session_id, session in self.sessions.items():
                if not session.is_connected and (current_time - session.last_active) > max_age_seconds:
                    sessions_to_delete.append(session_id)
                    
            for session_id in sessions_to_delete:
                self.delete_session(session_id)
                self.logger.info(f"Cleaned up old session: {session_id}")
                
    def shutdown(self):
        """Shutdown session manager"""
        self.running = False
        if self.persist_thread:
            self.persist_thread.join(timeout=2)
            
        # Final save of all sessions
        with self.lock:
            for session_id in self.sessions.keys():
                self._save_session(session_id)
                
        self.logger.info("Session Manager shutdown complete")

