"""
FSDP File Transfer System
Implements chunked file transfer with verification
- 4MB chunk size
- SHA-256 hash verification for each chunk
- Resume capability for interrupted transfers
- Progress tracking
"""

import os
import hashlib
import time
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import base64

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 4MB chunk size
CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB


class TransferStatus(Enum):
    """File transfer status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFYING = "verifying"


@dataclass
class ChunkInfo:
    """Information about a file chunk"""
    chunk_index: int
    chunk_hash: str
    chunk_size: int
    is_verified: bool = False


@dataclass
class FileTransferInfo:
    """Information about a file transfer"""
    transfer_id: str
    file_name: str
    file_path: str
    file_size: int
    total_chunks: int
    chunks: Dict[int, ChunkInfo]
    status: TransferStatus
    created_at: float
    completed_at: Optional[float] = None
    file_hash: Optional[str] = None
    direction: str = "upload"  # "upload" or "download"
    session_id: Optional[str] = None
    
    def get_progress(self) -> float:
        """Get transfer progress percentage"""
        if self.total_chunks == 0:
            return 0.0
        verified_chunks = sum(1 for c in self.chunks.values() if c.is_verified)
        return (verified_chunks / self.total_chunks) * 100
        
    def is_complete(self) -> bool:
        """Check if all chunks are verified"""
        return all(c.is_verified for c in self.chunks.values())


class FileTransferManager:
    """
    Manages file transfers with chunking and verification
    """
    
    def __init__(self, protocol):
        """
        Initialize File Transfer Manager
        
        Args:
            protocol: FSDPProtocol instance for sending messages
        """
        self.protocol = protocol
        self.transfers: Dict[str, FileTransferInfo] = {}
        self.logger = logging.getLogger("FileTransferManager")
        self.progress_callbacks: Dict[str, Callable] = {}
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of entire file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {e}")
            return ""
            
    def calculate_chunk_hash(self, chunk_data: bytes) -> str:
        """Calculate SHA-256 hash of a chunk"""
        return hashlib.sha256(chunk_data).hexdigest()
        
    def prepare_upload(self, file_path: str, transfer_id: str, session_id: str) -> Optional[FileTransferInfo]:
        """
        Prepare a file for upload
        
        Args:
            file_path: Path to file to upload
            transfer_id: Unique transfer ID
            session_id: Session ID
            
        Returns:
            FileTransferInfo if successful
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return None
                
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE  # Ceiling division
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            
            # Create chunk info
            chunks = {}
            with open(file_path, 'rb') as f:
                for i in range(total_chunks):
                    chunk_data = f.read(CHUNK_SIZE)
                    chunk_hash = self.calculate_chunk_hash(chunk_data)
                    chunks[i] = ChunkInfo(
                        chunk_index=i,
                        chunk_hash=chunk_hash,
                        chunk_size=len(chunk_data),
                        is_verified=False
                    )
                    
            transfer_info = FileTransferInfo(
                transfer_id=transfer_id,
                file_name=file_name,
                file_path=file_path,
                file_size=file_size,
                total_chunks=total_chunks,
                chunks=chunks,
                status=TransferStatus.PENDING,
                created_at=time.time(),
                file_hash=file_hash,
                direction="upload",
                session_id=session_id
            )
            
            self.transfers[transfer_id] = transfer_info
            self.logger.info(f"Upload prepared: {file_name} ({file_size} bytes, {total_chunks} chunks)")
            
            return transfer_info
            
        except Exception as e:
            self.logger.error(f"Error preparing upload: {e}")
            return None
            
    def start_upload(self, transfer_id: str, target_node: str) -> bool:
        """
        Start uploading a file
        
        Args:
            transfer_id: Transfer ID
            target_node: Target node ID
            
        Returns:
            True if upload started successfully
        """
        if transfer_id not in self.transfers:
            self.logger.error(f"Transfer not found: {transfer_id}")
            return False
            
        transfer_info = self.transfers[transfer_id]
        transfer_info.status = TransferStatus.IN_PROGRESS
        
        # Send file upload start message
        from .fsdp_protocol import MessageType
        self.protocol.send_message(
            target_node,
            MessageType.FILE_UPLOAD_START,
            {
                'transfer_id': transfer_id,
                'file_name': transfer_info.file_name,
                'file_size': transfer_info.file_size,
                'total_chunks': transfer_info.total_chunks,
                'file_hash': transfer_info.file_hash,
                'session_id': transfer_info.session_id
            }
        )
        
        self.logger.info(f"Upload started: {transfer_id}")
        return True
        
    def send_chunk(self, transfer_id: str, chunk_index: int, target_node: str) -> bool:
        """
        Send a specific chunk
        
        Args:
            transfer_id: Transfer ID
            chunk_index: Index of chunk to send
            target_node: Target node ID
            
        Returns:
            True if chunk sent successfully
        """
        if transfer_id not in self.transfers:
            self.logger.error(f"Transfer not found: {transfer_id}")
            return False
            
        transfer_info = self.transfers[transfer_id]
        
        if chunk_index not in transfer_info.chunks:
            self.logger.error(f"Invalid chunk index: {chunk_index}")
            return False
            
        try:
            # Read chunk from file
            with open(transfer_info.file_path, 'rb') as f:
                f.seek(chunk_index * CHUNK_SIZE)
                chunk_data = f.read(CHUNK_SIZE)
                
            chunk_info = transfer_info.chunks[chunk_index]
            
            # Encode chunk data to base64 for JSON transmission
            chunk_data_b64 = base64.b64encode(chunk_data).decode('utf-8')
            
            # Send chunk
            from .fsdp_protocol import MessageType
            self.protocol.send_message(
                target_node,
                MessageType.FILE_UPLOAD_CHUNK,
                {
                    'transfer_id': transfer_id,
                    'chunk_index': chunk_index,
                    'chunk_data': chunk_data_b64,
                    'chunk_hash': chunk_info.chunk_hash,
                    'chunk_size': chunk_info.chunk_size
                }
            )
            
            self.logger.debug(f"Chunk sent: {transfer_id} chunk {chunk_index}/{transfer_info.total_chunks}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending chunk: {e}")
            return False
            
    def verify_chunk(self, transfer_id: str, chunk_index: int, chunk_hash: str) -> bool:
        """
        Verify a received chunk
        
        Args:
            transfer_id: Transfer ID
            chunk_index: Chunk index
            chunk_hash: Expected chunk hash
            
        Returns:
            True if chunk is verified
        """
        if transfer_id not in self.transfers:
            return False
            
        transfer_info = self.transfers[transfer_id]
        
        if chunk_index in transfer_info.chunks:
            chunk_info = transfer_info.chunks[chunk_index]
            if chunk_info.chunk_hash == chunk_hash:
                chunk_info.is_verified = True
                self.logger.debug(f"Chunk verified: {transfer_id} chunk {chunk_index}")
                
                # Call progress callback
                if transfer_id in self.progress_callbacks:
                    self.progress_callbacks[transfer_id](transfer_info.get_progress())
                    
                # Check if transfer is complete
                if transfer_info.is_complete():
                    self._complete_transfer(transfer_id)
                    
                return True
            else:
                self.logger.warning(f"Chunk hash mismatch: {transfer_id} chunk {chunk_index}")
                return False
        return False
        
    def receive_chunk(self, transfer_id: str, chunk_index: int, chunk_data_b64: str, 
                     chunk_hash: str, output_path: str) -> bool:
        """
        Receive and save a chunk
        
        Args:
            transfer_id: Transfer ID
            chunk_index: Chunk index
            chunk_data_b64: Base64 encoded chunk data
            chunk_hash: Expected chunk hash
            output_path: Path to save the file
            
        Returns:
            True if chunk received and verified successfully
        """
        try:
            # Decode chunk data
            chunk_data = base64.b64decode(chunk_data_b64)
            
            # Verify chunk hash
            calculated_hash = self.calculate_chunk_hash(chunk_data)
            if calculated_hash != chunk_hash:
                self.logger.error(f"Chunk hash verification failed: {transfer_id} chunk {chunk_index}")
                return False
                
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write chunk to file
            mode = 'ab' if chunk_index > 0 else 'wb'
            with open(output_path, mode) as f:
                f.seek(chunk_index * CHUNK_SIZE)
                f.write(chunk_data)
                
            # Mark chunk as verified
            if transfer_id in self.transfers:
                self.verify_chunk(transfer_id, chunk_index, chunk_hash)
                
            self.logger.debug(f"Chunk received and saved: {transfer_id} chunk {chunk_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error receiving chunk: {e}")
            return False
            
    def _complete_transfer(self, transfer_id: str):
        """Mark transfer as completed"""
        if transfer_id not in self.transfers:
            return
            
        transfer_info = self.transfers[transfer_id]
        transfer_info.status = TransferStatus.COMPLETED
        transfer_info.completed_at = time.time()
        
        duration = transfer_info.completed_at - transfer_info.created_at
        speed_mbps = (transfer_info.file_size / (1024 * 1024)) / duration if duration > 0 else 0
        
        self.logger.info(
            f"Transfer completed: {transfer_id} - {transfer_info.file_name} "
            f"({transfer_info.file_size} bytes in {duration:.2f}s, {speed_mbps:.2f} MB/s)"
        )
        
        # Send completion message
        if transfer_info.session_id:
            session = self.protocol.sessions.get(transfer_info.session_id)
            if session:
                target_node = session.target_id if self.protocol.node_type == 'admin' else session.admin_id
                from .fsdp_protocol import MessageType
                self.protocol.send_message(
                    target_node,
                    MessageType.FILE_UPLOAD_COMPLETE if transfer_info.direction == 'upload' else MessageType.FILE_DOWNLOAD_COMPLETE,
                    {
                        'transfer_id': transfer_id,
                        'file_name': transfer_info.file_name,
                        'file_hash': transfer_info.file_hash,
                        'status': 'success'
                    }
                )
                
    def verify_file(self, transfer_id: str, file_path: str) -> bool:
        """
        Verify complete file integrity
        
        Args:
            transfer_id: Transfer ID
            file_path: Path to file to verify
            
        Returns:
            True if file hash matches expected hash
        """
        if transfer_id not in self.transfers:
            self.logger.error(f"Transfer not found: {transfer_id}")
            return False
            
        transfer_info = self.transfers[transfer_id]
        
        if not transfer_info.file_hash:
            self.logger.warning("No file hash available for verification")
            return False
            
        transfer_info.status = TransferStatus.VERIFYING
        
        # Calculate file hash
        calculated_hash = self.calculate_file_hash(file_path)
        
        if calculated_hash == transfer_info.file_hash:
            self.logger.info(f"File verification successful: {transfer_id}")
            return True
        else:
            self.logger.error(f"File verification failed: {transfer_id}")
            transfer_info.status = TransferStatus.FAILED
            return False
            
    def get_transfer_info(self, transfer_id: str) -> Optional[FileTransferInfo]:
        """Get transfer information"""
        return self.transfers.get(transfer_id)
        
    def register_progress_callback(self, transfer_id: str, callback: Callable):
        """Register a callback for transfer progress updates"""
        self.progress_callbacks[transfer_id] = callback
        
    def cancel_transfer(self, transfer_id: str):
        """Cancel a transfer"""
        if transfer_id in self.transfers:
            self.transfers[transfer_id].status = TransferStatus.FAILED
            self.logger.info(f"Transfer cancelled: {transfer_id}")
            
    def cleanup_transfer(self, transfer_id: str):
        """Remove transfer from memory"""
        if transfer_id in self.transfers:
            del self.transfers[transfer_id]
            if transfer_id in self.progress_callbacks:
                del self.progress_callbacks[transfer_id]

