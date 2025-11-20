# Email (SMTP) Setup Guide for growHigh

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

The app now includes `email-validator==2.1.0` for email validation.

---

## Email Platform Configuration

### Using Gmail ✉️

**Step 1: Enable 2-Factor Authentication**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification

**Step 2: Generate App Password**
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Copy the 16-character password
4. In growHigh, enter your Gmail address and this app password (NOT your regular password)

**Step 3: Test Connection**
1. Click "🧪 TEST EMAIL" button
2. You should see "✅ Email connection successful!" message

---

### Using Outlook/Hotmail 📧

**Step 1: Generate App Password**
1. Go to https://account.microsoft.com/security
2. Advanced security options
3. Create app passwords
4. Copy the generated password

**Step 2: Configure in growHigh**
1. Enter your Outlook email address
2. Paste the app password
3. Click "🧪 TEST EMAIL" to verify

---

### Custom Email Providers (Optional)

The app auto-detects:
- Gmail → `smtp.gmail.com:465 (SSL)`
- Outlook/Hotmail → `smtp-mail.outlook.com:587 (TLS)`

For other providers, contact your email administrator for SMTP settings.

---

## CSV Format for Email

### Required Column: `email` or `email_address`

```csv
email,name,subject
john@example.com,John Smith,Custom Subject
jane@example.com,Jane Doe,Hello Jane
```

### Supported Column Names:
- **Email**: `email`, `email_address`, `mail`, `recipient`
- **Name**: `name`, `contact_name`, `fullname`, `full_name`, `customer_name`, `recipient_name`
- **Subject** (optional): `subject`, `email_subject`

### Auto-Generated Subject
If no subject column exists, the app creates:
```
Subject: Hello {name}!
```

---

## Features

✅ **Email Validation**: Checks email format before sending
✅ **Name Personalization**: "Hello {name}," in message body
✅ **Custom Subjects**: Per-recipient subject lines
✅ **Connection Testing**: Verify credentials before bulk send
✅ **Countdown Timer**: Shows wait time between emails (5 seconds)
✅ **Error Handling**: Detailed logging of failed sends
✅ **Real-time Stats**: Track sent/failed/pending emails

---

## Platform Switching

1. **Select Platform**: Use radio buttons at top (WhatsApp / Email)
2. **WhatsApp Mode**:
   - Need phone numbers in CSV
   - Requires WhatsApp Web login
   - 60-second delay between messages

3. **Email Mode**:
   - Need email addresses in CSV
   - Requires SMTP credentials
   - 5-second delay between emails
   - Faster than WhatsApp (no QR scanning needed)

---

## Common Issues

### ❌ "Authentication failed" Error
- **Cause**: Wrong email or password
- **Solution**: 
  - For Gmail: Use 16-char app password, not your regular password
  - For Outlook: Double-check password is copied correctly
  - Click "🧪 TEST EMAIL" to verify credentials

### ❌ "Invalid email format" Warning
- **Cause**: CSV contains malformed email addresses
- **Solution**: Check CSV for typos in email column
- **Example of invalid**: `john@`, `jane@.com`, `noemail`

### ❌ "No valid emails found" Error
- **Cause**: Column named "email" not found in CSV
- **Solution**: 
  - Ensure CSV has `email` or `email_address` column
  - Check column names are exact (case-insensitive)

### ⚠️ Emails being marked as spam
- **Cause**: Sending from automated account
- **Solution**:
  - Add unsubscribe link in message
  - Include contact information
  - Avoid spam trigger words
  - Limit sending rate (5-10 second delays)

---

## Security Notes

⚠️ **Password Storage**:
- Passwords are stored **in memory only** during sending
- NOT saved to file or configuration
- Cleared when app closes
- Never hardcoded in the app

✅ **Best Practices**:
- Use app passwords, not your main password
- Enable 2-Factor Authentication on your email
- Don't share screenshots with passwords visible
- Review all emails before bulk sending

---

## Performance Tips

1. **Batch Size**: Send in groups of 100-500 to avoid rate limits
2. **Delays**: 5 seconds between emails is safe
3. **Time of Day**: Send during business hours (9 AM - 5 PM)
4. **Subject Lines**: Keep under 70 characters for mobile
5. **Message Length**: Shorter messages send faster

---

## Email vs WhatsApp Comparison

| Feature | Email (SMTP) | WhatsApp |
|---------|-------------|----------|
| **Setup Time** | 2 minutes | 1 minute |
| **Authentication** | App Password | QR Scan |
| **Delay Between** | 5 seconds | 60 seconds |
| **Speed (100 msgs)** | ~8 minutes | ~100 minutes |
| **Personalization** | Subject + Body | Body only |
| **Delivery Rate** | 95%+ | 99%+ |
| **Cost** | Free | Free |
| **Best For** | Marketing, Info | Personal Messages |

---

## Example Workflows

### Workflow 1: Marketing Campaign
```
CSV: customer_emails.csv
├─ email: customer@company.com
├─ name: John
├─ subject: Exclusive Offer Just for You!

Message: "Check out our new products..."
Platform: Email (SMTP)
Expected Time: ~5 minutes for 100 recipients
```

### Workflow 2: Event Reminders
```
CSV: attendees.csv
├─ email: attendee@company.com
├─ name: Jane

Message: "Event starts tomorrow at 2 PM. Don't miss it!"
Platform: Email (SMTP)
Expected Time: ~10 minutes for 500 recipients
```

### Workflow 3: Notification Blast
```
CSV: users.csv
├─ phone: 9779803661701
├─ name: Sam

Message: "Your order is ready for pickup"
Platform: WhatsApp
Expected Time: ~2 hours for 100 recipients (with 60s delays)
```

---

## Contact & Support

For issues or questions:
1. Check this guide first
2. Review Activity Log for specific errors
3. Test connection before bulk sending
4. Verify CSV format matches requirements

Good luck with your campaigns! 🚀
