# 🚀 Quick Reference Guide

## Running the App

```bash
python app.py
```

## File Structure

```
app.py              → Main application (START HERE)
platforms/          → Platform sender modules
  ├── whatsapp.py   → WhatsApp sender
  ├── email_sender.py → Email sender
  ├── sms.py        → SMS sender
  └── messenger.py  → Messenger sender
utils/              → Utility functions
  └── driver.py     → Chrome WebDriver
```

## Common Tasks

### Fix WhatsApp Issues
Edit: `platforms/whatsapp.py`

### Fix Email Issues
Edit: `platforms/email_sender.py`

### Fix SMS Issues
Edit: `platforms/sms.py`

### Fix Messenger Issues
Edit: `platforms/messenger.py`

### Change Browser Settings
Edit: `utils/driver.py`

### Change GUI or Add Features
Edit: `app.py`

## Importing Modules

```python
# In app.py or your test scripts:
from platforms import (
    send_message_whatsapp,
    send_email_smtp,
    send_message_sms,
    send_message_messenger
)
from utils import create_driver
```

## Testing Individual Platforms

```python
# Test WhatsApp only
from platforms.whatsapp import send_message_whatsapp
from utils import create_driver

driver = create_driver()
# Test send_message_whatsapp...
```

## Documentation

- **PROJECT_STRUCTURE.md** - Detailed structure explanation
- **ARCHITECTURE_DIAGRAM.md** - Visual diagrams & flowcharts
- **RESTRUCTURING_COMPLETE.md** - Summary of changes

## Backup

Original file backed up at: `app_original_backup.py`
