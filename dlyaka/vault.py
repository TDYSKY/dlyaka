import json
import getpass
from pathlib import Path
from typing import Optional

from .crypto import derive_key, generate_salt, encrypt, decrypt

VAULT_DIR = Path.home() / ".dlyaka"
VAULT_FILE = VAULT_DIR / "vault.enc"
SALT_FILE = VAULT_DIR / "salt.bin"


def _ensure_dir() -> None:
    VAULT_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def _load_salt() -> bytes:
    _ensure_dir()
    if SALT_FILE.exists():
        return SALT_FILE.read_bytes()
    salt = generate_salt()
    SALT_FILE.write_bytes(salt)
    SALT_FILE.chmod(0o600)
    return salt


def _get_fernet_key(password: str) -> bytes:
    return derive_key(password, _load_salt())


def _load_vault(password: str) -> dict:
    if not VAULT_FILE.exists():
        return {}
    try:
        encrypted = VAULT_FILE.read_bytes()
        decrypted = decrypt(encrypted, _get_fernet_key(password))
        return json.loads(decrypted)
    except Exception:
        raise ValueError("Wrong password or corrupted vault.")


def _save_vault(data: dict, password: str) -> None:
    _ensure_dir()
    encrypted = encrypt(json.dumps(data).encode(), _get_fernet_key(password))
    VAULT_FILE.write_bytes(encrypted)
    VAULT_FILE.chmod(0o600)


def add_key(name: str, api_key: str, password: str) -> None:
    vault = _load_vault(password)
    vault[name] = api_key
    _save_vault(vault, password)


def get_key(name: str, password: Optional[str] = None) -> str:
    if password is None:
        password = getpass.getpass("DLYAKA master password: ")
    vault = _load_vault(password)
    if name not in vault:
        raise KeyError(f"No key stored for '{name}'. Run: dlyaka add {name} <your-key>")
    return vault[name]


def remove_key(name: str, password: str) -> None:
    vault = _load_vault(password)
    if name not in vault:
        raise KeyError(f"No key stored for '{name}'.")
    del vault[name]
    _save_vault(vault, password)


def list_keys(password: str) -> list:
    return list(_load_vault(password).keys())


def get_all_keys(password: str) -> dict:
    return _load_vault(password)
