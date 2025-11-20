# growHigh - Bulk Message & Email Sender - AI Coding Instructions

## Project Overview
This is a Python automation tool for sending bulk messages via WhatsApp Web OR bulk emails via SMTP. It features a Tkinter GUI with platform selection and can be packaged as a Windows executable using PyInstaller.

## Key Architecture

### Core Components
- **`app.py`**: Single-file application with dual-platform support (WhatsApp + Email)
- **Platform Support**: 
  - WhatsApp Web (`web.whatsapp.com`) via Selenium
  - Email (SMTP) via `smtplib` (Gmail, Outlook, custom providers)
- **Build System**: PyInstaller via `build_exe.bat` and `Sendorar.spec` config

### Critical Design Patterns

**Message Formatting for WhatsApp**:
- WhatsApp Web's contenteditable div collapses plain `\n` characters
- **MUST use** `Keys.SHIFT + Keys.ENTER` for line breaks (not plain `\n`)
- Messages are split by lines and sent with proper shift-enter between them:
  ```python
  for i, line in enumerate(lines):
      input_box.send_keys(line)
      if i < len(lines) - 1:
          input_box.send_keys(Keys.SHIFT + Keys.ENTER)
  ```

**Email Sending via SMTP**:
- Auto-detects SMTP server based on email domain:
  - Gmail: `smtp.gmail.com:465 (SSL)`
  - Outlook: `smtp-mail.outlook.com:587 (STARTTLS)`
- Uses `smtplib` for sending via `SMTP_SSL` or `SMTP.starttls()`
- Email validation using regex before sending: `^[^@]+@[^@]+\.[^@]+$`
- Personalization: Subject and body both support `{name}` substitution
- 5-second delay between emails (vs 60s for WhatsApp)

**Rate Limiting & Anti-Detection**:
- WhatsApp: 60-second delay between messages to prevent account flagging
- Email: 5-second delay between messages (SMTP doesn't have rate limiting issues)
- Random delays (3-7s) between operations via `MIN_DELAY`/`MAX_DELAY`
- Chrome profile persistence in `APPDATA/AutoMessenger/chrome_profile` for WhatsApp login
- Anti-automation flags disabled: `--disable-blink-features=AutomationControlled`

**Threading Model**:
- GUI runs on main thread
- Message/email sending runs on daemon thread to keep UI responsive
- `stop_event` (threading.Event) for graceful cancellation
- Thread-safe logging via `root.after(0, _append)` to update Tkinter widgets
- Platform detection via `platform_var.get()` to route to correct sender

**Platform Selection UI**:
- Radio buttons at top: "WhatsApp" or "Email (SMTP)"
- Dynamic UI elements show/hide based on selection:
  - Email mode: Shows sender email + password input fields + test button
  - WhatsApp mode: Hides email credentials section
- CSV column detection adapts to platform:
  - WhatsApp: Looks for `phone`, `phone_number`, `number`
  - Email: Looks for `email`, `email_address`, `recipient`

## Developer Workflows

### Running Locally
```powershell
python app.py
```

### Building Executable
```powershell
.\build_exe.bat
# Creates dist/Sendorar.exe (windowed, no console)
```

### Dependencies

Install via: `pip install -r requirements.txt`
- `selenium==4.15.2`: Browser automation
- `pandas==2.1.4`: CSV parsing
- `webdriver-manager==4.0.1`: Auto-downloads ChromeDriver
- `email-validator==2.1.0`: Email validation

## CSV Format Requirements
- **WhatsApp**: Requires column named `phone`, `phone_number`, `phone_number_e164`, or `number` (case-insensitive)
- **Email (SMTP)**: Requires column named `email`, `email_address`, `mail`, or `recipient` (case-insensitive)
- **Names**: Optional `name`, `contact_name`, `fullname`, `full_name`, `customer_name`, `recipient_name` column
- **Email Subject** (Email mode only): Optional `subject` or `email_subject` column
- Per-row `message` column overrides GUI message field (both platforms)

## Common Issues & Solutions

**"Chat not ready" timeout**: User not logged in to WhatsApp Web or Messenger. App pauses 20s on first launch for QR scan/login.

**Messages appear on single line**: Ensure `Keys.SHIFT + Keys.ENTER` is used, not plain `\n` or `Keys.ENTER` between lines.

**"CSV_FILE not defined" error**: CSV path must be selected via Browse button; no default fallback exists.

**WebDriver crashes on build**: Ensure `--disable-dev-shm-usage` and `--no-sandbox` flags are present in Chrome options for sandboxed environments.

## PyInstaller Configuration
- **Entry point**: `app.py`
- **Console mode**: `console=False` (windowed GUI)
- **Icon**: `auto.ico` (must exist in project root)
- **UPX compression**: Enabled to reduce exe size
- Hidden imports automatically detected (no manual specification needed)
