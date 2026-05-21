# Contributing to DLYAKA

Thanks for considering a contribution. DLYAKA is a small project — I'd rather have well-thought-out PRs than a flood of churn.

## Quick start

```bash
git clone https://github.com/TDYSKY/dlyaka
cd dlyaka
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

All tests should pass (12 currently). If you break tests, fix them before opening a PR.

## What I'm looking for

**Yes please:**

- Bug fixes (with a test that reproduces the bug)
- New provider integrations (Google Gemini, Mistral, etc.) — keep them small and optional
- Cross-platform fixes (Windows, Linux quirks)
- Documentation improvements
- Performance fixes (if measurable)

**Probably not:**

- A new master-password backend (use the keyring extension once it exists, don't replace Fernet)
- A GUI — DLYAKA is intentionally a CLI tool
- "Refactor everything" PRs — small, focused changes only
- Dependencies for things that don't need them (anything in the standard library should stay in the standard library)

**Definitely not:**

- Anything that weakens the crypto
- Anything that auto-fetches the master password from a network source
- Anything that logs key values

## Code style

- Follow what's already there
- Tests live in `tests/`, use `pytest`
- Cryptography changes need a test that proves they work and a note on the threat model
- New CLI subcommands need a `--help` block and a README entry

## Commits & PRs

- One feature per PR
- Reference any related issue (`Closes #42`)
- Write a clear PR description — what changed, why, how to test

## Reporting bugs

Open an issue with:

- DLYAKA version (`dlyaka --version`)
- Python version
- OS
- Steps to reproduce
- Expected vs actual behavior

**For security bugs, see [SECURITY.md](SECURITY.md) — do not open a public issue.**

## Community

Questions and discussion: [Discord](https://discord.gg/RTax3aBMUs).
