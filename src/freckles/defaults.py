# defaults.py
#
# Copyright (c) 2026 Markus Binsteiner
# All rights reserved.
#
# SPDX-License-Identifier: AGPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Filesystem locations for data bundled with the freckles package."""

import sys
from pathlib import Path

if hasattr(sys, "_MEIPASS"):
    # Running from a PyInstaller bundle: package data is unpacked under the
    # bundle's temp dir instead of living next to this file.
    PACKAGE_MODULE_BASE_FOLDER = Path(sys._MEIPASS) / "freckles"
else:
    PACKAGE_MODULE_BASE_FOLDER = Path(__file__).parent

RESOURCES_FOLDER = PACKAGE_MODULE_BASE_FOLDER / "resources"
