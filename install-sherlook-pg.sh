#!/usr/bin/env bash

set -Eeuo pipefail

# ============================================================
# 🦅 Sherlook Installer
# ============================================================

REPO_RAW="https://raw.githubusercontent.com/SherlookHolmz/multi/main"

INSTALL_DIR="${HOME}/.sherlook"
BIN_DIR="${HOME}/bin"

SHERLOOK_SH="${INSTALL_DIR}/sherlook.sh"
PASARGUARD_MANAGER="${INSTALL_DIR}/pasarguard_host_manager.py"
LAUNCHER="${BIN_DIR}/sherlook"

echo
echo "============================================================"
echo "                 🦅 SHERLOOK INSTALLER"
echo "============================================================"
echo

log() {
    echo "[+] $1"
}

warn() {
    echo "[!] $1"
}

die() {
    echo "[-] $1"
    exit 1
}

# ------------------------------------------------------------
# Check required commands
# ------------------------------------------------------------

command -v wget >/dev/null 2>&1 || die "wget is required."
command -v bash >/dev/null 2>&1 || die "bash is required."

# ------------------------------------------------------------
# Create directories
# ------------------------------------------------------------

log "Creating Sherlook directories..."

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# ------------------------------------------------------------
# Download files
# ------------------------------------------------------------

download_file() {
    local url="$1"
    local output="$2"

    log "Downloading $(basename "$output")..."

    if ! wget -q --show-progress -O "$output" "$url"; then
        rm -f "$output"
        die "Failed to download $(basename "$output")."
    fi

    [ -s "$output" ] || die "$(basename "$output") is empty."
}

download_file \
    "${REPO_RAW}/sherlook.sh" \
    "$SHERLOOK_SH"

download_file \
    "${REPO_RAW}/pasarguard_host_manager.py" \
    "$PASARGUARD_MANAGER"

chmod +x "$SHERLOOK_SH"
chmod +x "$PASARGUARD_MANAGER"

# ------------------------------------------------------------
# Check Python
# ------------------------------------------------------------

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    warn "python3 was not found."
    PYTHON_BIN=""
fi

# ------------------------------------------------------------
# Create sherlook launcher
# ------------------------------------------------------------

log "Creating 'sherlook' command..."

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash

SHERLOOK_DIR="\$HOME/.sherlook"

if [ ! -d "\$SHERLOOK_DIR" ]; then
    echo "[!] Sherlook installation not found."
    echo "[!] Run the installer again."
    exit 1
fi

echo
echo "🦅 Sherlook"
echo

echo "Select tool:"
echo
echo "  1) 🌍 Sherlook Location Manager"
echo "  2) 📋 PasarGuard Host Manager"
echo "  0) 🚪 Exit"
echo

read -r -p "> " CHOICE

case "\$CHOICE" in

    1)
        exec bash "\$SHERLOOK_DIR/sherlook.sh"
        ;;

    2)
        if command -v python3 >/dev/null 2>&1; then
            exec python3 "\$SHERLOOK_DIR/pasarguard_host_manager.py"
        else
            echo "[!] python3 is required for PasarGuard Host Manager."
            exit 1
        fi
        ;;

    0)
        exit 0
        ;;

    *)
        echo "[!] Invalid option."
        exit 1
        ;;

esac
EOF

chmod +x "$LAUNCHER"

# ------------------------------------------------------------
# Add ~/bin to PATH
# ------------------------------------------------------------

add_path_if_needed() {

    local shell_rc=""

    case "${SHELL:-}" in
        */zsh)
            shell_rc="${HOME}/.zshrc"
            ;;
        */bash)
            shell_rc="${HOME}/.bashrc"
            ;;
        *)
            shell_rc="${HOME}/.profile"
            ;;
    esac

    if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then

        if ! grep -Fqs 'export PATH="$HOME/bin:$PATH"' "$shell_rc" 2>/dev/null; then
            {
                echo
                echo '# Sherlook'
                echo 'export PATH="$HOME/bin:$PATH"'
            } >> "$shell_rc"
        fi

        export PATH="${BIN_DIR}:${PATH}"

        log "~/bin added to PATH."
    else
        log "~/bin is already in PATH."
    fi
}

add_path_if_needed

# ------------------------------------------------------------
# Verify installation
# ------------------------------------------------------------

echo
log "Verifying installation..."

[ -f "$SHERLOOK_SH" ] || die "sherlook.sh installation failed."
[ -f "$PASARGUARD_MANAGER" ] || die "PasarGuard manager installation failed."
[ -x "$LAUNCHER" ] || die "Sherlook launcher installation failed."

# ------------------------------------------------------------
# Create version/info file
# ------------------------------------------------------------

cat > "${INSTALL_DIR}/VERSION" <<EOF
Sherlook
Repository: ${REPO_RAW}
Installed: $(date '+%Y-%m-%d %H:%M:%S')
EOF

# ------------------------------------------------------------
# Finish
# ------------------------------------------------------------

echo
echo "============================================================"
echo "             ✅ SHERLOOK INSTALLED SUCCESSFULLY"
echo "============================================================"
echo
echo "📁 Installation:"
echo "   ${INSTALL_DIR}"
echo
echo "🚀 Command:"
echo "   sherlook"
echo
echo "📋 Installed:"
echo "   ✓ sherlook.sh"
echo "   ✓ pasarguard_host_manager.py"
echo "   ✓ sherlook command"
echo

if [[ ":${PATH}:" != *":${BIN_DIR}:"* ]]; then
    echo "⚠️  Restart your terminal or run:"
    echo
    echo "   source ~/.bashrc"
    echo
    echo "Then:"
    echo
    echo "   sherlook"
else
    echo "🚀 Run now:"
    echo
    echo "   sherlook"
fi

echo
echo "🦅 Sherlook — Simple Tools • Faster Workflows"
echo
