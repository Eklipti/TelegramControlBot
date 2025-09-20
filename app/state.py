# SPDX-FileCopyrightText: 2025 ControlBot contributors
# SPDX-License-Identifier: AGPL-3.0-or-later

# Shared in-memory state containers

upload_requests: dict[int, str] = {}
download_requests: dict[int, str] = {}
mouse_positions: dict[str, tuple[int, int]] = {}
screen_find_requests: set[int] = set()
