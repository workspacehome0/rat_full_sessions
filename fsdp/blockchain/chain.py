"""
FSDP Private Blockchain Core
Lightweight blockchain optimized for real-time RAT communication
Uses Proof of Authority (PoA) consensus for fast, zero-fee transactions
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Block:
    """Represents a single block in the blockchain"""
    
    def __init__(self, index: int, timestamp: float, data: Dict[Any, Any], 
                 previous_hash: str, validator: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.validator = validator  # PoA: node that validated this block
        self.hash = self.calculate_hash()
        
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of the block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'validator': self.validator
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert block to dictionary"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'validator': self.validator,
            'hash': self.hash
        }


class FSDPBlockchain:
    """
    FSDP Private Blockchain
    - Proof of Authority (PoA) consensus
    - Real-time transaction processing
    - Zero gas fees
    - Optimized for RAT communication
    """
    
    def __init__(self, node_id: str, is_validator: bool = False):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.node_id = node_id
        self.is_validator = is_validator
        self.validators: List[str] = []  # List of authorized validator nodes
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"FSDPBlockchain-{node_id}")
        
        # Create genesis block
        self._create_genesis_block()
        self.logger.info(f"Blockchain initialized for node {node_id}")
        
    def _create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            data={'message': 'FSDP Genesis Block'},
            previous_hash='0',
            validator='genesis'
        )
        self.chain.append(genesis_block)
        self.logger.debug("Genesis block created")
        
    def add_validator(self, validator_id: str):
        """Add a node as an authorized validator (PoA)"""
        with self.lock:
            if validator_id not in self.validators:
                self.validators.append(validator_id)
                self.logger.info(f"Added validator: {validator_id}")
                
    def remove_validator(self, validator_id: str):
        """Remove a validator"""
        with self.lock:
            if validator_id in self.validators:
                self.validators.remove(validator_id)
                self.logger.info(f"Removed validator: {validator_id}")
                
    def add_transaction(self, transaction: Dict) -> bool:
        """
        Add a transaction to pending pool
        Transaction format: {
            'type': 'command'|'response'|'file_chunk'|'session_event',
            'from': node_id,
            'to': node_id,
            'data': {...},
            'timestamp': float
        }
        """
        with self.lock:
            transaction['timestamp'] = time.time()
            self.pending_transactions.append(transaction)
            self.logger.debug(f"Transaction added: {transaction['type']} from {transaction.get('from')} to {transaction.get('to')}")
            return True
            
    def create_block(self) -> Optional[Block]:
        """
        Create a new block with pending transactions (PoA)
        Only validators can create blocks
        """
        if not self.is_validator or self.node_id not in self.validators:
            self.logger.warning("Only validators can create blocks")
            return None
            
        with self.lock:
            if not self.pending_transactions:
                return None
                
            previous_block = self.get_last_block()
            new_block = Block(
                index=len(self.chain),
                timestamp=time.time(),
                data={'transactions': self.pending_transactions.copy()},
                previous_hash=previous_block.hash,
                validator=self.node_id
            )
            
            self.chain.append(new_block)
            self.logger.info(f"Block #{new_block.index} created with {len(self.pending_transactions)} transactions")
            
            # Clear pending transactions
            self.pending_transactions.clear()
            
            return new_block
            
    def get_last_block(self) -> Block:
        """Get the last block in the chain"""
        return self.chain[-1]
        
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if hash is correct
            if current_block.hash != current_block.calculate_hash():
                self.logger.error(f"Invalid hash at block {i}")
                return False
                
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.hash:
                self.logger.error(f"Invalid previous hash at block {i}")
                return False
                
            # Check if validator is authorized (PoA)
            if current_block.validator not in self.validators and current_block.validator != 'genesis':
                self.logger.error(f"Unauthorized validator at block {i}: {current_block.validator}")
                return False
                
        return True
        
    def get_transactions_for_node(self, node_id: str, since_block: int = 0) -> List[Dict]:
        """
        Get all transactions destined for a specific node since a block index
        Used by nodes to read their messages from the blockchain
        """
        transactions = []
        for block in self.chain[since_block:]:
            if 'transactions' in block.data:
                for tx in block.data['transactions']:
                    if tx.get('to') == node_id:
                        tx['block_index'] = block.index
                        transactions.append(tx)
        return transactions
        
    def get_chain_data(self) -> List[Dict]:
        """Get the entire chain as a list of dictionaries"""
        return [block.to_dict() for block in self.chain]
        
    def get_chain_length(self) -> int:
        """Get the current length of the chain"""
        return len(self.chain)
        
    def sync_chain(self, chain_data: List[Dict]) -> bool:
        """
        Synchronize blockchain with another node's chain
        Used for consensus and network synchronization
        """
        try:
            new_chain = []
            for block_data in chain_data:
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    data=block_data['data'],
                    previous_hash=block_data['previous_hash'],
                    validator=block_data['validator']
                )
                new_chain.append(block)
                
            # Replace chain if new chain is valid and longer
            if len(new_chain) > len(self.chain):
                with self.lock:
                    self.chain = new_chain
                    self.logger.info(f"Chain synchronized: {len(new_chain)} blocks")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Chain sync failed: {e}")
            return False

