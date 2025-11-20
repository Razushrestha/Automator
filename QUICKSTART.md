# growHigh - Quick Start Guide

## 🚀 Installation & Setup

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```

---

## 📱 WhatsApp Mode

### Setup:
1. Select "WhatsApp" platform
2. Choose CSV file with phone numbers
3. Type your message
4. Click "START SENDING"
5. **IMPORTANT**: Scan the QR code that appears in 20 seconds

### CSV Format:
```csv
phone,name
9779803661701,John
9779807776666,Jane
```

### Supported Column Names:
- Phone: `phone`, `phone_number`, `phone_number_e164`, `number`
- Name: `name`, `contact_name`, `fullname`, `full_name`, `customer_name`

### Features:
- 60-second delay between messages (prevents account flagging)
- Automatic "Hello {name}," greeting
- Real-time stats tracking
- Stop anytime with STOP button

---

## 📧 Email Mode

### Setup:
1. Select "Email (SMTP)" platform
2. Enter sender email and app password
3. Click "🧪 TEST EMAIL" to verify credentials
4. Choose CSV file with email addresses
5. Type your message
6. Click "START SENDING"

### Getting App Password:

**Gmail:**
- Go to https://myaccount.google.com/apppasswords
- Select "Mail" and "Windows Computer"
- Copy 16-character password
- Use it in the app (NOT your regular password)

**Outlook:**
- Go to https://account.microsoft.com/security
- Create app password
- Copy and use in app

### CSV Format:
```csv
email,name,subject
john@example.com,John,Welcome!
jane@example.com,Jane,Special Offer
```

### Supported Column Names:
- Email: `email`, `email_address`, `mail`, `recipient`
- Name: `name`, `contact_name`, `fullname`, `full_name`, `customer_name`, `recipient_name`
- Subject (optional): `subject`, `email_subject`

### Features:
- 5-second delay between emails (faster than WhatsApp)
- Email validation before sending
- Auto-generates subject if not provided
- Custom subject per recipient support
- Connection test button

---

## 📊 CSV File Requirements

### Minimum Valid CSV:
```csv
phone,name
9779803661701,John
```

```csv
email,name
john@example.com,John
```

### Full Featured CSV:
```csv
email,name,subject
john@example.com,John Smith,Custom Subject Line
jane@example.com,Jane Doe,Another Subject
admin@company.com,Admin,Hello Admin
```

### Rules:
✅ First row must be column headers
✅ Column names are **case-insensitive**
✅ At least one contact required
✅ Phone: digits only (no + or spaces)
✅ Email: valid format (user@domain.com)

---

## 💡 Usage Tips

### Before Sending:
- ✅ Test CSV file with 2-3 contacts first
- ✅ Verify message content is correct
- ✅ Check phone numbers are valid format
- ✅ Test email credentials if using Email mode
- ✅ Ensure WhatsApp is logged in for WhatsApp mode

### During Sending:
- ✅ Keep app window open
- ✅ Watch Activity Log for errors
- ✅ Don't close browser if using WhatsApp
- ✅ Check Statistics panel for progress

### After Sending:
- ✅ Review Failed contacts list
- ✅ Save Activity Log if needed
- ✅ Retry failed contacts later

---

## ⚠️ Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "CSV file not found" | Wrong file path | Use Browse button to select file |
| "No message typed" | Empty message | Type message in message box |
| "No valid phone numbers" | Bad CSV format | Check phone column name and format |
| "No valid emails found" | Missing email column | Ensure CSV has `email` column |
| "Chat not ready" (WhatsApp) | Not logged in | Scan QR code when prompted |
| "Auth failed" (Email) | Wrong password | Use app password, not regular password |
| "Invalid email format" | Bad email in CSV | Check email column for typos |

---

## 🎯 Example Workflows

### Example 1: Send WhatsApp to Friends
```
1. Export contacts from phone → CSV
2. Columns: phone, name
3. Select WhatsApp
4. Type personal message
5. Click START
6. Scan QR code
```

### Example 2: Email Marketing Campaign
```
1. Create CSV with customer emails and names
2. Columns: email, name, subject
3. Select Email (SMTP)
4. Enter Gmail app password
5. Click "TEST EMAIL" to verify
6. Type message
7. Click START
```

### Example 3: Event Notification
```
1. Create CSV with invitee info
2. Add subject in CSV
3. Use Email or WhatsApp
4. Personalize with {name}
5. Send to all invitees
```

---

## 🔐 Security & Privacy

⚠️ **Password Security:**
- Passwords stored in memory only (not saved)
- Cleared when app closes
- Never hardcoded in files
- Never displayed in Activity Log

✅ **Safe Practices:**
- Use app passwords, not main passwords
- Enable 2-Factor Authentication
- Review all messages before sending
- Keep contacts list confidential

---

## 📞 Troubleshooting

**WhatsApp issues?**
- Ensure WhatsApp Web is accessible
- Check internet connection
- Clear browser cache
- Try disabling VPN

**Email issues?**
- Test connection first
- Check email spelling
- Verify app password
- Try different email provider

**CSV issues?**
- Open in Excel to check format
- Ensure column headers match
- Remove extra blank rows
- Save as CSV (not XLSX)

---

## 📈 Performance Guide

### Recommended Batch Sizes:
- **WhatsApp**: 50-100 messages (1-2 hours)
- **Email**: 500-1000 messages (1 hour)

### Timing:
- **WhatsApp**: 60s between messages = ~1 msg/min
- **Email**: 5s between emails = ~12 msgs/min

### Example:
- 100 WhatsApp messages = ~100 minutes
- 100 emails = ~8 minutes

---

## 🆘 Need Help?

1. **Check Activity Log** - Detailed error messages
2. **Review CSV Format** - Most issues are CSV related
3. **Test Connection** - Click TEST EMAIL before bulk send
4. **Start Small** - Test with 2-3 contacts first

---

## 📝 Version Info
- **App**: growHigh v1.0
- **Python**: 3.7+
- **Platform**: Windows, Mac, Linux
- **Build**: PyInstaller compatible

Enjoy using growHigh! 🚀
