#!/usr/bin/env python3
"""
AUREON Desktop Launcher
Windows Desktop App with OS Keychain integration
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
from datetime import datetime

# Import our modules
from credentials import CredentialManager
from setup_wizard import SetupWizard

class AureonLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🐙 AUREON Trading System")
        self.root.geometry("600x500")
        self.root.configure(bg='#0a0a0f')
        self.root.resizable(False, False)
        
        # Set icon if available
        try:
            self.root.iconbitmap('aureon.ico')
        except:
            pass
        
        self.cred_manager = CredentialManager()
        self.trading_process = None
        self.is_trading = False
        
        # Check if first run
        if not self.cred_manager.has_credentials():
            self.show_setup_wizard()
        else:
            self.build_main_ui()
    
    def show_setup_wizard(self):
        """Show first-time setup wizard"""
        wizard = SetupWizard(self.root, self.cred_manager, self.on_setup_complete)
    
    def on_setup_complete(self):
        """Called when setup wizard completes"""
        self.build_main_ui()
    
    def build_main_ui(self):
        """Build main launcher UI"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0a0f')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Label(
            main_frame,
            text="🐙 AUREON",
            font=('Segoe UI', 32, 'bold'),
            fg='#00ff88',
            bg='#0a0a0f'
        )
        header.pack(pady=(0, 5))
        
        subtitle = tk.Label(
            main_frame,
            text="Quantum Trading System",
            font=('Segoe UI', 12),
            fg='#666',
            bg='#0a0a0f'
        )
        subtitle.pack(pady=(0, 20))
        
        # Status panel
        status_frame = tk.Frame(main_frame, bg='#111118', relief='flat')
        status_frame.pack(fill='x', pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="⚪ Ready to Trade",
            font=('Segoe UI', 14),
            fg='#888',
            bg='#111118',
            pady=15
        )
        self.status_label.pack()
        
        # Exchange status
        exchanges_frame = tk.Frame(main_frame, bg='#0a0a0f')
        exchanges_frame.pack(fill='x', pady=10)
        
        self.exchange_labels = {}
        exchanges = ['binance', 'kraken', 'alpaca', 'capital']
        exchange_names = {'binance': '🟡 Binance', 'kraken': '🐙 Kraken', 'alpaca': '🦙 Alpaca', 'capital': '💼 Capital.com'}
        
        for ex in exchanges:
            has_creds = self.cred_manager.get_credentials(ex) is not None
            status = "✅" if has_creds else "⚪"
            
            label = tk.Label(
                exchanges_frame,
                text=f"{status} {exchange_names[ex]}",
                font=('Segoe UI', 10),
                fg='#00ff88' if has_creds else '#444',
                bg='#0a0a0f'
            )
            label.pack(side='left', padx=10)
            self.exchange_labels[ex] = label
        
        # Start/Stop button
        self.start_button = tk.Button(
            main_frame,
            text="▶ START TRADING",
            font=('Segoe UI', 16, 'bold'),
            fg='#0a0a0f',
            bg='#00ff88',
            activebackground='#00cc66',
            activeforeground='#0a0a0f',
            relief='flat',
            cursor='hand2',
            width=20,
            height=2,
            command=self.toggle_trading
        )
        self.start_button.pack(pady=30)
        
        # Log area
        log_frame = tk.Frame(main_frame, bg='#111118')
        log_frame.pack(fill='both', expand=True, pady=10)
        
        log_label = tk.Label(
            log_frame,
            text="Activity Log",
            font=('Segoe UI', 10),
            fg='#666',
            bg='#111118',
            anchor='w'
        )
        log_label.pack(fill='x', padx=10, pady=(10, 5))
        
        self.log_text = tk.Text(
            log_frame,
            font=('Consolas', 9),
            fg='#00ff88',
            bg='#0a0a0f',
            height=8,
            relief='flat',
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Bottom buttons
        bottom_frame = tk.Frame(main_frame, bg='#0a0a0f')
        bottom_frame.pack(fill='x', pady=10)
        
        settings_btn = tk.Button(
            bottom_frame,
            text="⚙ Settings",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a22',
            activebackground='#2a2a32',
            relief='flat',
            cursor='hand2',
            command=self.show_settings
        )
        settings_btn.pack(side='left')
        
        web_btn = tk.Button(
            bottom_frame,
            text="🌐 Open Dashboard",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a22',
            activebackground='#2a2a32',
            relief='flat',
            cursor='hand2',
            command=self.open_web_dashboard
        )
        web_btn.pack(side='right')
        
        self.log("Launcher initialized")
        self.log(f"Connected exchanges: {sum(1 for ex in exchanges if self.cred_manager.get_credentials(ex))}/4")
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
    
    def toggle_trading(self):
        """Start or stop trading"""
        if self.is_trading:
            self.stop_trading()
        else:
            self.start_trading()
    
    def start_trading(self):
        """Start the trading bot"""
        self.is_trading = True
        self.start_button.config(
            text="⏹ STOP TRADING",
            bg='#ff4444',
            activebackground='#cc3333'
        )
        self.status_label.config(text="🟢 Trading Active", fg='#00ff88')
        self.log("Starting trading engine...")
        
        # Start trading in background thread
        self.trading_thread = threading.Thread(target=self.run_trading_engine)
        self.trading_thread.daemon = True
        self.trading_thread.start()
    
    def stop_trading(self):
        """Stop the trading bot"""
        self.is_trading = False
        self.start_button.config(
            text="▶ START TRADING",
            bg='#00ff88',
            activebackground='#00cc66'
        )
        self.status_label.config(text="⚪ Stopped", fg='#888')
        self.log("Stopping trading engine...")
        
        if self.trading_process:
            self.trading_process.terminate()
            self.trading_process = None
    
    def run_trading_engine(self):
        """Run the actual trading engine"""
        try:
            # Get credentials from keychain
            binance_creds = self.cred_manager.get_credentials('binance')
            kraken_creds = self.cred_manager.get_credentials('kraken')
            
            # Set environment variables for the trading script
            env = os.environ.copy()
            if binance_creds:
                env['BINANCE_API_KEY'] = binance_creds['api_key']
                env['BINANCE_API_SECRET'] = binance_creds['api_secret']
            if kraken_creds:
                env['KRAKEN_API_KEY'] = kraken_creds['api_key']
                env['KRAKEN_API_SECRET'] = kraken_creds['api_secret']
            
            # Run the trading script
            script_path = os.path.join(os.path.dirname(__file__), '..', 'aureon_kraken_ecosystem.py')
            if os.path.exists(script_path):
                self.trading_process = subprocess.Popen(
                    [sys.executable, script_path],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Read output and log it
                for line in self.trading_process.stdout:
                    if not self.is_trading:
                        break
                    self.root.after(0, lambda l=line: self.log(l.strip()[:80]))
            else:
                self.root.after(0, lambda: self.log("⚠ Trading script not found"))
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error: {str(e)}"))
            self.root.after(0, self.stop_trading)
    
    def show_settings(self):
        """Show settings dialog"""
        self.show_setup_wizard()
    
    def open_web_dashboard(self):
        """Open web dashboard in browser"""
        import webbrowser
        webbrowser.open('https://owfeyxrfyhprpcgqwxqh.lovableproject.com/')
        self.log("Opened web dashboard")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == '__main__':
    app = AureonLauncher()
    app.run()
