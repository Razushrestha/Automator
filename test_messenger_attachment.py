"""
Test script to find Messenger file input elements
Run this to debug attachment issues
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# Setup Chrome
PROFILE_DIR = os.path.join(os.getenv("APPDATA"), "AutoMessenger", "chrome_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)

options = Options()
options.add_argument(f"--user-data-dir={PROFILE_DIR}")
driver_path = ChromeDriverManager().install()
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

try:
    # Open Messenger
    print("Opening Messenger...")
    driver.get("https://www.messenger.com")
    time.sleep(3)
    
    # Ask user to open a chat manually
    input("Press Enter after you open a chat conversation...")
    
    print("\n🔍 Searching for file input elements...")
    
    # Try different selectors
    selectors = [
        ("//input[@type='file']", "Direct file input"),
        ("//input[@accept]", "Input with accept attribute"),
        ("//div[@aria-label='Attach a file']", "Attach button (aria-label)"),
        ("//div[@aria-label='Add Files']", "Add Files button"),
        ("//div[contains(@aria-label, 'Attach')]", "Contains 'Attach'"),
        ("//div[contains(@aria-label, 'ttach')]", "Contains 'ttach'"),
    ]
    
    found_elements = []
    
    for selector, description in selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                print(f"✅ Found {len(elements)} element(s): {description}")
                print(f"   Selector: {selector}")
                for i, elem in enumerate(elements):
                    try:
                        print(f"   Element {i+1}:")
                        print(f"     - Tag: {elem.tag_name}")
                        print(f"     - Type: {elem.get_attribute('type')}")
                        print(f"     - Accept: {elem.get_attribute('accept')}")
                        print(f"     - Aria-label: {elem.get_attribute('aria-label')}")
                        print(f"     - Class: {elem.get_attribute('class')[:50] if elem.get_attribute('class') else 'None'}...")
                        print(f"     - Visible: {elem.is_displayed()}")
                        found_elements.append((elem, description))
                    except:
                        print(f"     - Error reading element attributes")
                print()
        except Exception as e:
            print(f"❌ Failed: {description} - {e}")
    
    print(f"\n📊 Summary: Found {len(found_elements)} potential file inputs")
    
    if found_elements:
        print("\n💡 Recommendations:")
        for elem, desc in found_elements:
            if elem.get_attribute('type') == 'file':
                print(f"  ✅ BEST: {desc} - This is a file input!")
    
    input("\nPress Enter to close browser...")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    driver.quit()
