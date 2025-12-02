# 📱 SMS Setup Guide - Android Phone Integration

## Quick Overview

This guide helps you set up your Android phone to send bulk SMS messages through the growHigh application using USB connection and ADB (Android Debug Bridge).

---

## ✅ Requirements

- **Android phone** with active SIM card
- **USB cable** to connect phone to computer
- **Windows PC** (Windows 7 or later)
- **ADB drivers** (usually auto-installed)
- **growHigh application** with SMS support

---

## 🚀 Step-by-Step Setup

### **Step 1: Enable Developer Options on Android**

1. Open **Settings** on your Android phone
2. Scroll down to **About Phone**
3. Find **Build Number** (usually at the bottom)
4. **Tap Build Number 7 times** rapidly
5. You'll see "You are now a developer!" message

---

### **Step 2: Enable USB Debugging**

1. Go back to **Settings**
2. Find **Developer Options** (or **System** > **Developer Options**)
3. Enable **USB Debugging** toggle
4. You may also want to enable:
   - **Stay awake** (keeps screen on while charging)
   - **USB debugging (Security settings)** (if available)

---

### **Step 3: Connect Phone to Computer**

1. Connect phone to PC using **USB cable**
2. On your phone, you'll see a prompt: **"Allow USB debugging?"**
3. Check **"Always allow from this computer"**
4. Tap **OK** or **Allow**

**Important:** Make sure you select **File Transfer** or **MTP mode**, not just charging!

---

### **Step 4: Install ADB on Your Computer**

#### **Option A: Install via Python (Automatic)**
```bash
pip install pure-python-adb
pip install adb-shell
```

This is already done if you ran:
```bash
pip install -r requirements.txt
```

#### **Option B: Install Platform Tools (Manual)**

1. Download **Android Platform Tools** from:
   https://developer.android.com/studio/releases/platform-tools

2. Extract ZIP file to a folder (e.g., `C:\adb`)

3. Add ADB to Windows PATH:
   - Right-click **This PC** > **Properties**
   - Click **Advanced system settings**
   - Click **Environment Variables**
   - Under **System Variables**, find **Path**
   - Click **Edit** > **New**
   - Add: `C:\adb\platform-tools` (or your extraction path)
   - Click **OK** on all windows

---

### **Step 5: Start ADB Server**

Open **Command Prompt** or **PowerShell** and run:

```powershell
adb start-server
```

You should see:
```
* daemon not running; starting now at tcp:5037
* daemon started successfully
```

**Check connected devices:**
```powershell
adb devices
```

Expected output:
```
List of devices attached
ABC123456789    device
```

If you see "unauthorized", check your phone for the USB debugging prompt.

---

### **Step 6: Test Connection in growHigh**

1. Open **growHigh** application
2. Select **SMS** platform (radio button)
3. Click **🧪 TEST PHONE CONNECTION** button
4. You should see: ✅ **"Android phone ready for SMS sending!"**

---

## 🎯 Sending SMS via growHigh

### **Basic Workflow:**

1. **Prepare CSV file** with phone numbers:
   ```csv
   phone,name
   9779803661701,John
   9779807776666,Jane
   9801234567,Mike
   ```

2. **Open growHigh** application

3. **Select SMS platform**

4. **Load CSV file** (Browse button)

5. **Type your message** (keep under 160 characters for single SMS)

6. **Optional:** Set delay between messages (default: 5 seconds)

7. **Click START SENDING**

8. **Watch the Activity Log** for real-time progress

---

## ⚙️ Advanced Settings

### **Message Length**
- **Single SMS:** Up to 160 characters
- **Multi-part SMS:** Over 160 chars splits into multiple SMS
  - 153 chars per SMS after first
  - Example: 320 chars = 3 SMS messages

### **Delay Between SMS**
- Default: **5 seconds**
- Adjust in **Advanced Settings** section
- Recommended: 3-10 seconds to avoid carrier throttling

### **Row Range**
- Send to specific rows only
- Example: Rows 10-50 from CSV
- Useful for testing or resuming failed sends

### **Skip 01 Numbers**
- Enable to skip landline numbers
- Only applicable to Nepal-specific numbers

---

## 🛠️ Troubleshooting

### **❌ "No Android device detected"**

**Causes:**
- USB debugging not enabled
- Phone not connected
- USB debugging prompt not accepted
- ADB server not running
- Wrong USB mode (charging only)

**Solutions:**
1. Check USB debugging is ON
2. Reconnect USB cable
3. Accept USB debugging prompt on phone
4. Run `adb start-server` in command prompt
5. Change USB mode to **File Transfer**
6. Try different USB port or cable

---

### **❌ "ADB library not installed"**

**Solution:**
```bash
pip install pure-python-adb adb-shell
```

Or reinstall requirements:
```bash
pip install -r requirements.txt
```

---

### **❌ "Device unauthorized"**

**Solution:**
1. Check your phone screen
2. Accept the **"Allow USB debugging?"** prompt
3. Check **"Always allow from this computer"**
4. Run `adb devices` again

---

### **❌ SMS not sending / stuck**

**Possible causes:**
1. **Phone screen locked** - Unlock phone during sending
2. **Battery saver active** - Disable battery optimization
3. **SMS app permissions** - Grant SMS permissions
4. **Network issues** - Check SIM has signal

**Solutions:**
1. Keep phone **unlocked** during sending
2. Disable **battery saver mode**
3. Grant SMS app all permissions
4. Check phone has **network signal**
5. Try sending 1 test SMS manually first

---

### **❌ "Error: SMS send failed"**

**Solution:**
1. Check if SMS app is default messaging app
2. Clear SMS app cache (Settings > Apps > Messages > Clear Cache)
3. Restart phone
4. Re-enable USB debugging
5. Try different SMS app (e.g., Google Messages)

---

## 💡 Tips & Best Practices

### **Performance Tips:**
- ✅ Keep phone screen **unlocked** during bulk sending
- ✅ Connect phone to **charger** (battery drains fast)
- ✅ Disable **battery optimization** for SMS app
- ✅ Use **airplane mode off** (need network for SMS)
- ✅ Close other apps on phone
- ✅ Use high-quality USB cable

### **Message Tips:**
- ✅ Keep messages **under 160 characters** when possible
- ✅ Avoid special characters (😊 emojis count as multiple chars)
- ✅ Test with **2-3 contacts** before bulk sending
- ✅ Personalize with {name} placeholder
- ✅ Include unsubscribe instructions for marketing

### **Privacy & Compliance:**
- ✅ Get **consent** before sending bulk SMS
- ✅ Include **opt-out option**
- ✅ Follow local SMS marketing laws
- ✅ Don't send spam or unsolicited messages
- ✅ Respect Do Not Disturb hours

---

## 📊 SMS vs WhatsApp vs Email

| Feature | SMS (Android) | WhatsApp | Email |
|---------|--------------|----------|-------|
| **Setup Time** | 5-10 minutes | 2 minutes | 2 minutes |
| **Hardware Needed** | Android phone | None | None |
| **Cost** | Carrier charges | Free (internet) | Free (internet) |
| **Speed** | 1-2 SMS/sec | 1 msg/min | 12 msgs/min |
| **Length Limit** | 160 chars | Unlimited | Unlimited |
| **Delivery Rate** | 99%+ | 99%+ | 95%+ |
| **Attachments** | No (MMS only) | Yes | Yes |
| **Internet Required** | No | Yes | Yes |
| **Best For** | OTP, Alerts | Personal msgs | Marketing |

---

## 🔒 Security & Privacy

### **What Data is Accessed?**
- **Phone serial number** (for identification)
- **SMS sending capability** (via ADB commands)
- **No personal data** is collected or stored

### **Is it Safe?**
- ✅ Uses official Android Debug Bridge (ADB)
- ✅ No root required
- ✅ No malware or spyware
- ✅ Open-source libraries
- ✅ All operations local (no cloud)

### **What About My Contacts?**
- Your phone contacts are **NOT accessed**
- Only phone numbers from your CSV file are used
- No data sent to external servers

---

## 🆘 Common Questions

### **Q: Will this drain my phone battery?**
**A:** Yes, keep phone connected to charger during bulk sending.

### **Q: Can I use this on iPhone?**
**A:** No, this feature requires Android with USB debugging. iPhone doesn't support ADB.

### **Q: Does my phone need to be rooted?**
**A:** No, USB debugging is sufficient. No root required.

### **Q: Will this delete my phone's SMS history?**
**A:** No, sent messages appear in your SMS app like normal messages.

### **Q: Can I send to international numbers?**
**A:** Yes, as long as your SIM plan supports international SMS.

### **Q: What happens if phone disconnects during sending?**
**A:** The app will stop and log an error. Reconnect and resume from where it stopped.

### **Q: Can I use multiple phones?**
**A:** Only one phone at a time. ADB connects to first detected device.

### **Q: Does the SMS app need to be open?**
**A:** No, the app sends SMS via intents (background sending).

---

## 📞 Support & Help

### **Still Having Issues?**

1. **Check Activity Log** in growHigh for detailed error messages
2. **Run ADB commands** manually:
   ```bash
   adb devices
   adb shell pm list packages | findstr sms
   ```
3. **Test manual SMS send** via ADB:
   ```bash
   adb shell am start -a android.intent.action.SENDTO -d sms:1234567890 --es sms_body "Test"
   ```

### **Additional Resources:**
- Android Developer Docs: https://developer.android.com/studio/command-line/adb
- Pure Python ADB: https://github.com/Swind/pure-python-adb
- XDA Forums: https://forum.xda-developers.com/

---

## ✅ Quick Checklist

Before sending SMS, verify:

- [ ] USB debugging enabled on phone
- [ ] Phone connected via USB cable
- [ ] USB debugging prompt accepted
- [ ] ADB server running (`adb start-server`)
- [ ] Phone detected (`adb devices`)
- [ ] Phone unlocked (screen on)
- [ ] Phone has network signal (SIM active)
- [ ] CSV file with phone numbers loaded
- [ ] Message typed (< 160 chars recommended)
- [ ] TEST PHONE CONNECTION successful

---

## 🎉 You're Ready!

Your Android phone is now configured as an SMS gateway. Start sending bulk SMS messages through growHigh!

**Happy Messaging! 📱✉️**

---

**Version:** 1.0  
**Last Updated:** November 13, 2025  
**Status:** ✅ Complete
