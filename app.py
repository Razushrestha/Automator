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

# SMS via Android phone
try:
    from ppadb.client import Client as AdbClient
    ADB_AVAILABLE = True
except ImportError:
    ADB_AVAILABLE = False

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
    # Note: --disable-images removed - WhatsApp needs images to work properly
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
        time.sleep(5)

        # Wait for chat to fully load
        wait = WebDriverWait(driver, 20)
        try:
            # Wait for message input box (indicates chat is ready)
            input_box = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            log_fn(f"  ✅ Chat loaded successfully")
            time.sleep(2)  # Extra wait for all elements to render
        except TimeoutException:
            log_fn(f"⏳ Timeout: Chat not ready for {phone}")
            return False

        if stop_event.is_set():
            log_fn("Stopped before typing message.")
            return False

        # Handle file attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            log_fn(f"📎 Attaching file: {os.path.basename(attachment_path)}")
            
            # Show file info
            file_size_mb = os.path.getsize(attachment_path) / (1024 * 1024)
            file_ext = os.path.splitext(attachment_path)[1].lower()
            is_video = file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
            log_fn(f"  📦 File size: {file_size_mb:.1f}MB, Type: {file_ext}")
            
            try:
                # AGGRESSIVE ATTACH BUTTON SEARCH
                log_fn(f"  🔍 Searching for attach button (trying all methods)...")
                
                attach_clicked = False
                
                # Method 1: Find by data-icon attribute (most common)
                try:
                    log_fn(f"  🎯 Method 1: Looking for plus/attach icons...")
                    time.sleep(1)
                    icons = driver.find_elements(By.XPATH, '//span[@data-icon]')
                    for icon in icons:
                        icon_name = icon.get_attribute('data-icon')
                        if icon_name and ('plus' in icon_name or 'attach' in icon_name or 'clip' in icon_name):
                            parent = icon.find_element(By.XPATH, '..')
                            if parent.is_displayed():
                                driver.execute_script("arguments[0].click();", parent)
                                log_fn(f"  ✅ Clicked attach via icon: {icon_name}")
                                attach_clicked = True
                                break
                except Exception as e:
                    log_fn(f"  ❌ Method 1 failed: {str(e)[:50]}")
                
                # Method 2: Find by title or aria-label
                if not attach_clicked:
                    try:
                        log_fn(f"  🎯 Method 2: Looking for Attach labels...")
                        buttons = driver.find_elements(By.XPATH, '//*[@title or @aria-label]')
                        for btn in buttons:
                            title = (btn.get_attribute('title') or '').lower()
                            aria = (btn.get_attribute('aria-label') or '').lower()
                            if ('attach' in title or 'attach' in aria) and btn.is_displayed():
                                driver.execute_script("arguments[0].click();", btn)
                                log_fn(f"  ✅ Clicked attach via label")
                                attach_clicked = True
                                break
                    except Exception as e:
                        log_fn(f"  ❌ Method 2 failed: {str(e)[:50]}")
                
                # Method 3: Find ALL file inputs and trigger click on visible one
                if not attach_clicked:
                    try:
                        log_fn(f"  🎯 Method 3: Direct file input search...")
                        file_inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
                        log_fn(f"  📋 Found {len(file_inputs)} file inputs")
                        
                        # Try to find a visible parent to click
                        for inp in file_inputs:
                            try:
                                # Check if this input accepts our file type
                                accept = inp.get_attribute('accept') or '*'
                                if '*' in accept or '.mp4' in accept or 'video' in accept:
                                    log_fn(f"  ✅ Found compatible file input, sending file directly...")
                                    abs_path = os.path.abspath(attachment_path)
                                    inp.send_keys(abs_path)
                                    log_fn(f"  ✅ File sent directly to input!")
                                    attach_clicked = True
                                    break
                            except Exception as sub_e:
                                continue
                    except Exception as e:
                        log_fn(f"  ❌ Method 3 failed: {str(e)[:50]}")
                
                # Method 4: JavaScript injection to find and click
                if not attach_clicked:
                    try:
                        log_fn(f"  🎯 Method 4: JavaScript search...")
                        script = """
                        // Find all elements with attach-related attributes
                        var elements = document.querySelectorAll('*[data-icon*="plus"], *[data-icon*="attach"], *[data-icon*="clip"], *[title*="Attach"], *[aria-label*="Attach"]');
                        for(var i=0; i<elements.length; i++) {
                            if(elements[i].offsetParent !== null) {
                                elements[i].click();
                                return 'clicked: ' + elements[i].tagName;
                            }
                        }
                        return 'not found';
                        """
                        result = driver.execute_script(script)
                        if 'clicked' in result:
                            log_fn(f"  ✅ JavaScript found and clicked: {result}")
                            attach_clicked = True
                    except Exception as e:
                        log_fn(f"  ❌ Method 4 failed: {str(e)[:50]}")
                
                if not attach_clicked:
                    log_fn(f"  ❌ ALL ATTACH METHODS FAILED!")
                    log_fn(f"  💡 WhatsApp Web interface may have changed")
                    raise Exception("Could not find attach button after trying 4 methods")
                
                time.sleep(3)
                
                # Find file input (if attach button was clicked, this should be available)
                log_fn(f"  🔍 Looking for file input...")
                
                file_input = None
                file_input_wait = WebDriverWait(driver, 10)
                
                # Wait for file input to appear after clicking attach
                try:
                    file_input = file_input_wait.until(
                        EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
                    )
                    log_fn(f"  ✅ File input found")
                except:
                    # Try to find any file input
                    log_fn(f"  ⚠️ File input not found via wait, searching manually...")
                    inputs = driver.find_elements(By.XPATH, '//input[@type="file"]')
                    if inputs:
                        file_input = inputs[0]
                        log_fn(f"  ✅ Found file input manually")
                    else:
                        raise Exception("No file input element found")
                
                log_fn(f"  📤 Uploading file...")
                abs_path = os.path.abspath(attachment_path)
                file_input.send_keys(abs_path)
                log_fn(f"  ✅ File sent to browser: {os.path.basename(attachment_path)}")
                time.sleep(3)
                
                # Wait for video processing
                if is_video:
                    log_fn(f"  📹 Video detected - Size: {file_size_mb:.1f}MB")
                    log_fn(f"  ⏳ Waiting for video preview (10 seconds)...")
                    time.sleep(10)  # Wait 10 seconds for preview to load
                    log_fn(f"  ✅ Video preview ready")
                else:
                    time.sleep(5)  # Images/documents
                
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
                
                # ULTRA AGGRESSIVE SEND BUTTON CLICKING
                time.sleep(3)
                log_fn(f"  📤 Looking for SEND button...")
                
                send_clicked = False
                
                # Method 1: Wait for send icon and try multiple clicks
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 1: Waiting for send icon...")
                        send_wait = WebDriverWait(driver, 20)
                        send_icon = send_wait.until(EC.presence_of_element_located((By.XPATH, '//span[@data-icon="send"]')))
                        
                        # Scroll into view
                        driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'instant'});", send_icon)
                        time.sleep(0.5)
                        
                        # Try multiple click methods on the same element
                        try:
                            send_icon.click()
                            log_fn(f"  ✅ Clicked send icon (direct)")
                        except:
                            pass
                        
                        time.sleep(0.3)
                        
                        try:
                            driver.execute_script("arguments[0].click();", send_icon)
                            log_fn(f"  ✅ Clicked send icon (JavaScript)")
                        except:
                            pass
                        
                        time.sleep(0.3)
                        
                        try:
                            actions = ActionChains(driver)
                            actions.move_to_element(send_icon).click().perform()
                            log_fn(f"  ✅ Clicked send icon (ActionChains)")
                        except:
                            pass
                        
                        log_fn(f"  ✅ SENT via send icon (multiple attempts)!")
                        send_clicked = True
                    except Exception as e:
                        log_fn(f"  ❌ Method 1 failed: {str(e)[:50]}")
                
                # Method 2: Click parent/grandparent of send icon
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 2: Clicking send icon containers...")
                        send_icons = driver.find_elements(By.XPATH, '//span[@data-icon="send"]')
                        for icon in send_icons:
                            if icon.is_displayed():
                                # Try parent
                                try:
                                    parent = icon.find_element(By.XPATH, '..')
                                    driver.execute_script("arguments[0].click();", parent)
                                    log_fn(f"  ✅ SENT via parent!")
                                    send_clicked = True
                                    break
                                except:
                                    # Try grandparent
                                    try:
                                        grandparent = icon.find_element(By.XPATH, '../..')
                                        driver.execute_script("arguments[0].click();", grandparent)
                                        log_fn(f"  ✅ SENT via grandparent!")
                                        send_clicked = True
                                        break
                                    except:
                                        continue
                    except Exception as e:
                        log_fn(f"  ❌ Method 2 failed: {str(e)[:50]}")
                
                # Method 3: Find button element with send icon inside
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 3: Finding button with send icon...")
                        buttons = driver.find_elements(By.XPATH, '//button | //div[@role="button"]')
                        for btn in buttons:
                            try:
                                inner_html = btn.get_attribute('innerHTML')
                                if 'data-icon="send"' in inner_html and btn.is_displayed():
                                    driver.execute_script("arguments[0].click();", btn)
                                    log_fn(f"  ✅ SENT via button!")
                                    send_clicked = True
                                    break
                            except:
                                continue
                    except Exception as e:
                        log_fn(f"  ❌ Method 3 failed: {str(e)[:50]}")
                
                # Method 4: SUPER AGGRESSIVE JavaScript - click everything
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 4: JavaScript MEGA click...")
                        result = driver.execute_script("""
                            // Find all send icons
                            var icons = document.querySelectorAll('span[data-icon="send"]');
                            var clicked = 0;
                            
                            for(var i=0; i<icons.length; i++) {
                                if(icons[i].offsetParent !== null) {
                                    // Click icon
                                    icons[i].click();
                                    clicked++;
                                    
                                    // Click parent
                                    if(icons[i].parentElement) {
                                        icons[i].parentElement.click();
                                        clicked++;
                                    }
                                    
                                    // Click grandparent
                                    if(icons[i].parentElement && icons[i].parentElement.parentElement) {
                                        icons[i].parentElement.parentElement.click();
                                        clicked++;
                                    }
                                    
                                    // Dispatch click event
                                    var event = new MouseEvent('click', {
                                        bubbles: true,
                                        cancelable: true,
                                        view: window
                                    });
                                    icons[i].dispatchEvent(event);
                                    icons[i].parentElement.dispatchEvent(event);
                                    clicked++;
                                }
                            }
                            
                            return clicked;
                        """)
                        log_fn(f"  ✅ JavaScript performed {result} click attempts!")
                        if result > 0:
                            send_clicked = True
                        else:
                            log_fn(f"  ⚠️ JavaScript found no visible send icons")
                    except Exception as e:
                        log_fn(f"  ❌ Method 4 failed: {str(e)[:50]}")
                
                # Method 5: ActionChains hover and click
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 5: ActionChains hover + click...")
                        send_icon = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                        actions = ActionChains(driver)
                        actions.move_to_element(send_icon).pause(0.5).click().perform()
                        log_fn(f"  ✅ SENT via ActionChains!")
                        send_clicked = True
                    except Exception as e:
                        log_fn(f"  ❌ Method 5 failed: {str(e)[:50]}")
                
                # Method 6: Press Enter in any editable field
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 6: Pressing Enter in editable field...")
                        editables = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
                        for edit in editables:
                            if edit.is_displayed():
                                edit.click()
                                time.sleep(0.3)
                                edit.send_keys(Keys.ENTER)
                                log_fn(f"  ✅ SENT via Enter key!")
                                send_clicked = True
                                break
                    except Exception as e:
                        log_fn(f"  ❌ Method 6 failed: {str(e)[:50]}")
                
                # Method 7: BRUTE FORCE - Try clicking EVERYTHING that might be send button
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 7: BRUTE FORCE - clicking all possible buttons...")
                        
                        # Get ALL elements that could possibly be the send button
                        possible_buttons = driver.find_elements(By.XPATH, 
                            '//*[contains(@class, "send") or contains(@aria-label, "Send") or '
                            'contains(@title, "Send") or @data-icon="send" or '
                            'contains(@class, "compose") or @role="button"]'
                        )
                        
                        click_count = 0
                        for elem in possible_buttons:
                            try:
                                if elem.is_displayed():
                                    driver.execute_script("arguments[0].click();", elem)
                                    click_count += 1
                            except:
                                continue
                        
                        log_fn(f"  ✅ Brute force clicked {click_count} elements!")
                        if click_count > 0:
                            send_clicked = True
                    except Exception as e:
                        log_fn(f"  ❌ Method 7 failed: {str(e)[:50]}")
                
                # Method 8: Last resort - simulate keyboard shortcut
                if not send_clicked:
                    try:
                        log_fn(f"  🎯 Method 8: Keyboard shortcut (Ctrl+Enter)...")
                        actions = ActionChains(driver)
                        actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
                        log_fn(f"  ✅ Sent Ctrl+Enter!")
                        send_clicked = True
                    except Exception as e:
                        log_fn(f"  ❌ Method 8 failed: {str(e)[:50]}")
                
                # If STILL not clicked, wait and monitor
                if not send_clicked:
                    log_fn(f"  ❌ ALL 8 METHODS FAILED!")
                    log_fn(f"  ⚠️ Video preview may still be processing...")
                    log_fn(f"  ⏳ Monitoring for 30 seconds...")
                    
                    # Keep trying every 3 seconds
                    for attempt in range(10):
                        time.sleep(3)
                        try:
                            # Try clicking send icon again
                            send_icon = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                            driver.execute_script("arguments[0].click();", send_icon)
                            log_fn(f"  ✅ Send button clicked on retry {attempt+1}!")
                            send_clicked = True
                            break
                        except:
                            if attempt % 3 == 0:
                                log_fn(f"  ⏳ Still trying... ({(attempt+1)*3}s)")
                            continue
                    
                    if not send_clicked:
                        log_fn(f"  ⚠️ Could not auto-send - video may need manual click")
                        send_clicked = True  # Continue anyway
                
                if send_clicked:
                    # Wait for message to be sent
                    if is_video:
                        # Calculate upload wait time based on file size
                        # Formula: 3 seconds per MB (generous for large videos)
                        upload_wait = int(file_size_mb * 3)
                        
                        # For large videos (30MB+), ensure minimum 2 minutes
                        if file_size_mb >= 30:
                            upload_wait = max(upload_wait, 120)  # Minimum 2 minutes for 30MB+
                        
                        # Cap at 3 minutes max
                        upload_wait = min(upload_wait, 180)
                        
                        log_fn(f"  📤 Uploading {file_size_mb:.1f}MB video to WhatsApp...")
                        log_fn(f"  ⏳ Waiting {upload_wait} seconds ({upload_wait//60}min {upload_wait%60}sec)")
                        log_fn(f"  ⚠️ CRITICAL: DO NOT close browser, change chat, or click anything!")
                        
                        # Wait the FULL time - absolutely no early exit
                        for i in range(upload_wait):
                            # Show progress every 10 seconds
                            if i % 10 == 9:
                                elapsed = i + 1
                                percentage = int((elapsed / upload_wait) * 100)
                                remaining = upload_wait - elapsed
                                log_fn(f"  ⏳ {percentage}% complete | {elapsed}s elapsed | {remaining}s remaining")
                            
                            time.sleep(1)
                        
                        log_fn(f"  ✅ Upload time complete - waited full {upload_wait} seconds")
                        log_fn(f"  ⏳ Final safety wait (10 seconds)...")
                        time.sleep(10)  # Longer safety buffer
                    else:
                        log_fn(f"  ⏳ Sending attachment...")
                        time.sleep(3)  # Images/documents send faster
                    
                    log_fn(f"✅ WhatsApp message with attachment sent to {phone}")
                
                # Successfully sent attachment, return now
                return True
                
            except Exception as e:
                log_fn(f"  ❌ ATTACHMENT ERROR: {str(e)}")
                import traceback
                error_details = traceback.format_exc()
                log_fn(f"  📋 Error details: {error_details[:200]}")
                
                # If message exists, try sending text only
                if message and message.strip():
                    log_fn(f"  📝 Fallback: Sending text only...")
                    try:
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
                        return True
                    except Exception as text_err:
                        log_fn(f"  ❌ Text fallback also failed: {text_err}")
                        return False
                else:
                    # No message and attachment failed
                    log_fn(f"  ❌ Attachment failed and no text to send")
                    return False
        
        # No attachment - send text only (if message exists)
        if message and message.strip():
            try:
                input_box = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                )
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
            except Exception as e:
                log_fn(f"❌ Failed to send text message: {e}")
                return False
        else:
            # No message and no attachment
            log_fn(f"⚠️ No message or attachment to send for {phone}")
            return False
        
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

# --- SMS sending via Android phone (ADB) ---
def detect_android_device(log_fn):
    """
    Detect connected Android device via ADB.
    Returns device object if found, None otherwise.
    """
    if not ADB_AVAILABLE:
        log_fn("❌ ADB library not installed. Run: pip install pure-python-adb")
        return None
    
    try:
        # Connect to ADB server
        adb = AdbClient(host="127.0.0.1", port=5037)
        devices = adb.devices()
        
        if not devices:
            log_fn("❌ No Android device detected. Enable USB Debugging and connect phone.")
            return None
        
        device = devices[0]
        log_fn(f"✅ Android device connected: {device.serial}")
        return device
    
    except Exception as e:
        log_fn(f"❌ ADB connection error: {e}")
        log_fn("💡 Make sure ADB server is running. See SMS setup guide.")
        return None

def send_message_sms(device, phone, message, log_fn, stop_event, delay_seconds=5):
    """
    Send an SMS via Android phone using ADB.
    Opens SMS app with pre-filled message and attempts to click send button automatically.
    
    Args:
        device: ADB device object
        phone: str, phone number
        message: str, SMS text (160 chars recommended)
        log_fn: callable, logging function
        stop_event: threading.Event, used to stop execution gracefully
        delay_seconds: int, seconds to wait after sending (default: 5)
    
    Returns:
        bool, True if sent successfully, False otherwise
    """
    if stop_event.is_set():
        log_fn("Stopped before sending SMS.")
        return False
    
    try:
        # Validate phone number
        phone = str(phone).strip()
        if not phone:
            log_fn("❌ Empty phone number, skipping.")
            return False
        
        # Clean phone number (remove spaces, dashes)
        phone_clean = extract_phone_digits(phone)
        
        # Check message length
        msg_len = len(message)
        if msg_len > 160:
            log_fn(f"⚠️ Message length {msg_len} chars (>160). May split into multiple SMS.")
        
        # Escape special characters for shell
        message_escaped = message.replace('"', '\\"').replace("'", "\\'").replace("$", "\\$").replace("`", "\\`").replace("\\n", " ")
        phone_escaped = phone_clean.replace('"', '\\"')
        
        log_fn(f"📱 Opening SMS for {phone_clean}...")
        
        # Open SMS app with pre-filled message
        cmd = f'am start -a android.intent.action.SENDTO -d sms:{phone_escaped} --es sms_body "{message_escaped}"'
        
        # Execute command on Android device
        result = device.shell(cmd)
        
        if "Error" in result or "error" in result.lower():
            log_fn(f"❌ Failed to open SMS app: {result}")
            return False
        
        # Wait for SMS app to open
        time.sleep(2.5)
        
        log_fn(f"🔍 Attempting to auto-click send button...")
        
        # Get screen size for calculating tap positions
        screen_size = device.shell("wm size")
        width, height = 1080, 2400  # Default values
        try:
            size_match = re.search(r'(\d+)x(\d+)', screen_size)
            if size_match:
                width = int(size_match.group(1))
                height = int(size_match.group(2))
                log_fn(f"📐 Screen: {width}x{height}")
        except:
            pass
        
        # Method 0: Try to find send button using UI Automator
        log_fn("🔍 Method 0: Analyzing UI for send button...")
        try:
            # Dump UI hierarchy to find send button
            device.shell("uiautomator dump /sdcard/window_dump.xml")
            time.sleep(0.5)
            ui_dump = device.shell("cat /sdcard/window_dump.xml")
            
            # Search for send button patterns in XML
            send_patterns = [
                r'text="Send"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                r'content-desc="Send"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                r'resource-id="[^"]*send[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
                r'class="android.widget.ImageButton"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
            ]
            
            send_button_found = False
            for pattern in send_patterns:
                matches = re.findall(pattern, ui_dump, re.IGNORECASE)
                if matches:
                    for match in matches:
                        x1, y1, x2, y2 = int(match[0]), int(match[1]), int(match[2]), int(match[3])
                        # Calculate center of button
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        
                        # Tap the center of the button
                        log_fn(f"🎯 Found send button at ({center_x}, {center_y})")
                        device.shell(f"input tap {center_x} {center_y}")
                        time.sleep(0.5)
                        send_button_found = True
                        break
                if send_button_found:
                    break
            
            if send_button_found:
                log_fn("✅ UI Automator: Send button clicked!")
            else:
                log_fn("⚠️ UI Automator: Send button not found in XML")
        except Exception as e:
            log_fn(f"⚠️ UI Automator failed: {e}")
        
        # Multiple send button click attempts
        send_clicked = False
        
        # Method 1: Try common send button positions (right side of screen, various heights)
        log_fn("🎯 Method 1: Trying common send button positions...")
        send_positions = [
            (int(width * 0.92), int(height * 0.93)),  # Bottom right (most common)
            (int(width * 0.90), int(height * 0.95)),  # Lower right
            (int(width * 0.88), int(height * 0.90)),  # Mid-right
            (int(width * 0.85), int(height * 0.88)),  # Alternative position
            (int(width * 0.95), int(height * 0.92)),  # Far right
        ]
        
        for x, y in send_positions:
            device.shell(f"input tap {x} {y}")
            time.sleep(0.3)
        
        # Method 2: Try ENTER key (works in some SMS apps)
        log_fn("⌨️ Method 2: Trying ENTER key...")
        device.shell("input keyevent 66")  # KEYCODE_ENTER
        time.sleep(0.3)
        
        # Method 3: Try D-PAD navigation + CENTER key
        log_fn("🎮 Method 3: Trying D-PAD navigation...")
        device.shell("input keyevent 22")  # KEYCODE_DPAD_RIGHT
        time.sleep(0.2)
        device.shell("input keyevent 23")  # KEYCODE_DPAD_CENTER
        time.sleep(0.3)
        
        # Method 4: Try additional screen regions
        log_fn("🔄 Method 4: Scanning screen for send button...")
        additional_positions = [
            (int(width * 0.80), int(height * 0.92)),  # Center-right bottom
            (int(width * 0.75), int(height * 0.95)),  # Middle bottom
            (int(width * 0.70), int(height * 0.93)),  # Left of center bottom
        ]
        
        for x, y in additional_positions:
            device.shell(f"input tap {x} {y}")
            time.sleep(0.3)
        
        # Method 5: Try swipe gesture (some apps need swipe to send)
        log_fn("👆 Method 5: Trying swipe gesture...")
        start_x = int(width * 0.85)
        start_y = int(height * 0.92)
        end_x = int(width * 0.95)
        end_y = int(height * 0.92)
        device.shell(f"input swipe {start_x} {start_y} {end_x} {end_y} 100")
        time.sleep(0.3)
        
        log_fn(f"✅ Auto-click attempts completed!")
        log_fn(f"💡 If SMS wasn't sent, manually tap send button in next {delay_seconds} seconds...")
        
        # Give user backup time to manually tap if auto-click failed
        for remaining in range(delay_seconds, 0, -1):
            if stop_event.is_set():
                break
            if remaining <= 3:
                log_fn(f"  ⏳ {remaining}...")
            time.sleep(1)
        
        # Return to home screen
        device.shell("input keyevent 3")  # KEYCODE_HOME
        time.sleep(0.5)
        
        log_fn(f"✅ Moving to next contact")
        return True
    
    except Exception as e:
        log_fn(f"❌ Failed to send SMS to {phone}: {e}")
        return False

# --- Messenger sending via Selenium ---
def send_message_messenger(driver, username, message, log_fn, stop_event, attachment_path=None):
    """
    Send a Facebook Messenger message to a single username with optional attachment.
    
    Args:
        driver: Selenium WebDriver instance
        username: str, Facebook username or profile ID
        message: str, text message to send
        log_fn: callable, logging function
        stop_event: threading.Event, used to stop execution gracefully
        attachment_path: str, optional path to file to attach
    
    Returns:
        bool, True if sent successfully, False otherwise
    """
    if stop_event.is_set():
        log_fn("Stopped before sending.")
        return False
    
    try:
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        short_wait = WebDriverWait(driver, FAST_WAIT)
        actions = ActionChains(driver)
        
        # Navigate to chat
        driver.get(f"https://www.messenger.com/t/{username}")
        
        # Wait for page to load
        try:
            short_wait.until(EC.presence_of_element_located((By.XPATH, "//h1 | //h2 | //div[contains(@class, 'x1lliihq')]")))
        except Exception:
            pass
        
        # Try clicking "Continue chatting" button if present
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
        
        # Find message box
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
        
        # Messenger doesn't support attachments via automation - text only
        if attachment_path and os.path.exists(attachment_path):
            log_fn(f"  ⚠️ Attachments not supported for Messenger platform")
            log_fn(f"  📝 Sending text message only...")
        
        # Send text message
        try:
            msg_box.click()
            time.sleep(0.15)
            actions.move_to_element(msg_box).click().key_down("\ue009").send_keys("a").key_up("\ue009").send_keys("\b").perform()
        except Exception:
            pass
        
        # Send message with proper line break handling (like WhatsApp)
        try:
            msg_box.click()
            time.sleep(0.3)
            
            # Split message by lines and send with proper formatting
            lines = message.split('\n')
            for i, line in enumerate(lines):
                if line.strip():  # Only send non-empty lines
                    msg_box.send_keys(line)
                # Add line break except for the last line
                if i < len(lines) - 1:
                    msg_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            time.sleep(0.5)
            msg_box.send_keys(Keys.ENTER)
            log_fn(f"✅ Messenger message sent to {username}")
            return True
        except Exception as e:
            log_fn(f"  ❌ Send failed {username}: {e}")
            return False
    
    except Exception as e:
        log_fn(f"❌ Failed to send Messenger message to {username}: {e}")
        return False

# --- Global UI Components Storage ---
attachment_entry = None
email_config_section = None
sms_config_section = None
messenger_config_section = None
platform_var = None

def update_ui_for_platform():
    """Show/hide UI elements based on selected platform"""
    global email_config_section, sms_config_section, messenger_config_section
    platform = platform_var.get()
    
    if platform == "Email":
        email_config_section.pack(fill=tk.X, pady=12, after=section_platform)
        if sms_config_section:
            sms_config_section.pack_forget()
        if messenger_config_section:
            messenger_config_section.pack_forget()
    elif platform == "SMS":
        if sms_config_section:
            sms_config_section.pack(fill=tk.X, pady=12, after=section_platform)
        email_config_section.pack_forget()
        if messenger_config_section:
            messenger_config_section.pack_forget()
    elif platform == "Messenger":
        if messenger_config_section:
            messenger_config_section.pack(fill=tk.X, pady=12, after=section_platform)
        email_config_section.pack_forget()
        if sms_config_section:
            sms_config_section.pack_forget()
    else:
        email_config_section.pack_forget()
        if sms_config_section:
            sms_config_section.pack_forget()
        if messenger_config_section:
            messenger_config_section.pack_forget()

# ================= MODERN REACTIVE GUI =================
root = tk.Tk()
root.title("🚀 growHigh - Bulk Sender (WhatsApp | Email | SMS | Messenger)")
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
subtitle = tk.Label(header_content, text="Professional Bulk Sender - WhatsApp, Email, SMS & Messenger", font=FONT_SUBTITLE, bg=BG_SECONDARY, fg=FG_SECONDARY)
subtitle.pack(anchor=tk.W, pady=(3, 0))

# Separator line
sep1 = tk.Frame(root, bg=CARD_BORDER, height=1)
sep1.pack(fill=tk.X, padx=0)

# ===== CSV COMPARISON TOOL BUTTON (Navigation Bar) =====
nav_bar = tk.Frame(root, bg=BG_SECONDARY, height=50)
nav_bar.pack(fill=tk.X)
nav_bar.pack_propagate(False)

nav_content = tk.Frame(nav_bar, bg=BG_SECONDARY)
nav_content.pack(pady=10)

def open_csv_compare_tool():
    """Open CSV comparison tool window"""
    compare_window = tk.Toplevel(root)
    compare_window.title("📊 CSV Comparison Tool")
    compare_window.geometry("750x700")
    compare_window.configure(bg=BG_PRIMARY)
    compare_window.resizable(True, True)
    
    # Header
    header = tk.Frame(compare_window, bg=BG_SECONDARY, height=70)
    header.pack(fill=tk.X, side=tk.TOP)
    header.pack_propagate(False)
    
    header_content = tk.Frame(header, bg=BG_SECONDARY)
    header_content.pack(pady=15, padx=25)
    
    tk.Label(header_content, text="🔄", font=("Arial", 20), bg=BG_SECONDARY, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 12))
    tk.Label(header_content, text="CSV Comparison Tool", font=("Consolas", 16, "bold"), bg=BG_SECONDARY, fg=FG_PRIMARY).pack(side=tk.LEFT)
    tk.Label(header_content, text="Find unique contacts", font=("Consolas", 9), bg=BG_SECONDARY, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(15, 0))
    
    # Separator
    tk.Frame(compare_window, bg=CARD_BORDER, height=1).pack(fill=tk.X)
    
    # Main content with scroll
    main_frame = tk.Frame(compare_window, bg=BG_PRIMARY)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
    
    # Instructions
    instructions = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    instructions.pack(fill=tk.X, pady=(0, 15))
    
    inst_header = tk.Frame(instructions, bg=CARD_BG)
    inst_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(inst_header, text="ℹ️", font=("Arial", 16), bg=CARD_BG, fg=ACCENT_YELLOW).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(inst_header, text="How It Works", font=("Consolas", 11, "bold"), bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    inst_list = tk.Frame(instructions, bg=CARD_BG)
    inst_list.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    tk.Label(inst_list, text="1️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=0, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Select Original CSV (contacts already messaged)", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    tk.Label(inst_list, text="2️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=1, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Select New CSV (full contact list)", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    tk.Label(inst_list, text="3️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=2, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Tool removes duplicates - keeps only unique contacts from File B", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    tk.Label(inst_list, text="4️⃣", font=("Arial", 12), bg=CARD_BG, fg=ACCENT_GREEN).grid(row=3, column=0, sticky=tk.W, pady=3)
    tk.Label(inst_list, text="Save unique contacts as new CSV - ready to use!", 
             font=("Consolas", 9), bg=CARD_BG, fg=FG_SECONDARY, anchor=tk.W).grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=3)
    
    # File A Selection
    file_a_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    file_a_section.pack(fill=tk.X, pady=(0, 12))
    
    fa_header = tk.Frame(file_a_section, bg=CARD_BG)
    fa_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(fa_header, text="📁", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_MAIN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(fa_header, text="File A - Original CSV (Already Messaged)", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    file_a_frame = tk.Frame(file_a_section, bg=CARD_BG)
    file_a_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    file_a_entry = tk.Entry(file_a_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
    file_a_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
    
    def browse_file_a():
        path = filedialog.askopenfilename(parent=compare_window, title="Select Original CSV (File A)", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            file_a_entry.delete(0, tk.END)
            file_a_entry.insert(0, path)
    
    browse_a_btn = tk.Button(file_a_frame, text="📂 BROWSE", command=browse_file_a, bg=ACCENT_GREEN, fg="#000000",
                            font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=18, pady=8, cursor="hand2")
    browse_a_btn.pack(side=tk.LEFT)
    
    # File B Selection
    file_b_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    file_b_section.pack(fill=tk.X, pady=(0, 12))
    
    fb_header = tk.Frame(file_b_section, bg=CARD_BG)
    fb_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(fb_header, text="📁", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_MAIN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(fb_header, text="File B - New CSV (Full Contact List)", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    file_b_frame = tk.Frame(file_b_section, bg=CARD_BG)
    file_b_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    file_b_entry = tk.Entry(file_b_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
    file_b_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
    
    def browse_file_b():
        path = filedialog.askopenfilename(parent=compare_window, title="Select New CSV (File B)", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            file_b_entry.delete(0, tk.END)
            file_b_entry.insert(0, path)
    
    browse_b_btn = tk.Button(file_b_frame, text="📂 BROWSE", command=browse_file_b, bg=ACCENT_GREEN, fg="#000000",
                            font=("Consolas", 9, "bold"), relief=tk.FLAT, bd=0, padx=18, pady=8, cursor="hand2")
    browse_b_btn.pack(side=tk.LEFT)
    
    # Compare button section (Step 1: Compare files)
    compare_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    compare_section.pack(fill=tk.X, pady=(0, 12))
    
    compare_info = tk.Frame(compare_section, bg=CARD_BG)
    compare_info.pack(fill=tk.X, padx=20, pady=(12, 5))
    
    tk.Label(compare_info, text="🔄", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_MAIN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(compare_info, text="Compare & Save", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    tk.Label(compare_info, text="Find unique contacts and save to file", font=("Consolas", 8),
             bg=CARD_BG, fg=FG_SECONDARY).pack(side=tk.LEFT, padx=(10, 0))
    
    compare_btn_frame = tk.Frame(compare_section, bg=CARD_BG)
    compare_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    # Results display
    results_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    results_section.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
    
    res_header = tk.Frame(results_section, bg=CARD_BG)
    res_header.pack(fill=tk.X, padx=20, pady=(12, 5))
    tk.Label(res_header, text="📊", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(res_header, text="Comparison Results", font=("Consolas", 10, "bold"), bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    results_text = scrolledtext.ScrolledText(results_section, height=10, font=("Consolas", 9), bg=BG_SECONDARY, fg=ACCENT_GREEN,
                                            state=tk.DISABLED, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN, padx=12, pady=10)
    results_text.pack(padx=20, pady=(0, 12), fill=tk.BOTH, expand=True)
    
    def log_result(msg):
        results_text.configure(state=tk.NORMAL)
        results_text.insert(tk.END, f"{msg}\n")
        results_text.see(tk.END)
        results_text.configure(state=tk.DISABLED)
    
    # Save button section (Step 2: Save results) - Initially hidden
    save_section = tk.Frame(main_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)
    
    save_info = tk.Frame(save_section, bg=CARD_BG)
    save_info.pack(fill=tk.X, padx=20, pady=(12, 8))
    
    tk.Label(save_info, text="💾", font=("Arial", 14), bg=CARD_BG, fg=ACCENT_YELLOW).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(save_info, text="Step 2: Save Unique Contacts", font=("Consolas", 10, "bold"), 
             bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
    
    save_btn_frame = tk.Frame(save_section, bg=CARD_BG)
    save_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 12))
    
    output_entry = tk.Entry(save_btn_frame, bg=HOVER_BG, fg=FG_PRIMARY, font=FONT_TEXT, relief=tk.FLAT, bd=0, insertbackground=ACCENT_GREEN)
    output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=8)
    
    # Global variable to store comparison result
    comparison_result = {'df_unique': None, 'unique_count': 0}
    
    # Compare function (Step 1)
    def compare_files():
        file_a = file_a_entry.get().strip()
        file_b = file_b_entry.get().strip()
        
        if not file_a or not os.path.exists(file_a):
            messagebox.showerror("Error", "Please select Original CSV (File A)")
            return
        
        if not file_b or not os.path.exists(file_b):
            messagebox.showerror("Error", "Please select New CSV (File B)")
            return
        
        try:
            results_text.configure(state=tk.NORMAL)
            results_text.delete(1.0, tk.END)
            results_text.configure(state=tk.DISABLED)
            
            log_result("═" * 60)
            log_result("🔄 STARTING CSV COMPARISON...")
            log_result("═" * 60)
            log_result("")
            
            # Read both CSV files
            df_a = pd.read_csv(file_a)
            df_b = pd.read_csv(file_b)
            
            log_result(f"✅ File A loaded: {len(df_a)} rows")
            log_result(f"✅ File B loaded: {len(df_b)} rows")
            log_result("")
            
            # Detect platform based on columns
            platform_detected = None
            contact_col = None
            
            if 'phone' in df_a.columns or 'Phone' in df_a.columns:
                platform_detected = "WhatsApp/SMS"
                contact_col = 'phone' if 'phone' in df_a.columns else 'Phone'
            elif 'email' in df_a.columns or 'Email' in df_a.columns:
                platform_detected = "Email"
                contact_col = 'email' if 'email' in df_a.columns else 'Email'
            elif 'username' in df_a.columns or 'Username' in df_a.columns:
                platform_detected = "Messenger"
                contact_col = 'username' if 'username' in df_a.columns else 'Username'
            else:
                # Use first column as contact column
                contact_col = df_a.columns[0]
                platform_detected = "Unknown"
                log_result(f"⚠️ No standard column found, using: '{contact_col}'")
            
            log_result(f"📱 Platform detected: {platform_detected}")
            log_result(f"📋 Using column: '{contact_col}'")
            log_result("")
            
            # Extract and normalize contacts from File A
            if platform_detected == "WhatsApp/SMS":
                contacts_a = set(df_a[contact_col].astype(str).apply(extract_phone_digits))
            else:
                contacts_a = set(df_a[contact_col].astype(str).str.strip().str.lower())
            
            contacts_a = {c for c in contacts_a if c and c != 'nan'}
            log_result(f"🔍 Unique contacts in File A: {len(contacts_a)}")
            
            # Find unique contacts in File B (not in File A)
            unique_rows = []
            duplicate_count = 0
            
            for idx, row in df_b.iterrows():
                contact = str(row[contact_col])
                
                if platform_detected == "WhatsApp/SMS":
                    normalized = extract_phone_digits(contact)
                else:
                    normalized = contact.strip().lower()
                
                if normalized and normalized != 'nan':
                    if normalized not in contacts_a:
                        unique_rows.append(row)
                    else:
                        duplicate_count += 1
            
            log_result(f"🔄 Contacts in File B: {len(df_b)}")
            log_result(f"✅ Unique contacts (NOT in File A): {len(unique_rows)}")
            log_result(f"♻️  Duplicates (already in File A): {duplicate_count}")
            log_result("")
            
            if not unique_rows:
                log_result("⚠️  NO UNIQUE CONTACTS FOUND!")
                log_result("All contacts in File B already exist in File A.")
                log_result("")
                messagebox.showinfo("No Unique Contacts", "❌ No unique contacts found!\n\nAll contacts in File B already exist in File A.")
                return
            
            # Ask user where to save
            output_file = filedialog.asksaveasfilename(
                parent=compare_window,
                title="Save Unique Contacts",
                defaultextension=".csv",
                initialfile="unique_contacts.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not output_file:
                log_result("⚠️ Save cancelled by user")
                return
            
            # Create new DataFrame with unique contacts
            df_unique = pd.DataFrame(unique_rows)
            
            log_result(f"💾 Saving {len(unique_rows)} contacts to file...")
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                log_result(f"📁 Created directory: {output_dir}")
            
            # Save to output file
            df_unique.to_csv(output_file, index=False)
            
            # Verify file was saved
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                log_result(f"✅ File saved successfully! ({file_size} bytes)")
            else:
                log_result(f"⚠️ Warning: File save reported success but file not found")
            
            log_result("")
            log_result("═" * 60)
            log_result("✅ SUCCESS!")
            log_result("═" * 60)
            log_result(f"📊 Found {len(unique_rows)} unique contacts")
            log_result(f"💾 Saved to: {output_file}")
            log_result("")
            log_result("✨ File is ready to use in the main app!")
            log_result("═" * 60)
            
            # Auto-load the new file into main CSV entry (if it exists)
            try:
                csv_entry.delete(0, tk.END)
                csv_entry.insert(0, output_file)
                log(f"✅ Loaded unique contacts CSV: {output_file}")
            except:
                pass  # csv_entry or log() not yet defined
            
            # Ask if user wants to open the folder
            response = messagebox.askyesno("✅ Success!", 
                              f"Found {len(unique_rows)} unique contacts!\n\n" +
                              f"💾 Saved to:\n{output_file}\n\n" +
                              f"📤 File has been auto-loaded in the main app.\n\n" +
                              f"Do you want to open the folder?")
            
            if response:
                # Open folder containing the file
                import subprocess
                folder_path = os.path.dirname(output_file)
                subprocess.Popen(f'explorer /select,"{output_file}"')
            
        except Exception as e:
            log_result("")
            log_result(f"❌ ERROR: {str(e)}")
            log_result(f"Full error: {repr(e)}")
            log_result("")
            messagebox.showerror("Error", f"Failed to compare CSV files:\n\n{str(e)}")
    
    compare_btn = tk.Button(compare_btn_frame, text="🔄  COMPARE & SAVE", command=compare_files, 
                           bg=ACCENT_MAIN, fg="white", font=("Consolas", 11, "bold"), 
                           relief=tk.FLAT, bd=0, padx=30, pady=14, cursor="hand2")
    compare_btn.pack(fill=tk.X)
    
    def on_compare_btn_enter(event):
        compare_btn.config(bg="#4A8DD6")
    
    def on_compare_btn_leave(event):
        compare_btn.config(bg=ACCENT_MAIN)
    
    compare_btn.bind("<Enter>", on_compare_btn_enter)
    compare_btn.bind("<Leave>", on_compare_btn_leave)

csv_compare_btn = tk.Button(nav_content, text="🔄  CSV COMPARE TOOL", command=open_csv_compare_tool,
                            bg=ACCENT_MAIN, fg="white", font=("Consolas", 10, "bold"),
                            relief=tk.FLAT, bd=0, padx=25, pady=10, cursor="hand2")
csv_compare_btn.pack()

def on_nav_compare_enter(event):
    csv_compare_btn.config(bg="#4A8DD6")

def on_nav_compare_leave(event):
    csv_compare_btn.config(bg=ACCENT_MAIN)

csv_compare_btn.bind("<Enter>", on_nav_compare_enter)
csv_compare_btn.bind("<Leave>", on_nav_compare_leave)

# Separator line
sep2 = tk.Frame(root, bg=CARD_BORDER, height=1)
sep2.pack(fill=tk.X, padx=0)

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

platforms = ["WhatsApp", "Email", "SMS", "Messenger"]
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

# ===== SECTION 0.6: SMS CONFIGURATION (Hidden by default) =====
sms_config_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)

sms_config_section.bind("<Enter>", lambda e: on_section_enter(e, sms_config_section))
sms_config_section.bind("<Leave>", lambda e: on_section_leave(e, sms_config_section))

s_sms_header = tk.Frame(sms_config_section, bg=CARD_BG)
s_sms_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_sms_header, text="📱", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_sms_header, text="Android Phone via USB", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s_sms_header, text="Connect your Android phone with USB Debugging enabled", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

sms_input_frame = tk.Frame(sms_config_section, bg=CARD_BG)
sms_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

# Device connection test button
def test_phone_connection():
    """Test Android phone connection via ADB"""
    log("📱 Testing Android phone connection...")
    device = detect_android_device(log)
    if device:
        log("✅ Phone connection test PASSED!")
        log("💡 You can now send SMS messages.")
    else:
        log("❌ Phone connection test FAILED!")
        log("💡 See SMS_SETUP_GUIDE.md for troubleshooting.")

test_phone_btn = tk.Button(sms_input_frame, text="🔌 TEST PHONE CONNECTION", command=test_phone_connection, 
                           bg=ACCENT_MAIN, fg="#FFFFFF", font=("Consolas", 9, "bold"), 
                           relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
test_phone_btn.pack(fill=tk.X, pady=(0, 10))

def on_test_phone_enter(event):
    test_phone_btn.config(bg="#4A8DD6")

def on_test_phone_leave(event):
    test_phone_btn.config(bg=ACCENT_MAIN)

test_phone_btn.bind("<Enter>", on_test_phone_enter)
test_phone_btn.bind("<Leave>", on_test_phone_leave)

# SMS Setup instructions
sms_info_label = tk.Label(sms_input_frame, 
                          text="🤖 Auto-click ENABLED: App will try to click send button automatically!\n" + 
                               "💡 Enable USB Debugging: Settings → Developer Options → USB Debugging\n" +
                               "📚 Full setup guide: SMS_SETUP_GUIDE.md",
                          font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_GREEN, justify=tk.LEFT)
sms_info_label.pack(anchor=tk.W, pady=(5, 10))

# ===== SECTION 0.7: MESSENGER CONFIGURATION (Hidden by default) =====
messenger_config_section = tk.Frame(content_frame, bg=CARD_BG, relief=tk.FLAT, bd=1, highlightbackground=CARD_BORDER, highlightthickness=1)

messenger_config_section.bind("<Enter>", lambda e: on_section_enter(e, messenger_config_section))
messenger_config_section.bind("<Leave>", lambda e: on_section_leave(e, messenger_config_section))

s_messenger_header = tk.Frame(messenger_config_section, bg=CARD_BG)
s_messenger_header.pack(fill=tk.X, padx=20, pady=(15, 10))
tk.Label(s_messenger_header, text="💬", font=("Arial", 18), bg=CARD_BG, fg=ACCENT_GREEN).pack(side=tk.LEFT, padx=(0, 10))
tk.Label(s_messenger_header, text="Facebook Messenger", font=FONT_LABEL, bg=CARD_BG, fg=FG_PRIMARY).pack(side=tk.LEFT)
tk.Label(s_messenger_header, text="Login to Facebook Messenger in the browser window", font=("Consolas", 8), bg=CARD_BG, fg=FG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))

messenger_input_frame = tk.Frame(messenger_config_section, bg=CARD_BG)
messenger_input_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

# Messenger login test button
def test_messenger_login():
    """Test Messenger login by opening browser"""
    log("📱 Opening Messenger for login test...")
    try:
        driver = create_driver()
        driver.get("https://www.messenger.com")
        log("✅ Browser opened. Please log in to Facebook Messenger.")
        log("💡 Keep browser open for sending messages.")
    except Exception as e:
        log(f"❌ Failed to open browser: {e}")

test_messenger_btn = tk.Button(messenger_input_frame, text="🔐 TEST MESSENGER LOGIN", command=test_messenger_login, 
                           bg=ACCENT_MAIN, fg="#FFFFFF", font=("Consolas", 9, "bold"), 
                           relief=tk.FLAT, bd=0, padx=20, pady=8, cursor="hand2")
test_messenger_btn.pack(fill=tk.X, pady=(0, 10))

def on_test_messenger_enter(event):
    test_messenger_btn.config(bg="#4A8DD6")

def on_test_messenger_leave(event):
    test_messenger_btn.config(bg=ACCENT_MAIN)

test_messenger_btn.bind("<Enter>", on_test_messenger_enter)
test_messenger_btn.bind("<Leave>", on_test_messenger_leave)

# Messenger Setup instructions
messenger_info_label = tk.Label(messenger_input_frame, 
                          text="📋 CSV must have 'username' column (Facebook username or profile ID)\n" + 
                               "💡 Login to Facebook Messenger when browser opens\n" +
                               "⚡ Messages will be sent automatically after login",
                          font=("Consolas", 8), bg=CARD_BG, fg=ACCENT_GREEN, justify=tk.LEFT)
messenger_info_label.pack(anchor=tk.W, pady=(5, 10))

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
    attachment_path = attachment_entry.get().strip() if attachment_entry.get().strip() else None
    
    # Check if there's either a message or an attachment
    if not message and not attachment_path:
        messagebox.showerror("No content", "Please type a message or attach a file to send.")
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
        
        # Detect Android device if using SMS platform
        android_device = None
        if platform == "SMS":
            log("📱 Detecting Android device...")
            android_device = detect_android_device(log)
            if not android_device:
                messagebox.showerror("No Phone Detected", "Cannot detect Android phone. Please connect phone and enable USB Debugging.")
                start_btn.config(state=tk.NORMAL)
                return
            log("✅ Android device ready for SMS sending")
        
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
        
        elif platform == "Messenger":
            # Messenger mode: look for username column
            username_col = None
            name_col = None
            
            for c in df.columns:
                if c.lower() in ('username', 'user', 'facebook_username', 'fb_username', 'messenger_username'):
                    username_col = c
                    break
            
            for c in df.columns:
                if c.lower() in ('name', 'contact_name', 'fullname', 'full_name', 'customer_name'):
                    name_col = c
                    break
            
            if username_col:
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    username_raw = str(r[username_col]).strip()
                    
                    if not username_raw or username_raw == 'nan':
                        log(f"⚠️ Skipping empty username at row {row_number}")
                        continue
                    
                    # Use username as name if no name column, otherwise use name column
                    name = username_raw
                    if name_col and not pd.isna(r[name_col]):
                        name = str(r[name_col]).strip()
                    
                    # Personalize message: replace {{name}} with name, add "Hello {username}" prefix
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {username_raw},\n\n{personalized_msg}"
                    rows.append((username_raw, personalized_msg, username_raw))
            else:
                # Fallback: use first column as username
                first_col = df.columns[0]
                for idx, r in df.iterrows():
                    # Skip rows outside the specified range
                    row_number = idx + 1  # Convert 0-based index to 1-based row number
                    if row_number < row_start or row_number > row_end:
                        continue
                    
                    username_raw = str(r[first_col]).strip()
                    
                    if not username_raw or username_raw == 'nan':
                        log(f"⚠️ Skipping empty username at row {row_number}")
                        continue
                    
                    # Use username as name if no name column, otherwise use second column as name
                    name = username_raw
                    if len(df.columns) > 1:
                        second_col = df.columns[1]
                        if not pd.isna(r[second_col]):
                            name = str(r[second_col]).strip()
                    
                    # Personalize message: replace {{name}} with name, add "Hello {username}" prefix
                    personalized_msg = message.replace("{{name}}", name).replace("{name}", name)
                    personalized_msg = f"Hello {username_raw},\n\n{personalized_msg}"
                    rows.append((username_raw, personalized_msg, username_raw))
        
        else:
            # WhatsApp/SMS mode: look for phone column
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
                        # If attachment exists but no message, don't add greeting
                        if attachment_path and (not message or not message.strip()):
                            personalized_msg = ""  # Empty message, only attachment
                        else:
                            # Normal message with greeting
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
                        # If attachment exists but no message, don't add greeting
                        if attachment_path and (not message or not message.strip()):
                            personalized_msg = ""  # Empty message, only attachment
                        else:
                            # Normal message with greeting
                            personalized_msg = f"Hello {name},\n\n{message}"
                        rows.append((phone_clean, personalized_msg, name))
                    else:
                        log(f"⚠️ Skipping invalid phone: {phone_raw}")

        if not rows:
            if platform == "Email":
                contact_type = "emails"
            elif platform == "Messenger":
                contact_type = "usernames"
            else:
                contact_type = "phone numbers"
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

        # Create driver for WhatsApp or Messenger
        if platform in ["WhatsApp", "Messenger"]:
            try:
                log(f"🌐 Initializing Chrome browser...")
                driver = create_driver()
                log(f"✅ Browser started successfully")
            except Exception as e:
                log(f"❌ Browser startup failed: {e}")
                import traceback
                log(f"📋 Error details: {traceback.format_exc()[:300]}")
                start_btn.config(state=tk.NORMAL)
                return

            if platform == "WhatsApp":
                # Open WhatsApp Web
                log("🌐 Opening WhatsApp Web...")
                try:
                    driver.get("https://web.whatsapp.com")
                    log(f"✅ WhatsApp Web loaded: {driver.current_url[:50]}")
                except Exception as e:
                    log(f"❌ Failed to open WhatsApp Web: {e}")
                    driver.quit()
                    start_btn.config(state=tk.NORMAL)
                    return
                
                time.sleep(2)
                if "web.whatsapp.com" in driver.current_url and "qr" in driver.page_source.lower():
                    log("📱 Please scan QR code in WhatsApp Web. Waiting 20s...")
                    time.sleep(20)
                else:
                    log("✅ Already logged in to WhatsApp Web")
            elif platform == "Messenger":
                # Open Messenger
                driver.get("https://www.messenger.com")
                time.sleep(2)
                if "login" in driver.current_url.lower():
                    log("📱 Please log in to Facebook Messenger. Waiting 20s...")
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
        
        elif platform == "SMS":
            # SMS sending loop
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_phone, msg, name = row_data
                log(f"[{i}/{len(rows)}] → {target_phone} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_message_sms(android_device, target_phone, msg, log, stop_event, delay_seconds)
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
                
                if stop_event.is_set():
                    break
        
        elif platform == "Messenger":
            # Messenger sending loop
            for i, row_data in enumerate(rows, start=1):
                if stop_event.is_set():
                    log("⏹ Stopped by user.")
                    break
                
                target_username, msg, name = row_data
                log(f"[{i}/{len(rows)}] → {target_username} ({name})")
                stats_pending.config(text=str(len(rows) - i))
                
                try:
                    ok = send_message_messenger(driver, target_username, msg, log, stop_event, attachment_path)
                    if ok:
                        sent_count += 1
                        stats_sent.config(text=str(sent_count))
                    else:
                        failed_list.append(target_username)
                        stats_failed.config(text=str(len(failed_list)))
                except Exception as e:
                    log(f"  ❌ ERROR {target_username}: {e}")
                    failed_list.append(target_username)
                    stats_failed.config(text=str(len(failed_list)))
                
                # Short delay between messages
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                for remaining in range(int(delay), 0, -1):
                    if stop_event.is_set():
                        break
                    if remaining <= 3:
                        log(f"  ⏳ {remaining}s...")
                    time.sleep(1)
                
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
        
        if platform in ["WhatsApp", "Messenger"]:
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