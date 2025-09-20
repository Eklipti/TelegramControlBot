# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

# методы/поведение взяты из Settings и уже присутствуют в коде

import os
from app.config import reload_settings

def test_log_level_allows_trace(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "TRACE")
    s = reload_settings()
    assert s.log_level == "TRACE"

def test_allowed_users_parsing(monkeypatch):
    monkeypatch.setenv("ALLOWED_USER_IDS", "1, 2; 3")
    s = reload_settings()
    assert s.get_allowed_user_ids() == [1, 2, 3]
