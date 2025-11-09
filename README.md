# 🥬 Marr's Veggie Orders Bot

A WhatsApp chatbot for managing vegetable orders using Twilio, Flask, and Google Sheets.

## 📋 Features

- **WhatsApp Integration**: Customers can place orders directly through WhatsApp
- **Interactive Chat**: Conversational order flow that asks for name, bundle quantity, and delivery time
- **Google Sheets Storage**: All orders are automatically saved to a Google Sheet
- **Real-time Confirmation**: Customers receive instant order confirmation

## 🛠️ Tech Stack

- **Flask**: Web framework for handling webhook requests
- **Twilio**: WhatsApp Business API integration
- **Google Sheets API**: Order storage and management
- **Python 3**: Backend logic

## 📦 Prerequisites

- Python 3.x
- Twilio account with WhatsApp sandbox
- Google Cloud Project with:
  - Google Sheets API enabled
  - Google Drive API enabled
  - Service account credentials
- ngrok (for local testing)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/maramba-takunda-tapiwa/veggie_bot.git
   cd veggie_bot
   ```

2. **Install dependencies**
   ```bash
   pip install flask twilio gspread google-auth
   ```

3. **Set up Google Sheets**
   - Create a Google Sheet named "Veggie_Orders"
   - Add headers: `Name`, `Bundles`, `Delivery Time`, `Phone`, `Timestamp`
   - Share the sheet with your service account email (found in `veggiebot-key.json`)

4. **Add your service account credentials**
   - Download your service account JSON file from Google Cloud Console
   - Rename it to `veggiebot-key.json`
   - Place it in the project root directory

5. **Enable required APIs**
   - Go to Google Cloud Console
   - Enable Google Sheets API
   - Enable Google Drive API

## 🏃 Running the Application

1. **Start the Flask app**
   ```bash
   python app.py
   ```

2. **Expose your local server (for development)**
   ```bash
   ngrok http 5000
   ```

3. **Configure Twilio**
   - Copy your ngrok URL (e.g., `https://xxxx.ngrok.io`)
   - Go to Twilio Console → WhatsApp Sandbox Settings
   - Set webhook URL to: `https://xxxx.ngrok.io/whatsapp`

## 💬 How to Use

Customers interact with the bot through WhatsApp:

1. Send a message to start
2. Bot asks for their name
3. Bot asks how many bundles they want
4. Bot asks for delivery time
5. Order is confirmed and saved to Google Sheets

**Example conversation:**
```
Bot: 👋 Welcome to Marr's Veggie Orders 🥬!
     Please tell me your name to start your order.

User: John

Bot: Nice to meet you, John! 🧺
     How many bundles would you like to order?

User: 3

Bot: Got it ✅
     When should we deliver your veggies? (e.g. Saturday 3PM)

User: Saturday 2PM

Bot: ✅ Order confirmed!
     👤 Name: John
     🥬 Bundles: 3
     🕒 Delivery: Saturday 2PM
     We'll deliver this weekend 🚚
     Thank you for supporting Marr's Veggie Orders! 💚
```

## 📁 Project Structure

```
veggie_bot/
├── app.py                          # Main Flask application
├── veggiebot-key.json             # Google service account credentials (DO NOT COMMIT)
├── .gitignore                      # Git ignore file
├── Procfile                        # Deployment configuration
├── requirements.txt                # Python dependencies (if needed)
└── README.md                       # This file
```

## 🔒 Security

- Never commit `veggiebot-key.json` to version control
- The `.gitignore` file is configured to exclude sensitive files
- Keep your Twilio credentials secure

## 🌐 Deployment

For production deployment, consider using:
- **Heroku**: Easy deployment with Procfile
- **Google Cloud Run**: Serverless container deployment
- **AWS EC2**: Traditional server hosting

## 📝 License

This project is open source and available under the MIT License.

## 👤 Author

**Maramba Takunda Tapiwa**
- GitHub: [@maramba-takunda-tapiwa](https://github.com/maramba-takunda-tapiwa)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

Made with 💚 for fresh veggie deliveries
