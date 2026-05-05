"""Test isolation for A-sistemo — minimal, no persistent storage used."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_sistemo(monkeypatch, tmp_path):
    """Isolate any config or keyring access.

    A-sistemo has no persistent database but may access config_dir or keyring
    through A-core utilities. Mock them for safety.
    """
    monkeypatch.setattr("A.core.ai.save_api_key", lambda key, **kw: True)
    monkeypatch.setattr("A.core.ai.get_api_key", lambda **kw: "mock-key")
