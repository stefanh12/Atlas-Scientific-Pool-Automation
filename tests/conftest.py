"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure `custom_components` is importable during CI test collection.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

pytest_plugins = "pytest_homeassistant_custom_component"
