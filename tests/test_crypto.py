import pytest
from cryptography.fernet import InvalidToken

from dlyaka.crypto import derive_key, generate_salt, encrypt, decrypt


def test_derive_key_is_deterministic():
    salt = generate_salt()
    assert derive_key("password", salt) == derive_key("password", salt)


def test_derive_key_differs_with_different_salts():
    key1 = derive_key("password", generate_salt())
    key2 = derive_key("password", generate_salt())
    assert key1 != key2


def test_encrypt_decrypt_roundtrip():
    salt = generate_salt()
    key = derive_key("testpass", salt)
    data = b"super-secret-api-key"
    assert decrypt(encrypt(data, key), key) == data


def test_encrypt_produces_different_ciphertext():
    salt = generate_salt()
    key = derive_key("testpass", salt)
    data = b"same data"
    assert encrypt(data, key) != encrypt(data, key)  # Fernet uses random IV


def test_decrypt_fails_with_wrong_key():
    salt = generate_salt()
    key1 = derive_key("password1", salt)
    key2 = derive_key("password2", salt)
    with pytest.raises(InvalidToken):
        decrypt(encrypt(b"secret", key1), key2)
