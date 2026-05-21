# Security Policy

DLYAKA is a security tool. If you find a vulnerability, please tell me before telling the internet.

## Reporting a vulnerability

**Do not open a public issue for security bugs.**

Report security issues privately via one of these channels:

- **GitHub Security Advisories:** https://github.com/TDYSKY/dlyaka/security/advisories/new (preferred)
- **Email:** leorud2016@gmail.com
- **Discord (DM, not public channel):** https://discord.gg/RTax3aBMUs

You will get an initial response within 72 hours. Critical issues get a fix within 7 days where possible.

## Scope

In scope:

- Cryptographic weaknesses in `dlyaka.crypto` or `dlyaka.vault`
- Vault file disclosure or tampering issues
- Key leakage through error messages, logs, or process state
- Anything that lets an attacker read the vault without the master password

Out of scope:

- Attacks requiring local root or physical access (DLYAKA assumes the user's machine is not already compromised)
- Issues in dependencies (please report upstream to `cryptography` or `click`)
- Master password guessing (use a strong password — DLYAKA uses 480k PBKDF2 iterations to slow this down, but cannot prevent it for weak passwords)

## Threat model

DLYAKA protects API keys against:

- Accidental commit to git
- Accidental upload to a code-sharing site
- A non-root attacker reading `~/.dlyaka/vault.enc` without your master password

DLYAKA does **not** protect against:

- Malware running as your user
- A keylogger capturing your master password
- A compromised Python interpreter
- A backup tool that backs up an unlocked process's memory

## Disclosure

Once a fix is shipped, I will credit reporters in the release notes unless they prefer to stay anonymous.
