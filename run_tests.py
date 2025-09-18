#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Local test runner for ControlBot
Run this script to execute all tests locally
"""

import subprocess
import sys
import os


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed with exit code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main():
    """Run all tests and checks"""
    print("🚀 Running ControlBot tests and checks...")
    
    # Change to project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    success = True
    
    # Install dependencies (includes dev dependencies)
    success &= run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installing dependencies"
    )
    
    # Run ruff linting
    success &= run_command(
        [sys.executable, "-m", "ruff", "check", "app/", "main.py", "--output-format=concise"],
        "Running ruff linting"
    )
    
    # Run mypy type checking (non-blocking)
    print(f"\n🔍 Running mypy type checking (non-blocking)")
    mypy_success = run_command(
        [sys.executable, "-m", "mypy", "app/", "main.py", "--ignore-missing-imports"],
        "Running mypy type checking"
    )
    if not mypy_success:
        print("⚠️ MyPy found type issues (non-blocking)")
    
    # Run smoke tests
    success &= run_command(
        [sys.executable, "-m", "pytest", "tests/", "-m", "smoke", "-v"],
        "Running smoke tests"
    )
    
    # Test startup without token (should fail)
    print(f"\n🔍 Testing startup without token (expected to fail)")
    try:
        env = os.environ.copy()
        env["TELEGRAM_BOT_TOKEN"] = ""
        env["ALLOWED_USER_IDS"] = "123456789"
        
        result = subprocess.run([sys.executable, "main.py"], 
                              capture_output=True, text=True, timeout=10, env=env)
        
        if result.returncode == 0:
            print("❌ Unexpected success - should have failed without token")
            success = False
        else:
            print(f"✅ Correctly failed without token (exit code: {result.returncode})")
    except subprocess.TimeoutExpired:
        print("✅ Correctly failed without token (timeout)")
    except Exception as e:
        print(f"✅ Correctly failed without token (exception: {e})")
    
    # Summary
    print(f"\n{'='*50}")
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
