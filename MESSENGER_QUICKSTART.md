# 🚀 Messenger Quick Start

## ⚡ 3-Minute Setup

### Step 1: Find Your Facebook Username
Go to your Facebook profile → Look at URL:
- `facebook.com/john.doe` → Username is `john.doe`
- `facebook.com/100012345678` → Username is `100012345678`

### Step 2: Create CSV File
Create `test.csv` with:
```csv
username
your.username.here
```

### Step 3: Send Test Message
1. Run app.py
2. Select **Messenger** platform
3. Click **🔐 TEST MESSENGER LOGIN** (browser opens)
4. Log in to Facebook
5. Import your `test.csv`
6. Type: "Testing Messenger automation"
7. Click **▶ START SENDING**

### Step 4: Check Messenger
Open messenger.com → You should see the message you sent to yourself!

## ✅ If It Works
You're ready! Create a CSV with friend usernames and send bulk messages.

## ❌ If It Doesn't Work
1. Check Activity Log in app for errors
2. Verify username is correct (test at messenger.com/t/your.username)
3. Make sure you're logged in to Facebook
4. Read MESSENGER_SETUP_GUIDE.md for troubleshooting

## 📋 CSV Format for Bulk Sending
```csv
username,name
john.doe,John Doe
jane.smith,Jane Smith
mark.wilson,Mark Wilson
```

## 💡 Tips
- Test with yourself first (safest)
- Use real usernames from facebook.com/username
- Limit to 20-50 messages per session
- Take breaks to avoid spam detection

## 🔗 Need Help?
Read: `MESSENGER_SETUP_GUIDE.md` (complete guide)
