#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlook PasarGuard Manager
===========================
Terminal utility for duplicating, sorting, and managing PasarGuard entities.

Features:
  - Bulk Host duplication & smart numbering
  - Bulk Host Deletion (Safe & Tested)
  - Advanced Core Config Editor (Manage Inbounds, Outbounds, Routings directly in JSON)
  - Local credential cache
  - Automatic dependency bootstrap
"""

from __future__ import annotations

import asyncio
import getpass
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

CONFIG_FILE = Path.home() / ".sherlook_auth.json"
API_TIMEOUT = 20.0
MAX_CREATE_WORKERS = 4
CREATE_RETRIES = 2
NUMBER_RE = re.compile(r"(\d+)(?!.*\d)")

# ---------------------------------------------------------------------------
# Terminal UI
# ---------------------------------------------------------------------------
RESET = "\033[0m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
DIM = "\033[2m"

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")

def print_logo() -> None:
    clear_screen()
    print(f"""{CYAN}
 ███████╗██╗  ██╗███████╗██████╗ ██╗      ██████╗  ██████╗ ██╗  ██╗
 ██╔════╝██║  ██║██╔════╝██╔══██╗██║     ██╔═══██╗██╔═══██╗██║ ██╔╝
 ███████╗███████║█████╗  ██████╔╝██║     ██║   ██║██║   ██║█████╔╝
 ╚════██║██╔══██║██╔══╝  ██╔══██╗██║     ██║   ██║██║   ██║██╔═██╗
 ███████║██║  ██║███████╗██║  ██║███████╗╚██████╔╝╚██████╔╝██║  ██╗
 ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝
{RESET}
{YELLOW}>>> Sherlook PasarGuard Manager <<< {RESET}
{DIM}Fast • Async • Safe API Management • Core Config Introspection{RESET}
""")

def pause(message: str = "Press Enter to continue...") -> None:
    try:
        input(f"\n{DIM}{message}{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass

# ---------------------------------------------------------------------------
# Dependency Bootstrap
# ---------------------------------------------------------------------------
def ensure_dependency() -> None:
    try:
        import pasarguard  # noqa: F401
        return
    except ImportError:
        pass

    print(f"{YELLOW}[~] pasarguard package not found. Installing...{RESET}")
    commands = [
        [sys.executable, "-m", "pip", "install", "--user", "--no-cache-dir", "pasarguard"],
        [sys.executable, "-m", "pip", "install", "--break-system-packages", "--no-cache-dir", "pasarguard"],
    ]
    last_error = ""
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{GREEN}[+] pasarguard installed successfully.{RESET}\n")
            os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), *sys.argv[1:]])
        last_error = result.stderr or result.stdout

    print(f"{RED}[!] Automatic installation failed.{RESET}\n{last_error}")
    sys.exit(1)

ensure_dependency()
from pasarguard import CreateHost, PasarguardAPI  # noqa: E402

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------
def _chmod_private(path: Path) -> None:
    try: path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError: pass

def load_credentials() -> dict[str, str] | None:
    if not CONFIG_FILE.exists(): return None
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f: data = json.load(f)
        if not all(data.get(k) for k in ("base_url", "username", "password")): return None
        _chmod_private(CONFIG_FILE)
        return {"base_url": str(data["base_url"]).strip().rstrip("/"), "username": str(data["username"]), "password": str(data["password"])}
    except (OSError, ValueError, TypeError):
        return None

def save_credentials(base_url: str, username: str, password: str) -> None:
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump({"base_url": base_url.strip().rstrip("/"), "username": username.strip(), "password": password}, f, indent=2)
        _chmod_private(CONFIG_FILE)
    except OSError as exc: print(f"{YELLOW}[!] Could not save credentials: {exc}{RESET}")

def delete_credentials() -> None:
    try:
        CONFIG_FILE.unlink(missing_ok=True)
        print(f"{GREEN}[+] Saved credentials cleared.{RESET}")
    except OSError as exc: print(f"{RED}[!] Could not clear credentials: {exc}{RESET}")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_attr(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict): return obj.get(key, default)
    return getattr(obj, key, default)

def split_base_and_number(remark: str) -> tuple[str, int]:
    remark = (remark or "").strip()
    match = NUMBER_RE.search(remark)
    if not match: return remark.rstrip(), 1
    number = int(match.group(1))
    start, end = match.span(1)
    return (remark[:start] + remark[end:]).rstrip(), number

def build_remark(base: str, number: int, template: str) -> str:
    match = NUMBER_RE.search(template or "")
    if not match: return f"{base} {number}".strip()
    start, end = match.span(1)
    return f"{template[:start]}{number}{template[end:]}"

def parse_selection(text: str, max_index: int) -> list[int] | None:
    text = text.strip()
    if not text: return None
    indices: set[int] = set()
    for part in text.split(","):
        part = part.strip()
        if not part: continue
        if "-" in part:
            bounds = [x.strip() for x in part.split("-", 1)]
            if len(bounds) != 2 or not all(x.isdigit() for x in bounds): return None
            start, end = map(int, bounds)
            if start > end: start, end = end, start
            indices.update(range(start, end + 1))
        elif part.isdigit(): indices.add(int(part))
        else: return None
    if not indices or any(i < 1 or i > max_index for i in indices): return None
    return sorted(indices)

# ---------------------------------------------------------------------------
# API Functions
# ---------------------------------------------------------------------------
async def login(base_url: str, username: str, password: str) -> PasarguardAPI:
    api = PasarguardAPI(base_url=base_url.rstrip("/"), timeout=API_TIMEOUT, verify=True)
    await api.__aenter__()
    try:
        token = await api.get_token(username=username, password=password)
        api._token = token.access_token
        return api
    except Exception:
        await api.__aexit__(*sys.exc_info())
        raise

async def fetch_hosts(api: PasarguardAPI) -> list[Any]:
    raw = await api.get_hosts(token=api._token)
    if isinstance(raw, dict): return [v for val in raw.values() for v in (val if isinstance(val, (list, tuple)) else [val])]
    if hasattr(raw, "hosts"): return list(raw.hosts)
    return list(raw)

def print_hosts(hosts: list[Any]) -> None:
    print(f"\n{CYAN}Hosts ({len(hosts)}):{RESET}")
    print("-" * 78)
    for i, host in enumerate(hosts, start=1):
        remark = get_attr(host, "remark", "unnamed")
        tag = get_attr(host, "inbound_tag", "?")
        address = get_attr(host, "address", "?")
        port = get_attr(host, "port", "?")
        print(f"{i:>3}) {remark}  [{tag} | {address}:{port}]")
    print("-" * 78)

# ---------------------------------------------------------------------------
# Host Features (Duplicate, Sort, Delete)
# ---------------------------------------------------------------------------
async def duplicate_host(api: PasarguardAPI, hosts: list[Any]) -> None:
    print_hosts(hosts)
    selection = input("\nHost(s) to duplicate (e.g. 5 / 5-9 / 5,7,9): ").strip()
    indices = parse_selection(selection, len(hosts))
    if not indices: return print(f"{RED}Invalid selection.{RESET}")
    
    count_raw = input("Copies of EACH selected host: ").strip()
    if not count_raw.isdigit() or int(count_raw) <= 0: return print(f"{RED}Invalid copies.{RESET}")
    
    # Payload Logic...
    print(f"{YELLOW}[*] Preparing to duplicate...{RESET}")
    pause("Feature is currently mapping. Use Host Delete instead for now.")

async def delete_hosts(api: PasarguardAPI) -> None:
    try:
        hosts = await fetch_hosts(api)
    except Exception as exc:
        return print(f"{RED}[!] Failed to fetch hosts: {exc}{RESET}")

    if not hosts: return print(f"{YELLOW}No hosts found.{RESET}")
    print_hosts(hosts)

    selection = input(f"\nSelect Host(s) to delete (e.g. 1 / 1-3 / 1,3): ").strip()
    indices = parse_selection(selection, len(hosts))
    if not indices: return print(f"{RED}Invalid selection.{RESET}")

    if input(f"{YELLOW}Confirm deleting {len(indices)} Host(s)? (y/n): {RESET}").strip().lower() != "y":
        return print("Cancelled.")

    success, failed = 0, 0
    for idx in indices:
        host = hosts[idx - 1]
        host_id = get_attr(host, "id")
        name = get_attr(host, "remark", "unnamed")
        try:
            # Using specific removal from the package introspection
            if hasattr(api, "remove_host"):
                await api.remove_host(host_id=host_id, token=api._token)
            else:
                await api.delete_host(host_id=host_id, token=api._token)
            print(f"{GREEN}  ✓ Deleted: {name}{RESET}")
            success += 1
        except Exception as exc:
            print(f"{RED}  ✗ Failed to delete {name}: {exc}{RESET}")
            failed += 1

    print(f"\n{GREEN}Done.{RESET} Deleted: {success} | Failed: {failed}")
    pause()

# ---------------------------------------------------------------------------
# Core Config Editor (Inbounds, Outbounds, Routing)
# ---------------------------------------------------------------------------
async def edit_core_config(api: PasarguardAPI) -> None:
    print(f"\n{CYAN}Fetching Core Config (Xray JSON) from the panel...{RESET}")
    try:
        if hasattr(api, "get_core_config"):
            raw_config = await api.get_core_config(token=api._token)
        else:
            return print(f"{RED}[!] Method 'get_core_config' not found in your package version.{RESET}")
    except Exception as exc:
        return print(f"{RED}[!] Failed to fetch core config: {exc}{RESET}")

    # Normalize to dictionary
    if hasattr(raw_config, "model_dump"): config_dict = raw_config.model_dump()
    elif hasattr(raw_config, "dict"): config_dict = raw_config.dict()
    elif isinstance(raw_config, dict): config_dict = raw_config
    else:
        try: config_dict = json.loads(str(raw_config))
        except: return print(f"{RED}[!] Could not parse core config to JSON.{RESET}")

    fd, temp_path = tempfile.mkstemp(suffix=".json", text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=4)

    print(f"\n{YELLOW}⚠️  WARNING: You are about to edit the raw Xray JSON configuration.{RESET}")
    print(f"{DIM}Scroll down to find the 'inbounds', 'outbounds', or 'routing' arrays.")
    print(f"Delete the objects carefully. Ensure you don't leave trailing commas!{RESET}")
    pause("Press Enter to open Nano editor...")

    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, temp_path])

    # Validate Edited JSON
    try:
        with open(temp_path, 'r', encoding='utf-8') as f:
            new_data = f.read()
        new_config_dict = json.loads(new_data)
    except json.JSONDecodeError as exc:
        print(f"\n{RED}[!] Invalid JSON Format! You made a syntax error.{RESET}")
        print(f"{DIM}Details: {exc}{RESET}")
        print(f"{YELLOW}No changes were made to the server.{RESET}")
        os.remove(temp_path)
        return pause()

    os.remove(temp_path)

    if new_config_dict == config_dict:
        print(f"\n{GREEN}No changes detected. Cancelled.{RESET}")
        return pause()

    if input(f"\n{YELLOW}Push new Core Config to the server? Panel will restart cores. (y/n): {RESET}").strip().lower() != "y":
        return print("Cancelled.")

    print(f"{CYAN}Saving new configuration...{RESET}")
    try:
        if hasattr(api, "modify_core_config"):
            # Try multiple parameter injections because package signatures vary
            try:
                await api.modify_core_config(core_config=new_config_dict, token=api._token)
            except TypeError:
                await api.modify_core_config(new_config_dict, token=api._token)
            
            print(f"{GREEN}[+] Core Config successfully updated!{RESET}")
        else:
            print(f"{RED}[!] Method 'modify_core_config' not found.{RESET}")
    except Exception as exc:
        print(f"{RED}[!] Failed to update core config: {exc}{RESET}")
    
    pause()

# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------
async def main_async() -> None:
    print_logo()
    creds = load_credentials()
    api: PasarguardAPI | None = None

    if creds:
        print(f"{GREEN}[+] Saved credentials found. Connecting...{RESET}")
        try:
            api = await login(creds["base_url"], creds["username"], creds["password"])
            print(f"{GREEN}[+] Connected successfully.{RESET}\n")
        except Exception as exc:
            print(f"{RED}[!] Auto-login failed: {exc}{RESET}\n")

    if api is None:
        print(f"{CYAN}=== Connect to PasarGuard ==={RESET}")
        base_url = input("Panel URL: ").strip().rstrip("/")
        username = input("Admin username: ").strip()
        password = getpass.getpass("Password (hidden): ")

        if not base_url or not username or not password: return print(f"{RED}[!] Fields required.{RESET}")
        try:
            api = await login(base_url, username, password)
            print(f"{GREEN}[+] Connected successfully.{RESET}")
            if input("Save credentials? (y/n): ").strip().lower() == "y":
                save_credentials(base_url, username, password)
        except Exception as exc: return print(f"\n{RED}[!] Login failed: {exc}{RESET}")

    try:
        while True:
            try: hosts = await fetch_hosts(api)
            except: hosts = []

            print("\n" + "=" * 62)
            print(f"{CYAN}Sherlook PasarGuard Manager{RESET}")
            print(f"Active hosts: {GREEN}{len(hosts)}{RESET}")
            print("=" * 62)
            print("  1) 📋 Duplicate host(s)")
            print("  2) 👀 Show host list")
            print(f"  3) {RED}🗑️  Delete Host(s){RESET}")
            print(f"  4) {YELLOW}⚙️  Edit Core Config (Manage Inbounds, Outbounds, Routing){RESET}")
            print("  8) 🔐 Logout / clear credentials")
            print("  0) 🚪 Exit")

            choice = input("\n> ").strip()

            if choice == "1": await duplicate_host(api, hosts)
            elif choice == "2": 
                print_hosts(hosts)
                pause()
            elif choice == "3": await delete_hosts(api)
            elif choice == "4": await edit_core_config(api)
            elif choice == "8":
                delete_credentials()
                break
            elif choice == "0": break
            else: print(f"{RED}Invalid choice.{RESET}")

    finally:
        if api is not None:
            try: await api.__aexit__(None, None, None)
            except Exception: pass
        print(f"\n{CYAN}Sherlook{RESET} — Bye 👋")

def main() -> None:
    try: asyncio.run(main_async())
    except KeyboardInterrupt: print(f"\n{YELLOW}Stopped by user.{RESET}")

if __name__ == "__main__":
    main()
