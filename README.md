# ControlBot - Telegram Bot for Remote PC Control

A powerful Telegram bot for remote computer management through Telegram using Aiogram 3.

## ⚠️ Important Security Notice

**USE THIS BOT ONLY ON YOUR OWN DEVICES AND WITH PROPER PERMISSION!**

This bot provides remote control capabilities that can be potentially dangerous if misused. Only use it on:
- Your own personal computers
- Devices you have explicit permission to control
- Trusted networks and environments

**Never use this bot on devices you don't own or without proper authorization.**

## ⚖️ Legal & Ethical Use

**This bot is intended for administering your own machines only.**

### ✅ Permitted Use
- **Personal devices** you own and control
- **Work computers** with explicit employer permission
- **Family devices** with explicit owner consent
- **Educational purposes** in controlled environments

### ❌ Prohibited Use
- **Unauthorized access** to any system without explicit permission
- **Corporate networks** without written authorization
- **Public or shared computers** without owner consent
- **Any malicious activities** or unauthorized surveillance
- **Violation of local laws** or regulations

### 🚨 Legal Disclaimer
- **You are solely responsible** for your use of this software
- **Unauthorized access** to computer systems is illegal in most jurisdictions
- **Always obtain explicit permission** before using on any device
- **Respect privacy and security** of others
- **Use at your own risk** - developers assume no liability

**By using this software, you agree to use it ethically and legally.**

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Windows operating system
- Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Eklipti/TelegramControlBot.git
   cd TelegramControlBot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   .\.venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure the bot**
   - Create `.env` file based on `.env.example`
   - Add your Telegram Bot Token
   - Configure allowed user IDs

6. **Run the bot**
   ```bash
   python main.py
   ```
   
   Or use the provided batch file:
   ```bash
   ControlBot.bat
   ```

## 📚 Documentation

- **[Russian Documentation](docs/README_ru.md)** - Detailed installation and usage guide
- **[Command Reference](docs/all_commands.md)** - Complete list of all commands with examples
- **[Future Plans](docs/FUTURE.md)** - Upcoming features and improvements

## 🔧 Features

- **System Control**: Shutdown, restart, sleep, hibernate
- **File Management**: Upload, download, browse files
- **Process Management**: View and terminate processes
- **Screen Control**: Take screenshots, remote desktop
- **Security**: User authentication and private chat only
- **Monitoring**: System status and performance metrics

## 🎯 User Experience

- **Auto-command registration**: All commands automatically appear in Telegram menu
- **Startup notifications**: Users receive "🟢 Bot started" notification
- **Shutdown notifications**: Users receive "⛔ Bot stopped" notification
- **Intuitive interface**: `/start` for welcome, `/help` for command list
- **Context-aware help**: `/help <command>` for detailed information

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**.

Authors: Eklipti, Nlan_Cat

See [LICENSE](LICENSE) for the complete license text.

## 🧪 Testing

The project includes automated testing via GitHub Actions:

- **Code Quality**: Ruff linting and MyPy type checking
- **Smoke Tests**: Basic functionality and import validation
- **Compatibility**: Python 3.11 and 3.12 support

Run tests locally:
```bash
python run_tests.py
```

## 🤝 Contributing

Contributions are welcome! Please read the license terms and ensure compliance with AGPL-3.0-or-later requirements.

Before submitting a pull request:
1. Run the test suite: `python run_tests.py`
2. Ensure all tests pass
3. Follow the existing code style

## 📞 Support

For questions and support, please open an issue on the [GitHub repository](https://github.com/Eklipti/TelegramControlBot).

---

**Remember: Use responsibly and only on devices you own or have permission to control!**
