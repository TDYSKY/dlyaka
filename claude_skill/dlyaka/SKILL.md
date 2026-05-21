---
name: dlyaka
description: Use API keys from the local DLYAKA encrypted vault without ever putting them in chat, code, or shell history. Trigger when the user wants to run an AI-powered script, asks how to use their API key securely, mentions putting API keys in code/.env files, pastes (or is about to paste) an API key, or worries about leaking credentials. Especially important whenever the user is using Claude, ChatGPT, OpenAI, or any other AI API.
---

# DLYAKA — Encrypted API Key Vault

This skill lets you (Claude) help the user run scripts that need API keys, **without the key ever appearing in chat, your tool input/output, source code, or shell history**.

The user's keys live in `~/.dlyaka/vault.enc`, encrypted with their master password using AES (Fernet) + PBKDF2-HMAC-SHA256.

## Trigger this skill when…

- The user writes or runs a script that calls Anthropic / Claude / OpenAI / ChatGPT / any other AI API
- The user pastes or is about to paste an API key into chat
- The user says "use my API key", "I have an API key", or "I need to give you my key"
- The user mentions `.env`, `dotenv`, or environment variables for AI credentials
- The user worries about leaking, exposing, or rotating keys
- You're about to commit code that talks to an AI provider

## Absolute rules — never break these

1. **Never accept an API key pasted in chat.** If the user pastes a key, immediately stop, tell them to revoke it at the provider's dashboard, generate a new one, and store the new one via `dlyaka add <name>` (which uses a hidden prompt, so the key won't enter shell history either).

2. **Never run `dlyaka get`, `dlyaka env`, or any command that prints the key value.** Those commands print the raw key to stdout — when *you* run them via a shell tool, the key lands in your tool output, which is part of conversation history. They're for the user's own terminal only.

3. **Never write `api_key = "sk-..."` in code.** Always use `os.environ` or `get_key()` from the library.

4. **Never suggest `.env` files with real keys.** DLYAKA exists to replace them.

5. **Never log, echo, print, or quote a key value.** Not even partially. Not even "to check it's right."

## The secure transmission pattern

When the user needs to give you access to a key:

**Step 1 — Tell the user to add the key in their own terminal:**

```bash
dlyaka add openai
```

(Note: no key on the command line. They'll get a hidden prompt — the key never appears in chat *or* in shell history.)

**Step 2 — Wait for them to confirm it's stored.** You can verify the key is registered without seeing its value:

```bash
dlyaka list
```

This shows key names and SHA-256 fingerprints — never the raw values.

**Step 3 — Run your script with the key injected:**

```bash
dlyaka run python my_script.py
```

`dlyaka run` decrypts the vault locally, injects `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` (or whatever you stored) into the child process environment, then executes the command. Your script reads env vars normally:

```python
import anthropic
client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY automatically
```

You will see the script's intended output — never the key value. As a safety net, `dlyaka run` **automatically redacts** any occurrence of a stored key value in subprocess stdout/stderr, replacing it with `[REDACTED-API-KEY]`. Don't rely on that — write scripts that don't print keys — but it catches mistakes.

## Use cases

### "Run my AI script for me"

```bash
dlyaka run python my_ai_script.py
```

### "Compare Claude and GPT-4 on this prompt"

Write a single script that uses both APIs, then:

```bash
dlyaka run python compare.py
```

Both env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) are available inside the subprocess.

### "Make a quick API call as a one-liner"

```bash
dlyaka run python -c "import anthropic; print(anthropic.Anthropic().messages.create(model='claude-sonnet-4-6', max_tokens=200, messages=[{'role':'user','content':'Hi!'}]).content[0].text)"
```

### "Did I store this key correctly?"

Ask the user to run `dlyaka list` themselves and report what they see. **Don't run it yourself** — the fingerprint output is safe in *their* terminal but should still flow through them.

## Writing scripts for the user

When the user asks you to write a script that uses an AI API, default to this template:

```python
"""my_script.py — run with: dlyaka run python my_script.py"""
import os
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(message.content[0].text)
```

Then tell the user to run:

```bash
dlyaka run python my_script.py
```

## If dlyaka isn't installed

```bash
pip install dlyaka
```

If `pip install` is blocked (offline / locked-down env), download from:

> https://github.com/TDYSKY/dlyaka/releases/latest

…and `pip install dlyaka-X.Y.Z-py3-none-any.whl`.

If even that's not possible, fall back to OS keyring (`python -m keyring set <service> <user>`). Never fall back to plaintext `.env` files unless `.gitignore` already excludes them.

## Quick reference

| Goal | Command | Safe for you to run? |
|------|---------|----------------------|
| Add a key (hidden prompt) | `dlyaka add <name>` | ⚠️ ask the user to run it (key goes through their stdin, not yours) |
| Add a key (key on argv) | `dlyaka add <name> <key>` | ❌ NEVER — key would be in your tool call |
| List stored key names + fingerprints | `dlyaka list` | ⚠️ output is non-sensitive but flow through the user when possible |
| Get key fingerprint (safe to share) | `dlyaka fingerprint <name>` | ✅ |
| Run script with keys injected | `dlyaka run <cmd>` | ✅ |
| Get raw key value | `dlyaka get <name>` | ❌ NEVER |
| Print export statements | `dlyaka env` | ❌ NEVER |
| Remove a key | `dlyaka remove <name>` | ✅ |
