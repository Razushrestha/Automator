"""
Utility functions for the Automator application.
Includes browser driver creation and helper functions.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

# Configuration
PROFILE_DIR = os.path.join(os.getenv('APPDATA'), 'AutoMessenger', 'chrome_profile')
HEADLESS = False  # Set to True to run browser in background


def create_driver(profile_dir=PROFILE_DIR, headless=HEADLESS):
    """
    Create and configure a Chrome WebDriver instance.
    
    Args:
        profile_dir: str, path to Chrome profile directory (default: APPDATA/AutoMessenger/chrome_profile)
        headless: bool, whether to run browser in headless mode (default: False)
    
    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
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
