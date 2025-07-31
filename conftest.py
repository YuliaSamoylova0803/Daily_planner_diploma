import os
import sys
import pytest

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def mock_timezone(monkeypatch):
    """Фикстура для мока timezone.now()"""
    monkeypatch.setattr('django.utils.timezone.now', lambda: "2025-01-01 00:00:00")
