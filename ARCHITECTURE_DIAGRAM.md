# Sendora - Code Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          app.py                                  │
│                    (Main Application)                            │
│  - GUI (Tkinter)                                                 │
│  - CSV Loading                                                   │
│  - Broadcast Orchestration                                       │
│  - Country Code Management                                       │
│  - Threading & Stop Events                                       │
└────────────┬─────────────────────┬──────────────────────┬────────┘
             │                     │                      │
             │                     │                      │
     ┌───────▼────────┐    ┌──────▼──────┐      ┌───────▼─────────┐
     │  platforms/     │    │   utils/    │      │  Standard Libs  │
     │                 │    │             │      │                 │
     │  whatsapp.py    │    │  driver.py  │      │  - pandas       │
     │  email_sender.py│    │             │      │  - threading    │
     │  sms.py         │    │  Creates    │      │  - tkinter      │
     │  messenger.py   │    │  Chrome     │      │  - time         │
     │                 │    │  WebDriver  │      │  - os           │
     └────────┬────────┘    └─────────────┘      └─────────────────┘
              │
              │
     ┌────────▼─────────────────────────────────────┐
     │         External Dependencies                │
     │                                              │
     │  - selenium (Chrome automation)              │
     │  - webdriver-manager (ChromeDriver)          │
     │  - smtplib (Email sending)                   │
     │  - ppadb (Android debugging)                 │
     └──────────────────────────────────────────────┘
```

## 📊 Data Flow

```
User Input (CSV) ──────► app.py (Parse & Validate)
                            │
                            │
                ┌───────────▼──────────────┐
                │  Select Platform:        │
                │  - WhatsApp              │
                │  - Email                 │
                │  - SMS                   │
                │  - Messenger             │
                └───────────┬──────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
      ┌─────▼─────┐   ┌────▼────┐   ┌─────▼─────┐
      │ WhatsApp  │   │  Email  │   │    SMS    │
      │           │   │         │   │           │
      │ Browser   │   │  SMTP   │   │  Android  │
      │ Selenium  │   │ Server  │   │    ADB    │
      └───────────┘   └─────────┘   └───────────┘
            │               │               │
            └───────────────┼───────────────┘
                            │
                      ┌─────▼──────┐
                      │  Message   │
                      │   Sent!    │
                      └────────────┘
```

## 🔄 Function Call Flow

### WhatsApp Message Flow:
```
app.py:start_sending()
    │
    ├──► utils.driver.create_driver()
    │        │
    │        └──► Returns: Chrome WebDriver
    │
    └──► platforms.whatsapp.send_message_whatsapp()
             │
             ├──► Navigate to chat
             ├──► Wait for load
             ├──► Handle attachment (if any)
             │    ├──► Find attach button (4 methods)
             │    ├──► Upload file
             │    ├──► Wait for processing
             │    └──► Click send (8 methods)
             │
             ├──► Send text message
             └──► Countdown delay
```

### Email Message Flow:
```
app.py:start_sending()
    │
    └──► platforms.email_sender.send_email_smtp()
             │
             ├──► Detect SMTP server
             ├──► Connect & authenticate
             ├──► Compose message
             ├──► Attach file (if any)
             ├──► Send
             └──► Close connection
```

### SMS Message Flow:
```
app.py:start_sending()
    │
    ├──► platforms.sms.detect_android_device()
    │        │
    │        └──► Returns: ADB device
    │
    └──► platforms.sms.send_message_sms()
             │
             ├──► Open Messages app
             ├──► Input recipient
             ├──► Type message
             ├──► Click send (5 auto-methods)
             └──► Delay
```

## 📦 Module Dependencies

```
app.py
├── Imports from platforms/
│   ├── whatsapp.send_message_whatsapp
│   ├── email_sender.send_email_smtp
│   ├── sms.send_message_sms
│   ├── sms.detect_android_device
│   └── messenger.send_message_messenger
│
├── Imports from utils/
│   ├── driver.create_driver
│   ├── driver.PROFILE_DIR
│   └── driver.HEADLESS
│
└── Standard Library
    ├── pandas
    ├── tkinter
    ├── threading
    ├── time
    └── os

platforms/whatsapp.py
├── selenium (WebDriver, By, Keys, WebDriverWait, EC, ActionChains)
├── time
└── os

platforms/email_sender.py
├── smtplib
├── email.mime.*
├── time
├── os
└── re

platforms/sms.py
├── ppadb
├── time
└── re

platforms/messenger.py
├── selenium (WebDriver, By, Keys, WebDriverWait, EC)
├── time
└── os

utils/driver.py
├── selenium
├── webdriver_manager
└── os
```

## 🎨 Color-Coded Architecture

```
┌────────────────────────────────────────┐
│  🟦 BLUE - User Interface (GUI)        │
│     app.py (Tkinter components)        │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  🟩 GREEN - Business Logic             │
│     app.py (Orchestration)             │
│     - CSV parsing                      │
│     - Broadcasting                     │
│     - Threading                        │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  🟧 ORANGE - Platform Integrations     │
│     platforms/ modules                 │
│     - WhatsApp                         │
│     - Email                            │
│     - SMS                              │
│     - Messenger                        │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  🟨 YELLOW - Utilities                 │
│     utils/ modules                     │
│     - Driver creation                  │
│     - Helper functions                 │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│  🟪 PURPLE - External Services         │
│     - WhatsApp Web                     │
│     - Gmail/Outlook SMTP               │
│     - Android ADB                      │
│     - Facebook Messenger               │
└────────────────────────────────────────┘
```

## ⚙️ Configuration Flow

```
User selects settings in GUI
         │
         ▼
    app.py stores in variables:
    - platform_var (WhatsApp/Email/SMS/Messenger)
    - country_code_var (Country selection)
    - delay_seconds (Message delay)
    - attachment_path (File path)
    - email credentials
         │
         ▼
    Passed to platform modules as function parameters
         │
         ▼
    Platform module uses settings to send messages
```

## 📝 File Sizes (Approximate)

- **app.py**: 1,618 lines (GUI + orchestration)
- **platforms/whatsapp.py**: 607 lines (Most complex - video support)
- **platforms/email_sender.py**: 120 lines
- **platforms/sms.py**: 240 lines
- **platforms/messenger.py**: 145 lines
- **utils/driver.py**: 58 lines

**Total**: ~2,788 lines (well-organized vs 2,661 lines monolithic)

The modular structure adds slightly more lines but provides much better maintainability!
