# 🚀 Quick Start Guide - FoodStream Veggies Bot

## ✅ Setup Complete!

Your bot is ready to run locally. Here's what's been configured:

### Current Status
- ✅ Dependencies installed
- ✅ `.env` file created from template
- ✅ Google Sheets credentials found (`veggiebot-key.json`)
- ✅ App tested and running successfully

### What's Running
```
✅ Google Sheets connected: Veggie_Orders
⚠️  Using in-memory state storage (Redis not enabled - dev mode)
✅ FoodStream Veggies Bot Configuration
   - Environment: development
   - Price per Bundle: £5.00 (flat rate)
   - Volume Discounts: None (disabled)
   - Delivery Slots: 4 available
   - Admin Notifications: Disabled (costs Twilio credits)
```

---

## 🏃 Running the Bot Locally

### 1. **Start the Flask App**
```bash
py app.py
```

The app will start on `http://localhost:5000`

You should see:
```
✅ Google Sheets connected: Veggie_Orders
⚠️  Using in-memory state storage - data will be lost on restart!
 * Running on http://0.0.0.0:5000
```

### 2. **Expose with ngrok** (in a new terminal)
```bash
cd ngrok-v3-stable-windows-amd64
.\ngrok.exe http 5000
```

Copy the HTTPS URL shown (e.g., `https://abc123.ngrok.io`)

### 3. **Configure Twilio**
1. Go to [Twilio Console - WhatsApp Sandbox](https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox)
2. Set webhook URL to: `https://YOUR-NGROK-URL.ngrok.io/whatsapp`
3. Save settings

### 4. **Test It!**
Send a message to your Twilio WhatsApp number:
```
You: hi
Bot: Good afternoon! 👋 Welcome to FoodStream Veggies 🥬!
     Please tell me your name to start your order.
```

---

## ⚙️ Configuration (Optional)

Your `.env` file is already created. To customize:

```bash
notepad .env
```

### Key Settings to Update

**For Development (current setup):**
```bash
ENVIRONMENT=development
REDIS_ENABLED=false  # Uses in-memory (fine for local testing)
PRICE_PER_BUNDLE=5.00
ADMIN_NOTIFICATIONS_ENABLED=false  # Keeps it free
```

**For Production:**
```bash
ENVIRONMENT=production
REDIS_ENABLED=true
REDIS_URL=redis://your-redis-url:6379/0
PRICE_PER_BUNDLE=5.00
VOLUME_DISCOUNTS=  # Leave empty for flat pricing
ADMIN_PHONE=+447123456789
ADMIN_NOTIFICATIONS_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
```

---

## 🧪 Testing Commands

### Run Unit Tests
```bash
# Test pricing engine
py -m unittest tests.test_pricing -v

# Test validators
py -m unittest tests.test_validators -v

# Run all tests
py -m unittest discover tests -v
```

**Expected:** All 33 tests should pass ✅

### Test the API
```bash
# Check health endpoint (while app is running)
curl http://localhost:5000/
```

---

## 📊 Google Sheets Setup

Your sheet should have these headers:
```
Order ID | Name | Bundles | Unit Price | Total Price | Discount Applied | 
Address | Postcode | Delivery Date | Delivery Time Slot | Phone | 
Order Status | Created At | Updated At | Notes
```

**Note:** The bot will still work without these exact headers, but you'll get cleaner data with them.

---

## 🛠️ Troubleshooting

### "Redis connection failed"
This is normal in development! The bot automatically falls back to in-memory storage.
```
⚠️  Using in-memory state storage - data will be lost on restart!
```

### "Google Sheets error"
- Ensure `veggiebot-key.json` is in the project folder ✅ (already there)
- Check the service account has edit access to "Veggie_Orders" sheet

### "Twilio validation failed"
In development mode, webhook validation is automatically disabled. No action needed!

### Port already in use
```bash
# Kill any process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F

# Or change port in .env
PORT=5001
```

---

## 🚀 Deployment (When Ready)

### Option 1: Render (Recommended)
1. Push code to GitHub
2. Create new Web Service on [render.com](https://render.com)
3. Add Redis addon
4. Set environment variables from `.env`
5. Deploy!

### Option 2: Heroku
```bash
heroku create your-app-name
heroku addons:create heroku-redis:mini
heroku config:set GOOGLE_CREDS_JSON='paste_json_here'
git push heroku main
```

---

## 💡 Quick Tips

### Want to change pricing?
Edit `.env`:
```bash
PRICE_PER_BUNDLE=6.50
VOLUME_DISCOUNTS=  # Leave empty for flat pricing, or add like "10:10,20:15"
DELIVERY_FEE=2.00  # Optional delivery charge
```

### Want different delivery slots?
Edit `.env`:
```bash
DELIVERY_SLOTS=Saturday 2-4 PM,Saturday 4-6 PM,Sunday 10-12 PM,Sunday 2-4 PM
```

### Enable admin notifications?
Edit `.env` (requires Twilio credits):
```bash
ADMIN_PHONE=+447123456789
ADMIN_NOTIFICATIONS_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_PHONE_NUMBER=whatsapp:+14155238886
```

---

## 📱 WhatsApp Commands for Customers

- `HI` - Start new order
- `VIEW` - See last order
- `CANCEL` - Cancel order
- `HELP` - Show help
- `MODIFY` - Change order (during confirmation)

---

## 🎯 You're All Set!

Your enhanced veggie bot is ready to take orders! 🥬💚

**Next time you want to run it:**
1. Open terminal in `veggie_bot` folder
2. Run: `py app.py`
3. In another terminal: `.\ngrok-v3-stable-windows-amd64\ngrok.exe http 5000`
4. Update Twilio webhook with new ngrok URL
5. Start taking orders!

**Questions?** Check the main README.md for full documentation.

---

Made with 💚 for FoodStream Veggies
