# ControlBot v2.2.1 - Telegram Bot for Remote PC Control

A powerful Telegram bot for remote computer management through Telegram using Aiogram 3. ControlBot provides comprehensive remote control capabilities for Windows systems with a focus on security and ease of use.

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

## 📁 Project Structure

```
ControlBot_v2/
├── app/                    # Main application code
│   ├── config/            # Configuration modules (Pydantic Settings)
│   ├── core/              # Core functionality (security, etc.)
│   ├── handlers/          # Telegram bot handlers
│   └── services/          # Business logic services
├── docs/                  # Documentation
├── scripts/               # Platform-specific scripts
│   └── windows/           # Windows batch files
├── tests/                 # Test files
└── main.py               # Application entry point
```

## 📚 Documentation

- **[Russian Documentation](docs/README_ru.md)** - Detailed installation and usage guide
- **[Command Reference](docs/all_commands.md)** - Complete list of all commands with examples
- **[Configuration Guide](docs/CONFIG.md)** - Pydantic Settings configuration
- **[Future Plans](docs/FUTURE.md)** - Upcoming features and improvements
- **[Testing Guide](docs/TESTING.md)** - Testing and development information
- **[Headless Mode](docs/HEADLESS.md)** - Running in headless environments
- **[Development Guide](docs/DEVELOPMENT.md)** - Developer documentation
- **[Security Policy](docs/SECURITY.md)** - Security guidelines and reporting
- **[Changelog](docs/CHANGELOG.md)** - Version history and changes
- **[Migration Guide v2.2](docs/MIGRATION_v2.2.md)** - Migration guide for v2.2.0

## ⚙️ Configuration

ControlBot v2.2.1+ uses **Pydantic Settings** for advanced configuration management:

### Key Features
- **Environment Variables**: All settings via `.env` file or environment
- **Validation**: Automatic validation of all configuration parameters
- **Type Safety**: Full type hints and validation with Pydantic v2
- **Flexible Modes**: GUI/Headless mode switching
- **Security**: Built-in user authentication and access control

### Quick Configuration
```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
# Required: TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
# Optional: GUI_MODE, HEADLESS_MODE, LOG_LEVEL, etc.
```

See [Configuration Guide](docs/CONFIG.md) for complete setup instructions.

## 🔧 Features

### 🖥️ System Management
- **Process Control**: Launch, stop, and monitor processes
- **System Operations**: Shutdown, restart, sleep, hibernate
- **Process Monitoring**: View active processes and system resources
- **Path Management**: Quick access to frequently used applications

### 📁 File Operations
- **File Transfer**: Upload and download files/folders
- **File Search**: Advanced file search with filters
- **File Management**: Cut, copy, and organize files
- **Archive Support**: Automatic ZIP creation for folders

### 🖱️ Remote Control
- **Mouse Control**: Move, click, scroll, and save positions
- **Keyboard Input**: Send keys and type text
- **Screen Capture**: Screenshots with coordinate grid
- **Image Recognition**: Find elements on screen by image
- **RDP Streaming**: Real-time screen streaming (1-10 FPS)

### 💻 Command Line Interface
- **Interactive CMD**: Full command line session with auto-updates
- **Command Execution**: Run any command with real-time output
- **Session Management**: Start, stop, and manage command sessions
- **Output Export**: Save complete command output as files

### 📊 Monitoring & Security
- **File Monitoring**: Real-time file system change detection
- **User Authentication**: Whitelist-based access control
- **Private Chat Only**: Secure communication channel
- **Activity Logging**: Comprehensive operation tracking

### 🎯 User Experience
- **Auto-command Registration**: All commands appear in Telegram menu
- **Context-aware Help**: Detailed help for each command
- **Inline Keyboards**: Quick access buttons for common operations
- **Real-time Updates**: Live status updates and notifications

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
   scripts/windows/ControlBot.bat
   ```

## 🖥️ CLI Launch

ControlBot supports multiple ways to launch the application:

### Module Launch
```bash
# Run as Python module
python -m app
```

### Console Script (after installation)
```bash
# Install the package
pip install -e .

# Run using console script
controlbot
```

### Direct Script Launch
```bash
# Run main script directly
python main.py
```

### Windows Batch File
```bash
# Use provided Windows batch file
scripts/windows/ControlBot.bat
```

All launch methods support the same configuration options and environment variables.

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**.

Authors: Eklipti, Nlan_Cat

See [LICENSE](LICENSE) for the complete license text.

## 🧪 Testing

The project includes comprehensive testing with **67 tests** across multiple categories:

### Test Statistics (v2.2.1)
- **Total Tests**: 67 tests
- **Smoke Tests**: 16 tests (basic functionality and import validation)
- **Unit Tests**: 35 tests (component-level testing)
- **Headless Tests**: 51 tests (CI/GitHub Actions compatible)
- **GUI Tests**: 1 test (requires GUI modules)
- **Integration Tests**: 8 tests (end-to-end functionality)
- **Configuration Tests**: 7 tests (Pydantic Settings validation)

### Test Types
- **Smoke Tests**: Basic functionality and import validation
- **Unit Tests**: Individual component testing with mocks
- **Headless Tests**: Tests that work in CI/GitHub Actions environment
- **GUI Tests**: Tests requiring GUI modules (pyautogui, cv2, PIL)
- **Integration Tests**: End-to-end functionality tests
- **Configuration Tests**: Pydantic Settings validation and parsing

### Running Tests

**All tests (local development):**
```bash
python run_all_tests.py
# or
python -m pytest tests/ -v
```

**Headless tests only (CI/GitHub Actions):**
```bash
python run_headless_tests.py
# or
python -m pytest tests/ -m headless -v
```

**Specific test categories:**
```bash
# GUI tests only
python -m pytest tests/ -m gui -v

# Smoke tests only
python -m pytest tests/ -m smoke -v

# Configuration tests only
python -m pytest tests/test_config.py -v
```

### CI/CD
- **GitHub Actions**: Automated testing on Python 3.11 and 3.12
- **Code Quality**: Ruff linting and MyPy type checking
- **Headless Support**: Automatic headless mode detection

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
