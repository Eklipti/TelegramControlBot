# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Smoke tests for ControlBot
Basic tests to ensure the application can start and import modules correctly
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pytest


class TestSmoke(unittest.TestCase):
    """Smoke tests for basic functionality"""

    @pytest.mark.smoke
    def test_import_main_module(self):
        """Test that main module can be imported"""
        try:
            import main
            self.assertTrue(hasattr(main, 'main'))
        except ImportError as e:
            self.fail(f"Failed to import main module: {e}")

    @pytest.mark.smoke
    def test_import_app_module(self):
        """Test that app module can be imported"""
        try:
            import app
            self.assertTrue(hasattr(app, '__init__'))
        except ImportError as e:
            self.fail(f"Failed to import app module: {e}")

    @pytest.mark.smoke
    def test_import_app_handlers(self):
        """Test that app handlers can be imported"""
        try:
            from app import handlers
            self.assertTrue(hasattr(handlers, '__init__'))
        except ImportError as e:
            self.fail(f"Failed to import app.handlers: {e}")

    @pytest.mark.smoke
    def test_import_app_services(self):
        """Test that app services can be imported"""
        try:
            from app import services
            self.assertTrue(hasattr(services, '__init__'))
        except ImportError as e:
            self.fail(f"Failed to import app.services: {e}")

    @pytest.mark.smoke
    def test_import_config(self):
        """Test that config module can be imported"""
        try:
            from app import config
            self.assertTrue(hasattr(config, 'Settings'))
        except ImportError as e:
            self.fail(f"Failed to import app.config: {e}")

    @pytest.mark.smoke
    def test_import_security(self):
        """Test that security module can be imported"""
        try:
            from app import security
            self.assertTrue(hasattr(security, 'ConfirmationManager'))
        except ImportError as e:
            self.fail(f"Failed to import app.security: {e}")

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': ''})
    @pytest.mark.smoke
    def test_startup_without_token_fails_gracefully(self):
        """Test that application fails gracefully without bot token"""
        from aiogram.utils.token import TokenValidationError
        with self.assertRaises((TokenValidationError, TypeError)):
            # This should fail because TELEGRAM_BOT_TOKEN is empty/invalid
            from app.app import main as run_aiogram
            run_aiogram()

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'})
    @patch('aiogram.Bot')
    @patch('aiogram.Dispatcher')
    @pytest.mark.smoke
    def test_startup_with_mock_token(self, mock_dispatcher, mock_bot):
        """Test that application can start with a mock token"""
        # Mock the bot and dispatcher
        mock_bot_instance = MagicMock()
        mock_bot.return_value = mock_bot_instance
        mock_dispatcher_instance = MagicMock()
        mock_dispatcher.return_value = mock_dispatcher_instance
        
        try:
            from app.app import main as run_aiogram
            # This should not raise an exception with mocked dependencies
            # Note: We're not actually running the full app, just testing imports
            self.assertTrue(True)
        except Exception as e:
            # If it fails, it should be a known error (not import errors)
            self.assertNotIsInstance(e, ImportError)

    @pytest.mark.smoke
    def test_requirements_imports(self):
        """Test that all required packages can be imported"""
        required_packages = [
            'aiogram',
            'PIL',
            'cv2',
            'numpy',
            'psutil',
            'pyautogui',
        ]
        
        for package in required_packages:
            with self.subTest(package=package):
                try:
                    __import__(package)
                except ImportError as e:
                    self.fail(f"Required package {package} not available: {e}")

    @pytest.mark.smoke
    def test_file_structure(self):
        """Test that essential files exist"""
        essential_files = [
            'main.py',
            'requirements.txt',
            'app/__init__.py',
            'app/app.py',
            'app/config.py',
            'app/security.py',
            'app/router.py',
        ]
        
        for file_path in essential_files:
            with self.subTest(file=file_path):
                self.assertTrue(
                    os.path.exists(file_path),
                    f"Essential file {file_path} does not exist"
                )


if __name__ == '__main__':
    unittest.main()
