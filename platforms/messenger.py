"""
Facebook Messenger message sender module.

This module provides functionality to send messages via Facebook Messenger
using Selenium WebDriver automation.

Dependencies:
    - selenium
    - webdriver_manager

Usage:
    from platforms.messenger import send_message_messenger
    
    # Create driver first
    driver = create_driver()
    
    # Send message
    success = send_message_messenger(
        driver=driver,
        username="johndoe",
        message="Hello from Messenger!",
        log_fn=print,
        stop_event=threading.Event(),
        attachment_path=None
    )
"""

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
import time
import os

# ==================== CONFIG ====================
WAIT_TIMEOUT = 15
FAST_WAIT = 4
POST_CLICK_WAIT = 0.8
# ===============================================


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
