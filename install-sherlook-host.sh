#!/bin/bash
set -e

REPO="https://raw.githubusercontent.com/SherlookHolmz/sherlook-host.py/main"
INSTALL_DIR="$HOME/.sherlook-host"
BIN_DIR="$HOME/bin"
APP="$INSTALL_DIR/sherlook-host.py"

echo "[+] Installing Sherlook Host Manager..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

echo "[+] Downloading sherlook-host.py..."
curl -fL --retry 3 --connect-timeout 15 \
  -o "$APP" \
  "$REPO/sherlook-host.py"

chmod 700 "$INSTALL_DIR"
chmod 700 "$APP"

echo "[+] Installing PasarGuard dependency..."
# تلاش برای نصب پکیج با دسترسی سیستم یا کاربر
python3 -m pip install --quiet --break-system-packages pasarguard 2>/dev/null || \
python3 -m pip install --quiet --user pasarguard

echo "[+] Creating sherlook-host command..."
cat > "$BIN_DIR/sherlook-host" <<EOF
#!/bin/bash
exec python3 "$APP" "\$@"
EOF

chmod 755 "$BIN_DIR/sherlook-host"

# تنظیم PATH برای bash و zsh
for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC_FILE" ]; then
        grep -qxF 'export PATH="$HOME/bin:$PATH"' "$RC_FILE" 2>/dev/null || \
            echo 'export PATH="$HOME/bin:$PATH"' >> "$RC_FILE"
    fi
done

export PATH="$HOME/bin:$PATH"

echo
echo "=========================================="
echo "     SHERLOOK HOST MANAGER INSTALLED"
echo "=========================================="
echo
echo "Run:"
echo "  sherlook-host"
echo
echo "If the command is not found, reload your shell:"
echo "  source ~/.bashrc   # (or source ~/.zshrc if using Zsh)"
echo
