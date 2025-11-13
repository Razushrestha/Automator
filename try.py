# auto_messenger_ultra_fast_messenger_only.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import random
import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# ==================== CONFIG ====================
PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

HEADLESS = False
MIN_DELAY = 3
MAX_DELAY = 7
WAIT_TIMEOUT = 15
FAST_WAIT = 4
POST_CLICK_WAIT = 0.8
# ===============================================

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
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    except Exception:
        pass
    return driver

# --- Messenger automation ---
def send_message_messenger(driver, username, message, log_fn, stop_event):
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    short_wait = WebDriverWait(driver, FAST_WAIT)
    actions = ActionChains(driver)

    driver.get(f"https://www.messenger.com/t/{username}")
    try:
        short_wait.until(EC.presence_of_element_located((By.XPATH, "//h1 | //h2 | //div[contains(@class, 'x1lliihq')]")))
    except Exception:
        pass

    # Try clicking “Continue chatting”
    fast_sels = [
        "//button[.//span[normalize-space()='Continue chatting']]",
        "//button[normalize-space()='Continue chatting']",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue chatting')]"
    ]
    clicked = False
    for sel in fast_sels:
        if stop_event.is_set():
            return False
        try:
            btn = short_wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.05)
            actions.move_to_element(btn).click().perform()
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        try:
            fb = short_wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(., 'Continue')]")))
            actions.move_to_element(fb).click().perform()
        except Exception:
            pass

    time.sleep(POST_CLICK_WAIT)

    msg_sels = [
        "//div[@role='textbox' and @contenteditable='true']",
        "//div[@aria-label='Message' and @role='textbox']"
    ]
    msg_box = None
    for sel in msg_sels:
        if stop_event.is_set():
            return False
        try:
            msg_box = short_wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
            break
        except Exception:
            continue
    if not msg_box:
        log_fn(f"  ❌ No message box for {username}")
        return False

    try:
        msg_box.click()
        time.sleep(0.15)
        actions.move_to_element(msg_box).click().key_down("\ue009").send_keys("a").key_up("\ue009").send_keys("\b").perform()
    except Exception:
        pass

    try:
        msg_box.send_keys(message + "\n")
        log_fn(f"  ✅ Sent to {username}")
        return True
    except Exception as e:
        log_fn(f"  ❌ Send failed {username}: {e}")
        return False

# ================= GUI =================
root = tk.Tk()
root.title("📨 Auto Messenger (Facebook Messenger Only)")
root.geometry("650x700")
root.resizable(False, False)

def log(msg):
    def _append():
        log_box.configure(state=tk.NORMAL)
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        log_box.configure(state=tk.DISABLED)
    root.after(0, _append)

stop_event = threading.Event()

tk.Label(root, text="Messenger Bulk Sender", font=("Arial", 12, "bold")).pack(pady=8)

tk.Label(root, text="CSV File (must contain 'username' column):", font=("Arial", 10)).pack(pady=8)
csv_frame = tk.Frame(root)
csv_entry = tk.Entry(csv_frame, width=55)
csv_entry.pack(side=tk.LEFT, padx=5)

def browse_csv():
    path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if path:
        csv_entry.delete(0, tk.END)
        csv_entry.insert(0, path)

tk.Button(csv_frame, text="Browse", command=browse_csv).pack(side=tk.LEFT)
csv_frame.pack()

tk.Label(root, text="Message:", font=("Arial", 10)).pack(pady=8)
msg_text = tk.Text(root, height=7, width=70, wrap=tk.WORD)
msg_text.pack(pady=5)

btn_frame = tk.Frame(root)
start_btn = tk.Button(btn_frame, text="Start Sending", bg="#1877F2", fg="white", font=("Arial", 10, "bold"))
stop_btn = tk.Button(btn_frame, text="Stop", bg="red", fg="white")
start_btn.pack(side=tk.LEFT, padx=12)
stop_btn.pack(side=tk.LEFT, padx=12)
btn_frame.pack(pady=12)

log_box = scrolledtext.ScrolledText(root, height=20, font=("Courier", 9), state=tk.DISABLED)
log_box.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

def start_sending():
    if start_btn['state'] == tk.DISABLED:
        return
    csv_path = csv_entry.get().strip()
    if not os.path.exists(csv_path):
        messagebox.showerror("CSV not found", f"CSV file not found: {csv_path}")
        return
    message = msg_text.get("1.0", tk.END).strip()
    if not message:
        messagebox.showerror("No message", "Please type a message to send.")
        return

    stop_event.clear()
    start_btn.config(state=tk.DISABLED)
    log(f"Starting Messenger messages with {csv_path} ...")

    def worker():
        driver = None
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            log(f"CSV Error: {e}")
            start_btn.config(state=tk.NORMAL)
            return

        rows = []
        if {'username', 'message'}.issubset(df.columns):
            df2 = df[['username', 'message']].dropna()
            for _, r in df2.iterrows():
                rows.append((str(r['username']).strip(), str(r['message']).strip()))
        elif 'username' in df.columns:
            for _, r in df.iterrows():
                rows.append((str(r['username']).strip(), message))
        else:
            log("CSV missing 'username' column for Messenger.")
            start_btn.config(state=tk.NORMAL)
            return

        if not rows:
            log("No rows to send.")
            start_btn.config(state=tk.NORMAL)
            return

        try:
            driver = create_driver()
        except Exception as e:
            log(f"Driver error: {e}")
            start_btn.config(state=tk.NORMAL)
            return

        driver.get("https://www.messenger.com")
        time.sleep(2)
        if "login" in driver.current_url.lower():
            log("Please log in to Messenger in the opened browser. Waiting 20s...")
            time.sleep(20)

        sent = 0
        failed = []
        for i, (username, msg) in enumerate(rows, start=1):
            if stop_event.is_set():
                log("Stopped by user.")
                break
            log(f"[{i}/{len(rows)}] -> {username}")
            try:
                ok = send_message_messenger(driver, username, msg, log, stop_event)
                if ok:
                    sent += 1
                else:
                    failed.append(username)
            except Exception as e:
                log(f"  ERROR {username}: {e}")
                failed.append(username)

            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            log(f"  Sleeping {delay:.1f}s")
            for _ in range(int(delay*10)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
            if stop_event.is_set():
                break

        log(f"DONE: {sent}/{len(rows)} sent | Failed: {len(failed)}")
        if failed:
            log("Failed samples: " + ", ".join(failed[:5]))
        try:
            driver.quit()
        except Exception:
            pass
        start_btn.config(state=tk.NORMAL)

    threading.Thread(target=worker, daemon=True).start()

def stop_sending():
    stop_event.set()
    log("Stop requested. Waiting for current operation to finish...")

start_btn.config(command=start_sending)
stop_btn.config(command=stop_sending)

log("App ready – select CSV, type message, and click Start.")
root.mainloop()
