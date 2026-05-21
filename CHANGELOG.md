# Changelog

All notable changes to DLYAKA will be documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [0.2.0] — 2026-05-21

### Added — Secure Transmission

- **Hidden-prompt mode for `dlyaka add <name>`** — omit the key argument and DLYAKA reads it via `getpass.getpass()`. The key never enters shell history or chat.
- **Automatic output redaction in `dlyaka run`** — any occurrence of a stored key value in subprocess stdout/stderr is replaced with `[REDACTED-API-KEY]` before reaching the parent terminal. Catches `print(api_key)` mistakes inside user scripts.
- **`--no-redact` flag** on `dlyaka run` for power-users who explicitly want raw output.
- **`dlyaka fingerprint <name>`** — prints SHA-256 of a stored key. Safe to share; useful for AI assistants to verify a key version is in use without seeing the value.
- **Fingerprints in `dlyaka list` output** — verify keys without exposing them.
- **Updated SKILL.md** with hard rules: never accept keys in chat, never run `dlyaka get`/`env` from an AI assistant's shell tool, always use the hidden-prompt add flow.

### Added — Repo polish

- CodeQL workflow (security scanning on every push/PR + weekly schedule)
- Dependabot config (weekly pip + GitHub Actions updates)
- SECURITY.md private disclosure channels
- CONTRIBUTING.md scope guidelines
- Issue templates (bug, feature) + PR template
- FUNDING.yml pointing to shop.agencyg.de

### Changed

- README: new "Using DLYAKA with Claude Code & AI assistants" section explaining the secure transmission pattern with guarantees
- CLI help text emphasizes secure-by-default flow

[0.2.0]: https://github.com/TDYSKY/dlyaka/releases/tag/v0.2.0

## [0.1.0] — 2026-05-21

### Added

- Initial public release
- `dlyaka` CLI with `add`, `get`, `list`, `remove`, `run`, `env` commands
- Python library: `get_key()`, `add_key()`, `remove_key()`, `list_keys()`, `get_all_keys()`
- Provider helpers for Claude (Anthropic) and ChatGPT (OpenAI)
- Claude Code Skill (`claude_skill/dlyaka/SKILL.md`) that teaches Claude to use the vault
- Fernet (AES-128-CBC + HMAC-SHA256) encryption with PBKDF2-HMAC-SHA256 key derivation (480,000 iterations)
- Pre-built wheel and source distribution on the Releases page
- GitHub Actions CI matrix on Python 3.9 – 3.12
- 12 unit tests covering crypto and vault behavior

[0.1.0]: https://github.com/TDYSKY/dlyaka/releases/tag/v0.1.0
