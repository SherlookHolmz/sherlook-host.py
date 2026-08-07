#!/bin/bash

set -e

REPO="https://raw.githubusercontent.com/SherlookHolmz/pasarguard_host_manager.py/main"
INSTALL_DIR="$HOME/.sherlook"
BIN_DIR="$HOME/bin"

echo "[+] Creating Sherlook directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

echo "[+] Downloading sherlook.sh..."

curl -fL --retry 3 --connect-timeout 15 \
    -o "$INSTALL_DIR/sherlook.sh" \
    "$REPO/sherlook.sh"

chmod +x "$INSTALL_DIR/sherlook.sh"

echo "[+] Downloading pasarguard_host_manager.py..."

curl -fL --retry 3 --connect-timeout 15 \
    -o "$INSTALL_DIR/pasarguard_host_manager.py" \
    "$REPO/pasarguard_host_manager.py"

chmod +x "$INSTALL_DIR/pasarguard_host_manager.py"

echo "[+] Installing Python dependency..."

python3 -m pip install --quiet --break-system-packages pasarguard 2>/dev/null || \
python3 -m pip install --quiet --user pasarguard

echo "[+] Creating sherlook command..."

cat > "$BIN_DIR/sherlook" <<EOF
#!/bin/bash
exec bash "$INSTALL_DIR/sherlook.sh" "\$@"
EOF

chmod +x "$BIN_DIR/sherlook"

echo "[+] Creating sherlook-host command..."

cat > "$BIN_DIR/sherlook-host" <<EOF
#!/bin/bash
exec python3 "$INSTALL_DIR/pasarguard_host_manager.py" "\$@"
EOF

chmod +x "$BIN_DIR/sherlook-host"

if ! grep -qxF 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
fi

export PATH="$HOME/bin:$PATH"

echo
echo "=========================================="
echo "          SHERLOOK INSTALLED"
echo "=========================================="
echo
echo "[+] Location Manager:"
echo "    sherlook"
echo
echo "[+] PasarGuard Host Manager:"
echo "    sherlook-host"
echo
echo "[+] Files installed in:"
echo "    $INSTALL_DIR"
echo
echo "=========================================="
echo
echo "[+] Installation completed successfully."
