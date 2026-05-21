"""Tests for the CLI helpers: redaction, fingerprint, env-name mapping."""
import subprocess
import sys
from pathlib import Path

import pytest

from dlyaka.cli import (
    MIN_REDACT_LEN,
    REDACTION_PLACEHOLDER,
    _fingerprint,
    _redact,
    _to_env_name,
)


# ---------- _redact ----------

def test_redact_replaces_a_long_secret():
    out = _redact("token=sk-abc123def456ghi789", ["sk-abc123def456ghi789"])
    assert "sk-abc123def456ghi789" not in out
    assert REDACTION_PLACEHOLDER in out


def test_redact_replaces_multiple_secrets():
    text = "first=sk-aaa-bbb-ccc and second=sk-xxx-yyy-zzz"
    out = _redact(text, ["sk-aaa-bbb-ccc", "sk-xxx-yyy-zzz"])
    assert "sk-aaa" not in out
    assert "sk-xxx" not in out
    assert out.count(REDACTION_PLACEHOLDER) == 2


def test_redact_replaces_multiple_occurrences_of_same_secret():
    text = "key sk-longsecretkey here and again sk-longsecretkey there"
    out = _redact(text, ["sk-longsecretkey"])
    assert "sk-longsecretkey" not in out
    assert out.count(REDACTION_PLACEHOLDER) == 2


def test_redact_skips_short_strings_below_threshold():
    # Strings shorter than MIN_REDACT_LEN are not redacted (false-positive guard)
    short = "a" * (MIN_REDACT_LEN - 1)
    text = f"this contains {short} but not a real key"
    out = _redact(text, [short])
    assert out == text  # unchanged


def test_redact_handles_empty_secret_list():
    assert _redact("hello world", []) == "hello world"


def test_redact_handles_empty_secret_string():
    assert _redact("hello world", [""]) == "hello world"


def test_redact_preserves_non_secret_text():
    text = "this line has no secret in it at all"
    out = _redact(text, ["sk-something-not-in-text"])
    assert out == text


# ---------- _fingerprint ----------

def test_fingerprint_is_deterministic():
    assert _fingerprint("sk-test-key") == _fingerprint("sk-test-key")


def test_fingerprint_changes_with_different_inputs():
    assert _fingerprint("sk-a") != _fingerprint("sk-b")


def test_fingerprint_is_hex_sha256():
    fp = _fingerprint("anything")
    assert fp.startswith("sha256:")
    assert len(fp) == len("sha256:") + 64  # 64 hex chars
    int(fp.split(":")[1], 16)  # raises if not valid hex


def test_fingerprint_does_not_contain_key_value():
    key = "sk-very-secret-key-do-not-leak"
    fp = _fingerprint(key)
    assert key not in fp


# ---------- _to_env_name ----------

def test_to_env_name_known_aliases():
    assert _to_env_name("anthropic") == "ANTHROPIC_API_KEY"
    assert _to_env_name("claude") == "ANTHROPIC_API_KEY"
    assert _to_env_name("openai") == "OPENAI_API_KEY"
    assert _to_env_name("chatgpt") == "OPENAI_API_KEY"


def test_to_env_name_custom_name():
    assert _to_env_name("my-service") == "MY_SERVICE_API_KEY"
    assert _to_env_name("foo") == "FOO_API_KEY"


# ---------- Integration: dlyaka run actually redacts subprocess output ----------

@pytest.fixture
def isolated_vault_with_key(tmp_path, monkeypatch):
    """Set up a real on-disk vault with a known secret for integration testing."""
    from dlyaka import vault

    monkeypatch.setattr(vault, "VAULT_DIR", tmp_path)
    monkeypatch.setattr(vault, "VAULT_FILE", tmp_path / "vault.enc")
    monkeypatch.setattr(vault, "SALT_FILE", tmp_path / "salt.bin")
    vault.add_key("testservice", "supersecret-value-xyz-12345", "pw")
    return vault


def test_run_redacts_secret_from_subprocess_stdout(isolated_vault_with_key, monkeypatch, capsys):
    """End-to-end: dlyaka run executes a subprocess and scrubs the key from its stdout."""
    from click.testing import CliRunner
    from dlyaka.cli import cli

    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw")

    runner = CliRunner()
    # Build a tiny Python one-liner that prints the key value
    script = (
        "import os; "
        "print('the key is', os.environ['TESTSERVICE_API_KEY'])"
    )
    result = runner.invoke(cli, ["run", sys.executable, "-c", script])

    # Subprocess succeeded
    assert result.exit_code == 0
    # The raw key MUST NOT appear in captured output
    assert "supersecret-value-xyz-12345" not in result.output
    # The placeholder must appear
    assert REDACTION_PLACEHOLDER in result.output


def test_run_injects_env_var_into_subprocess(isolated_vault_with_key, monkeypatch):
    """The subprocess can read the key via its env var, but parent never sees it."""
    from click.testing import CliRunner
    from dlyaka.cli import cli

    monkeypatch.setattr("getpass.getpass", lambda *a, **k: "pw")

    runner = CliRunner()
    script = (
        "import os, sys; "
        "key = os.environ.get('TESTSERVICE_API_KEY', ''); "
        "sys.exit(0 if key == 'supersecret-value-xyz-12345' else 1)"
    )
    result = runner.invoke(cli, ["run", sys.executable, "-c", script])
    assert result.exit_code == 0  # subprocess saw the right key
