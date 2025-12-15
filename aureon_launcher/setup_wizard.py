#!/usr/bin/env python3
"""
AUREON Setup Wizard
First-time configuration for API keys and settings
"""

import tkinter as tk
from tkinter import ttk, messagebox


class SetupWizard:
    """Setup wizard for first-time configuration"""
    
    def __init__(self, parent, cred_manager, on_complete):
        self.parent = parent
        self.cred_manager = cred_manager
        self.on_complete = on_complete
        
        self.window = tk.Toplevel(parent)
        self.window.title("AUREON Setup Wizard")
        self.window.geometry("500x600")
        self.window.configure(bg='#0a0a0f')
        self.window.transient(parent)
        self.window.grab_set()
        
        self.current_step = 0
        self.steps = ['welcome', 'binance', 'kraken', 'alpaca', 'capital', 'complete']
        
        self.build_ui()
        self.show_step(0)
    
    def build_ui(self):
        """Build wizard UI"""
        # Main container
        self.main_frame = tk.Frame(self.window, bg='#0a0a0f')
        self.main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Content area (changes per step)
        self.content_frame = tk.Frame(self.main_frame, bg='#0a0a0f')
        self.content_frame.pack(fill='both', expand=True)
        
        # Navigation buttons
        nav_frame = tk.Frame(self.main_frame, bg='#0a0a0f')
        nav_frame.pack(fill='x', pady=(20, 0))
        
        self.back_btn = tk.Button(
            nav_frame,
            text="← Back",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a22',
            relief='flat',
            cursor='hand2',
            command=self.prev_step
        )
        self.back_btn.pack(side='left')
        
        self.next_btn = tk.Button(
            nav_frame,
            text="Next →",
            font=('Segoe UI', 10, 'bold'),
            fg='#0a0a0f',
            bg='#00ff88',
            relief='flat',
            cursor='hand2',
            command=self.next_step
        )
        self.next_btn.pack(side='right')
        
        self.skip_btn = tk.Button(
            nav_frame,
            text="Skip",
            font=('Segoe UI', 10),
            fg='#666',
            bg='#0a0a0f',
            relief='flat',
            cursor='hand2',
            command=self.skip_step
        )
        self.skip_btn.pack(side='right', padx=10)
    
    def clear_content(self):
        """Clear content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_step(self, step_index):
        """Show specific step"""
        self.current_step = step_index
        self.clear_content()
        
        step = self.steps[step_index]
        
        # Update navigation buttons
        self.back_btn.config(state='normal' if step_index > 0 else 'disabled')
        
        if step == 'welcome':
            self.show_welcome()
        elif step == 'complete':
            self.show_complete()
        else:
            self.show_exchange_setup(step)
    
    def show_welcome(self):
        """Welcome screen"""
        self.skip_btn.pack_forget()
        
        tk.Label(
            self.content_frame,
            text="🐙",
            font=('Segoe UI', 64),
            fg='#00ff88',
            bg='#0a0a0f'
        ).pack(pady=(20, 10))
        
        tk.Label(
            self.content_frame,
            text="Welcome to AUREON",
            font=('Segoe UI', 24, 'bold'),
            fg='#fff',
            bg='#0a0a0f'
        ).pack()
        
        tk.Label(
            self.content_frame,
            text="Quantum Trading System",
            font=('Segoe UI', 12),
            fg='#666',
            bg='#0a0a0f'
        ).pack(pady=(0, 30))
        
        info_text = """Let's set up your exchange API keys.

Your credentials are stored securely in
Windows Credential Manager - never in files.

You'll need API keys from at least one exchange:
• Binance (recommended)
• Kraken
• Alpaca (US stocks)
• Capital.com (CFDs)

⚠️ IMPORTANT: Only enable SPOT trading.
   Never enable withdrawal permissions!"""
        
        tk.Label(
            self.content_frame,
            text=info_text,
            font=('Segoe UI', 11),
            fg='#aaa',
            bg='#0a0a0f',
            justify='left'
        ).pack(pady=20)
    
    def show_exchange_setup(self, exchange):
        """Exchange API key setup screen"""
        self.skip_btn.pack(side='right', padx=10)
        
        names = {
            'binance': ('🟡 Binance', 'https://www.binance.com/en/my/settings/api-management'),
            'kraken': ('🐙 Kraken', 'https://www.kraken.com/u/security/api'),
            'alpaca': ('🦙 Alpaca', 'https://app.alpaca.markets/paper/dashboard/overview'),
            'capital': ('💼 Capital.com', 'https://capital.com/trading/platform')
        }
        
        name, url = names.get(exchange, (exchange, ''))
        
        tk.Label(
            self.content_frame,
            text=name,
            font=('Segoe UI', 24, 'bold'),
            fg='#00ff88',
            bg='#0a0a0f'
        ).pack(pady=(20, 30))
        
        # Check if credentials exist
        existing = self.cred_manager.get_credentials(exchange)
        if existing:
            tk.Label(
                self.content_frame,
                text="✅ Credentials already saved",
                font=('Segoe UI', 11),
                fg='#00ff88',
                bg='#0a0a0f'
            ).pack(pady=(0, 20))
        
        # API Key
        tk.Label(
            self.content_frame,
            text="API Key",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#0a0a0f',
            anchor='w'
        ).pack(fill='x')
        
        self.api_key_entry = tk.Entry(
            self.content_frame,
            font=('Consolas', 11),
            fg='#00ff88',
            bg='#111118',
            insertbackground='#00ff88',
            relief='flat',
            width=50
        )
        self.api_key_entry.pack(fill='x', pady=(5, 15), ipady=8)
        if existing:
            self.api_key_entry.insert(0, existing.get('api_key', '')[:8] + '...')
        
        # API Secret
        tk.Label(
            self.content_frame,
            text="API Secret",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#0a0a0f',
            anchor='w'
        ).pack(fill='x')
        
        self.api_secret_entry = tk.Entry(
            self.content_frame,
            font=('Consolas', 11),
            fg='#00ff88',
            bg='#111118',
            insertbackground='#00ff88',
            relief='flat',
            width=50,
            show='•'
        )
        self.api_secret_entry.pack(fill='x', pady=(5, 20), ipady=8)
        
        # Show/hide toggle
        self.show_secret = tk.BooleanVar(value=False)
        toggle_btn = tk.Checkbutton(
            self.content_frame,
            text="Show secret",
            variable=self.show_secret,
            font=('Segoe UI', 9),
            fg='#666',
            bg='#0a0a0f',
            selectcolor='#0a0a0f',
            activebackground='#0a0a0f',
            command=lambda: self.api_secret_entry.config(show='' if self.show_secret.get() else '•')
        )
        toggle_btn.pack(anchor='w')
        
        # Help link
        help_btn = tk.Button(
            self.content_frame,
            text=f"📖 How to get {exchange.capitalize()} API keys",
            font=('Segoe UI', 10),
            fg='#00aaff',
            bg='#0a0a0f',
            relief='flat',
            cursor='hand2',
            command=lambda: __import__('webbrowser').open(url)
        )
        help_btn.pack(pady=20)
        
        # Security warning
        tk.Label(
            self.content_frame,
            text="⚠️ Enable SPOT trading only. Never enable withdrawals!",
            font=('Segoe UI', 10),
            fg='#ffaa00',
            bg='#0a0a0f'
        ).pack(pady=10)
        
        # Store current exchange for save
        self.current_exchange = exchange
    
    def show_complete(self):
        """Completion screen"""
        self.skip_btn.pack_forget()
        self.next_btn.config(text="Finish ✓")
        
        tk.Label(
            self.content_frame,
            text="✅",
            font=('Segoe UI', 64),
            fg='#00ff88',
            bg='#0a0a0f'
        ).pack(pady=(30, 10))
        
        tk.Label(
            self.content_frame,
            text="Setup Complete!",
            font=('Segoe UI', 24, 'bold'),
            fg='#fff',
            bg='#0a0a0f'
        ).pack()
        
        # Show configured exchanges
        status = self.cred_manager.get_all_exchanges_status()
        configured = sum(1 for v in status.values() if v)
        
        tk.Label(
            self.content_frame,
            text=f"{configured} exchange(s) configured",
            font=('Segoe UI', 12),
            fg='#666',
            bg='#0a0a0f'
        ).pack(pady=(10, 30))
        
        for exchange, has_creds in status.items():
            icon = "✅" if has_creds else "⚪"
            tk.Label(
                self.content_frame,
                text=f"{icon} {exchange.capitalize()}",
                font=('Segoe UI', 11),
                fg='#00ff88' if has_creds else '#444',
                bg='#0a0a0f'
            ).pack()
        
        tk.Label(
            self.content_frame,
            text="\nYour credentials are securely stored in\nWindows Credential Manager.",
            font=('Segoe UI', 10),
            fg='#666',
            bg='#0a0a0f'
        ).pack(pady=30)
    
    def save_current_exchange(self):
        """Save credentials for current exchange"""
        if not hasattr(self, 'current_exchange'):
            return True
        
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        
        # Skip if both empty or placeholder
        if not api_key or not api_secret or '...' in api_key:
            return True
        
        success = self.cred_manager.save_credentials(
            self.current_exchange,
            api_key,
            api_secret
        )
        
        if success:
            return True
        else:
            messagebox.showerror("Error", f"Failed to save {self.current_exchange} credentials")
            return False
    
    def next_step(self):
        """Go to next step"""
        # Save current exchange if on exchange step
        if self.steps[self.current_step] in ['binance', 'kraken', 'alpaca', 'capital']:
            if not self.save_current_exchange():
                return
        
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)
        else:
            self.finish()
    
    def prev_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def skip_step(self):
        """Skip current step"""
        self.next_step()
    
    def finish(self):
        """Complete wizard"""
        self.window.destroy()
        self.on_complete()


if __name__ == '__main__':
    # Test wizard standalone
    from credentials import CredentialManager
    
    root = tk.Tk()
    root.withdraw()
    
    cm = CredentialManager()
    wizard = SetupWizard(root, cm, lambda: root.destroy())
    root.mainloop()
