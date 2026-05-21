---
name: dlyaka
description: Use API keys from the local DLYAKA encrypted vault when writing or executing scripts that call Claude (Anthropic), ChatGPT (OpenAI), or any other AI API. Trigger this skill whenever the user wants to run an AI-powered script, asks how to use their API key securely, mentions putting API keys in code or .env files, or worries about leaking credentials.
---

# DLYAKA — Encrypted API Key Vault

This skill lets you (Claude) help the user run scripts that need API keys, **without ever putting the keys in source code, .env files, or chat messages**.

The user's keys live in `~/.dlyaka/vault.enc`, encrypted with a master password using AES-256 (Fernet) + PBKDF2-HMAC-SHA256.

## When to use this skill

Activate whenever the user:

- Writes or runs a script that calls Anthropic / Claude / OpenAI / ChatGPT / any other AI API
- Says "use my API key", "I have an API key", or pastes one
- Mentions `.env`, `dotenv`, or environment variables for AI credentials
- Worries about exposing or leaking API keys
- Asks to commit code that talks to an AI provider

## Step 1 — Verify dlyaka is installed

```bash
which dlyaka
```

If it's missing, install it:

```bash
pip install dlyaka
```

## Step 2 — Check what keys are stored

```bash
dlyaka list
```

The user types their master password once. You'll see something like:

```
Stored keys:
  anthropic  →  ANTHROPIC_API_KEY
  openai     →  OPENAI_API_KEY
```

If the key the script needs is missing, ask the user to add it:

```bash
dlyaka add anthropic sk-ant-...
dlyaka add openai sk-...
```

**Never** type the actual key value in your shell history — pipe from a prompt or have the user run it themselves.

## Step 3 — Run the script with keys injected

This is the core pattern. Pick whichever fits the user's workflow:

### Pattern A — Wrap the command (recommended)

```bash
dlyaka run python my_script.py
dlyaka run node app.js
dlyaka run jupyter notebook
```

`dlyaka run` decrypts the vault, injects `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` into the child process environment, then runs the command. The user's script just reads env vars normally:

```python
import anthropic
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY automatically
```

### Pattern B — Inject into the current shell

```bash
eval $(dlyaka env)
python my_script.py
```

Useful for interactive sessions where the user runs many commands.

### Pattern C — Python library (no shell needed)

```python
from dlyaka.providers.claude import get_client
client = get_client()

# Or, for any key:
from dlyaka import get_key
api_key = get_key("anthropic")
```

## Rules — Strict

1. **Never** print, echo, log, or paste an API key value. Not in code, not in shell output, not in chat.
2. **Never** write `api_key = "sk-..."` in code. Use `os.environ`, `get_key()`, or `dlyaka run`.
3. **Never** commit a `.env` file with real keys. Suggest dlyaka instead.
4. If the user pastes an API key in chat, immediately tell them to **revoke and rotate it** — the key is now in conversation history and possibly logs.
5. If a script you wrote needs a key the user hasn't stored yet, stop and ask them to run `dlyaka add <name> <key>` themselves. Do not put the key into a command you run for them.

## Writing scripts for the user

When the user asks you to write a script that uses an AI API, default to this template:

```python
"""my_script.py — run with: dlyaka run python my_script.py"""
import os
import anthropic

client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY from env

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(message.content[0].text)
```

Tell the user how to run it:

```bash
dlyaka run python my_script.py
```

## If dlyaka isn't available

If the user is on a system where dlyaka can't be installed (e.g., a locked-down environment), fall back to:

1. Using a system keyring (`python-keyring`)
2. A `.env` file that is **explicitly added to `.gitignore` first**
3. Direct env var export (e.g., `export ANTHROPIC_API_KEY=...`) in the user's shell rc

Always verify `.gitignore` excludes `.env` before writing one.

## Quick reference

| Goal | Command |
|------|---------|
| Add a key | `dlyaka add <name> <key>` |
| List stored keys (names only) | `dlyaka list` |
| Print a key | `dlyaka get <name>` |
| Remove a key | `dlyaka remove <name>` |
| Run a script with keys injected | `dlyaka run <cmd>` |
| Export to current shell | `eval $(dlyaka env)` |
