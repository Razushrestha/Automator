# Sendora - Project Structure

## 📁 Folder Organization

```
Automator-main/
│
├── app.py                      # Main application - START HERE
├── app_original_backup.py      # Backup of original monolithic app
│
├── platforms/                  # Platform-specific sender modules
│   ├── __init__.py            # Module exports
│   ├── whatsapp.py            # WhatsApp sender (607 lines)
│   ├── email_sender.py        # Email/SMTP sender
│   ├── sms.py                 # SMS via Android ADB
│   └── messenger.py           # Facebook Messenger sender
│
├── utils/                      # Utility functions
│   ├── __init__.py            # Module exports
│   └── driver.py              # Chrome WebDriver creation
│
├── requirements.txt            # Python dependencies
├── contacts.csv               # Sample contacts file
└── README.md                  # This file
```

## 🚀 How to Run

Simply run the main application file:

```bash
python app.py
```

## 📝 Code Structure

### Main Application (`app.py`)
- GUI code (Tkinter)
- Configuration
- CSV loading and parsing
- Broadcast orchestration
- Threading and stop events
- Country code management

### Platform Modules (`platforms/`)

Each platform has its own module with a sending function:

**`whatsapp.py`**
- `send_message_whatsapp(driver, phone, message, log_fn, stop_event, attachment_path, delay_seconds)`
- Handles text messages and attachments (images, videos, documents)
- Multiple fallback methods for UI element detection
- Video processing with intelligent wait times

**`email_sender.py`**
- `send_email_smtp(email_to, subject, body, sender_email, sender_password, log_fn, stop_event, attachment_path)`
- Supports Gmail and Outlook SMTP
- Attachment support
- Email validation

**`sms.py`**
- `send_message_sms(device, phone, message, log_fn, stop_event, delay_seconds)`
- `detect_android_device(log_fn)` - Find connected Android via ADB
- Requires Android phone connected via USB with USB debugging enabled

**`messenger.py`**
- `send_message_messenger(driver, username, message, log_fn, stop_event, attachment_path)`
- Facebook Messenger via web interface
- Multi-line message support

### Utilities (`utils/`)

**`driver.py`**
- `create_driver(profile_dir, headless)` - Create Chrome WebDriver
- Configuration constants (PROFILE_DIR, HEADLESS)

## 🔧 Making Changes

### To modify WhatsApp functionality:
Edit `platforms/whatsapp.py`

### To modify Email functionality:
Edit `platforms/email_sender.py`

### To modify SMS functionality:
Edit `platforms/sms.py`

### To modify Messenger functionality:
Edit `platforms/messenger.py`

### To modify GUI or main logic:
Edit `app.py`

### To modify Chrome browser settings:
Edit `utils/driver.py`

## 📦 Benefits of This Structure

1. **Modularity** - Each platform is independent
2. **Maintainability** - Easy to find and fix issues
3. **Scalability** - Add new platforms easily
4. **Testability** - Test each platform separately
5. **Readability** - Smaller files are easier to understand

## 🆕 Adding a New Platform

1. Create `platforms/your_platform.py`
2. Implement `send_message_your_platform()` function
3. Add import to `platforms/__init__.py`
4. Import in `app.py`
5. Add GUI elements in `app.py`
6. Add sending logic in broadcast function

## 📋 Original Backup

The original monolithic `app.py` (2661 lines) is backed up as `app_original_backup.py` for reference.

## 🎯 Key Features

- **Multi-Platform**: WhatsApp, Email, SMS, Facebook Messenger
- **Attachments**: Images, videos, documents (platform-dependent)
- **Country Codes**: 43 countries supported
- **Bulk Sending**: CSV-based contact management
- **Smart Delays**: Prevent account flagging
- **Error Handling**: Comprehensive logging and fallback mechanisms
- **Video Support**: Intelligent upload time calculation (30MB+ videos)
