#!/usr/bin/env python3
"""
FSDP Admin GUI v2 - Connects to external validator
Simple graphical interface that shares blockchain with validator
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import time
from datetime import datetime
import json

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsdp.blockchain.chain import FSDPBlockchain
from fsdp.protocol.fsdp_protocol import FSDPProtocol, MessageType
from fsdp.protocol.session_manager import SessionManager

class FSDPAdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FSDP Admin Control Panel v2")
        self.root.geometry("1200x800")
        
        # Ask for validator connection
        self.validator_address = simpledialog.askstring(
            "Validator Connection",
            "Enter validator address (e.g., localhost:5000):",
            initialvalue="localhost:5000"
        )
        
        if not self.validator_address:
            messagebox.showerror("Error", "Validator address is required!")
            sys.exit(1)
        
        # Initialize FSDP components - SHARED blockchain
        self.node_id = "admin-gui-v2"
        
        # Create blockchain that will sync with validator
        self.blockchain = FSDPBlockchain(node_id=self.node_id, is_validator=False)
        self.protocol = FSDPProtocol(self.blockchain, self.node_id, "admin")
        self.session_manager = SessionManager(storage_dir="./admin_sessions_v2")
        
        self.current_session = None
        self.current_terminal = None
        self.targets = {}
        self.running = False
        
        self.setup_ui()
        self.start_protocol()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Top info bar
        info_bar = tk.Frame(self.root, bg='#2c3e50', height=40)
        info_bar.pack(fill='x', side='top')
        
        tk.Label(info_bar, text=f"🔗 Validator: {self.validator_address}", 
                bg='#2c3e50', fg='white', font=('Arial', 10)).pack(side='left', padx=10, pady=5)
        
        tk.Label(info_bar, text=f"📡 Node: {self.node_id}", 
                bg='#2c3e50', fg='white', font=('Arial', 10)).pack(side='left', padx=10, pady=5)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Dashboard
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text='📊 Dashboard')
        self.setup_dashboard()
        
        # Tab 2: Targets
        self.targets_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.targets_frame, text='🎯 Targets')
        self.setup_targets()
        
        # Tab 3: Terminal
        self.terminal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text='💻 Terminal')
        self.setup_terminal()
        
        # Tab 4: Sessions
        self.sessions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sessions_frame, text='📁 Sessions')
        self.setup_sessions()
        
        # Tab 5: Blockchain
        self.blockchain_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.blockchain_frame, text='⛓️ Blockchain')
        self.setup_blockchain()
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg='#ecf0f1')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_dashboard(self):
        """Setup dashboard tab"""
        
        # Title
        title = tk.Label(self.dashboard_frame, text="FSDP Admin Control Panel", 
                        font=('Arial', 20, 'bold'), fg='#2c3e50')
        title.pack(pady=20)
        
        subtitle = tk.Label(self.dashboard_frame, text="Connected to Validator Blockchain", 
                           font=('Arial', 12), fg='#27ae60')
        subtitle.pack()
        
        # Stats frame
        stats_frame = tk.Frame(self.dashboard_frame)
        stats_frame.pack(fill='x', padx=20, pady=20)
        
        # Stat cards
        self.create_stat_card(stats_frame, "Connected Targets", "0", "#3498db", 0)
        self.create_stat_card(stats_frame, "Active Sessions", "0", "#e74c3c", 1)
        self.create_stat_card(stats_frame, "Blockchain Blocks", "1", "#9b59b6", 2)
        self.create_stat_card(stats_frame, "Transactions", "0", "#f39c12", 3)
        
        # Buttons
        btn_frame = tk.Frame(self.dashboard_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_dashboard).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🎯 View Targets", command=lambda: self.notebook.select(1)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="💻 Open Terminal", command=lambda: self.notebook.select(2)).pack(side='left', padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(self.dashboard_frame, text="📝 Activity Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled', 
                                                  font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
    def create_stat_card(self, parent, title, value, color, col):
        """Create a stat card"""
        card = tk.Frame(parent, bg=color, relief=tk.RAISED, bd=2)
        card.grid(row=0, column=col, padx=10, pady=10, sticky='ew')
        parent.columnconfigure(col, weight=1)
        
        tk.Label(card, text=title, bg=color, fg='white', font=('Arial', 10)).pack(pady=(10, 5))
        label = tk.Label(card, text=value, bg=color, fg='white', font=('Arial', 24, 'bold'))
        label.pack(pady=(5, 10))
        
        # Store reference
        if "Targets" in title:
            self.stats_targets = label
        elif "Sessions" in title:
            self.stats_sessions = label
        elif "Blocks" in title:
            self.stats_blockchain = label
        elif "Transactions" in title:
            self.stats_transactions = label
        
    def setup_targets(self):
        """Setup targets tab"""
        
        # Toolbar
        toolbar = tk.Frame(self.targets_frame, bg='#ecf0f1')
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_targets).pack(side='left', padx=5)
        ttk.Button(toolbar, text="📡 Open Session", command=self.open_session_from_target).pack(side='left', padx=5)
        ttk.Button(toolbar, text="ℹ️ Target Info", command=self.show_target_info).pack(side='left', padx=5)
        
        # Targets list
        list_frame = ttk.LabelFrame(self.targets_frame, text="Connected Targets", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ('Target ID', 'Hostname', 'IP', 'Platform', 'Status', 'Last Seen')
        self.targets_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        widths = [200, 150, 150, 150, 100, 150]
        for col, width in zip(columns, widths):
            self.targets_tree.heading(col, text=col)
            self.targets_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.targets_tree.yview)
        self.targets_tree.configure(yscrollcommand=scrollbar.set)
        
        self.targets_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def setup_terminal(self):
        """Setup terminal tab"""
        
        # Session info bar
        info_frame = tk.Frame(self.terminal_frame, bg='#34495e', height=50)
        info_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(info_frame, text="Session:", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=10)
        self.session_label = tk.Label(info_frame, text="No session", bg='#34495e', fg='#e74c3c', font=('Arial', 10))
        self.session_label.pack(side='left', padx=5)
        
        tk.Label(info_frame, text="Terminal:", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=20)
        self.terminal_label = tk.Label(info_frame, text="No terminal", bg='#34495e', fg='#e74c3c', font=('Arial', 10))
        self.terminal_label.pack(side='left', padx=5)
        
        ttk.Button(info_frame, text="➕ Create Terminal", command=self.create_new_terminal).pack(side='right', padx=10)
        
        # Output area
        output_frame = ttk.LabelFrame(self.terminal_frame, text="Terminal Output", padding=5)
        output_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.terminal_output = scrolledtext.ScrolledText(output_frame, height=25, 
                                                         bg='#0c0c0c', fg='#00ff00',
                                                         font=('Consolas', 10),
                                                         insertbackground='#00ff00')
        self.terminal_output.pack(fill='both', expand=True)
        
        # Command input
        cmd_frame = tk.Frame(self.terminal_frame, bg='#2c3e50')
        cmd_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(cmd_frame, text="$", bg='#2c3e50', fg='#00ff00', font=('Consolas', 12, 'bold')).pack(side='left', padx=5)
        
        self.command_entry = tk.Entry(cmd_frame, font=('Consolas', 10), bg='#34495e', fg='white', 
                                      insertbackground='white')
        self.command_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.command_entry.bind('<Return>', lambda e: self.execute_command())
        
        ttk.Button(cmd_frame, text="▶️ Execute", command=self.execute_command).pack(side='right', padx=5)
        ttk.Button(cmd_frame, text="🗑️ Clear", command=self.clear_terminal).pack(side='right', padx=5)
        
    def setup_sessions(self):
        """Setup sessions tab"""
        
        # Toolbar
        toolbar = tk.Frame(self.sessions_frame, bg='#ecf0f1')
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_sessions).pack(side='left', padx=5)
        ttk.Button(toolbar, text="❌ Close Session", command=self.close_selected_session).pack(side='left', padx=5)
        
        # Sessions list
        list_frame = ttk.LabelFrame(self.sessions_frame, text="Active Sessions", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('Session ID', 'Target ID', 'Status', 'Terminals', 'Created')
        self.sessions_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.sessions_tree.heading(col, text=col)
            self.sessions_tree.column(col, width=180)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.sessions_tree.yview)
        self.sessions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sessions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def setup_blockchain(self):
        """Setup blockchain tab"""
        
        # Toolbar
        toolbar = tk.Frame(self.blockchain_frame, bg='#ecf0f1')
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_blockchain).pack(side='left', padx=5)
        
        # Blockchain info
        info_frame = ttk.LabelFrame(self.blockchain_frame, text="Blockchain Information", padding=10)
        info_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.blockchain_text = scrolledtext.ScrolledText(info_frame, height=30, font=('Consolas', 9))
        self.blockchain_text.pack(fill='both', expand=True)
        
    def start_protocol(self):
        """Start FSDP protocol"""
        self.protocol.start()
        self.running = True
        self.log("✓ FSDP Protocol started")
        self.log(f"✓ Admin Node ID: {self.node_id}")
        self.log(f"✓ Connected to validator: {self.validator_address}")
        
        # Start background update thread
        self.update_thread = threading.Thread(target=self.background_update, daemon=True)
        self.update_thread.start()
        
        # Auto-refresh every 5 seconds
        self.auto_refresh()
        
    def auto_refresh(self):
        """Auto-refresh data"""
        if self.running:
            self.discover_targets()
            self.root.after(5000, self.auto_refresh)
            
    def background_update(self):
        """Background thread to update data"""
        while self.running:
            try:
                time.sleep(2)
            except Exception as e:
                print(f"Background update error: {e}")
                
    def discover_targets(self):
        """Discover connected targets from blockchain"""
        try:
            # Get all blocks and look for target registrations
            for block in self.blockchain.chain:
                for tx in block.data.get('transactions', []):
                    if tx.get('type') == 'heartbeat' or tx.get('type') == 'register':
                        sender = tx.get('from')
                        if sender and sender != self.node_id and 'validator' not in sender:
                            data = tx.get('data', {})
                            
                            # Update or add target
                            self.targets[sender] = {
                                'target_id': sender,
                                'hostname': data.get('hostname', 'Unknown'),
                                'ip': data.get('ip_address', 'Unknown'),
                                'platform': data.get('platform', 'Unknown'),
                                'status': 'Online',
                                'last_seen': time.time()
                            }
                            
        except Exception as e:
            print(f"Discover targets error: {e}")
            
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        self.stats_targets.config(text=str(len(self.targets)))
        self.stats_sessions.config(text=str(len(self.session_manager.sessions)))
        self.stats_blockchain.config(text=str(self.blockchain.get_chain_length()))
        
        # Count transactions
        total_tx = sum(len(block.data.get('transactions', [])) for block in self.blockchain.chain)
        self.stats_transactions.config(text=str(total_tx))
        
        self.log("Dashboard refreshed")
        
    def refresh_targets(self):
        """Refresh targets list"""
        # Clear tree
        for item in self.targets_tree.get_children():
            self.targets_tree.delete(item)
        
        # Add targets
        for target_id, info in self.targets.items():
            last_seen = datetime.fromtimestamp(info.get('last_seen', 0)).strftime('%H:%M:%S')
            self.targets_tree.insert('', 'end', values=(
                target_id[:32] + '...' if len(target_id) > 32 else target_id,
                info.get('hostname', 'Unknown'),
                info.get('ip', 'Unknown'),
                info.get('platform', 'Unknown'),
                info.get('status', 'Unknown'),
                last_seen
            ))
        
        self.log(f"Targets refreshed: {len(self.targets)} found")
        self.refresh_dashboard()
        
    def refresh_sessions(self):
        """Refresh sessions list"""
        # Clear tree
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)
        
        # Add sessions
        for session_id, session in self.session_manager.sessions.items():
            created = datetime.fromtimestamp(session.created_at).strftime('%H:%M:%S')
            self.sessions_tree.insert('', 'end', values=(
                session_id[:24] + '...' if len(session_id) > 24 else session_id,
                session.target_id[:24] + '...' if len(session.target_id) > 24 else session.target_id,
                'Active' if session.is_connected else 'Disconnected',
                len(session.terminals),
                created
            ))
        
        self.log(f"Sessions refreshed: {len(self.session_manager.sessions)} found")
        
    def refresh_blockchain(self):
        """Refresh blockchain information"""
        self.blockchain_text.delete('1.0', tk.END)
        
        info = f"""
Blockchain Statistics
{'='*60}

Chain Length: {self.blockchain.get_chain_length()}
Pending Transactions: {len(self.blockchain.pending_transactions)}
Chain Valid: {self.blockchain.is_chain_valid()}
Node ID: {self.node_id}
Validator Address: {self.validator_address}

Recent Blocks:
{'='*60}

"""
        self.blockchain_text.insert(tk.END, info)
        
        # Show last 10 blocks
        for block in self.blockchain.chain[-10:]:
            block_info = f"""
Block #{block.index}
  Timestamp: {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
  Hash: {block.hash[:32]}...
  Previous: {block.previous_hash[:32]}...
  Transactions: {len(block.data.get('transactions', []))}
  
"""
            self.blockchain_text.insert(tk.END, block_info)
            
            # Show transactions
            for tx in block.data.get('transactions', []):
                tx_info = f"    - {tx.get('type', 'unknown')} from {tx.get('from', 'unknown')[:16]}...\n"
                self.blockchain_text.insert(tk.END, tx_info)
        
        self.log("Blockchain refreshed")
        
    def show_target_info(self):
        """Show detailed target information"""
        selection = self.targets_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a target first")
            return
        
        item = self.targets_tree.item(selection[0])
        target_id_short = item['values'][0].replace('...', '')
        
        # Find full target ID
        target_id = None
        for tid in self.targets.keys():
            if tid.startswith(target_id_short) or target_id_short in tid:
                target_id = tid
                break
        
        if target_id and target_id in self.targets:
            info = self.targets[target_id]
            msg = f"""Target Information:

Target ID: {target_id}
Hostname: {info.get('hostname', 'Unknown')}
IP Address: {info.get('ip', 'Unknown')}
Platform: {info.get('platform', 'Unknown')}
Status: {info.get('status', 'Unknown')}
Last Seen: {datetime.fromtimestamp(info.get('last_seen', 0)).strftime('%Y-%m-%d %H:%M:%S')}
"""
            messagebox.showinfo("Target Information", msg)
        
    def open_session_from_target(self):
        """Open session with selected target"""
        selection = self.targets_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a target first")
            return
        
        item = self.targets_tree.item(selection[0])
        target_id_short = item['values'][0].replace('...', '')
        
        # Find full target ID
        target_id = None
        for tid in self.targets.keys():
            if tid.startswith(target_id_short) or target_id_short in tid:
                target_id = tid
                break
        
        if not target_id:
            messagebox.showerror("Error", "Could not find target ID")
            return
        
        # Create session
        session_id = f"session-{int(time.time())}"
        session = self.session_manager.create_session(
            session_id=session_id,
            admin_id=self.node_id,
            target_id=target_id
        )
        
        self.current_session = session_id
        self.session_label.config(text=session_id[:24] + '...', fg='#27ae60')
        
        self.log(f"✓ Session opened: {session_id}")
        self.log(f"✓ Target: {target_id[:32]}...")
        
        # Switch to terminal tab
        self.notebook.select(2)
        
        messagebox.showinfo("Success", f"Session opened!\n\nSession ID: {session_id[:32]}...\n\nNow create a terminal to execute commands.")
        
    def create_new_terminal(self):
        """Create a new terminal in current session"""
        if not self.current_session:
            messagebox.showwarning("No Session", "Please open a session first from the Targets tab")
            return
        
        terminal_id = f"terminal-{int(time.time())}"
        
        session = self.session_manager.sessions.get(self.current_session)
        if not session:
            messagebox.showerror("Error", "Session not found")
            return
        
        # Create terminal
        terminal = self.session_manager.create_terminal(self.current_session, terminal_id)
        self.current_terminal = terminal_id
        self.terminal_label.config(text=terminal_id[:24] + '...', fg='#27ae60')
        
        self.log(f"✓ Terminal created: {terminal_id}")
        self.terminal_write(f"╔═══════════════════════════════════════════════════════════╗\n")
        self.terminal_write(f"║  FSDP Terminal - {terminal_id[:20]}...  ║\n")
        self.terminal_write(f"╚═══════════════════════════════════════════════════════════╝\n\n")
        self.terminal_write(f"Working directory: {terminal.current_dir}\n")
        self.terminal_write(f"Ready to execute commands.\n\n")
        self.terminal_write(f"$ ")
        
    def execute_command(self):
        """Execute command in current terminal"""
        if not self.current_session or not self.current_terminal:
            messagebox.showwarning("Not Ready", "Please:\n1. Open a session (Targets tab)\n2. Create a terminal (Create Terminal button)")
            return
        
        command = self.command_entry.get().strip()
        if not command:
            return
        
        self.terminal_write(f"{command}\n")
        self.command_entry.delete(0, tk.END)
        
        session = self.session_manager.sessions.get(self.current_session)
        if not session:
            self.terminal_write("ERROR: Session not found\n$ ")
            return
        
        # Execute locally (for demo - in production this would send to target)
        terminal = session.terminals.get(self.current_terminal)
        if terminal:
            try:
                result = terminal.execute_command(command)
                
                if result['output']:
                    self.terminal_write(result['output'])
                if result['error']:
                    self.terminal_write(f"ERROR: {result['error']}\n")
                
                self.log(f"Command executed: {command[:30]}...")
            except Exception as e:
                self.terminal_write(f"ERROR: {str(e)}\n")
        
        self.terminal_write("\n$ ")
        
    def clear_terminal(self):
        """Clear terminal output"""
        self.terminal_output.delete('1.0', tk.END)
        self.terminal_write("Terminal cleared.\n\n$ ")
        
    def terminal_write(self, text):
        """Write to terminal output"""
        self.terminal_output.insert(tk.END, text)
        self.terminal_output.see(tk.END)
        
    def close_selected_session(self):
        """Close selected session"""
        selection = self.sessions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a session first")
            return
        
        item = self.sessions_tree.item(selection[0])
        session_id_short = item['values'][0].replace('...', '')
        
        # Find full session ID
        session_id = None
        for sid in self.session_manager.sessions.keys():
            if sid.startswith(session_id_short) or session_id_short in sid:
                session_id = sid
                break
        
        if session_id:
            self.session_manager.close_session(session_id)
            self.log(f"✓ Session closed: {session_id}")
            self.refresh_sessions()
            
            if self.current_session == session_id:
                self.current_session = None
                self.current_terminal = None
                self.session_label.config(text="No session", fg='#e74c3c')
                self.terminal_label.config(text="No terminal", fg='#e74c3c')
                self.clear_terminal()
        
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
        self.status_bar.config(text=message)
        
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit FSDP Admin?"):
            self.running = False
            self.protocol.stop()
            self.session_manager.shutdown()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = FSDPAdminGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

