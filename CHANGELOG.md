# Changelog

All notable changes to DLYAKA will be documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows [SemVer](https://semver.org/).

## [0.3.1] — 2026-05-25

### Fixed

- **release-binaries.yml**: dropped `macos-13` (Intel) runner from the build matrix. GitHub's macOS 13 runner pool had multi-hour queue times that blocked the entire workflow. Apple Silicon binaries run on Intel Macs via Rosetta 2; users who need a native Intel binary can build from source with `pyinstaller packaging/entry_cli.py`.
- No behavior changes in the package itself — same code as 0.3.0, only the release pipeline changed.

[0.3.1]: https://github.com/TDYSKY/dlyaka/releases/tag/v0.3.1

## [0.3.0] — 2026-05-21

### Added — Native apps for all platforms

- **Tkinter GUI app** (`dlyaka-gui`) with all CLI features:
  - Add / remove keys
  - List with fingerprints (no values ever shown)
  - Copy key to clipboard with **auto-clear after 30 seconds**
  - "Run script…" file picker that injects keys into the subprocess and shows live, redacted output in a window
  - Master password cached only in memory; "Lock vault" button to forget it
- **Native single-file binaries** for every major platform via PyInstaller:
  - Linux x86_64 (CLI + GUI)
  - macOS x86_64 (Intel) and arm64 (Apple Silicon) — CLI + GUI + `.app` bundle
  - Windows x86_64 (CLI + GUI)
- **`release-binaries.yml`** GitHub Actions workflow that builds and attaches all binaries to every tagged release, with per-platform SHA-256 checksums.
- New `dlyaka-gui` entry point in `pyproject.toml`.

[0.3.0]: https://github.com/TDYSKY/dlyaka/releases/tag/v0.3.0

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
