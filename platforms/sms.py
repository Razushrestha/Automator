"""
SMS Sender Module
Sends SMS messages via Android phone using ADB (Android Debug Bridge).

Requirements:
- Android phone with USB Debugging enabled
- ADB server running
- pure-python-adb library installed
"""

import time
import re

# SMS via Android phone
try:
    from ppadb.client import Client as AdbClient
    ADB_AVAILABLE = True
except ImportError:
    ADB_AVAILABLE = False


def extract_phone_digits(phone_str):
    """
    Extract only numeric digits from a phone number string.
    Examples:
        "+977-980-3661701" -> "9779803661701"
        "Phone: 9779803661701" -> "9779803661701"
        "977 (980) 366-1701" -> "9779803661701"
    """
    digits = re.sub(r'\D', '', str(phone_str))
    return digits.strip()


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
