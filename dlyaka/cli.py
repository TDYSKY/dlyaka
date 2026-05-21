import getpass
import os
import subprocess
import sys

import click

from . import vault as _vault
from .vault import SALT_FILE


def _prompt_password(confirm: bool = False) -> str:
    pw = getpass.getpass("DLYAKA master password: ")
    if confirm:
        pw2 = getpass.getpass("Confirm master password: ")
        if pw != pw2:
            click.echo("Error: passwords do not match.", err=True)
            sys.exit(1)
    return pw


# Maps friendly names to standard env var names
_ENV_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "chatgpt": "OPENAI_API_KEY",
}


def _to_env_name(name: str) -> str:
    return _ENV_MAP.get(name.lower(), name.upper().replace("-", "_") + "_API_KEY")


@click.group()
@click.version_option()
def cli():
    """DLYAKA — Don't Leak Your API Key Again.

    Encrypt and store API keys locally. Use them without ever
    putting credentials in your code or .env files.

    \b
    Quickstart:
      dlyaka add anthropic sk-ant-...
      dlyaka run python my_script.py
    """


@cli.command()
@click.argument("name")
@click.argument("api_key")
def add(name: str, api_key: str):
    """Store or update an API key.

    \b
    Examples:
      dlyaka add anthropic sk-ant-...
      dlyaka add openai sk-...
      dlyaka add my-custom-service abc123
    """
    is_new = not SALT_FILE.exists()
    password = _prompt_password(confirm=is_new)
    try:
        _vault.add_key(name, api_key, password)
        click.echo(f"Key '{name}' saved.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
def get(name: str):
    """Print a stored API key to stdout."""
    password = _prompt_password()
    try:
        key = _vault.get_key(name, password)
        click.echo(key)
    except (ValueError, KeyError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("list")
def list_keys():
    """List stored key names (values are never shown)."""
    password = _prompt_password()
    try:
        keys = _vault.list_keys(password)
        if not keys:
            click.echo("No keys stored yet. Run: dlyaka add <name> <key>")
        else:
            click.echo("Stored keys:")
            for k in keys:
                click.echo(f"  {k}  →  {_to_env_name(k)}")
    except ValueError as e:
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
    """Print export statements to inject keys into your shell.

    \b
    Usage:
      eval $(dlyaka env)
      python my_script.py
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
@click.argument("command", nargs=-1, required=True)
def run(command):
    """Run a command with API keys injected as environment variables.

    \b
    Examples:
      dlyaka run python my_script.py
      dlyaka run node app.js
      dlyaka run jupyter notebook
    """
    password = _prompt_password()
    try:
        keys = _vault.get_all_keys(password)
        env = os.environ.copy()
        for name, value in keys.items():
            env[_to_env_name(name)] = value
        result = subprocess.run(list(command), env=env)
        sys.exit(result.returncode)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
