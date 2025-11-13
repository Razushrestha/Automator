# auto_messenger_ultra_fast.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import random
import os
import threading
import urllib.parse
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import re

# ==================== CONFIG ====================

PROFILE_DIR = os.path.join(os.getenv("APPDATA"), "AutoMessenger", "chrome_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

HEADLESS = False
MIN_DELAY = 3
MAX_DELAY = 7
WAIT_TIMEOUT = 15
FAST_WAIT = 4
POST_CLICK_WAIT = 0.8
# ===============================================

# --- Helper: Extract numeric digits from phone numbers ---
def extract_phone_digits(phone_str):
    """
    Extract only numeric digits from a phone number string.
    Examples:
        "+977-980-3661701" -> "9779803661701"
        "Phone: 9779803661701" -> "9779803661701"
        "977 (980) 366-1701" -> "9779803661701"
    """
    import re
    digits = re.sub(r'\D', '', str(phone_str))
    return digits.strip()

# --- Helper: create Chrome driver on demand (so GUI can start first) ---
def create_driver(profile_dir=PROFILE_DIR, headless=HEADLESS):
    os.makedirs(profile_dir, exist_ok=True)
    options = Options()
    options.add_argument(f"--user-data-dir={profile_dir}")
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--disable-plugins")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    })
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    # hide webdriver flag
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    except Exception:
        pass
    return driver

# --- Messaging actions (WhatsApp with attachment support) ---
def send_message_whatsapp(driver, phone, message, log_fn, stop_event, attachment_path=None, delay_seconds=60):
    """
    Send a WhatsApp message to a single phone number using a Selenium driver.
    Compatible with web.whatsapp.com, assuming user is logged in.

    Args:
        driver: Selenium WebDriver instance
        phone: str, phone number (with or without '+')
        message: str, text message to send
        log_fn: callable, logging function
        stop_event: threading.Event, used to stop execution gracefully
        attachment_path: str, optional path to file to attach (PDF, PNG, JPG, etc.)
        delay_seconds: int, number of seconds to wait after sending (default: 60)
    """
    if stop_event.is_set():
        log_fn("Stopped before sending.")
        return False

    try:
        # Format phone correctly
        phone = str(phone).strip()
        if not phone:
            log_fn("❌ Empty phone number, skipping.")
            return False
        if phone.startswith("+"):
            phone = phone[1:]

        # Navigate to chat URL
        url = f"https://web.whatsapp.com/send?phone={phone}&app_absent=0"
        driver.get(url)
        log_fn(f"Opening chat with {phone}...")
        time.sleep(3)

        # Wait for input box
        wait = WebDriverWait(driver, 15)
        try:
            input_box = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
        except TimeoutException:
            log_fn(f"⏳ Timeout: Chat not ready for {phone}")
            return False

        if stop_event.is_set():
            log_fn("Stopped before typing message.")
            return False

        # Handle file attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            log_fn(f"📎 Attaching file: {os.path.basename(attachment_path)}")
            try:
                # Click attachment button (clip icon)
                attach_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@title="Attach" or @aria-label="Attach"]'))
                )
                attach_btn.click()
                time.sleep(1.5)
                
                # Find and click the file input for document/image
                file_input = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//input[@accept="*" or @type="file"]'))
                )
                file_input.send_keys(os.path.abspath(attachment_path))
                log_fn(f"  ✅ File uploaded: {os.path.basename(attachment_path)}")
                time.sleep(4)  # Wait for file to upload and preview to load
                
                # Add caption if message provided
                if message and message.strip():
                    try:
                        # Wait for preview to fully load
                        time.sleep(1)
                        
                        # Try multiple selectors for caption box
                        caption_box = None
                        caption_selectors = [
                            '//div[@contenteditable="true"][@role="textbox"]',
                            '//div[@contenteditable="true" and contains(@aria-label, "caption")]',
                            '//div[@contenteditable="true" and @data-tab="10"]',
                            '//div[@contenteditable="true" and contains(@class, "lexical")]',
                            '//div[contains(@aria-placeholder, "Add a caption")]',
                        ]
                        
                        for selector in caption_selectors:
                            try:
                                caption_box = driver.find_element(By.XPATH, selector)
                                log_fn(f"  ✅ Caption box found with selector: {selector[:40]}...")
                                break
                            except:
                                continue
                        
                        if caption_box:
                            # Scroll into view and focus
                            driver.execute_script("arguments[0].scrollIntoView(true);", caption_box)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].focus();", caption_box)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].click();", caption_box)
                            time.sleep(0.5)
                            
                            # Type caption
                            log_fn(f"  📝 Typing caption...")
                            lines = message.split('\n')
                            for i, line in enumerate(lines):
                                if line.strip():
                                    caption_box.send_keys(line)
                                if i < len(lines) - 1:
                                    caption_box.send_keys(Keys.SHIFT + Keys.ENTER)
                            
                            log_fn(f"  ✅ Caption added successfully!")
                        else:
                            log_fn(f"  ⚠️ Caption box not found - attachment will send without caption")
                            
                    except Exception as e:
                        log_fn(f"  ⚠️ Caption error: {str(e)[:80]}")
                
                # Wait a bit before sending
                time.sleep(2)
                log_fn(f"  🔍 Looking for send button...")
                
                # Try multiple methods to click send button
                send_clicked = False
                
                # Method 1: Try clicking green send button directly
                try:
                    send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                    driver.execute_script("arguments[0].scrollIntoView(true);", send_btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", send_btn)
                    log_fn(f"  ✅ Send clicked (JavaScript on icon)")
                    send_clicked = True
                except Exception as e1:
                    log_fn(f"  ⚠️ Method 1 failed: {str(e1)[:80]}")
                
                if not send_clicked:
                    # Method 2: Find button by data-testid or role
                    try:
                        send_btn = driver.find_element(By.XPATH, '//button[@data-testid="send" or contains(@aria-label, "Send")]')
                        send_btn.click()
                        log_fn(f"  ✅ Send clicked (button element)")
                        send_clicked = True
                    except Exception as e2:
                        log_fn(f"  ⚠️ Method 2 failed: {str(e2)[:80]}")
                
                if not send_clicked:
                    # Method 3: Find send button in footer area
                    try:
                        send_btn = driver.find_element(By.XPATH, '//footer//button[contains(@class, "compose")]')
                        driver.execute_script("arguments[0].click();", send_btn)
                        log_fn(f"  ✅ Send clicked (footer button)")
                        send_clicked = True
                    except Exception as e3:
                        log_fn(f"  ⚠️ Method 3 failed: {str(e3)[:80]}")
                
                if not send_clicked:
                    # Method 4: Press Enter in caption box
                    log_fn(f"  ⚠️ Trying Enter key...")
                    try:
                        caption_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"]')
                        caption_box.send_keys(Keys.ENTER)
                        log_fn(f"  ✅ Enter key pressed")
                        send_clicked = True
                    except Exception as e4:
                        log_fn(f"  ⚠️ Method 4 failed: {str(e4)[:80]}")
                
                if not send_clicked:
                    log_fn(f"  ❌ ALL METHODS FAILED - Message not sent!")
                else:
                    time.sleep(3)  # Wait for message to send
                    log_fn(f"✅ WhatsApp message with attachment sent to {phone}")
                
            except Exception as e:
                log_fn(f"  ❌ Attachment failed, sending text only: {e}")
                # Fallback: send text without attachment
                input_box = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                )
                input_box.click()
                time.sleep(0.3)
                lines = message.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        input_box.send_keys(line)
                    if i < len(lines) - 1:
                        input_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.5)
                input_box.send_keys(Keys.ENTER)
                log_fn(f"✅ WhatsApp text message sent to {phone} (attachment failed)")
        else:
            # No attachment - send text only
            if not message or not message.strip():
                log_fn(f"❌ No message to send for {phone}")
                return False
            
            input_box.click()
            time.sleep(0.3)
            
            # Split message by lines and send with proper formatting
            lines = message.split('\n')
            for i, line in enumerate(lines):
                if line.strip():  # Only send non-empty lines
                    input_box.send_keys(line)
                # Add line break except for the last line
                if i < len(lines) - 1:
                    input_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            time.sleep(0.5)
            input_box.send_keys(Keys.ENTER)
            log_fn(f"✅ WhatsApp message sent to {phone}")
        
        # Countdown delay to prevent account flagging (using user-configured delay)
        for remaining in range(delay_seconds, 0, -1):
            if stop_event.is_set():
                break
            log_fn(f"  ⏳ Waiting {remaining} seconds before next message...")
            time.sleep(1)
            
            # Keep session alive by checking page title every 10 seconds
            if remaining % 10 == 0:
                try:
                    driver.title  # This keeps the connection alive
                except:
                    log_fn(f"  ⚠️ Browser connection check failed")
        
        return True

    except Exception as e:
        log_fn(f"❌ Failed to send WhatsApp to {phone}: {e}")
        return False

# --- Email sending via SMTP with attachment support ---
def send_email_smtp(email_to, subject, body, sender_email, sender_password, log_fn, stop_event, attachment_path=None):
    """
    Send an email via SMTP (Gmail/Outlook) with optional attachment.
    
    Args:
        email_to: str, recipient email address
        subject: str, email subject line
        body: str, email body (plain text or HTML)
        sender_email: str, sender email address
        sender_password: str, sender app password
        log_fn: callable, logging function
        stop_event: threading.Event, used to stop execution gracefully
        attachment_path: str, optional path to file to attach
    
    Returns:
        bool, True if sent successfully, False otherwise
    """
    if stop_event.is_set():
        log_fn("Stopped before sending email.")
        return False
    
    try:
        # Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_to):
            log_fn(f"❌ Invalid email format: {email_to}")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email_to
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach file if provided
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                msg.attach(part)
                log_fn(f"  📎 Attached: {os.path.basename(attachment_path)}")
            except Exception as e:
                log_fn(f"  ⚠️ Attachment failed: {e}")
        
        # Detect SMTP server based on email domain
        domain = sender_email.split('@')[1].lower()
        if 'gmail' in domain:
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
        elif 'outlook' in domain or 'hotmail' in domain:
            smtp_server = 'smtp-mail.outlook.com'
            smtp_port = 587
        else:
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email_to, msg.as_string())
        server.quit()
        
        log_fn(f"✅ Email sent to {email_to}")
        
        # Short delay between emails
        for remaining in range(2, 0, -1):
            if stop_event.is_set():
                break
            log_fn(f"  ⏳ Waiting {remaining} seconds...")
            time.sleep(1)
        
        return True
    
    except smtplib.SMTPAuthenticationError:
        log_fn(f"❌ Authentication failed. Check email/password (use App Password for Gmail).")
        return False
    except smtplib.SMTPException as e:
        log_fn(f"❌ SMTP error for {email_to}: {e}")
        return False
    except Exception as e:
        log_fn(f"❌ Failed to send email to {email_to}: {e}")
        return False

# --- Global UI Components Storage ---
attachment_entry = None
email_config_section = None
platform_var = None

def update_ui_for_platform():
    """Show/hide UI elements based on selected platform"""
    global email_config_section
    platform = platform_var.get()
    
    if platform == "Email":
        email_config_section.pack(fill=tk.X, pady=12, after=section_platform)
    else:
        email_config_section.pack_forget()

# ================= MODERN REACTIVE GUI =================
root = tk.Tk()
root.title("🚀 growHigh - Bulk Sender (WhatsApp & Email)")
root.geometry("1000x950")
root.resizable(True, True)
root.minsize(800, 750)

# ===== ULTRA MODERN COLOR SCHEME =====
BG_PRIMARY = "#0D1117"
BG_SECONDARY = "#161B22"
CARD_BG = "#0D1117"
CARD_BORDER = "#30363D"
FG_PRIMARY = "#E6EDF3"
FG_SECONDARY = "#8B949E"
ACCENT_MAIN = "#58A6FF"
ACCENT_GREEN = "#3FB950"
ACCENT_RED = "#F85149"
ACCENT_YELLOW = "#D29922"
HOVER_BG = "#21262D"
BUTTON_HOVER = "#238636"

root.configure(bg=BG_PRIMARY)

# Modern Fonts
FONT_TITLE = ("Consolas", 28, "bold")
FONT_SUBTITLE = ("Consolas", 11)
FONT_LABEL = ("Consolas", 11, "bold")
FONT_TEXT = ("Consolas", 10)
FONT_LOG = ("Courier New", 9)

# ===== MAIN LAYOUT =====
# Top banner
banner = tk.Frame(root, bg=ACCENT_MAIN, height=3)
banner.pack(fill=tk.X, pady=0)

# Header
header = tk.Frame(root, bg=BG_SECONDARY, height=90)
header.pack(fill=tk.X, padx=0, pady=0)
header.pack_propagate(False)

header_content = tk.Frame(header, bg=BG_SECONDARY)
header_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)

title = tk.Label(header_content, text="🚀 growHigh", font=FONT_TITLE, bg=BG_SECONDARY, fg=ACCENT_GREEN)
title.pack(anchor=tk.W)
subtitle = tk.Label(header_content, text="Professional Bulk Sender - WhatsApp & Email with Attachments", font=FONT_SUBTITLE, bg=BG_SECONDARY, fg=FG_SECONDARY)
subtitle.pack(anchor=tk.W, pady=(3, 0))

# Separator line
sep1 = tk.Frame(root, bg=CARD_BORDER, height=1)
sep1.pack(fill=tk.X, padx=0)

# Main scrollable container
main_container = tk.Frame(root, bg=BG_PRIMARY)
main_container.pack(fill=tk.BOTH, expand=True)

# Create canvas for scrolling
canvas = tk.Canvas(main_container, bg=BG_PRIMARY, highlightthickness=0)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add scrollbar
scrollbar = tk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview, bg=BG_SECONDARY)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Configure canvas
canvas.configure(yscrollcommand=scrollbar.set)

# Create frame inside canvas
content_frame = tk.Frame(canvas, bg=BG_PRIMARY)
canvas_window = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

# Bind canvas resize
def on_canvas_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    # Make content frame width match canvas width
    canvas.itemconfig(canvas_window, width=event.width)

canvas.bind('<Configure>', on_canvas_configure)
content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Enable mouse wheel scrolling
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

# Add padding to content
content_inner = tk.Frame(content_frame, bg=BG_PRIMARY)
content_inner.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

# Replace content_frame with content_inner for all sections below
content_frame = content_inner

# ===== SECTION 0: PLATFORM SELECTOR =====
section_platform = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section_platform.pack(fill=tk.X, pady=12)

def on_section_enter(event, section):
    section.config(highlightbackground=ACCENT_MAIN, highlightthickness=2)

def on_section_leave(event, section):
    section.config(highlightbackground=CARD_BORDER, highlightthickness=1)

section_platform.bind("<Enter>", lambda e: on_section_enter(e, section_platform))
section_platform.bind("<Leave>", lambda e: on_section_leave(e, section_platform))

s_platform_header = tk.Frame(section_platform, bg=CARD_BG)
s_platform_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_platform_header, text="🔀", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_platform_header, text="Select Platform", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)

# Platform selection
platform_frame = tk.Frame(section_platform, bg=CARD_BG)
platform_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

platform_var = tk.StringVar(value="WhatsApp")

def on_platform_change(*args):
    selected = platform_var.get()
    log(f"📱 Platform switched to: {selected}")
    update_ui_for_platform()

platform_var.trace('w', on_platform_change)

platforms = ["WhatsApp", "Email"]
for platform in platforms:
    platform_rb = tk.Radiobutton(
        platform_frame, text=f"  {platform}",
        variable=platform_var, value=platform,
        bg=CARD_BG, fg=FG_PRIMARY, selectcolor=BG_SECONDARY,
        activebackground=HOVER_BG, activeforeground=ACCENT_GREEN,
        font=FONT_TEXT, highlightthickness=0
    )
    platform_rb.pack(side=tk.LEFT, padx=10, pady=5)

# ===== SECTION 0.5: EMAIL CREDENTIALS (Hidden by default) =====
email_config_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)

email_config_section.bind("<Enter>", lambda e: on_section_enter(e, email_config_section))
email_config_section.bind("<Leave>", lambda e: on_section_leave(e, email_config_section))

s_email_header = tk.Frame(email_config_section, bg=CARD_BG)
s_email_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_email_header, text="🔐", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_email_header, text="Email Sender Credentials", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s_email_header, text="Enter your Gmail/Outlook credentials", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

email_input_frame = tk.Frame(email_config_section, bg=CARD_BG)
email_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

tk.Label(email_input_frame, text="Sender Email:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
email_sender_entry = tk.Entry(email_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
email_sender_entry.pack(fill=tk.X, ipady=6, pady=(0, 10))

tk.Label(email_input_frame, text="App Password (Gmail: 16-char App Password):", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
email_password_entry = tk.Entry(email_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, show="•")
email_password_entry.pack(fill=tk.X, ipady=6, pady=(0, 10))

tk.Label(email_input_frame, text="Email Subject:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(anchor=tk.W, pady=(0, 3))
email_subject_entry = tk.Entry(email_input_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
email_subject_entry.pack(fill=tk.X, ipady=6, pady=(0, 15))

# ===== SECTION 1: CSV FILE INPUT =====
section1 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section1.pack(fill=tk.X, pady=12)

section1.bind("<Enter>", lambda e: on_section_enter(e, section1))
section1.bind("<Leave>", lambda e: on_section_leave(e, section1))

s1_header = tk.Frame(section1, bg=CARD_BG)
s1_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s1_header, text="📂", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s1_header, text="Import Contacts (CSV)", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s1_header, text="Select a CSV file with phone numbers", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

s1_input = tk.Frame(section1, bg=CARD_BG)
s1_input.pack(fill=tk.X, padx=20, pady=(0, 15))

csv_entry = tk.Entry(s1_input, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)

def on_csv_focus_in(event):
    csv_entry.config(bg=BG_SECONDARY)

def on_csv_focus_out(event):
    csv_entry.config(bg=HOVER_BG)

csv_entry.bind("<FocusIn>", on_csv_focus_in)
csv_entry.bind("<FocusOut>", on_csv_focus_out)

def browse_csv():
    path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
    if path:
        csv_entry.delete(0, tk.END)
        csv_entry.insert(0, path)
        log(f"✅ CSV loaded: {path}")

browse_btn = tk.Button(s1_input, text="📁 BROWSE", command=browse_csv, bg=ACCENT_GREEN, fg="#000000", 
                       font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
browse_btn.pack(side=tk.LEFT)

def on_browse_enter(event):
    browse_btn.config(bg=BUTTON_HOVER, fg="#FFF")

def on_browse_leave(event):
    browse_btn.config(bg=ACCENT_GREEN, fg="#000000")

browse_btn.bind("<Enter>", on_browse_enter)
browse_btn.bind("<Leave>", on_browse_leave)

# ===== SECTION 1.5: FILE ATTACHMENT (OPTIONAL) =====
section_attachment = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section_attachment.pack(fill=tk.X, pady=12)

section_attachment.bind("<Enter>", lambda e: on_section_enter(e, section_attachment))
section_attachment.bind("<Leave>", lambda e: on_section_leave(e, section_attachment))

sa_header = tk.Frame(section_attachment, bg=CARD_BG)
sa_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(sa_header, text="📎", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(sa_header, text="Attach File (Optional)", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(sa_header, text="Select a file to send with each message (PDF, PNG, JPG, etc.)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

sa_input = tk.Frame(section_attachment, bg=CARD_BG)
sa_input.pack(fill=tk.X, padx=20, pady=(0, 15))

attachment_entry = tk.Entry(sa_input, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
attachment_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)

def on_attachment_focus_in(event):
    attachment_entry.config(bg=BG_SECONDARY)

def on_attachment_focus_out(event):
    attachment_entry.config(bg=HOVER_BG)

attachment_entry.bind("<FocusIn>", on_attachment_focus_in)
attachment_entry.bind("<FocusOut>", on_attachment_focus_out)

def browse_attachment():
    path = filedialog.askopenfilename(
        filetypes=[
            ("All Files", "*.*"),
            ("PDF files", "*.pdf"),
            ("Image files", "*.png;*.jpg;*.jpeg;*.gif"),
            ("Documents", "*.doc;*.docx;*.xls;*.xlsx")
        ]
    )
    if path:
        attachment_entry.delete(0, tk.END)
        attachment_entry.insert(0, path)
        log(f"✅ Attachment selected: {os.path.basename(path)}")

browse_attachment_btn = tk.Button(sa_input, text="📎 BROWSE FILE", command=browse_attachment, bg=ACCENT_YELLOW, fg="#000000", 
                       font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
browse_attachment_btn.pack(side=tk.LEFT, padx=(0, 10))

def on_browse_attachment_enter(event):
    browse_attachment_btn.config(bg="#E8B923", fg="#000000")

def on_browse_attachment_leave(event):
    browse_attachment_btn.config(bg=ACCENT_YELLOW, fg="#000000")

browse_attachment_btn.bind("<Enter>", on_browse_attachment_enter)
browse_attachment_btn.bind("<Leave>", on_browse_attachment_leave)

# Clear attachment button
clear_attachment_btn = tk.Button(sa_input, text="✖ CLEAR", command=lambda: (attachment_entry.delete(0, tk.END), log("🗑️ Attachment cleared")), 
                       bg=ACCENT_RED, fg="white", font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=15, pady=8, cursor="hand2")
clear_attachment_btn.pack(side=tk.LEFT)

def on_clear_attachment_enter(event):
    clear_attachment_btn.config(bg="#E03C3C")

def on_clear_attachment_leave(event):
    clear_attachment_btn.config(bg=ACCENT_RED)

clear_attachment_btn.bind("<Enter>", on_clear_attachment_enter)
clear_attachment_btn.bind("<Leave>", on_clear_attachment_leave)

# ===== SECTION 1.7: ADVANCED SETTINGS (WhatsApp) =====
section_advanced = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section_advanced.pack(fill=tk.X, pady=12)

section_advanced.bind("<Enter>", lambda e: on_section_enter(e, section_advanced))
section_advanced.bind("<Leave>", lambda e: on_section_leave(e, section_advanced))

adv_header = tk.Frame(section_advanced, bg=CARD_BG)
adv_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(adv_header, text="⚙️", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(adv_header, text="Advanced Settings", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(adv_header, text="Configure delay time, row range, and filters", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

adv_content = tk.Frame(section_advanced, bg=CARD_BG)
adv_content.pack(fill=tk.X, padx=20, pady=(10, 15))

# Skip 01 numbers checkbox
skip_01_var = tk.BooleanVar(value=False)
skip_01_check = tk.Checkbutton(
    adv_content, text="  Skip phone numbers starting with 01",
    variable=skip_01_var,
    bg=CARD_BG, fg=FG_PRIMARY, selectcolor=BG_SECONDARY,
    activebackground=HOVER_BG, activeforeground=ACCENT_GREEN,
    font=FONT_TEXT, highlightthickness=0
)
skip_01_check.pack(anchor=tk.W, pady=(0, 15))

# Delay time configuration
delay_frame = tk.Frame(adv_content, bg=CARD_BG)
delay_frame.pack(fill=tk.X, pady=(0, 15))

tk.Label(delay_frame, text="Message Delay (seconds):", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 10))
delay_entry = tk.Entry(delay_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, width=10)
delay_entry.insert(0, "60")  # Default 60 seconds
delay_entry.pack(side=tk.LEFT, ipady=5)
tk.Label(delay_frame, text="(Time between messages)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(10, 0))

# Row range configuration
range_frame = tk.Frame(adv_content, bg=CARD_BG)
range_frame.pack(fill=tk.X, pady=(0, 5))

tk.Label(range_frame, text="Send to rows:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(range_frame, text="From:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 5))
row_start_entry = tk.Entry(range_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, width=8)
row_start_entry.insert(0, "1")  # Default start from row 1
row_start_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 10))

tk.Label(range_frame, text="To:", font=FONT_TEXT, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT, padx=(0, 5))
row_end_entry = tk.Entry(range_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, width=8)
row_end_entry.insert(0, "999999")  # Default to very large number (all rows)
row_end_entry.pack(side=tk.LEFT, ipady=5)
tk.Label(range_frame, text="(Leave 'To' as large number for all rows)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(10, 0))

# ===== SECTION 2: MESSAGE COMPOSER =====
section2 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section2.pack(fill=tk.BOTH, expand=True, pady=12)

section2.bind("<Enter>", lambda e: on_section_enter(e, section2))
section2.bind("<Leave>", lambda e: on_section_leave(e, section2))

s2_header = tk.Frame(section2, bg=CARD_BG)
s2_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s2_header, text="💬", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s2_header, text="Compose Your Message", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s2_header, text="Type your message here (use \\n for line breaks)", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

msg_text = tk.Text(section2, height=10, width=80, wrap=tk.WORD, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, 
                   relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=12, pady=10)
msg_text.pack(padx=20, pady=(10, 10), fill=tk.BOTH, expand=True)

def update_char_count(event=None):
    char_count = len(msg_text.get("1.0", tk.END)) - 1
    char_label.config(text=f"Characters: {char_count}")

msg_text.bind("<KeyRelease>", update_char_count)

char_label = tk.Label(section2, text="Characters: 0", font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_YELLOW)
char_label.pack(anchor=tk.E, padx=20, pady=(0, 15))

# ===== SECTION 3: ACTION BUTTONS =====
button_section = tk.Frame(content_frame, bg=BG_PRIMARY)
button_section.pack(fill=tk.X, pady=15)

start_btn = tk.Button(button_section, text="▶  START SENDING", bg=ACCENT_GREEN, fg="#000000",
                     font=("Consolas", 11, "bold"), relief=tk.FLAT, bd=0, padx=30, pady=12, cursor="hand2")
start_btn.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

stop_btn = tk.Button(button_section, text="⏹  STOP", bg=ACCENT_RED, fg="white",
                    font=("Consolas", 11, "bold"), relief=tk.FLAT, bd=0, padx=30, pady=12, cursor="hand2")
stop_btn.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

def on_start_enter(event):
    start_btn.config(bg=BUTTON_HOVER)

def on_start_leave(event):
    start_btn.config(bg=ACCENT_GREEN, fg="#000000")

def on_stop_enter(event):
    stop_btn.config(bg="#E03C3C")

def on_stop_leave(event):
    stop_btn.config(bg=ACCENT_RED)

start_btn.bind("<Enter>", on_start_enter)
start_btn.bind("<Leave>", on_start_leave)
stop_btn.bind("<Enter>", on_stop_enter)
stop_btn.bind("<Leave>", on_stop_leave)

# ===== SECTION 4: ACTIVITY LOG =====
section3 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section3.pack(fill=tk.BOTH, expand=True, pady=12)

section3.bind("<Enter>", lambda e: on_section_enter(e, section3))
section3.bind("<Leave>", lambda e: on_section_leave(e, section3))

s3_header = tk.Frame(section3, bg=CARD_BG)
s3_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s3_header, text="📋", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s3_header, text="Activity Log", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)

log_box = scrolledtext.ScrolledText(section3, height=12, font=FONT_LOG, bg=BG_SECONDARY, fg=ACCENT_GREEN, 
                                    state=tk.DISABLED, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=12, pady=10)
log_box.pack(padx=20, pady=(5, 15), fill=tk.BOTH, expand=True)

# ===== SECTION 5: STATISTICS =====
section4 = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
section4.pack(fill=tk.X, pady=12)

section4.bind("<Enter>", lambda e: on_section_enter(e, section4))
section4.bind("<Leave>", lambda e: on_section_leave(e, section4))

s4_header = tk.Frame(section4, bg=CARD_BG)
s4_header.pack(fill=tk.X, padx=20, pady=(15, 5))
tk.Label(s4_header, text="📊", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s4_header, text="Statistics", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)

stats_frame = tk.Frame(section4, bg=CARD_BG)
stats_frame.pack(fill=tk.X, padx=20, pady=(5, 15))

# Stat boxes
def create_stat_box(parent, label, color):
    box = tk.Frame(parent, bg=HOVER_BG, relief=tk.FLAT, bd=0)
    box.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.BOTH)
    tk.Label(box, text=label, font=("Consolas", 9), bg=HOVER_BG, fg=FG_SECONDARY).pack(pady=(8, 2))
    value_label = tk.Label(box, text="0", font=("Consolas", 20, "bold"), bg=HOVER_BG, fg=color)
    value_label.pack(pady=(2, 8))
    return value_label

stats_sent = create_stat_box(stats_frame, "✅ Sent", ACCENT_GREEN)
stats_failed = create_stat_box(stats_frame, "❌ Failed", ACCENT_RED)
stats_pending = create_stat_box(stats_frame, "⏳ Pending", ACCENT_YELLOW)

# logging helper (thread-safe)
def log(msg):
    def _append():
        log_box.configure(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        log_box.insert(tk.END, f"[{timestamp}] {msg}\n")
        log_box.see(tk.END)
        log_box.configure(state=tk.DISABLED)
    root.after(0, _append)

# stop event for threads
stop_event = threading.Event()

# Worker thread
def start_sending():
    if start_btn['state'] == tk.DISABLED:
        return
    csv_path = csv_entry.get().strip()
    if not csv_path or not os.path.exists(csv_path):
        messagebox.showerror("CSV not found", f"CSV file not found: {csv_path}")
        return
    message = msg_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showerror("No message", "Please type a message to send.")
    message = msg_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showerror("No message", "Please type a message to send.")
        return

    stop_event.clear()
    start_btn.config(state=tk.DISABLED)

    def worker():
        driver = None
        sent_count = 0
        failed_count = 0
        
        # Get platform and attachment
        platform = platform_var.get()
        attachment_path = attachment_entry.get().strip() if attachment_entry.get().strip() else None
        
        # Get advanced settings
        skip_01_numbers = skip_01_var.get()
        
        # Get delay time
        try:
            delay_seconds = int(delay_entry.get().strip())
            if delay_seconds < 1:
                delay_seconds = 60
        except ValueError:
            delay_seconds = 60
            log("⚠️ Invalid delay value, using default 60 seconds")
        
        # Get row range
        try:
            row_start = int(row_start_entry.get().strip())
            if row_start < 1:
                row_start = 1
        except ValueError:
            row_start = 1
            log("⚠️ Invalid start row, using row 1")
        
        try:
            row_end = int(row_end_entry.get().strip())
        except ValueError:
            row_end = 999999
            log("⚠️ Invalid end row, processing all rows")
        
        # Validate email credentials if using Email platform
        if platform == "Email":
            sender_email = email_sender_entry.get().strip()
            sender_password = email_password_entry.get().strip()
            email_subject = email_subject_entry.get().strip()
            
            if not sender_email or not sender_password:
                messagebox.showerror("Missing Credentials", "Please enter email and password.")
                start_btn.config(state=tk.NORMAL)
                return
            
            if not email_subject:
                email_subject = "Message from growHigh"
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            log(f"❌ CSV Error: {e}")
            start_btn.config(state=tk.NORMAL)
            return

        # Extract contacts based on platform
        rows = []
        
        if platform == "Email":
            # Email mode: look for email column
            email_col = None
            name_col = None
            
            for c in df.columns:
                if c.lower() in ('email', 'email_address', 'mail', 'recipient'):
                    email_col = c
                    break
            
            for c in df.columns:
                if c.lower() in ('name', 'contact_name', 'fullname', 'full_name', 'customer_name'):
                    name_col = c
                    break
            
            if email_col:
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    email_raw = str(r[email_col]).strip()
                    
                    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_raw):
                        log(f"⚠️ Skipping invalid email: {email_raw}")
                        continue
                    
                    name = "Friend"
                    if name_col and not pd.isna(r[name_col]):
                        name = str(r[name_col]).strip()
                    
                    # Personalize message with name
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {name},\n\n{personalized_msg}"
                    rows.append((email_raw, personalized_msg, name))
            else:
                # Fallback: use first column as email
                first_col = df.columns[0]
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    email_raw = str(r[first_col]).strip()
                    
                    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_raw):
                        log(f"⚠️ Skipping invalid email: {email_raw}")
                        continue
                    
                    name = "Friend"
                    if len(df.columns) > 1:
                        second_col = df.columns[1]
                        if not pd.isna(r[second_col]):
                            name = str(r[second_col]).strip()
                    
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {name},\n\n{personalized_msg}"
                    rows.append((email_raw, personalized_msg, name))
        
        else:
            # WhatsApp mode: look for phone column
            phone_col = None
            name_col = None
            
            for c in df.columns:
                if c.lower() in ('phone','phone_number','phone_number_e164','number'):
                    phone_col = c
                    break
            
            for c in df.columns:
                if c.lower() in ('name', 'contact_name', 'fullname', 'full_name', 'customer_name'):
                    name_col = c
                    break
            
            if phone_col:
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    phone_raw = str(r[phone_col]).strip()
                    phone_clean = extract_phone_digits(phone_raw)
                    
                    # Skip numbers starting with 01
                    if skip_01_numbers and phone_clean.startswith("01"):
                        log(f"⏭️ Skipping number starting with 01: {phone_raw}")
                        continue
                    
                    name = "Friend"
                    if name_col and not pd.isna(r[name_col]):
                        name = str(r[name_col]).strip()
                    
                    if phone_clean:
                        personalized_msg = f"Hello {name},\n\n{message}"
                        rows.append((phone_clean, personalized_msg, name))
                    else:
                        log(f"⚠️ Skipping invalid phone: {phone_raw}")
            else:
                # fallback: use first column as phone
                first_col = df.columns[0]
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    phone_raw = str(r[first_col]).strip()
                    phone_clean = extract_phone_digits(phone_raw)
                    
                    # Skip numbers starting with 01
                    if skip_01_numbers and phone_clean.startswith("01"):
                        log(f"⏭️ Skipping number starting with 01: {phone_raw}")
                        continue
                    
                    name = "Sir/Ma'am"
                    if len(df.columns) > 1:
                        second_col = df.columns[1]
                        if not pd.isna(r[second_col]):
                            name = str(r[second_col]).strip()
                    
                    if phone_clean:
                        personalized_msg = f"Hello {name},\n\n{message}"
                        rows.append((phone_clean, personalized_msg, name))
                    else:
                        log(f"⚠️ Skipping invalid phone: {phone_raw}")

        if not rows:
            contact_type = "emails" if platform == "Email" else "phone numbers"
            log(f"❌ No valid {contact_type} found.")
            start_btn.config(state=tk.NORMAL)
            return

        log(f"🚀 Starting broadcast to {len(rows)} contacts via {platform}...")
        log(f"📂 CSV File: {csv_path}")
        log(f"📊 Row Range: {row_start} to {row_end}")
        if platform == "WhatsApp":
            log(f"⏱️ Delay between messages: {delay_seconds} seconds")
            if skip_01_numbers:
                log(f"⏭️ Skipping numbers starting with 01: ENABLED")
        if attachment_path:
            log(f"📎 Attachment: {os.path.basename(attachment_path)}")

        # Create driver for WhatsApp
        if platform == "WhatsApp":
            try:
                driver = create_driver()
            except Exception as e:
                log(f"❌ Driver error: {e}")
                start_btn.config(state=tk.NORMAL)
                return

            # Open WhatsApp Web
            driver.get("https://web.whatsapp.com")
            time.sleep(2)
            if "web.whatsapp.com" in driver.current_url and "qr" in driver.page_source.lower():
                log("📱 Please scan QR code in WhatsApp Web. Waiting 20s...")
                time.sleep(20)

        sent_count = 0
        failed_list = []
        
        # Sending loop based on platform
        if platform == "Email":
            # Email sending loop
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_email, msg, name = row_data
                log(f"[{i}/{len(rows)}] → {target_email} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_email_smtp(target_email, email_subject, msg, sender_email, sender_password, log, stop_event, attachment_path)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_email)
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_email}: {e}")
                    failed_list.append(target_email)
                    stats_failed.config(text=str(len(failed_list)))
                
                if stop_event.is_set():
                    break
        
        else:
            # WhatsApp sending loop
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_phone, msg, name = row_data
                log(f"[{i}/{len(rows)}] → {target_phone} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_message_whatsapp(driver, target_phone, msg, log, stop_event, attachment_path, delay_seconds)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_phone)
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_phone}: {e}")
                    failed_list.append(target_phone)
                    stats_failed.config(text=str(len(failed_list)))
                
                # Delay is now handled inside send_message_whatsapp function with countdown
                
                if stop_event.is_set():
                    break

        log(f"✅ COMPLETE: {sent_count}/{len(rows)} sent | ❌ Failed: {len(failed_list)}")
        if failed_list:
            log("📌 Failed contacts: " + ", ".join(failed_list[:5]))
        
        if platform == "WhatsApp":
            try:
                driver.quit()
            except Exception:
                pass
        
        start_btn.config(state=tk.NORMAL)
        stats_pending.config(text="0")

    threading.Thread(target=worker, daemon=True).start()

def stop_sending():
    stop_event.set()
    log("⏹ Stop requested. Completing current message...")

start_btn.config(command=start_sending)
stop_btn.config(command=stop_sending)

log("🎉 App ready – select CSV, type message, and click START SENDING")
root.mainloop()