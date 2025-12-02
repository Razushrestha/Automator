"""
WhatsApp messaging module for bulk message sending.
Uses Selenium WebDriver to automate WhatsApp Web.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import time
import os


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
