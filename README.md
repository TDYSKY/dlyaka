<div align="center">

# DLYAKA

### Don't Leak Your API Key Again

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![tests](https://github.com/TDYSKY/dlyaka/actions/workflows/tests.yml/badge.svg)](https://github.com/TDYSKY/dlyaka/actions/workflows/tests.yml)
[![Discord](https://img.shields.io/discord/0?label=Discord&logo=discord&logoColor=white&color=5865F2)](https://discord.gg/RTax3aBMUs)

**A tiny CLI + Python library that keeps your Claude and ChatGPT API keys encrypted on your machine — and out of your code.**

[Download](https://github.com/TDYSKY/dlyaka/releases/latest) · [Discord](https://discord.gg/RTax3aBMUs) · [agencyg.de](https://agencyg.de) · [Shop](https://shop.agencyg.de)

</div>

---

## The Problem

You've done it. Everyone has. API key in a `.env` file → forgot to gitignore it → pushed to GitHub → seconds later you're frantically revoking the key.

> GitHub detects roughly **10 million leaked secrets per year**. Most of them are API keys for AI providers, cloud platforms, and databases. Don't be the next one.

DLYAKA fixes this by keeping your API keys in an **encrypted vault on your local machine**, completely separated from your projects. Your scripts read them via a CLI wrapper or a one-line Python call — never as literal strings in code.

## Why DLYAKA?

|                                  | `.env` files | OS keyring | **DLYAKA** |
|----------------------------------|:-:|:-:|:-:|
| Keys never in your repo          | ⚠️ (easy to forget gitignore) | ✅ | ✅ |
| Encrypted at rest                | ❌ | ✅ | ✅ |
| Works in headless scripts        | ✅ | ⚠️ (OS prompts) | ✅ |
| Works across Mac / Linux / Win   | ✅ | ⚠️ (different backends) | ✅ |
| Built-in `run <cmd>` wrapper     | ❌ | ❌ | ✅ |
| Bundled Claude Code skill        | ❌ | ❌ | ✅ |
| Zero config to use the keys      | ⚠️ | ❌ | ✅ |

## Features

- **AES-256 encryption** via [Fernet](https://cryptography.io/en/latest/fernet/) with PBKDF2-HMAC-SHA256 (480k iterations)
- **Master password** protects the vault — only you can decrypt it
- **Works with Claude, ChatGPT, and any other API** — bring your own key name
- **`dlyaka run <cmd>`** — execute any script with keys injected as env vars
- **Python library** — `get_key("anthropic")` from inside your code
- **Claude Code Skill included** — teach Claude how to use the vault automatically
- **Zero keys in your code, .env files, or git history**

## Installation

### Option 1 — From the latest release (recommended)

Grab the wheel from the [Releases page](https://github.com/TDYSKY/dlyaka/releases/latest) and install it:

```bash
pip install dlyaka-0.2.0-py3-none-any.whl
```

### Option 2 — From source

```bash
git clone https://github.com/TDYSKY/dlyaka
cd dlyaka
pip install -e .
```

### Option 3 — Directly from GitHub

```bash
pip install git+https://github.com/TDYSKY/dlyaka.git
```

## Quick Start

**1.** Store your API keys:

```bash
dlyaka add anthropic     # hidden prompt — no shell history, no chat
dlyaka add openai        # same
```

You'll be prompted for the API key (hidden input) and then a master password on first use. The master password encrypts the vault.

> Power-user shortcut: `dlyaka add anthropic sk-ant-...` works too, but the key lands in your shell history. Prefer the prompt mode.

**2.** Run any script with keys injected automatically:

```bash
dlyaka run python my_script.py
```

Your script reads `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` from the environment — no keys in your code:

```python
# my_script.py
import anthropic
client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY from env
print(client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hi!"}],
).content[0].text)
```

**3.** Or use the Python library directly:

```python
from dlyaka import get_key

import anthropic
client = anthropic.Anthropic(api_key=get_key("anthropic"))
```

## Using DLYAKA with Claude Code & AI assistants

Pasting an API key into a chat with Claude, ChatGPT, Copilot, or any AI tool puts that key into the conversation history — and possibly logs, training data, and backend storage. DLYAKA is built to make sure that never happens.

### The secure transmission pattern

```
You:    "Claude, query GPT-4 to compare answers on this prompt."

Claude: "Don't paste your OpenAI key. Run this in your own terminal:
            dlyaka add openai
         You'll get a hidden prompt — the key never enters chat
         or shell history."

You:    [adds key in your terminal]
You:    "Done."

Claude: [writes a Python script that uses openai client]
        [runs `dlyaka run python script.py`]

dlyaka: → decrypts vault locally (master password prompt)
        → injects OPENAI_API_KEY into the subprocess environment
        → captures stdout/stderr and redacts any accidental key leak
        → streams the cleaned output back

Claude: [sees only the GPT-4 answer — never the key value]
```

### Security guarantees

1. The key **never enters chat history** — you add it in your own terminal via `dlyaka add <name>` (hidden prompt)
2. The key **never enters shell history** — the prompt is hidden input, not a CLI argument
3. The key **never appears in Claude's tool input/output** — `dlyaka run` injects it into the subprocess env, bypassing Claude entirely
4. **Accidental leaks are redacted** — if a script accidentally `print()`s the key, `dlyaka run` replaces it with `[REDACTED-API-KEY]` before output reaches Claude
5. The key **never touches a `.env` file** in your repo

### Install the Claude Code skill

```bash
./claude_skill/install.sh
```

After install, Claude Code will:

- Refuse to accept API keys pasted in chat (and tell you to revoke them)
- Use `dlyaka run` for every AI API call
- Never run `dlyaka get` or `dlyaka env` from its shell tool
- Verify key presence via `dlyaka fingerprint` (a hash, safe to share)

See [`claude_skill/dlyaka/SKILL.md`](claude_skill/dlyaka/SKILL.md) for the full skill definition.

## CLI Reference

| Command | Description |
|---------|-------------|
| `dlyaka add <name>` | Store or update a key — **hidden prompt, no shell history** |
| `dlyaka add <name> <key>` | Same, but key on argv (lands in shell history — convenience only) |
| `dlyaka get <name>` | Print a stored key value (use in your own terminal only) |
| `dlyaka list` | List stored key names + fingerprints |
| `dlyaka fingerprint <name>` | Print a SHA-256 fingerprint of a key (safe to share) |
| `dlyaka remove <name>` | Delete a key |
| `dlyaka run <cmd>` | Run a command with keys as env vars — **subprocess output is auto-redacted** |
| `dlyaka run --no-redact <cmd>` | Same, without redaction (not recommended) |
| `dlyaka env` | Print `export KEY=value` lines (eval into your shell) |

### Shell integration

```bash
# Inject all keys into the current shell session
eval $(dlyaka env)

# Then use however you like
python my_script.py
```

### Name → environment variable mapping

| Stored name | Env var injected |
|-------------|------------------|
| `anthropic` or `claude` | `ANTHROPIC_API_KEY` |
| `openai` or `chatgpt` | `OPENAI_API_KEY` |
| `my-custom-service` | `MY_CUSTOM_SERVICE_API_KEY` |

## Python API

```python
from dlyaka import get_key

# Prompts for master password
api_key = get_key("anthropic")

# Or pass it programmatically (only for tests / automation)
api_key = get_key("anthropic", password="mypw")
```

### Provider helpers

```python
# Claude
from dlyaka.providers.claude import get_client
client = get_client()
client.messages.create(...)

# OpenAI / ChatGPT
from dlyaka.providers.gpt import get_client
client = get_client()
client.chat.completions.create(...)
```

## Claude Code Skill

DLYAKA ships with a [Claude Code](https://docs.claude.com/en/docs/claude-code) skill so Claude knows how to use your vault automatically when writing or running AI-powered scripts.

**Install globally:**

```bash
./claude_skill/install.sh
```

**Install for the current project only:**

```bash
./claude_skill/install.sh --project
```

Once installed, Claude will:

- Check if `dlyaka` is set up before writing AI scripts
- Use `dlyaka run python script.py` to execute code without leaking keys
- Refuse to put API key literals into your code
- Warn you to rotate keys if they ever end up in chat

See [`claude_skill/dlyaka/SKILL.md`](claude_skill/dlyaka/SKILL.md) for the full skill definition.

## How It Works

```
~/.dlyaka/
├── vault.enc   ← Fernet-encrypted JSON blob containing your keys
└── salt.bin    ← random salt for key derivation (not secret, but unique to you)
```

1. On first use, you set a **master password**.
2. DLYAKA derives a 256-bit key from the password + a random salt using **PBKDF2-HMAC-SHA256** with 480,000 iterations.
3. Your API keys are encrypted with **Fernet** (AES-128-CBC + HMAC-SHA256) and stored in `vault.enc`.
4. To use a key, you provide the master password → DLYAKA decrypts in memory only → injects into env vars or returns to your Python code.

**Your master password is never stored anywhere.** If you forget it, your vault cannot be recovered.

## Security Notes

- The vault file is mode `0600` (read/write owner only)
- The salt file is `0600` and is **not secret** — it's just random data
- Fernet uses a random IV per encryption, so re-saving produces different ciphertext
- DLYAKA never writes the decrypted vault to disk
- If you suspect your master password was compromised, run `dlyaka remove` for each key and re-add with new keys

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=TDYSKY/dlyaka&type=Date)](https://star-history.com/#TDYSKY/dlyaka&Date)

If DLYAKA saved you 30 seconds of panicked key-rotation, a star takes 2.

## Contributing

```bash
git clone https://github.com/TDYSKY/dlyaka
cd dlyaka
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues → [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) — do whatever you want with it.

---

## Built by AgencyG

DLYAKA is built and maintained by **[AgencyG](https://agencyg.de)** — we ship high-quality developer tools and FiveM scripts.

<div align="center">

[**agencyg.de**](https://agencyg.de) &nbsp;·&nbsp; [**shop.agencyg.de**](https://shop.agencyg.de) &nbsp;·&nbsp; [**Discord community**](https://discord.gg/RTax3aBMUs)

</div>

If DLYAKA saved you from a leaked key, leave a star on the repo and come say hi in our Discord.

[![Tweet](https://img.shields.io/twitter/url/https/github.com/TDYSKY/dlyaka.svg?style=social)](https://twitter.com/intent/tweet?text=Stop%20leaking%20your%20API%20keys.%20DLYAKA%20is%20a%20tiny%20encrypted%20local%20vault%20for%20Claude%20%26%20ChatGPT%20keys%20%E2%80%94%20with%20a%20Claude%20Code%20skill%20bundled.&url=https%3A%2F%2Fgithub.com%2FTDYSKY%2Fdlyaka)

---

<div align="center">
Made to stop the key leaks. Built with paranoia.
</div>
