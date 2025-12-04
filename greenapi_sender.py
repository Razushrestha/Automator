
# greenapi_sender.py

# ===== CRITICAL: Prevent segmentation faults on Linux =====
import os
import sys

# Set environment variables BEFORE any GUI imports
os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Prevent Qt conflicts
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'  # Prevent debugger issues
os.environ['TK_SILENCE_DEPRECATION'] = '1' # Prevent Tkinter threading issues

# Chrome/Chromium stability (just in case, though we use requests)
os.environ['CHROME_DEVEL_SANDBOX'] = '/usr/local/sbin/chrome-devel-sandbox'
os.environ['DBUS_SESSION_BUS_ADDRESS'] = os.environ.get('DBUS_SESSION_BUS_ADDRESS', '/dev/null')
# ==========================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import requests
import pandas as pd
import re
import json

# ==================== CONFIGURATION ====================
APP_TITLE = "Green API Bulk Sender"
APP_VERSION = "1.0.0"
DEFAULT_API_URL = "https://7105.api.green-api.com"
DEFAULT_MEDIA_URL = "https://7105.media.green-api.com"
DEFAULT_INSTANCE_ID = "7105402179"

# Theme Colors (Dark Mode)
BG_COLOR = "#0D1117"        # GitHub Dark Dimmed Background
FG_COLOR = "#C9D1D9"        # GitHub Dark Dimmed Text
ACCENT_COLOR = "#238636"    # GitHub Green
ACCENT_HOVER = "#2EA043"
ENTRY_BG = "#010409"
ENTRY_FG = "#C9D1D9"
BORDER_COLOR = "#30363D"
ERROR_COLOR = "#DA3633"
WARNING_COLOR = "#D29922"
SUCCESS_COLOR = "#3FB950"

# Fonts
FONT_MAIN = ("Segoe UI", 10)
FONT_HEADER = ("Segoe UI", 14, "bold")
FONT_MONO = ("Consolas", 9)

# ==================== HELPER FUNCTIONS ====================

def extract_phone_digits(phone_str):
    """Extract only numeric digits from a phone number string."""
    digits = re.sub(r'\D', '', str(phone_str))
    return digits.strip()

def validate_green_api_credentials(instance_id, api_token, api_url):
    """Check if Green API credentials are valid."""
    try:
        url = f"{api_url}/waInstance{instance_id}/getStateInstance/{api_token}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            state = data.get('stateInstance')
            return True, state
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def send_message_greenapi(phone, message, instance_id, api_token, api_url):
    """Send text message via Green API."""
    try:
        phone = extract_phone_digits(phone)
        if not phone: return False, "Invalid phone number"
        
        chat_id = f"{phone}@c.us"
        url = f"{api_url}/waInstance{instance_id}/sendMessage/{api_token}"
        payload = {"chatId": chat_id, "message": message}
        
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return True, response.json().get('idMessage', 'N/A')
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def send_file_greenapi(phone, file_path, caption, instance_id, api_token, media_url):
    """Send file via Green API."""
    try:
        if not os.path.exists(file_path): return False, "File not found"
        
        phone = extract_phone_digits(phone)
        if not phone: return False, "Invalid phone number"
        
        chat_id = f"{phone}@c.us"
        file_name = os.path.basename(file_path)
        url = f"{media_url}/waInstance{instance_id}/sendFileByUpload/{api_token}"
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/octet-stream')}
            data = {'chatId': chat_id, 'caption': caption if caption else ''}
            response = requests.post(url, files=files, data=data, timeout=120)
            
        if response.status_code == 200:
            return True, response.json().get('idMessage', 'N/A')
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

# ==================== GUI APPLICATION ====================

class GreenApiSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry("900x800")
        self.root.configure(bg=BG_COLOR)
        self.root.minsize(800, 700)
        
        # Variables
        self.csv_path = tk.StringVar()
        self.attachment_path = tk.StringVar()
        self.delay_var = tk.StringVar(value="2")  # Default 2 seconds delay
        self.status_var = tk.StringVar(value="Ready")
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Style configuration
        self.setup_styles()
        
        # UI Layout
        self.create_header()
        self.create_credentials_section()
        self.create_message_section()
        self.create_controls_section()
        self.create_log_section()
        self.create_status_bar()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Card.TFrame", background=BG_COLOR, relief="flat", borderwidth=1)
        
        # Label styles
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=FONT_MAIN)
        style.configure("Header.TLabel", font=FONT_HEADER, foreground=SUCCESS_COLOR)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground=FG_COLOR)
        
        # Button styles
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, background=ENTRY_BG, foreground=FG_COLOR, borderwidth=1)
        style.map("TButton", background=[('active', HOVER_BG)], foreground=[('active', 'white')])
        
        style.configure("Action.TButton", background=ACCENT_COLOR, foreground="white", borderwidth=0)
        style.map("Action.TButton", background=[('active', ACCENT_HOVER)])
        
        style.configure("Stop.TButton", background=ERROR_COLOR, foreground="white", borderwidth=0)
        style.map("Stop.TButton", background=[('active', "#B62324")])
        
        # Entry styles
        style.configure("TEntry", fieldbackground=ENTRY_BG, foreground="white", borderwidth=1, relief="solid")
        
        # Checkbutton
        style.configure("TCheckbutton", background=BG_COLOR, foreground=FG_COLOR, font=FONT_MAIN)

    def create_header(self):
        header_frame = ttk.Frame(self.root, padding="20 20 20 10")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(header_frame, text=f"🌿 {APP_TITLE}", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(header_frame, text=f"v{APP_VERSION}", foreground=FG_SECONDARY)
        version_label.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))

    def create_credentials_section(self):
        frame = ttk.LabelFrame(self.root, text="API Configuration", padding="15")
        frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Grid layout for inputs
        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.X)
        
        # Row 1: Instance ID & Token
        ttk.Label(grid_frame, text="Instance ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.entry_instance = ttk.Entry(grid_frame, width=30)
        self.entry_instance.insert(0, DEFAULT_INSTANCE_ID)
        self.entry_instance.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(grid_frame, text="API Token:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.entry_token = ttk.Entry(grid_frame, width=40, show="*")
        self.entry_token.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        
        # Row 2: API URL & Media URL
        ttk.Label(grid_frame, text="API URL:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_api_url = ttk.Entry(grid_frame, width=30)
        self.entry_api_url.insert(0, DEFAULT_API_URL)
        self.entry_api_url.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(grid_frame, text="Media URL:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.entry_media_url = ttk.Entry(grid_frame, width=40)
        self.entry_media_url.insert(0, DEFAULT_MEDIA_URL)
        self.entry_media_url.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        
        # Validate Button
        self.btn_validate = ttk.Button(frame, text="Check Connection", command=self.check_connection)
        self.btn_validate.pack(anchor="e", pady=(10, 0))
        
        # Configure grid weights
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(3, weight=1)

    def create_message_section(self):
        frame = ttk.LabelFrame(self.root, text="Message & Recipients", padding="15")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # CSV Selection
        csv_frame = ttk.Frame(frame)
        csv_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(csv_frame, text="Contacts CSV:").pack(side=tk.LEFT)
        ttk.Entry(csv_frame, textvariable=self.csv_path, width=50).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        ttk.Button(csv_frame, text="Browse...", command=self.browse_csv).pack(side=tk.LEFT)
        
        # Message Body
        ttk.Label(frame, text="Message (use {{name}} for personalization):").pack(anchor="w", pady=(5, 5))
        self.text_message = tk.Text(frame, height=8, bg=ENTRY_BG, fg="white", insertbackground="white", 
                                   relief="flat", borderwidth=1, font=FONT_MAIN)
        self.text_message.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Attachment & Delay
        bottom_frame = ttk.Frame(frame)
        bottom_frame.pack(fill=tk.X)
        
        # Attachment
        ttk.Label(bottom_frame, text="Attachment (Optional):").pack(side=tk.LEFT)
        ttk.Entry(bottom_frame, textvariable=self.attachment_path, width=40).pack(side=tk.LEFT, padx=10)
        ttk.Button(bottom_frame, text="Browse...", command=self.browse_attachment).pack(side=tk.LEFT, padx=(0, 20))
        
        # Delay
        ttk.Label(bottom_frame, text="Delay (sec):").pack(side=tk.LEFT)
        ttk.Entry(bottom_frame, textvariable=self.delay_var, width=5).pack(side=tk.LEFT, padx=5)

    def create_controls_section(self):
        frame = ttk.Frame(self.root, padding="20 10")
        frame.pack(fill=tk.X)
        
        self.btn_start = ttk.Button(frame, text="▶ START SENDING", style="Action.TButton", command=self.start_sending_thread)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.btn_stop = ttk.Button(frame, text="⏹ STOP", style="Stop.TButton", command=self.stop_sending, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

    def create_log_section(self):
        frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.log_text = scrolledtext.ScrolledText(frame, height=10, bg=ENTRY_BG, fg=SUCCESS_COLOR, 
                                                 font=FONT_MONO, state='disabled', relief="flat")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        status_frame = ttk.Frame(self.root, padding="5")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 9)).pack(side=tk.LEFT)

    # ==================== LOGIC ====================

    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        def _update():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, formatted_msg)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
            
        self.root.after(0, _update)

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")])
        if path: self.csv_path.set(path)

    def browse_attachment(self):
        path = filedialog.askopenfilename()
        if path: self.attachment_path.set(path)

    def check_connection(self):
        instance = self.entry_instance.get().strip()
        token = self.entry_token.get().strip()
        url = self.entry_api_url.get().strip()
        
        if not instance or not token:
            messagebox.showwarning("Missing Info", "Please enter Instance ID and Token")
            return
            
        self.log("🔄 Checking connection...")
        threading.Thread(target=self._check_connection_thread, args=(instance, token, url), daemon=True).start()

    def _check_connection_thread(self, instance, token, url):
        valid, state = validate_green_api_credentials(instance, token, url)
        if valid:
            self.log(f"✅ Connection Successful! State: {state}")
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Connected!\nState: {state}"))
        else:
            self.log(f"❌ Connection Failed: {state}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Connection Failed:\n{state}"))

    def start_sending_thread(self):
        if self.is_running: return
        
        # Validation
        csv_file = self.csv_path.get()
        if not csv_file or not os.path.exists(csv_file):
            messagebox.showerror("Error", "Please select a valid CSV file")
            return
            
        instance = self.entry_instance.get().strip()
        token = self.entry_token.get().strip()
        if not instance or not token:
            messagebox.showerror("Error", "API Credentials required")
            return
            
        self.is_running = True
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        
        threading.Thread(target=self.process_queue, daemon=True).start()

    def stop_sending(self):
        if self.is_running:
            self.stop_event.set()
            self.log("⏹ Stopping... finishing current task.")

    def process_queue(self):
        try:
            # Read CSV
            csv_file = self.csv_path.get()
            try:
                if csv_file.endswith('.xlsx'):
                    try:
                        df = pd.read_excel(csv_file)
                    except ImportError:
                        self.log("❌ Error: 'openpyxl' library needed for Excel files.")
                        self.log("💡 Run: pip install openpyxl")
                        return
                else:
                    df = pd.read_csv(csv_file)
            except Exception as e:
                self.log(f"❌ Error reading file: {e}")
                return

            # Find columns
            phone_col = next((c for c in df.columns if 'phone' in c.lower() or 'number' in c.lower() or 'mobile' in c.lower()), df.columns[0])
            name_col = next((c for c in df.columns if 'name' in c.lower()), None)
            
            self.log(f"📂 Loaded {len(df)} contacts. Using column '{phone_col}' for numbers.")
            
            # Get config
            instance = self.entry_instance.get().strip()
            token = self.entry_token.get().strip()
            api_url = self.entry_api_url.get().strip()
            media_url = self.entry_media_url.get().strip()
            message_template = self.text_message.get("1.0", tk.END).strip()
            attachment = self.attachment_path.get().strip()
            
            # Get delay
            try:
                delay = float(self.delay_var.get())
            except ValueError:
                delay = 2.0
                self.log("⚠️ Invalid delay, using 2.0s")
            
            sent_count = 0
            failed_count = 0
            
            for index, row in df.iterrows():
                if self.stop_event.is_set():
                    break
                
                phone = str(row[phone_col])
                name = str(row[name_col]) if name_col else "Friend"
                
                # Personalize message
                message = message_template.replace("{{name}}", name).replace("{name}", name)
                
                self.status_var.set(f"Sending to {phone} ({index + 1}/{len(df)})...")
                
                success = False
                msg_id = ""
                
                # Send Attachment if present
                if attachment:
                    success, msg_id = send_file_greenapi(phone, attachment, message, instance, token, media_url)
                    type_str = "File"
                # Send Text otherwise
                elif message:
                    success, msg_id = send_message_greenapi(phone, message, instance, token, api_url)
                    type_str = "Text"
                else:
                    self.log(f"⚠️ Skipping {phone}: No message or attachment")
                    continue
                
                if success:
                    self.log(f"✅ {type_str} sent to {phone} (ID: {msg_id})")
                    sent_count += 1
                else:
                    if "466" in msg_id:
                        self.log(f"❌ Failed to send to {phone}: RATE LIMIT EXCEEDED (466)")
                        self.log("⚠️ You are sending too fast or have hit your plan limit.")
                        self.log("💡 Try increasing the delay or checking your Green API plan.")
                    else:
                        self.log(f"❌ Failed to send to {phone}: {msg_id}")
                    failed_count += 1
                
                # Delay
                time.sleep(delay)
            
            self.log(f"🏁 Completed! Sent: {sent_count}, Failed: {failed_count}")
            self.status_var.set("Ready")
            
        except Exception as e:
            self.log(f"❌ Critical Error: {e}")
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal"))
            self.root.after(0, lambda: self.btn_stop.config(state="disabled"))

# ==================== MAIN ====================

if __name__ == "__main__":
    # Global colors for imported modules if needed
    HOVER_BG = "#21262D"
    FG_SECONDARY = "#8B949E"
    
    try:
        root = tk.Tk()
        app = GreenApiSenderApp(root)
        root.mainloop()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
