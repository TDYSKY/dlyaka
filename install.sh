#!/usr/bin/env bash
# DLYAKA one-command installer.
# Downloads the latest release from GitHub, verifies the SHA-256 checksum,
# and installs the wheel using the best available method (pipx / pip --user / pip).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/TDYSKY/dlyaka/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/TDYSKY/dlyaka/main/install.sh | bash -s -- --pipx
#   curl -fsSL https://raw.githubusercontent.com/TDYSKY/dlyaka/main/install.sh | bash -s -- --version 0.2.0
#
# Flags:
#   --pipx              Force install via pipx (recommended for CLI tools)
#   --pip               Force install via pip --user
#   --version X.Y.Z     Install a specific version (default: latest)
#   --help              Print this help

set -euo pipefail

REPO="TDYSKY/dlyaka"
VERSION="latest"
FORCE_METHOD=""

# ---------- color output ----------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    BOLD=$'\033[1m'; DIM=$'\033[2m'
    GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; CYAN=$'\033[36m'
    RESET=$'\033[0m'
else
    BOLD=""; DIM=""; GREEN=""; YELLOW=""; RED=""; CYAN=""; RESET=""
fi

log()   { printf "${BOLD}==>${RESET} %s\n" "$1"; }
ok()    { printf "    ${GREEN}OK${RESET} %s\n" "$1"; }
warn()  { printf "    ${YELLOW}!${RESET}  %s\n" "$1"; }
err()   { printf "${RED}Error:${RESET} %s\n" "$1" >&2; }

# ---------- parse args ----------
while [ $# -gt 0 ]; do
    case "$1" in
        --pipx)    FORCE_METHOD="pipx"; shift ;;
        --pip)     FORCE_METHOD="pip-user"; shift ;;
        --version) VERSION="${2#v}"; shift 2 ;;
        -h|--help)
            sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) err "Unknown option: $1"; exit 1 ;;
    esac
done

# ---------- platform & python check ----------
case "$(uname -s)" in
    Darwin|Linux) ;;
    *) err "Unsupported platform: $(uname -s). On Windows, use: pip install <url>"; exit 1 ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
    err "python3 not found. Install Python 3.9 or newer and try again."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=${PY_VER%.*}
PY_MINOR=${PY_VER#*.}
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    err "Python 3.9+ required. Found $PY_VER."
    exit 1
fi

# Pick a sha256 tool
if command -v shasum >/dev/null 2>&1; then
    SHA_CMD="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
    SHA_CMD="sha256sum"
else
    warn "No shasum/sha256sum available — checksum verification will be skipped."
    SHA_CMD=""
fi

# ---------- detect install method ----------
detect_method() {
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo "venv"
    elif command -v pipx >/dev/null 2>&1; then
        echo "pipx"
    else
        echo "pip-user"
    fi
}

METHOD="${FORCE_METHOD:-$(detect_method)}"

# ---------- fetch release info ----------
if [ "$VERSION" = "latest" ]; then
    API_URL="https://api.github.com/repos/${REPO}/releases/latest"
else
    API_URL="https://api.github.com/repos/${REPO}/releases/tags/v${VERSION}"
fi

log "Querying GitHub for the ${VERSION} release..."
RELEASE_JSON=$(curl -fsSL --max-time 30 "$API_URL") || {
    err "Could not reach $API_URL"
    exit 1
}

# Extract fields with Python (avoid jq dependency)
TAG=$(printf '%s' "$RELEASE_JSON" | python3 -c '
import json, sys
print(json.load(sys.stdin)["tag_name"])
')

WHEEL_URL=$(printf '%s' "$RELEASE_JSON" | python3 -c '
import json, sys
data = json.load(sys.stdin)
urls = [a["browser_download_url"] for a in data.get("assets", []) if a["name"].endswith(".whl")]
print(urls[0] if urls else "")
')

SHA_URL=$(printf '%s' "$RELEASE_JSON" | python3 -c '
import json, sys
data = json.load(sys.stdin)
urls = [a["browser_download_url"] for a in data.get("assets", []) if a["name"] == "SHA256SUMS.txt"]
print(urls[0] if urls else "")
')

if [ -z "$WHEEL_URL" ]; then
    err "Could not find a wheel (.whl) in the $TAG release."
    exit 1
fi

WHEEL_NAME=$(basename "$WHEEL_URL")
log "Release: ${CYAN}${TAG}${RESET}"
log "Asset:   ${WHEEL_NAME}"
log "Method:  ${METHOD}"

# ---------- download ----------
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
WHEEL_FILE="$TMPDIR/$WHEEL_NAME"

log "Downloading wheel..."
curl -fSL --max-time 120 "$WHEEL_URL" -o "$WHEEL_FILE"

# ---------- verify checksum ----------
if [ -n "$SHA_CMD" ] && [ -n "$SHA_URL" ]; then
    log "Verifying SHA-256 checksum..."
    curl -fsSL --max-time 30 "$SHA_URL" -o "$TMPDIR/SHA256SUMS.txt"
    EXPECTED=$(grep -E "[[:space:]]${WHEEL_NAME}$" "$TMPDIR/SHA256SUMS.txt" | awk '{print $1}')
    ACTUAL=$($SHA_CMD "$WHEEL_FILE" | awk '{print $1}')
    if [ -z "$EXPECTED" ]; then
        warn "$WHEEL_NAME not listed in SHA256SUMS.txt — skipping verification."
    elif [ "$EXPECTED" != "$ACTUAL" ]; then
        err "Checksum mismatch!"
        err "  expected: $EXPECTED"
        err "  actual:   $ACTUAL"
        err "Refusing to install. Re-run; if the problem persists, open an issue."
        exit 1
    else
        ok "checksum matches ($EXPECTED)"
    fi
else
    warn "Skipping checksum verification."
fi

# ---------- install ----------
log "Installing via $METHOD..."

case "$METHOD" in
    venv)
        python3 -m pip install --upgrade "$WHEEL_FILE"
        ;;
    pipx)
        if ! command -v pipx >/dev/null 2>&1; then
            err "pipx requested but not installed. Try: python3 -m pip install --user pipx"
            exit 1
        fi
        # --force lets us upgrade an existing pipx install
        pipx install --force "$WHEEL_FILE"
        ;;
    pip-user)
        # PEP 668 fallback handling
        if ! python3 -m pip install --user --upgrade "$WHEEL_FILE" 2>"$TMPDIR/pip.err"; then
            if grep -q "externally-managed-environment" "$TMPDIR/pip.err"; then
                err "Your Python is externally-managed (PEP 668)."
                err "Best fix: install pipx and rerun with --pipx"
                err "  python3 -m pip install --user --break-system-packages pipx"
                err "  curl -fsSL ... | bash -s -- --pipx"
                err ""
                err "Or, less recommended: rerun with --break-system-packages"
                cat "$TMPDIR/pip.err" >&2
                exit 1
            fi
            cat "$TMPDIR/pip.err" >&2
            exit 1
        fi
        ;;
esac

# ---------- verify and report ----------
echo

# Ensure ~/.local/bin is mentioned if pip --user was used and dlyaka isn't on PATH yet
if ! command -v dlyaka >/dev/null 2>&1; then
    USER_BIN="$(python3 -m site --user-base)/bin"
    warn "'dlyaka' is installed, but not on your PATH."
    warn "Add this line to your shell rc (~/.bashrc or ~/.zshrc):"
    echo
    echo "    export PATH=\"$USER_BIN:\$PATH\""
    echo
    warn "Then open a new terminal."
else
    INSTALLED=$(dlyaka --version 2>&1 | head -1)
    ok "$INSTALLED"
fi

# ---------- next steps ----------
cat <<EOF

${BOLD}${GREEN}DLYAKA is installed.${RESET}

${BOLD}Quickstart:${RESET}
  ${DIM}# Store an API key (hidden prompt — won't enter shell history):${RESET}
  ${CYAN}dlyaka add anthropic${RESET}

  ${DIM}# Run any script with keys injected as env vars:${RESET}
  ${CYAN}dlyaka run python my_script.py${RESET}

  ${DIM}# Or from Python:${RESET}
  ${CYAN}from dlyaka import get_key${RESET}

${BOLD}Docs:${RESET}    https://github.com/TDYSKY/dlyaka
${BOLD}Discord:${RESET} https://discord.gg/RTax3aBMUs
${BOLD}Shop:${RESET}    https://shop.agencyg.de

EOF
