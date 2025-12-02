# 🚀 growHigh - Multi-Platform Bulk Messaging Application

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Mac-lightgrey.svg)

**Professional Bulk Sender for WhatsApp, Email, SMS & Messenger**

*Send personalized messages to thousands of contacts with ease*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Build](#-building-executable) • [Screenshots](#-screenshots)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Supported Platforms](#-supported-platforms)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [CSV Format](#-csv-format)
- [AI Text Generation](#-ai-text-generation)
- [Building Executable](#-building-executable)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**growHigh** (formerly Sendora) is a powerful, user-friendly desktop application that enables you to send bulk messages across multiple platforms from a single interface. Perfect for marketing campaigns, customer outreach, event invitations, and mass communication.

### Why growHigh?

✅ **Multi-Platform Support** - WhatsApp, Email, SMS, and Messenger in one app  
✅ **Personalized Messages** - Use placeholders like `{name}` for customization  
✅ **AI-Powered** - Generate professional messages with AI assistance  
✅ **CSV Management** - Import contacts and compare lists easily  
✅ **Attachment Support** - Send images, documents, and files  
✅ **Smart Delays** - Randomized delays to avoid spam detection  
✅ **Modern UI** - Beautiful, dark-themed interface  
✅ **Cross-Platform** - Works on Windows, Linux, and macOS  

---

## ✨ Features

### 🌐 Multi-Platform Messaging

| Platform | Features | Attachment Support |
|----------|----------|-------------------|
| **WhatsApp** | ✅ Web-based automation<br>✅ Personalized messages<br>✅ Smart delays | ✅ Images, PDFs, Documents |
| **Email** | ✅ SMTP support<br>✅ HTML formatting<br>✅ CC/BCC support | ✅ Multiple attachments |
| **SMS** | ✅ Android device integration<br>✅ ADB connection<br>✅ Bulk sending | ❌ Not supported |
| **Messenger** | ✅ Facebook Messenger<br>✅ Web automation<br>✅ Contact search | ✅ Images, Files |

### 🤖 AI Text Generation

- **Powered by Hugging Face & OpenAI** (optional)
- Generate professional business messages
- Multiple templates for different industries
- Customizable prompts
- Fallback templates when API unavailable

### 📊 CSV Comparison Tool

- **Compare two CSV files** to find unique contacts
- **Remove duplicates** automatically
- **Export unique contacts** for targeted campaigns
- **Smart detection** of phone numbers, emails, usernames

### 🎨 Modern User Interface

- **Dark theme** with vibrant accents
- **Real-time logging** with color-coded messages
- **Progress tracking** for bulk operations
- **Responsive design** that adapts to window size
- **Professional aesthetics** inspired by GitHub's UI

### ⚙️ Advanced Features

- **Variable delays** (3-7 seconds) to avoid detection
- **Placeholder support** - `{name}`, `{company}`, `{custom_field}`
- **Attachment handling** for images and documents
- **Error recovery** - continues on failure
- **Session persistence** - saves browser profiles
- **Headless mode** option for background operation

---

## 🖥️ Supported Platforms

### Messaging Platforms

- 📱 **WhatsApp Web** - Automated messaging via web interface
- 📧 **Email (SMTP)** - Gmail, Outlook, custom SMTP servers
- 💬 **SMS** - Via Android device (ADB required)
- 💙 **Facebook Messenger** - Web-based automation

### Operating Systems

- 🪟 **Windows** 10/11
- 🐧 **Linux** (Ubuntu, Debian, Fedora, etc.)
- 🍎 **macOS** 10.14+

---

## 📥 Installation

### Prerequisites

- **Python 3.8 or higher**
- **Google Chrome** browser (for WhatsApp/Messenger)
- **Android device** (optional, for SMS)
- **ADB tools** (optional, for SMS)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/Automator.git
cd Automator
```

### Step 2: Create Virtual Environment

```bash
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run Application

```bash
python app.py
```

---

## 🚀 Quick Start

### 1. Prepare Your CSV File

Create a CSV file with your contacts:

```csv
name,phone,email,company
John Doe,9779801234567,john@example.com,ABC Corp
Jane Smith,9779807654321,jane@example.com,XYZ Ltd
```

### 2. Launch Application

```bash
python app.py
```

### 3. Select Platform

Choose from: **WhatsApp**, **Email**, **SMS**, or **Messenger**

### 4. Load CSV File

Click **"📂 BROWSE CSV"** and select your contact file

### 5. Compose Message

Write your message with placeholders:
```
Hello {name},

We have an exciting offer for {company}!
```

### 6. Send Messages

Click **"🚀 SEND MESSAGES"** and watch the magic happen!

---

## 📖 Usage Guide

### WhatsApp Messaging

1. **Select Platform**: Choose "WhatsApp"
2. **Load CSV**: Must have `phone` column (format: `9779801234567`)
3. **Add Message**: Use `{name}` or other placeholders
4. **Optional**: Add attachment (image/PDF)
5. **Send**: First message opens WhatsApp Web for QR scan
6. **Wait**: App sends messages with smart delays

**CSV Format:**
```csv
name,phone
John Doe,9779801234567
Jane Smith,9779807654321
```

### Email Messaging

1. **Select Platform**: Choose "Email"
2. **Configure SMTP**:
   - SMTP Server: `smtp.gmail.com`
   - Port: `587`
   - Email: Your email address
   - Password: App password (not regular password)
3. **Load CSV**: Must have `email` column
4. **Compose**: Subject and message body
5. **Send**: Emails sent via SMTP

**Gmail Setup:**
- Enable 2-factor authentication
- Generate app password: [Google Account Settings](https://myaccount.google.com/apppasswords)
- Use app password in the application

**CSV Format:**
```csv
name,email,company
John Doe,john@example.com,ABC Corp
```

### SMS Messaging

1. **Connect Android Device**:
   ```bash
   # Enable USB debugging on phone
   # Connect via USB
   adb devices  # Verify connection
   ```
2. **Select Platform**: Choose "SMS"
3. **Load CSV**: Must have `phone` column
4. **Send**: Messages sent via connected device

**CSV Format:**
```csv
name,phone
John Doe,9779801234567
```

### Messenger Messaging

1. **Select Platform**: Choose "Messenger"
2. **Load CSV**: Must have `username` column (Facebook usernames)
3. **First Run**: Login to Facebook Messenger
4. **Send**: Messages sent automatically

**CSV Format:**
```csv
name,username
John Doe,john.doe.123
Jane Smith,jane.smith.456
```

---

## 📊 CSV Format

### Required Columns by Platform

| Platform | Required Column | Format | Example |
|----------|----------------|--------|---------|
| WhatsApp | `phone` | Country code + number | `9779801234567` |
| Email | `email` | Standard email | `user@example.com` |
| SMS | `phone` | Country code + number | `9779801234567` |
| Messenger | `username` | Facebook username | `john.doe.123` |

### Optional Columns

Add any custom columns for personalization:

```csv
name,phone,email,company,city,product
John Doe,9779801234567,john@example.com,ABC Corp,Kathmandu,Widget Pro
```

Use in messages:
```
Hello {name} from {city},

We have a special offer on {product} for {company}!
```

### CSV Comparison Tool

**Use Case:** You sent messages to 500 contacts last month. Now you have 1000 contacts. Find the 500 new ones.

1. Click **"📊 CSV COMPARISON TOOL"**
2. **File A**: Select old CSV (already messaged)
3. **File B**: Select new CSV (full list)
4. **Compare**: Tool finds unique contacts
5. **Save**: Export unique contacts as new CSV

---

## 🤖 AI Text Generation

### Setup

1. **Get API Key** (Optional):
   - Hugging Face: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

2. **Add to Code** (line 58 in `app.py`):
   ```python
   openai_key = "your-api-key-here"
   ```

### Usage

1. Click **"🤖 AI GENERATE"** button
2. Enter prompt: `"Write a professional message for handmade artisan products"`
3. AI generates message
4. Edit and use in your campaign

### Built-in Templates

Even without API keys, the app includes professional templates for:
- Handmade/Artisan products
- Professional services
- Website development
- General business outreach

---

## 🔨 Building Executable

Convert the application to a standalone executable:

### Linux/Mac

```bash
./build_exe.sh
```

### Windows

```cmd
build_exe.bat
```

### Result

```
dist/
└── Sendora  (or Sendora.exe on Windows)
```

**File size:** ~100-200 MB (includes Python + all dependencies)

**Distribution:** Just share the executable - no Python installation needed!

See [EXE_CONVERSION.md](EXE_CONVERSION.md) for detailed instructions.

---

## 🛠️ Troubleshooting

### WhatsApp Issues

**Problem:** QR code doesn't appear  
**Solution:** 
- Check Chrome is installed
- Clear `chrome_profile/` folder
- Restart application

**Problem:** Messages not sending  
**Solution:**
- Verify phone numbers include country code
- Check internet connection
- Increase delays in code (lines 35-36)

### Email Issues

**Problem:** Authentication failed  
**Solution:**
- Use app password, not regular password
- Enable "Less secure app access" (Gmail)
- Check SMTP server and port

**Problem:** Emails going to spam  
**Solution:**
- Warm up your email account
- Don't send too many at once
- Personalize messages
- Avoid spam trigger words

### SMS Issues

**Problem:** ADB connection failed  
**Solution:**
```bash
# Restart ADB server
adb kill-server
adb start-server
adb devices
```

**Problem:** Device not detected  
**Solution:**
- Enable USB debugging on phone
- Install ADB drivers (Windows)
- Try different USB cable/port

### Messenger Issues

**Problem:** Can't login to Facebook  
**Solution:**
- Clear `chrome_profile/` folder
- Login manually first time
- Check Facebook account isn't restricted

---

## 🎨 Screenshots

### Main Interface
```
┌─────────────────────────────────────────────────┐
│  🚀 growHigh                                    │
│  Professional Bulk Sender                       │
├─────────────────────────────────────────────────┤
│  Platform: [WhatsApp ▼]                        │
│  CSV File: [📂 BROWSE CSV]                     │
│  Message:  [Hello {name}...]                   │
│  [🤖 AI GENERATE] [🚀 SEND MESSAGES]          │
├─────────────────────────────────────────────────┤
│  📊 Logs:                                       │
│  ✅ Loaded 150 contacts                        │
│  📤 Sending to John Doe...                     │
│  ✅ Message sent successfully                  │
└─────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Razu Shrestha**  
CEO & Founder, NepaTronix Engineering Solution Pvt. Ltd.

- 📧 Email: contact@nepatronix.com
- 📱 Phone: 9803661701
- 🌐 Website: [NepaTronix](https://nepatronix.com)

---

## 🙏 Acknowledgments

- **Selenium** - Web automation framework
- **Pandas** - Data manipulation library
- **PyInstaller** - Executable builder
- **Tkinter** - GUI framework
- **Hugging Face** - AI text generation

---

## ⚠️ Disclaimer

This tool is for legitimate business communication only. Users are responsible for:
- Complying with anti-spam laws (CAN-SPAM, GDPR, etc.)
- Obtaining consent from recipients
- Following platform terms of service
- Respecting rate limits and usage policies

**Use responsibly and ethically!**

---

## 📞 Support

Need help? Found a bug? Have a feature request?

- 📧 Email: support@nepatronix.com
- 📱 Phone: 9803661701
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/Automator/issues)

---

<div align="center">

**Made with ❤️ by NepaTronix Engineering Solution**

⭐ Star this repo if you find it useful!

</div>
