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

python3 -m pip install --quiet --break-system-packages pasarguard 2>/dev/null || \
python3 -m pip install --quiet --user pasarguard

echo "[+] Creating sherlook-host command..."

cat > "$BIN_DIR/sherlook-host" <<EOF
#!/bin/bash
exec python3 "$APP" "\$@"
EOF

chmod 755 "$BIN_DIR/sherlook-host"

if [ -f "$HOME/.bashrc" ]; then
    grep -qxF 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null || \
        echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
fi

export PATH="$HOME/bin:$PATH"

echo
echo "=========================================="
echo "     SHERLOOK HOST MANAGER INSTALLED"
echo "=========================================="
echo
echo "Run:"
echo "  sherlook-host"
echo
echo "If the command is not found:"
echo "  source ~/.bashrc"
echo
