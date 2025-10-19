"""
FSDP Protocol Layer
Handles communication between Admin UI and Target through blockchain
Implements session management, command routing, and data transfer
"""

import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
import threading

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class MessageType(Enum):
    """FSDP Message Types"""
    # Session management
    SESSION_OPEN = "session_open"
    SESSION_CLOSE = "session_close"
    SESSION_RECONNECT = "session_reconnect"
    SESSION_HEARTBEAT = "session_heartbeat"
    
    # Terminal operations
    TERMINAL_CREATE = "terminal_create"
    TERMINAL_COMMAND = "terminal_command"
    TERMINAL_OUTPUT = "terminal_output"
    TERMINAL_CLOSE = "terminal_close"
    
    # File transfer
    FILE_UPLOAD_START = "file_upload_start"
    FILE_UPLOAD_CHUNK = "file_upload_chunk"
    FILE_UPLOAD_COMPLETE = "file_upload_complete"
    FILE_DOWNLOAD_START = "file_download_start"
    FILE_DOWNLOAD_CHUNK = "file_download_chunk"
    FILE_DOWNLOAD_COMPLETE = "file_download_complete"
    FILE_VERIFY = "file_verify"
    
    # General
    RESPONSE = "response"
    ERROR = "error"


class FSDPSession:
    """Represents a persistent session between admin and target"""
    
    def __init__(self, session_id: str, admin_id: str, target_id: str):
        self.session_id = session_id
        self.admin_id = admin_id
        self.target_id = target_id
        self.created_at = time.time()
        self.last_heartbeat = time.time()
        self.is_active = True
        self.terminals: Dict[str, Dict] = {}  # terminal_id -> terminal_info
        self.logger = logging.getLogger(f"FSDPSession-{session_id[:8]}")
        
    def add_terminal(self, terminal_id: str, terminal_info: Dict):
        """Add a new isolated terminal to the session"""
        self.terminals[terminal_id] = terminal_info
        self.logger.debug(f"Terminal added: {terminal_id}")
        
    def remove_terminal(self, terminal_id: str):
        """Remove a terminal from the session"""
        if terminal_id in self.terminals:
            del self.terminals[terminal_id]
            self.logger.debug(f"Terminal removed: {terminal_id}")
            
    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = time.time()
        
    def is_alive(self, timeout: int = 60) -> bool:
        """Check if session is still alive based on heartbeat"""
        return (time.time() - self.last_heartbeat) < timeout
        
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'admin_id': self.admin_id,
            'target_id': self.target_id,
            'created_at': self.created_at,
            'last_heartbeat': self.last_heartbeat,
            'is_active': self.is_active,
            'terminals': list(self.terminals.keys())
        }


class FSDPProtocol:
    """
    FSDP Protocol Handler
    Manages sessions, routes messages through blockchain, handles callbacks
    """
    
    def __init__(self, blockchain, node_id: str, node_type: str):
        """
        Initialize FSDP Protocol
        
        Args:
            blockchain: FSDPBlockchain instance
            node_id: Unique identifier for this node
            node_type: 'admin' or 'target'
        """
        self.blockchain = blockchain
        self.node_id = node_id
        self.node_type = node_type
        self.sessions: Dict[str, FSDPSession] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.last_processed_block = 0
        self.running = False
        self.listener_thread = None
        self.logger = logging.getLogger(f"FSDPProtocol-{node_id}")
        
    def start(self):
        """Start the protocol listener"""
        if not self.running:
            self.running = True
            self.listener_thread = threading.Thread(target=self._listen_blockchain, daemon=True)
            self.listener_thread.start()
            self.logger.info(f"FSDP Protocol started for {self.node_type} node: {self.node_id}")
            
    def stop(self):
        """Stop the protocol listener"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=2)
        self.logger.info("FSDP Protocol stopped")
        
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a callback handler for a specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        self.logger.debug(f"Handler registered for {message_type.value}")
        
    def _listen_blockchain(self):
        """Listen for new transactions on the blockchain"""
        while self.running:
            try:
                # Get new transactions since last processed block
                transactions = self.blockchain.get_transactions_for_node(
                    self.node_id, 
                    self.last_processed_block
                )
                
                for tx in transactions:
                    self._process_transaction(tx)
                    # Update last processed block
                    if 'block_index' in tx:
                        self.last_processed_block = max(self.last_processed_block, tx['block_index'])
                
                time.sleep(0.1)  # Poll every 100ms for real-time performance
                
            except Exception as e:
                self.logger.error(f"Error in blockchain listener: {e}")
                time.sleep(1)
                
    def _process_transaction(self, transaction: Dict):
        """Process a received transaction"""
        try:
            msg_type_str = transaction.get('type')
            msg_type = MessageType(msg_type_str)
            
            self.logger.debug(f"Processing message: {msg_type.value} from {transaction.get('from')}")
            
            # Call registered handlers
            if msg_type in self.message_handlers:
                for handler in self.message_handlers[msg_type]:
                    handler(transaction)
                    
        except Exception as e:
            self.logger.error(f"Error processing transaction: {e}")
            
    def send_message(self, to_node: str, message_type: MessageType, data: Dict) -> bool:
        """
        Send a message through the blockchain
        
        Args:
            to_node: Destination node ID
            message_type: Type of message
            data: Message payload
            
        Returns:
            True if message was added to blockchain
        """
        try:
            transaction = {
                'type': message_type.value,
                'from': self.node_id,
                'to': to_node,
                'data': data,
                'message_id': str(uuid.uuid4())
            }
            
            result = self.blockchain.add_transaction(transaction)
            self.logger.debug(f"Message sent: {message_type.value} to {to_node}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
            
    def create_session(self, target_id: str) -> Optional[str]:
        """
        Create a new session (Admin side)
        
        Args:
            target_id: Target node ID to connect to
            
        Returns:
            Session ID if successful
        """
        if self.node_type != 'admin':
            self.logger.error("Only admin nodes can create sessions")
            return None
            
        session_id = str(uuid.uuid4())
        session = FSDPSession(session_id, self.node_id, target_id)
        self.sessions[session_id] = session
        
        # Send session open message
        self.send_message(
            target_id,
            MessageType.SESSION_OPEN,
            {
                'session_id': session_id,
                'admin_id': self.node_id
            }
        )
        
        self.logger.info(f"Session created: {session_id} with target {target_id}")
        return session_id
        
    def accept_session(self, session_data: Dict) -> bool:
        """
        Accept a session request (Target side)
        
        Args:
            session_data: Session information from admin
            
        Returns:
            True if session accepted
        """
        if self.node_type != 'target':
            self.logger.error("Only target nodes can accept sessions")
            return False
            
        session_id = session_data['session_id']
        admin_id = session_data['admin_id']
        
        session = FSDPSession(session_id, admin_id, self.node_id)
        self.sessions[session_id] = session
        
        # Send response
        self.send_message(
            admin_id,
            MessageType.RESPONSE,
            {
                'session_id': session_id,
                'status': 'accepted',
                'target_id': self.node_id
            }
        )
        
        self.logger.info(f"Session accepted: {session_id} from admin {admin_id}")
        return True
        
    def close_session(self, session_id: str):
        """Close a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            
            # Notify the other party
            other_node = session.target_id if self.node_type == 'admin' else session.admin_id
            self.send_message(
                other_node,
                MessageType.SESSION_CLOSE,
                {'session_id': session_id}
            )
            
            del self.sessions[session_id]
            self.logger.info(f"Session closed: {session_id}")
            
    def create_terminal(self, session_id: str) -> Optional[str]:
        """
        Create a new isolated terminal in a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Terminal ID if successful
        """
        if session_id not in self.sessions:
            self.logger.error(f"Session not found: {session_id}")
            return None
            
        terminal_id = str(uuid.uuid4())
        session = self.sessions[session_id]
        
        terminal_info = {
            'terminal_id': terminal_id,
            'created_at': time.time(),
            'is_active': True
        }
        
        session.add_terminal(terminal_id, terminal_info)
        
        # Notify target to create terminal
        if self.node_type == 'admin':
            self.send_message(
                session.target_id,
                MessageType.TERMINAL_CREATE,
                {
                    'session_id': session_id,
                    'terminal_id': terminal_id
                }
            )
        
        self.logger.info(f"Terminal created: {terminal_id} in session {session_id}")
        return terminal_id
        
    def send_terminal_command(self, session_id: str, terminal_id: str, command: str):
        """
        Send a command to a terminal
        
        Args:
            session_id: Session ID
            terminal_id: Terminal ID
            command: Command to execute
        """
        if session_id not in self.sessions:
            self.logger.error(f"Session not found: {session_id}")
            return
            
        session = self.sessions[session_id]
        
        self.send_message(
            session.target_id,
            MessageType.TERMINAL_COMMAND,
            {
                'session_id': session_id,
                'terminal_id': terminal_id,
                'command': command
            }
        )
        
        self.logger.debug(f"Command sent to terminal {terminal_id}: {command[:50]}")
        
    def send_heartbeat(self, session_id: str):
        """Send heartbeat to keep session alive"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_heartbeat()
            
            other_node = session.target_id if self.node_type == 'admin' else session.admin_id
            self.send_message(
                other_node,
                MessageType.SESSION_HEARTBEAT,
                {'session_id': session_id}
            )
            
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        return [session.to_dict() for session in self.sessions.values() if session.is_active]

