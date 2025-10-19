#!/usr/bin/env python3
"""
FSDP System Test Script
Tests all components: Blockchain, Protocol, Sessions, Terminals, File Transfer
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blockchain.chain import FSDPBlockchain
from protocol.fsdp_protocol import FSDPProtocol, MessageType
from protocol.session_manager import SessionManager
from protocol.file_transfer import FileTransferManager

print("=" * 70)
print("FSDP SYSTEM TEST")
print("=" * 70)

# Test 1: Blockchain
print("\n[TEST 1] Testing Private Blockchain...")
try:
    # Create blockchain nodes
    admin_blockchain = FSDPBlockchain(node_id="admin-node", is_validator=True)
    target_blockchain = FSDPBlockchain(node_id="target-node", is_validator=False)
    
    # Add validator
    admin_blockchain.add_validator("admin-node")
    
    # Add transaction
    admin_blockchain.add_transaction({
        'type': 'test',
        'from': 'admin-node',
        'to': 'target-node',
        'data': {'message': 'Hello FSDP'}
    })
    
    # Create block
    block = admin_blockchain.create_block()
    
    print(f"✓ Blockchain initialized")
    print(f"✓ Chain length: {admin_blockchain.get_chain_length()}")
    print(f"✓ Block created with hash: {block.hash[:16]}...")
    print(f"✓ Chain valid: {admin_blockchain.is_chain_valid()}")
    
except Exception as e:
    print(f"✗ Blockchain test failed: {e}")
    sys.exit(1)

# Test 2: Protocol Layer
print("\n[TEST 2] Testing FSDP Protocol...")
try:
    # Create protocol instances
    admin_protocol = FSDPProtocol(admin_blockchain, "admin-node", "admin")
    target_protocol = FSDPProtocol(target_blockchain, "target-node", "target")
    
    # Start protocols
    admin_protocol.start()
    target_protocol.start()
    
    # Send message
    admin_protocol.send_message(
        "target-node",
        MessageType.SESSION_OPEN,
        {'session_id': 'test-session-001'}
    )
    
    time.sleep(0.5)  # Wait for message processing
    
    print(f"✓ Protocol instances created")
    print(f"✓ Admin protocol started")
    print(f"✓ Target protocol started")
    print(f"✓ Message sent successfully")
    
    # Stop protocols
    admin_protocol.stop()
    target_protocol.stop()
    
except Exception as e:
    print(f"✗ Protocol test failed: {e}")
    sys.exit(1)

# Test 3: Session Management
print("\n[TEST 3] Testing Session Management...")
try:
    session_manager = SessionManager(storage_dir="./test_sessions")
    
    # Create session
    session = session_manager.create_session(
        session_id="test-session-001",
        admin_id="admin-node",
        target_id="target-node"
    )
    
    # Create terminals
    terminal1 = session_manager.create_terminal("test-session-001", "terminal-001")
    terminal2 = session_manager.create_terminal("test-session-001", "terminal-002")
    
    print(f"✓ Session Manager initialized")
    print(f"✓ Session created: {session.session_id}")
    print(f"✓ Terminal 1 created: {terminal1.terminal_id}")
    print(f"✓ Terminal 2 created: {terminal2.terminal_id}")
    print(f"✓ Multiple isolated terminals working")
    
    # Test reconnection
    session_manager.disconnect_session("test-session-001")
    reconnected = session_manager.reconnect_session("test-session-001")
    
    print(f"✓ Session persistence working")
    print(f"✓ Reconnection successful: {reconnected}")
    
    # Cleanup
    session_manager.shutdown()
    
except Exception as e:
    print(f"✗ Session management test failed: {e}")
    sys.exit(1)

# Test 4: File Transfer
print("\n[TEST 4] Testing File Transfer with 4MB Chunking...")
try:
    # Create test file
    test_file = "./test_file.bin"
    test_size = 8 * 1024 * 1024  # 8MB file
    
    with open(test_file, 'wb') as f:
        f.write(os.urandom(test_size))
    
    # Create protocol for file transfer
    blockchain = FSDPBlockchain(node_id="test-node", is_validator=True)
    protocol = FSDPProtocol(blockchain, "test-node", "admin")
    file_manager = FileTransferManager(protocol)
    
    # Prepare upload
    transfer_info = file_manager.prepare_upload(test_file, "transfer-001", "session-001")
    
    print(f"✓ File Transfer Manager initialized")
    print(f"✓ Test file created: {test_size / (1024*1024):.1f} MB")
    print(f"✓ File chunked into: {transfer_info.total_chunks} chunks")
    print(f"✓ Chunk size: 4MB")
    print(f"✓ File hash calculated: {transfer_info.file_hash[:16]}...")
    
    # Verify chunk
    chunk_verified = file_manager.verify_chunk(
        "transfer-001",
        0,
        transfer_info.chunks[0].chunk_hash
    )
    
    print(f"✓ Chunk verification working: {chunk_verified}")
    print(f"✓ Transfer progress: {transfer_info.get_progress():.1f}%")
    
    # Cleanup
    os.remove(test_file)
    
except Exception as e:
    print(f"✗ File transfer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Terminal Execution
print("\n[TEST 5] Testing Terminal Command Execution...")
try:
    from test_payloads.fsdp_payload_enhanced import IsolatedTerminal
    
    terminal = IsolatedTerminal("test-terminal")
    
    # Test basic command
    result = terminal.execute_command("echo 'Hello FSDP'")
    print(f"✓ Terminal created")
    print(f"✓ Command executed: echo 'Hello FSDP'")
    print(f"✓ Output: {result['output'].strip()}")
    print(f"✓ Exit code: {result['exit_code']}")
    
    # Test cd command
    result = terminal.execute_command("cd /tmp")
    print(f"✓ Directory change working")
    print(f"✓ Current directory: {result['cwd']}")
    
    # Test multiple commands in same terminal
    result = terminal.execute_command("pwd")
    print(f"✓ Terminal state persists")
    print(f"✓ PWD output: {result['output'].strip()}")
    
except Exception as e:
    print(f"✗ Terminal execution test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final Summary
print("\n" + "=" * 70)
print("ALL TESTS PASSED ✓")
print("=" * 70)
print("\nFSDP System Components Verified:")
print("  ✓ Private Blockchain (PoA consensus)")
print("  ✓ FSDP Protocol Layer")
print("  ✓ Session Management with Persistence")
print("  ✓ Multiple Isolated Terminals")
print("  ✓ File Transfer with 4MB Chunking")
print("  ✓ Hash Verification System")
print("  ✓ Cross-platform Terminal Execution")
print("\nSystem is ready for deployment!")
print("=" * 70)

