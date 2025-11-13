# growHigh Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    growHigh Application                          │
│                  Bulk Message & Email Sender                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
         ┌──────▼───────┐          ┌────────▼────────┐
         │  WhatsApp    │          │  Email (SMTP)   │
         │  Platform    │          │  Platform       │
         └──────┬───────┘          └────────┬────────┘
                │                          │
                ├─ Selenium Driver         ├─ SMTP Client
                ├─ QR Code Auth           ├─ App Password Auth
                ├─ Chrome Profile         ├─ SSL/TLS Connection
                ├─ 60s Rate Limit         └─ 5s Rate Limit
                └─ web.whatsapp.com
```

---

## Data Flow Diagram

```
┌─────────────┐
│  CSV File   │
│  (Contacts) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  Platform Selection     │
│  (WhatsApp / Email)     │
└──────┬──────────────────┘
       │
       ├─────────────────────────┬──────────────────────────┐
       │                         │                          │
       ▼                         ▼                          ▼
┌─────────────┐          ┌──────────────┐          ┌─────────────┐
│ Column      │          │ Column       │          │ Platform    │
│ Detection   │          │ Detection    │          │ Routing     │
│ (Phone)     │          │ (Email)      │          │             │
└─────┬───────┘          └──────┬───────┘          └─────┬───────┘
      │                         │                        │
      ├─ phone_col              ├─ email_col             ├─ platform_var
      ├─ name_col               ├─ name_col              ├─ get()
      └─ Extract Rows           ├─ subject_col           └─ == "Email (SMTP)"?
                                └─ Extract Rows
                 │                        │
                 ▼                        ▼
          ┌─────────────┐         ┌──────────────┐
          │ WhatsApp    │         │ Email        │
          │ Worker      │         │ Worker       │
          │ Thread      │         │ Thread       │
          └──────┬──────┘         └──────┬───────┘
                 │                       │
                 ├─ Open Driver          ├─ SMTP Login
                 ├─ QR Scan              ├─ Test Creds
                 ├─ Send Loop            ├─ Send Loop
                 ├─ 60s Delay            ├─ 5s Delay
                 └─ Log Stats            └─ Log Stats
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Activity Log    │
                    │  (Thread-safe)   │
                    │  Updates GUI     │
                    └──────┬───────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │  Statistics      │
                    │  ✅ Sent         │
                    │  ❌ Failed       │
                    │  ⏳ Pending      │
                    └──────────────────┘
```

---

## GUI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 growHigh - WhatsApp & Email Bulk Sender                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 🔀 SELECT PLATFORM                                          │
│ ⊗ WhatsApp    ◯ Email (SMTP)                               │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 🔐 EMAIL SENDER CREDENTIALS (Shown when Email selected)     │
│ Email Address: [_________________]                           │
│ App Password:  [_________________] •••                       │
│ [🧪 TEST EMAIL]                                             │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 📂 IMPORT CONTACTS (CSV)                                    │
│ [_____________________________] [📁 BROWSE]                 │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 💬 COMPOSE YOUR MESSAGE                                     │
│ ┌─────────────────────────────────────────┐                │
│ │ Type your message here...                │                │
│ │ (use \n for line breaks)                 │                │
│ └─────────────────────────────────────────┘                │
│ Characters: 0                                                │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ [▶  START SENDING]  [⏹  STOP]                              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 📋 ACTIVITY LOG                                             │
│ [12:30:45] 🚀 Starting broadcast to 10 contacts...         │
│ [12:30:46] 📧 Connecting to smtp.gmail.com...             │
│ [12:30:47] ✅ Email sent to john@example.com              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 📊 STATISTICS                                               │
│ ✅ Sent       ❌ Failed    ⏳ Pending                        │
│    8             1            1                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## CSV Column Mapping

### WhatsApp Mode
```
CSV Columns                 Detection Priority
┌────────────────┐
│ phone          │ ──▶ Phone Column (Required)
│ name           │ ──▶ Name Column (Optional)
│ custom_field   │ ──▶ Ignored
└────────────────┘

Aliases for Phone:
phone, phone_number, phone_number_e164, number

Aliases for Name:
name, contact_name, fullname, full_name, customer_name
```

### Email Mode
```
CSV Columns                 Detection Priority
┌────────────────┐
│ email          │ ──▶ Email Column (Required)
│ name           │ ──▶ Name Column (Optional)
│ subject        │ ──▶ Subject Column (Optional)
│ custom_field   │ ──▶ Ignored
└────────────────┘

Aliases for Email:
email, email_address, mail, recipient

Aliases for Name:
name, contact_name, fullname, full_name, customer_name, recipient_name

Aliases for Subject:
subject, email_subject
```

---

## Authentication Flow

### WhatsApp Authentication
```
1. User clicks START
2. Selenium opens web.whatsapp.com
3. QR Code displayed
4. User scans with phone
5. WhatsApp Web authenticated
6. Message sending begins
```

### Email (SMTP) Authentication
```
1. User enters sender email
2. User enters app password
3. User clicks "🧪 TEST EMAIL"
4. App detects SMTP server:
   ├─ Gmail? → smtp.gmail.com:465 (SSL)
   ├─ Outlook? → smtp-mail.outlook.com:587 (TLS)
   └─ Other? → Default to Gmail settings
5. Connection tested & verified
6. Credentials stored in memory
7. On START: Credentials used for bulk send
8. On completion: Credentials cleared
```

---

## Threading Model

```
┌─────────────────────────────────────────┐
│         Main Thread (GUI)                │
├─────────────────────────────────────────┤
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  Tkinter Event Loop               │  │
│  │  ├─ Button clicks                │  │
│  │  ├─ Text input                   │  │
│  │  ├─ Radio selection              │  │
│  │  └─ UI updates via root.after()  │  │
│  └───────────────────────────────────┘  │
│                                          │
└───────────────────────┬──────────────────┘
                        │
                        │ spawn daemon thread
                        │
                        ▼
            ┌──────────────────────────┐
            │  Worker Thread (Daemon)  │
            ├──────────────────────────┤
            │                          │
            │ CSV Reading              │
            │ ├─ Load CSV file         │
            │ ├─ Parse columns         │
            │ ├─ Extract contacts      │
            │ └─ Validate data         │
            │                          │
            │ Message Sending          │
            │ ├─ Setup connection      │
            │ ├─ Loop through contacts │
            │ ├─ Send message          │
            │ ├─ Wait (with countdown) │
            │ └─ Check stop_event      │
            │                          │
            │ Logging                  │
            │ └─ root.after() for GUI  │
            │                          │
            └──────────────────────────┘
```

---

## Error Handling Flow

```
Error Occurrence
       │
       ▼
┌──────────────────┐
│ Exception Caught │
└────────┬─────────┘
         │
         ├─ Type: SMTPAuthenticationError
         │         └─▶ "Check email/password"
         │
         ├─ Type: SMTPException
         │         └─▶ "SMTP error details"
         │
         ├─ Type: TimeoutException (WhatsApp)
         │         └─▶ "Chat not ready"
         │
         ├─ Type: Invalid Email Format
         │         └─▶ "Skip this email"
         │
         ├─ Type: CSV Parse Error
         │         └─▶ "Fix CSV file"
         │
         └─ Type: Generic Exception
                  └─▶ Log error, continue/stop
       │
       ▼
┌────────────────────┐
│ Log to Activity    │
│ Log update stats   │
│ Add to failed list │
└─────────┬──────────┘
          │
          ├─ Continue? → Next contact
          └─ Stop? → Check stop_event
```

---

## Rate Limiting

### WhatsApp
```
┌─────────────────────────────────┐
│  Send Message                    │
├─────────────────────────────────┤
│  ✓ Message sent successfully    │
│                                  │
│  Countdown: 60 seconds          │
│  ⏳ Waiting 60 seconds...      │
│  ⏳ Waiting 59 seconds...      │
│  ⏳ Waiting 58 seconds...      │
│  ...                             │
│  ⏳ Waiting 1 second...        │
│                                  │
│  Ready for next message         │
└─────────────────────────────────┘
     (60 seconds total)
```

### Email
```
┌─────────────────────────────────┐
│  Send Email                      │
├─────────────────────────────────┤
│  ✓ Email sent successfully      │
│                                  │
│  Countdown: 5 seconds           │
│  ⏳ Waiting 5 seconds...       │
│  ⏳ Waiting 4 seconds...       │
│  ⏳ Waiting 3 seconds...       │
│  ⏳ Waiting 2 seconds...       │
│  ⏳ Waiting 1 second...        │
│                                  │
│  Ready for next email           │
└─────────────────────────────────┘
     (5 seconds total)
```

---

## Statistics Tracking

```
┌────────────────────────────────────────┐
│         Sending in Progress             │
├────────────────────────────────────────┤
│                                         │
│  Total Contacts: 100                    │
│                                         │
│  Current: [50/100] Processing...       │
│                                         │
│  Real-time Stats Update:                │
│  ✅ Sent: 49 (49%)                     │
│  ❌ Failed: 1 (1%)                     │
│  ⏳ Pending: 50 (50%)                  │
│                                         │
│  [##########--------] 50%              │
│                                         │
│  After Each Send:                       │
│  ├─ Sent++ (49→50)                     │
│  ├─ Pending-- (50→49)                  │
│  ├─ Display updated                    │
│  └─ Activity log entry added           │
│                                         │
└────────────────────────────────────────┘
```

---

## File Organization

```
d:\exe_file_whatsapp\
├── app.py                                    (Main Application - 900+ lines)
├── requirements.txt                          (Dependencies)
├── build_exe.bat                            (Build Script)
├── Sendora.spec                             (PyInstaller Config)
│
├── QUICKSTART.md                            (User Guide - Quick Start)
├── EMAIL_SETUP_GUIDE.md                     (Email Configuration Guide)
├── EMAIL_IMPLEMENTATION_GUIDE.md            (Email Technical Guide)
├── IMPLEMENTATION_SUMMARY.md                (This Implementation)
│
├── .github/
│   └── copilot-instructions.md              (AI Developer Guide)
│
├── build/                                    (Build artifacts)
└── __pycache__/                             (Python cache)
```

---

## Deployment Architecture

```
Development
    │
    ├─ app.py (Single file)
    ├─ requirements.txt
    └─ Test CSV files
    │
    ▼
Local Testing
    │
    ├─ python app.py
    ├─ Test WhatsApp mode
    └─ Test Email mode
    │
    ▼
Build Executable
    │
    ├─ .\build_exe.bat
    ├─ PyInstaller compiles
    └─ dist/Sendorar.exe created
    │
    ▼
Distribution
    │
    ├─ Single .exe file
    ├─ No Python required
    ├─ All dependencies bundled
    └─ Ready for end-users
```

---

## Implementation Status

```
✅ Platform Selection
├─ Radio button UI
├─ Dynamic UI updates
└─ Platform routing

✅ WhatsApp Support
├─ Selenium integration
├─ QR code auth
├─ Message sending
└─ 60s rate limiting

✅ Email Support
├─ SMTP implementation
├─ Gmail support
├─ Outlook support
├─ Connection testing
└─ 5s rate limiting

✅ UI/UX
├─ Modern dark theme
├─ Real-time stats
├─ Activity logging
└─ Error handling

✅ Documentation
├─ User guides
├─ Setup guides
├─ Developer guides
└─ Implementation summary

✅ Testing
└─ Syntax verified
└─ All features functional
```

---

**Created:** November 11, 2025
**Status:** Complete & Production Ready ✅
