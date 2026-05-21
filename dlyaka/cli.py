import getpass
import hashlib
import os
import subprocess
import sys
import threading
from typing import List

import click

from . import vault as _vault
from .vault import SALT_FILE

REDACTION_PLACEHOLDER = "[REDACTED-API-KEY]"
MIN_REDACT_LEN = 8  # never redact strings shorter than this (avoid false positives)


def _prompt_password(confirm: bool = False) -> str:
    pw = getpass.getpass("DLYAKA master password: ")
    if confirm:
        pw2 = getpass.getpass("Confirm master password: ")
        if pw != pw2:
            click.echo("Error: passwords do not match.", err=True)
            sys.exit(1)
    return pw


_ENV_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "chatgpt": "OPENAI_API_KEY",
}


def _to_env_name(name: str) -> str:
    return _ENV_MAP.get(name.lower(), name.upper().replace("-", "_") + "_API_KEY")


def _redact(text: str, secrets: List[str]) -> str:
    """Replace every occurrence of a secret with the redaction placeholder.

    Secrets shorter than MIN_REDACT_LEN are skipped to avoid false positives.
    """
    for s in secrets:
        if s and len(s) >= MIN_REDACT_LEN:
            text = text.replace(s, REDACTION_PLACEHOLDER)
    return text


def _stream_with_redaction(src, dst, secrets: List[str]) -> None:
    """Pump lines from src to dst, redacting any secret values along the way."""
    try:
        for line in iter(src.readline, ""):
            dst.write(_redact(line, secrets))
            dst.flush()
    except (ValueError, OSError):
        pass  # stream closed mid-read; ok


def _fingerprint(api_key: str) -> str:
    return "sha256:" + hashlib.sha256(api_key.encode()).hexdigest()


@click.group()
@click.version_option()
def cli():
    """DLYAKA — Don't Leak Your API Key Again.

    Encrypt and store API keys locally. Use them without ever
    putting credentials in your code, your .env files, or your AI chats.

    \b
    Quickstart:
      dlyaka add anthropic            # hidden prompt — no shell history
      dlyaka run python my_script.py  # injects keys, redacts output
    """


@cli.command()
@click.argument("name")
@click.argument("api_key", required=False)
def add(name: str, api_key: str):
    """Store or update an API key.

    Omit the api_key argument to get a hidden prompt (recommended — the
    key never enters your shell history).

    \b
    Examples:
      dlyaka add anthropic                  # secure: hidden prompt
      dlyaka add anthropic sk-ant-...       # convenient: appears in shell history
    """
    if api_key is None:
        api_key = getpass.getpass(f"API key for '{name}' (hidden input): ").strip()
        if not api_key:
            click.echo("Error: no key entered.", err=True)
            sys.exit(1)

    is_new = not SALT_FILE.exists()
    password = _prompt_password(confirm=is_new)
    try:
        _vault.add_key(name, api_key, password)
        click.echo(f"Key '{name}' saved. Fingerprint: {_fingerprint(api_key)}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
def get(name: str):
    """Print a stored API key to stdout.

    Intended for your own terminal — NOT for use inside an AI assistant's
    shell tool, because the key would land in chat output. Use `dlyaka run`
    instead for AI workflows.
    """
    password = _prompt_password()
    try:
        key = _vault.get_key(name, password)
        click.echo(key)
    except (ValueError, KeyError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("list")
def list_keys():
    """List stored key names with fingerprints (values are never shown)."""
    password = _prompt_password()
    try:
        keys = _vault.get_all_keys(password)
        if not keys:
            click.echo("No keys stored yet. Run: dlyaka add <name>")
        else:
            click.echo("Stored keys:")
            for name, value in keys.items():
                click.echo(f"  {name}  →  {_to_env_name(name)}  ({_fingerprint(value)[:23]}...)")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
def fingerprint(name: str):
    """Print the SHA-256 fingerprint of a stored key.

    Safe to share — the fingerprint cannot be reversed to recover the key.
    Useful for AI assistants to verify which key version is in use without
    ever seeing the actual key value.
    """
    password = _prompt_password()
    try:
        key = _vault.get_key(name, password)
        click.echo(_fingerprint(key))
    except (ValueError, KeyError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
def remove(name: str):
    """Remove a stored API key."""
    password = _prompt_password()
    try:
        _vault.remove_key(name, password)
        click.echo(f"Key '{name}' removed.")
    except (ValueError, KeyError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def env():
    """Print export statements to inject keys into your current shell.

    \b
    Usage:
      eval $(dlyaka env)
      python my_script.py

    Like `dlyaka get`, this prints key values — don't run it from an AI
    assistant's shell tool.
    """
    password = _prompt_password()
    try:
        keys = _vault.get_all_keys(password)
        for name, value in keys.items():
            click.echo(f"export {_to_env_name(name)}={value}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--no-redact",
    is_flag=True,
    help="Disable output redaction (NOT recommended — keys may leak to stdout).",
)
@click.argument("command", nargs=-1, required=True)
def run(no_redact: bool, command):
    """Run a command with API keys injected as environment variables.

    By default, any occurrence of a stored key value in the subprocess's
    stdout/stderr is replaced with [REDACTED-API-KEY] before reaching your
    terminal. This is the safe-by-default mode for use with AI assistants.

    \b
    Examples:
      dlyaka run python my_script.py
      dlyaka run node app.js
      dlyaka run jupyter notebook
    """
    password = _prompt_password()
    try:
        keys = _vault.get_all_keys(password)
        proc_env = os.environ.copy()
        secrets: List[str] = []
        for name, value in keys.items():
            proc_env[_to_env_name(name)] = value
            secrets.append(value)

        if no_redact:
            result = subprocess.run(list(command), env=proc_env)
            sys.exit(result.returncode)

        proc = subprocess.Popen(
            list(command),
            env=proc_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        threads = [
            threading.Thread(
                target=_stream_with_redaction,
                args=(proc.stdout, sys.stdout, secrets),
                daemon=True,
            ),
            threading.Thread(
                target=_stream_with_redaction,
                args=(proc.stderr, sys.stderr, secrets),
                daemon=True,
            ),
        ]
        for t in threads:
            t.start()
        proc.wait()
        for t in threads:
            t.join(timeout=2)
        sys.exit(proc.returncode)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"Error: command not found: {e.filename}", err=True)
        sys.exit(127)
