#!/bin/bash
set -e

REPO="https://raw.githubusercontent.com/SherlookHolmz/pasarguard_host_manager.py/main"
INSTALL_DIR="$HOME/.sherlook"
BIN_DIR="$HOME/bin"

echo "[+] Creating Sherlook directories..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

echo "[+] Downloading Sherlook PasarGuard Host Manager..."
curl -fL --retry 3 --connect-timeout 15 \
  -o "$INSTALL_DIR/sherlook_pasarguard_host_manager.py" \
  "$REPO/sherlook_pasarguard_host_manager.py"

chmod 700 "$INSTALL_DIR"
chmod 700 "$INSTALL_DIR/sherlook_pasarguard_host_manager.py"

echo "[+] Installing pasarguard dependency..."
python3 -m pip install --quiet --break-system-packages pasarguard 2>/dev/null || \
python3 -m pip install --quiet --user pasarguard

echo "[+] Creating 'sherlook' command..."
cat > "$BIN_DIR/sherlook" <<EOF
#!/bin/bash
exec python3 "$INSTALL_DIR/sherlook_pasarguard_host_manager.py" "\$@"
EOF
chmod 755 "$BIN_DIR/sherlook"

grep -qxF 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null || \
  echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"

export PATH="$HOME/bin:$PATH"

echo
echo "=========================================="
echo "      SHERLOOK HOST MANAGER INSTALLED"
echo "=========================================="
echo
echo "Run:"
echo "  sherlook"
echo
echo "Installed:"
echo "  $INSTALL_DIR/sherlook_pasarguard_host_manager.py"
echo
echo "If 'sherlook' is not found, run:"
echo "  source ~/.bashrc"
echo
