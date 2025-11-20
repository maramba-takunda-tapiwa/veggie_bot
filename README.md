# 🥬 FoodStream Veggies Bot

A production-ready WhatsApp chatbot for managing vegetable orders using Twilio, Flask, Google Sheets, and Redis.

## ✨ Features

### 🛒 **Customer Features**
- **WhatsApp Integration**: Customers can place orders directly through WhatsApp
- **Interactive Chat**: Conversational order flow (name → bundles → address → postcode → delivery slot)
- **Dynamic Pricing**: Real-time price calculation with volume discounts
- **Order Modification**: Change quantity, address, or delivery slot before confirmation
- **Order Tracking**: View and cancel orders with unique order IDs
- **Delivery Scheduling**: Choose from available delivery time slots

### 💰 **Pricing System**
- Configurable price per bundle (flat rate)
- Optional volume discounts (can be enabled if needed)
- Optional delivery fee
- Real-time pricing display before order confirmation

### 🔒 **Security & Reliability**
- **Webhook Validation**: Verifies requests are from Twilio
- **Rate Limiting**: Prevents abuse (max 10 messages/minute)
- **Input Sanitization**: Protects against injection attacks
- **Redis State Persistence**: Conversation state survives server restarts
- **Structured Logging**: Comprehensive logging for debugging and monitoring

### 👨‍💼 **Admin Features**
- **SMS/WhatsApp Notifications**: Instant alerts for new orders
- **Google Sheets Storage**: All orders automatically saved with pricing details
- **Order Status Tracking**: Monitor order lifecycle
- **Customer History**: Track repeat customers

## 🛠️ Tech Stack

- **Flask**: Web framework for webhook handling
- **Twilio**: WhatsApp Business API integration
- **Google Sheets API**: Order storage and management
- **Redis**: Persistent state management (optional, falls back to in-memory)
- **Python 3**: Backend logic with modular architecture

## 📦 Prerequisites

- Python 3.8+
- Twilio account with WhatsApp sandbox or Business API
- Google Cloud Project with:
  - Google Sheets API enabled
  - Google Drive API enabled
  - Service account credentials
- Redis (optional, for production state persistence)
- ngrok (for local testing)

## 🚀 Installation

### 1. **Clone the repository**
```bash
git clone https://github.com/maramba-takunda-tapiwa/veggie_bot.git
cd veggie_bot
```

### 2. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Set up Google Sheets**
- Create a Google Sheet named "Veggie_Orders"
- Add headers: 
  ```
  Order ID | Name | Bundles | Unit Price | Total Price | Discount Applied | 
  Address | Postcode | Delivery Date | Delivery Time Slot | Phone | 
  Order Status | Created At | Updated At | Notes
  ```
- Share the sheet with your service account email (found in `veggiebot-key.json`)

### 4. **Configure environment variables**
```bash
# Copy the example file
copy .env.example .env

# Edit .env with your actual values
notepad .env
```

**Required Configuration:**
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` - Get from [Twilio Console](https://console.twilio.com)
- `GOOGLE_CREDS_JSON` - Service account JSON (for production) or use `veggiebot-key.json` file
- `PRICE_PER_BUNDLE` - Your price per bundle (default: £5.00)
- `VOLUME_DISCOUNTS` - Discount tiers (e.g., "10:10,20:15")
- `DELIVERY_SLOTS` - Available delivery times

**Optional Configuration:**
- `REDIS_ENABLED=true` & `REDIS_URL` - For production state persistence
- `ADMIN_PHONE` & `ADMIN_NOTIFICATIONS_ENABLED=true` - For order notifications

### 5. **Enable required APIs**
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Enable Google Sheets API
- Enable Google Drive API

## 🏃 Running the Application

### **Development Mode**
```bash
# Start Flask app
python app.py

# In another terminal, start ngrok
ngrok http 5000
```

### **Configure Twilio**
1. Copy your ngrok URL (e.g., `https://xxxx.ngrok.io`)
2. Go to Twilio Console → WhatsApp Sandbox Settings
3. Set webhook URL to: `https://xxxx.ngrok.io/whatsapp`

### **Production Deployment**

#### **Option 1: Render**
1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Add environment variables
4. Deploy!

#### **Option 2: Heroku**
```bash
# Install Heroku CLI, then:
heroku create your-app-name
heroku addons:create heroku-redis:mini
git push heroku main
```

## 💬 How to Use

### **Customer Interaction**

**Example conversation:**
```
User: hi

Bot: Good afternoon! 👋 Welcome to FoodStream Veggies 🥬!
     Please tell me your name to start your order.

User: Sarah

Bot: Nice to meet you, Sarah! 🧺
     How many bundles would you like to order?

User: 12

Bot: Got it ✅
     
     💰 Pricing Breakdown
     • 12 bundles × £5.00 = £60.00
     • TOTAL: £60.00
     
     Please provide your delivery address:

User: 25 Oak Street

Bot: Thank you! 📍
     Now please provide your postcode:

User: SW1A 1AA

Bot: Perfect! 🎯
     
     Choose your delivery slot:
     🕒 1. Saturday 2-4 PM
     🕒 2. Saturday 4-6 PM
     🕒 3. Sunday 10-12 PM
     🕒 4. Sunday 2-4 PM
     
     Reply with the number of your preferred slot.

User: 1

Bot: ✅ Please Confirm Your Order
     
     👤 Name: Sarah
     🥬 Bundles: 12
     📍 Address: 25 Oak Street, SW1A 1AA
     🚚 Delivery: Saturday 2-4 PM
     
     💰 Pricing Breakdown
     • 12 bundles × £5.00 = £60.00
     • TOTAL: £60.00
     
     Reply YES to confirm or MODIFY to make changes.

User: yes

Bot: 🎉 Order Confirmed!
     
     🆔 Order ID: 3FA8B2
     👤 Name: Sarah
     🥬 Bundles: 12
     📍 Address: 25 Oak Street, SW1A 1AA
     🚚 Delivery: Saturday 2-4 PM
     
     💡 Commands:
     • Type VIEW to see your order
     • Type CANCEL to cancel
     • Type HI for a new order
     
     Thank you for supporting FoodStream Veggies! 💚
```

### **Available Commands**
- `HI` / `HELLO` / `START` - Start new order
- `VIEW` / `STATUS` - View your last order
- `CANCEL` - Cancel your order
- `HELP` - Show help information
- `MODIFY` - Modify order before confirmation (during confirmation stage)
- `DEBUG` - Show current conversation state (development only)

## 📁 Project Structure

```
veggie_bot/
├── app.py                     # Main Flask application
├── config.py                  # Configuration management
├── state_manager.py           # Redis/in-memory state storage
├── validators.py              # Input validation
├── pricing.py                 # Pricing engine
├── notifications.py           # Admin notifications
├── utils.py                   # Helper utilities
├── tests/                     # Unit tests
│   ├── __init__.py
│   ├── test_pricing.py
│   └── test_validators.py
├── .env.example              # Example environment variables
├── .env                      # Your environment variables (DO NOT COMMIT)
├── veggiebot-key.json       # Google service account (DO NOT COMMIT)
├── requirements.txt          # Python dependencies
├── Procfile                  # Deployment configuration
└── README.md                 # This file
```

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m unittest tests.test_pricing

# Run with coverage
pip install pytest pytest-cov
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

## 🔒 Security

- Never commit `.env` file or `veggiebot-key.json` to version control
- The `.gitignore` file is configured to exclude sensitive files
- Enable webhook validation in production (`TWILIO_AUTH_TOKEN` required)
- Use Redis with authentication in production
- Keep your Twilio credentials secure
- Rate limiting protects against message spam

## ⚙️ Configuration

### **Pricing Configuration**
```bash
# .env file
PRICE_PER_BUNDLE=5.00
CURRENCY_SYMBOL=£
DELIVERY_FEE=0.00
VOLUME_DISCOUNTS=  # Leave empty for flat pricing, or set like "10:10,20:15"
```

### **Delivery Slots**
```bash
DELIVERY_SLOTS=Saturday 2-4 PM,Saturday 4-6 PM,Sunday 10-12 PM,Sunday 2-4 PM
```

### **Feature Flags**
```bash
ENABLE_ORDER_MODIFICATION=true
ENABLE_ORDER_TRACKING=true
ENABLE_CUSTOMER_HISTORY=true
```

## 🐛 Troubleshooting

### **Redis Connection Issues**
If Redis is not available, the bot automatically falls back to in-memory storage with a warning:
```
⚠️  Using in-memory state storage - data will be lost on restart!
```
For development, this is fine. For production, set up Redis.

### **Google Sheets Errors**
- Ensure service account email has edit access to the sheet
- Verify sheet name matches `GOOGLE_SHEET_NAME` in `.env`
- Check that both Sheets API and Drive API are enabled

### **Rate Limiting**
If users see "Too many messages", adjust:
```bash
RATE_LIMIT_MESSAGES=20          # Increase limit
RATE_LIMIT_WINDOW_SECONDS=60    # Time window
```

## 📝 License

This project is open source and available under the MIT License.

## 👤 Author

**Maramba Takunda Tapiwa**
- GitHub: [@maramba-takunda-tapiwa](https://github.com/maramba-takunda-tapiwa)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 🙏 Acknowledgments

Built with:
- [Flask](https://flask.palletsprojects.com/)
- [Twilio](https://www.twilio.com/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Redis](https://redis.io/)

---

Made with 💚 for fresh veggie deliveries by FoodStream Veggies
