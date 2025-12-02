# Facebook Messenger Setup Guide

## 🎯 Overview
Send bulk messages to Facebook Messenger contacts using their Facebook usernames.

## 📋 Requirements
1. **Chrome Browser** (installed automatically)
2. **Facebook Account** (logged in to Messenger)
3. **CSV File** with username column

## 🚀 Quick Start

### 1. Prepare Your CSV File
Create a CSV file with the following structure:

```csv
username,name
john.doe,John Doe
jane.smith,Jane Smith
mark.wilson,Mark Wilson
```

**CSV Columns:**
- `username` (required): Facebook username or profile ID
- `name` (optional): Contact's name for personalization

### 2. Finding Facebook Usernames

**Method 1: From Profile URL**
1. Visit the person's Facebook profile
2. Look at the URL: `https://www.facebook.com/john.doe`
3. Username is: `john.doe`

**Method 2: From Messenger**
1. Open Messenger web (messenger.com)
2. Click on the conversation
3. Look at the URL: `https://www.messenger.com/t/100012345678`
4. ID is: `100012345678` (use this as username)

**Method 3: Custom Username**
- Some profiles have custom URLs like: `facebook.com/JohnDoeOfficial`
- Username would be: `JohnDoeOfficial`

### 3. Using the App

1. **Launch the app**
2. **Select Platform**: Choose "Messenger"
3. **Test Login**: Click "🔐 TEST MESSENGER LOGIN" button
   - Browser will open to messenger.com
   - Log in to your Facebook account
   - **Keep the browser window open**
4. **Import CSV**: Select your CSV file with usernames
5. **Compose Message**: Type your message
6. **Start Sending**: Click "▶ START SENDING"

## ⚙️ How It Works

1. **Browser Opens**: Chrome opens with Messenger web interface
2. **Login Once**: You log in to Facebook Messenger (saved in profile)
3. **Automated Sending**: For each username:
   - Opens chat: `messenger.com/t/{username}`
   - Finds message box
   - Types and sends message
   - Waits 3-7 seconds (random delay to avoid spam detection)

## 💡 Tips for Success

### 1. Valid Usernames
- ✅ Use exact Facebook username or profile ID
- ❌ Don't use display names (like "John Doe")
- ✅ Test with 1-2 contacts first

### 2. Message Personalization
Use `{{name}}` or `{name}` in your message to auto-insert contact names:

```
Hello {{name}},

This is a personalized message for you!

Best regards
```

Will become:
```
Hello John Doe,

This is a personalized message for you!

Best regards
```

### 3. Avoid Spam Blocks
- ⏱️ **Random Delays**: 3-7 seconds between messages (automatic)
- 📊 **Small Batches**: Send 20-50 messages per session
- ⏸️ **Take Breaks**: Wait 1-2 hours between batches
- 🔐 **Use Row Ranges**: Send rows 1-20, then 21-40, etc.

### 4. Browser Profile
- The app saves your login in a Chrome profile
- You only need to log in once
- Profile location: `%APPDATA%\AutoMessenger\chrome_profile`

## 🚨 Troubleshooting

### Problem: "No message box found"
**Solution:**
- Username might be invalid
- Profile might have messaging disabled
- Try opening `messenger.com/t/{username}` manually to verify

### Problem: Login keeps asking
**Solution:**
- Delete Chrome profile: `%APPDATA%\AutoMessenger\chrome_profile`
- Log in again using TEST LOGIN button
- Enable "Keep me logged in" on Facebook

### Problem: Messages not sending
**Solution:**
1. Check if you can send messages manually to that username
2. Verify the username is correct (check profile URL)
3. Some accounts block messages from non-friends

### Problem: "Continue chatting" button appears
**Solution:**
- This is normal for message requests
- The app automatically clicks this button
- If it fails, you might not have message permission

## 📝 CSV Format Examples

### Basic Format (Username Only)
```csv
username
john.doe
jane.smith
mark.wilson
```

### With Names (Recommended)
```csv
username,name
john.doe,John Doe
jane.smith,Jane Smith
mark.wilson,Mark Wilson
```

### With Profile IDs
```csv
username,name
100012345678,Customer A
100087654321,Customer B
john.doe,Customer C
```

## 🔒 Privacy & Security

- **Login Credentials**: Never stored by the app
- **Browser Profile**: Saved locally on your computer
- **Messages**: Sent directly from your Facebook account
- **Rate Limiting**: Built-in delays to prevent spam detection

## ⚠️ Facebook Policies

**Important Notes:**
1. **Terms of Service**: Automated messaging may violate Facebook's Terms
2. **Spam Prevention**: Only message people who expect to hear from you
3. **Friends Only**: Best results with Facebook friends
4. **Account Risk**: Excessive messaging can lead to temporary blocks
5. **Personal Use**: Use responsibly and respect privacy

## 🎯 Best Practices

✅ **DO:**
- Send to people who know you
- Personalize messages with names
- Use small batches (20-50 at a time)
- Take breaks between batches
- Test with 1-2 contacts first

❌ **DON'T:**
- Send spam or unsolicited messages
- Send to strangers without permission
- Use for marketing without consent
- Send identical messages rapidly
- Ignore Facebook's messaging limits

## 📊 Advanced Settings

### Row Range Control
Send specific rows from your CSV:
- **From**: Starting row number (e.g., 1)
- **To**: Ending row number (e.g., 20)

Example: Send to first 20 contacts, then 21-40, etc.

### Delay Configuration
- Default: 3-7 seconds (random)
- Configurable in Advanced Settings
- Minimum recommended: 3 seconds

## 🆘 Getting Help

If you encounter issues:
1. Check this guide first
2. Verify username format
3. Test manually at messenger.com
4. Use TEST LOGIN button to verify browser access
5. Check Activity Log in the app for error messages

## 📚 Additional Resources

- [Find Facebook Username](https://www.facebook.com/help/211813265517027)
- [Messenger Web](https://www.messenger.com)
- [Facebook Privacy Settings](https://www.facebook.com/settings?tab=privacy)

---

**Last Updated**: November 2025
**App Version**: 2.0 (with Messenger support)
