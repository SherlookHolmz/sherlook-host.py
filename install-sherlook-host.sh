#!/usr/bin/env bash
set -euo pipefail

REPO="https://raw.githubusercontent.com/SherlookHolmz/sherlook-host.py/main"
INSTALL_DIR="${HOME}/.sherlook-host"
BIN_DIR="${HOME}/bin"
APP="${INSTALL_DIR}/sherlook-host.py"
VENV="${INSTALL_DIR}/venv"
PYTHON_BIN="${VENV}/bin/python"
COMMAND="${BIN_DIR}/sherlook-host"
VERSION="2.4.0"

printf '\033[96m[+] Installing Sherlook Host Manager...\033[0m\n'
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 is required. Install Python 3.10+ and rerun."
  exit 1
fi

PY_MAJOR_MINOR="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10+ is required")
print(f"[+] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PY

if [ ! -x "$PYTHON_BIN" ]; then
  echo "[+] Creating isolated Python virtual environment..."
  python3 -m venv "$VENV" || {
    echo "[!] python3-venv is missing. On Debian/Ubuntu: apt install -y python3-venv"
    exit 1
  }
fi

echo "[+] Upgrading pip tooling..."
"$PYTHON_BIN" -m pip install --quiet --upgrade pip setuptools wheel

echo "[+] Installing Pasarguard SDK ${VERSION}..."
"$PYTHON_BIN" -m pip install --quiet --no-cache-dir "pasarguard==${VERSION}"

echo "[+] Downloading sherlook-host.py..."
TMP_APP="$(mktemp "${INSTALL_DIR}/.sherlook-host.XXXXXX.py")"
trap 'rm -f "$TMP_APP"' EXIT
curl -fL --retry 3 --connect-timeout 15 --max-time 120 \
  -o "$TMP_APP" \
  "$REPO/sherlook-host.py"

"$PYTHON_BIN" -m py_compile "$TMP_APP"
chmod 700 "$INSTALL_DIR" "$TMP_APP"
mv -f "$TMP_APP" "$APP"
chmod 700 "$APP"
trap - EXIT

echo "[+] Creating sherlook-host command..."
cat > "$COMMAND" <<EOF
#!/usr/bin/env bash
exec "$PYTHON_BIN" "$APP" "\$@"
EOF
chmod 755 "$COMMAND"

# Persist PATH for common interactive shells. No trailing-space backslash bugs.
PATH_LINE='export PATH="$HOME/bin:$PATH"'
for RC_FILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
  touch "$RC_FILE"
  grep -Fqx "$PATH_LINE" "$RC_FILE" 2>/dev/null || printf '\n%s\n' "$PATH_LINE" >> "$RC_FILE"
done

export PATH="$BIN_DIR:$PATH"

"$COMMAND" --help >/dev/null 2>&1 || true

printf '\n\033[92m==========================================\033[0m\n'
printf '\033[92m     SHERLOOK HOST MANAGER INSTALLED\033[0m\n'
printf '\033[92m==========================================\033[0m\n\n'
printf 'Run:\n  sherlook-host\n\n'
printf 'Environment:\n  Python: %s\n  Pasarguard SDK: %s\n  App: %s\n\n' "$PY_MAJOR_MINOR" "$VERSION" "$APP"
printf 'If the command is not found in the current shell, run:\n  export PATH="$HOME/bin:$PATH"\n'
printf 'Then:\n  sherlook-host\n'
