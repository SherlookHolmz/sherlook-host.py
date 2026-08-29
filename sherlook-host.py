#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlook PasarGuard Host Manager
================================
Terminal utility for duplicating, sorting, and managing PasarGuard entities.

Features:
  - Async PasarGuard API access
  - Bulk host duplication with bounded concurrency
  - Smart remark numbering
  - Group/sort preview
  - Safe Bulk Delete (Hosts, Inbounds, Routings, Outbounds)
  - Interactive Introspection for unknown package versions
  - Local credential cache with restrictive permissions
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
{YELLOW}>>> Sherlook PasarGuard Host Manager <<< {RESET}
{DIM}Fast • Async • Safe-ish local credential storage • PasarGuard API{RESET}
""")

def pause(message: str = "Press Enter to continue...") -> None:
    try:
        input(f"\n{DIM}{message}{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass

# ---------------------------------------------------------------------------
# Dependency bootstrap
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
# Credential cache
# ---------------------------------------------------------------------------

def _chmod_private(path: Path) -> None:
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

def load_credentials() -> dict[str, str] | None:
    if not CONFIG_FILE.exists(): return None
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not all(data.get(k) for k in ("base_url", "username", "password")): return None
        _chmod_private(CONFIG_FILE)
        return {
            "base_url": str(data["base_url"]).strip().rstrip("/"),
            "username": str(data["username"]),
            "password": str(data["password"]),
        }
    except (OSError, ValueError, TypeError):
        return None

def save_credentials(base_url: str, username: str, password: str) -> None:
    data = {"base_url": base_url.strip().rstrip("/"), "username": username.strip(), "password": password}
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        _chmod_private(CONFIG_FILE)
    except OSError as exc:
        print(f"{YELLOW}[!] Could not save credentials: {exc}{RESET}")

def delete_credentials() -> None:
    try:
        CONFIG_FILE.unlink(missing_ok=True)
        print(f"{GREEN}[+] Saved credentials cleared.{RESET}")
    except OSError as exc:
        print(f"{RED}[!] Could not clear credentials: {exc}{RESET}")

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
        elif part.isdigit():
            indices.add(int(part))
        else: return None
    if not indices or any(i < 1 or i > max_index for i in indices): return None
    return sorted(indices)

# ---------------------------------------------------------------------------
# API helpers
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
    if isinstance(raw, dict):
        hosts: list[Any] = []
        for value in raw.values():
            if isinstance(value, (list, tuple)): hosts.extend(value)
        return hosts
    if hasattr(raw, "hosts"): return list(raw.hosts)
    return list(raw)

def model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"): return model.model_dump()
    if hasattr(model, "dict"): return model.dict()
    if isinstance(model, dict): return dict(model)
    return dict(vars(model))

def host_to_create_payload(host: Any) -> dict[str, Any]:
    data = model_to_dict(host)
    if hasattr(CreateHost, "model_fields"): allowed = set(CreateHost.model_fields.keys())
    elif hasattr(CreateHost, "__fields__"): allowed = set(CreateHost.__fields__.keys())
    else: allowed = set(data)
    return {k: v for k, v in data.items() if k in allowed}

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
# Duplicate & Sorting
# ---------------------------------------------------------------------------

async def create_one(api: PasarguardAPI, payload: dict[str, Any], semaphore: asyncio.Semaphore) -> tuple[bool, str, str]:
    remark = str(payload.get("remark", "unnamed"))
    async with semaphore:
        for attempt in range(1, CREATE_RETRIES + 2):
            try:
                host = await api.create_host(CreateHost(**payload), token=api._token)
                return True, str(get_attr(host, "remark", remark)), ""
            except Exception as exc:
                if attempt > CREATE_RETRIES: return False, remark, f"{type(exc).__name__}: {exc}"
                await asyncio.sleep(0.6 * attempt)
    return False, remark, "Unknown error"

async def duplicate_host(api: PasarguardAPI, hosts: list[Any]) -> None:
    print_hosts(hosts)
    selection = input("\nHost(s) to duplicate (e.g. 5 / 5-9 / 5,7,9): ").strip()
    indices = parse_selection(selection, len(hosts))
    if not indices: return print(f"{RED}Invalid selection.{RESET}")
    
    count_raw = input("Copies of EACH selected host: ").strip()
    if not count_raw.isdigit() or int(count_raw) <= 0: return print(f"{RED}Invalid copies.{RESET}")
    count = int(count_raw)
    
    jobs: list[dict[str, Any]] = []
    reserved: dict[str, set[int]] = {}
    
    for idx in indices:
        source = hosts[idx - 1]
        source_remark = str(get_attr(source, "remark", ""))
        base, _ = split_base_and_number(source_remark)
        used = reserved.setdefault(base, set())
        existing = {num for h in hosts for ob, num in [split_base_and_number(str(get_attr(h, "remark", "")))] if ob == base}
        start = max(existing | used, default=0) + 1
        
        for offset in range(count):
            number = start + offset
            used.add(number)
            payload = host_to_create_payload(source)
            payload["remark"] = build_remark(base, number, source_remark)
            jobs.append(payload)

    print(f"\n{CYAN}Creating {len(jobs)} host(s)...{RESET}")
    semaphore = asyncio.Semaphore(MAX_CREATE_WORKERS)
    results = await asyncio.gather(*(create_one(api, p, semaphore) for p in jobs))
    
    created = sum(1 for ok, _, _ in results if ok)
    failed = len(jobs) - created
    for ok, remark, error in results:
        print(f"{GREEN}  ✓ Created: {remark}{RESET}" if ok else f"{RED}  ✗ Failed: {remark}\n    {error}{RESET}")
    print(f"\n{GREEN}Done.{RESET} Created: {created} | Failed: {failed}")
    pause()

async def sort_hosts(api: PasarguardAPI, hosts: list[Any]) -> None:
    groups, group_order = {}, []
    for host in hosts:
        base, number = split_base_and_number(str(get_attr(host, "remark", "")))
        if base not in groups:
            groups[base] = []
            group_order.append(base)
        groups[base].append((number, host))

    ordered = [host for base in group_order for _, host in sorted(groups[base], key=lambda x: x[0])]
    print(f"\n{CYAN}Proposed order:{RESET}")
    for i, host in enumerate(ordered, 1): print(f"{i:>3}) {get_attr(host, 'remark', '')}")
    if not ordered: return print(f"{YELLOW}No hosts to sort.{RESET}")

    if not get_attr(ordered[0], "priority") and not hasattr(ordered[0], "priority"):
        print(f"\n{YELLOW}This API model does not expose a 'priority' field. Nothing changed.{RESET}")
        return pause()

    if input("\nSave this order to the panel? (y/n): ").strip().lower() != "y": return print("Cancelled.")
    
    success = 0
    for priority, host in enumerate(ordered):
        try:
            payload = host_to_create_payload(host)
            payload["priority"] = priority
            await api.modify_host(host_id=get_attr(host, "id"), host=CreateHost(**payload), token=api._token)
            success += 1
        except Exception as exc:
            print(f"{RED}  ✗ Failed: {get_attr(host, 'remark', '')} — {exc}{RESET}")
    print(f"\n{GREEN}Order saved for {success}/{len(ordered)} host(s).{RESET}")
    pause()

# ---------------------------------------------------------------------------
# Extremely Robust Delete System
# ---------------------------------------------------------------------------

async def delete_items(api: PasarguardAPI, item_type: str) -> None:
    """Intelligently discovers API methods to fetch and delete without crashing."""
    
    # 1. Discover the FETCH method
    fetch_func = None
    possible_fetches = [f"get_{item_type}s", f"get_{item_type}", f"list_{item_type}s"]
    for method in possible_fetches:
        if hasattr(api, method):
            fetch_func = getattr(api, method)
            break
            
    if not fetch_func:
        print(f"\n{YELLOW}[!] The standard GET method for '{item_type}' was not found in this package version.{RESET}")
        all_methods = [m for m in dir(api) if callable(getattr(api, m)) and not m.startswith("_")]
        print(f"{CYAN}Available library methods:{RESET}\n  " + "\n  ".join(all_methods))
        manual_fetch = input(f"\n{GREEN}Please type the exact exact name of the method to FETCH {item_type}s:{RESET} ").strip()
        if not manual_fetch or not hasattr(api, manual_fetch):
            return print(f"{RED}Method not found or cancelled.{RESET}")
        fetch_func = getattr(api, manual_fetch)

    # 2. Fetch the items
    print(f"{CYAN}Fetching {item_type}s...{RESET}")
    try:
        raw = await fetch_func(token=api._token)
        if isinstance(raw, dict):
            items = [v for val in raw.values() for v in (val if isinstance(val, (list, tuple)) else [val])]
        else:
            # Check if it returned an object with a matching attribute (e.g., raw.hosts)
            attr_name = item_type + "s"
            if hasattr(raw, attr_name):
                items = list(getattr(raw, attr_name))
            else:
                items = list(raw)
    except Exception as exc:
        print(f"{RED}[!] Failed to fetch {item_type}s: {exc}{RESET}")
        pause()
        return

    if not items:
        print(f"{YELLOW}No {item_type}s found on the server.{RESET}")
        pause()
        return

    # 3. Print items
    print(f"\n{CYAN}{item_type.capitalize()}s ({len(items)}):{RESET}")
    print("-" * 78)
    for i, item in enumerate(items, start=1):
        name = get_attr(item, "remark", get_attr(item, "tag", get_attr(item, "name", "unnamed")))
        print(f"{i:>3}) {name}  [ID: {get_attr(item, 'id', '?')}]")
    print("-" * 78)

    selection = input(f"\nSelect {item_type}(s) to delete (e.g. 1 / 1-3 / 1,3): ").strip()
    indices = parse_selection(selection, len(items))
    if not indices: return print(f"{RED}Invalid selection.{RESET}")

    if input(f"{YELLOW}Confirm deleting {len(indices)} {item_type}(s)? (y/n): {RESET}").strip().lower() != "y":
        return print("Cancelled.")

    # 4. Discover the DELETE method
    delete_func = None
    possible_deletes = [f"delete_{item_type}", f"remove_{item_type}", f"del_{item_type}"]
    for method in possible_deletes:
        if hasattr(api, method):
            delete_func = getattr(api, method)
            break
            
    if not delete_func:
        print(f"\n{YELLOW}[!] The standard DELETE method for '{item_type}' was not found.{RESET}")
        all_methods = [m for m in dir(api) if callable(getattr(api, m)) and not m.startswith("_")]
        suggestions = [m for m in all_methods if item_type in m.lower() or "del" in m.lower() or "rem" in m.lower()]
        print(f"{CYAN}Suggested methods in your package for deletion:{RESET}\n  " + "\n  ".join(suggestions))
        manual_delete = input(f"\n{GREEN}Please type the exact name of the method to DELETE a {item_type}:{RESET} ").strip()
        if not manual_delete or not hasattr(api, manual_delete):
            return print(f"{RED}Method not found or cancelled.{RESET}")
        delete_func = getattr(api, manual_delete)

    # 5. Execute Delete with robust parameter injection
    success, failed = 0, 0
    for idx in indices:
        item = items[idx - 1]
        item_id = get_attr(item, "id")
        name = get_attr(item, "remark", get_attr(item, "tag", get_attr(item, "name", "unnamed")))
        
        try:
            # Fallback 1: specific kwarg (host_id=...)
            try:
                await delete_func(**{"token": api._token, f"{item_type}_id": item_id})
            except TypeError as te:
                if "keyword argument" in str(te).lower() or "unexpected" in str(te).lower():
                    # Fallback 2: generic kwarg (id=...)
                    try:
                        await delete_func(**{"token": api._token, "id": item_id})
                    except TypeError:
                        # Fallback 3: positional argument (id, token=...)
                        await delete_func(item_id, token=api._token)
                else:
                    raise te
                    
            print(f"{GREEN}  ✓ Deleted: {name}{RESET}")
            success += 1
        except Exception as exc:
            print(f"{RED}  ✗ Failed to delete {name}: {exc}{RESET}")
            failed += 1

    print(f"\n{GREEN}Done.{RESET} Deleted: {success} | Failed: {failed}")
    pause()

# ---------------------------------------------------------------------------
# Main
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

        if not base_url or not username or not password:
            return print(f"{RED}[!] URL, username and password are required.{RESET}")
        try:
            api = await login(base_url, username, password)
            print(f"{GREEN}[+] Connected successfully.{RESET}")
            if input("Save credentials locally? (y/n): ").strip().lower() == "y":
                save_credentials(base_url, username, password)
                print(f"{GREEN}[+] Saved to {CONFIG_FILE}{RESET}")
        except Exception as exc:
            return print(f"\n{RED}[!] Login failed: {type(exc).__name__}: {exc}{RESET}")

    try:
        while True:
            try:
                hosts = await fetch_hosts(api)
            except Exception as exc:
                print(f"{RED}[!] Failed to fetch hosts: {exc}{RESET}")
                pause()
                continue

            print("\n" + "=" * 62)
            print(f"{CYAN}Sherlook PasarGuard Manager{RESET}")
            print(f"Active hosts: {GREEN}{len(hosts)}{RESET}")
            print("=" * 62)
            print("  1) 📋 Duplicate host(s)")
            print("  2) 🔢 Sort / group hosts")
            print("  3) 👀 Show host list")
            print(f"  4) {RED}🗑️  Delete Host(s){RESET}")
            print(f"  5) {RED}🗑️  Delete Inbound(s){RESET}")
            print(f"  6) {RED}🗑️  Delete Routing(s){RESET}")
            print(f"  7) {RED}🗑️  Delete Outbound(s){RESET}")
            print("  8) 🔐 Logout / clear credentials")
            print("  0) 🚪 Exit")

            choice = input("\n> ").strip()

            if choice == "1":
                await duplicate_host(api, hosts)
            elif choice == "2":
                await sort_hosts(api, hosts)
            elif choice == "3":
                print_hosts(hosts)
                pause()
            elif choice == "4":
                await delete_items(api, "host")
            elif choice == "5":
                await delete_items(api, "inbound")
            elif choice == "6":
                await delete_items(api, "routing")
            elif choice == "7":
                await delete_items(api, "outbound")
            elif choice == "8":
                delete_credentials()
                break
            elif choice == "0":
                break
            else:
                print(f"{RED}Invalid choice.{RESET}")

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
