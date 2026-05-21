import importlib
from pathlib import Path

import pytest


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    """Point the vault at a temp dir for each test."""
    from dlyaka import vault

    monkeypatch.setattr(vault, "VAULT_DIR", tmp_path)
    monkeypatch.setattr(vault, "VAULT_FILE", tmp_path / "vault.enc")
    monkeypatch.setattr(vault, "SALT_FILE", tmp_path / "salt.bin")
    return vault


def test_add_and_get_key(isolated_vault):
    isolated_vault.add_key("openai", "sk-test-123", "masterpw")
    assert isolated_vault.get_key("openai", "masterpw") == "sk-test-123"


def test_multiple_keys(isolated_vault):
    isolated_vault.add_key("anthropic", "sk-ant-test", "pw")
    isolated_vault.add_key("openai", "sk-test", "pw")
    keys = isolated_vault.list_keys("pw")
    assert set(keys) == {"anthropic", "openai"}


def test_overwrite_key(isolated_vault):
    isolated_vault.add_key("openai", "sk-old", "pw")
    isolated_vault.add_key("openai", "sk-new", "pw")
    assert isolated_vault.get_key("openai", "pw") == "sk-new"


def test_remove_key(isolated_vault):
    isolated_vault.add_key("anthropic", "sk-ant", "pw")
    isolated_vault.remove_key("anthropic", "pw")
    with pytest.raises(KeyError):
        isolated_vault.get_key("anthropic", "pw")


def test_wrong_password(isolated_vault):
    isolated_vault.add_key("openai", "sk-test", "correct-pw")
    with pytest.raises(ValueError, match="Wrong password"):
        isolated_vault.get_key("openai", "wrong-pw")


def test_missing_key(isolated_vault):
    isolated_vault.add_key("openai", "sk-test", "pw")
    with pytest.raises(KeyError):
        isolated_vault.get_key("does-not-exist", "pw")


def test_get_all_keys(isolated_vault):
    isolated_vault.add_key("a", "1", "pw")
    isolated_vault.add_key("b", "2", "pw")
    all_keys = isolated_vault.get_all_keys("pw")
    assert all_keys == {"a": "1", "b": "2"}
