#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlook PasarGuard Host Manager
================================
Terminal utility for duplicating and sorting PasarGuard hosts.

Features:
  - Async PasarGuard API access
  - Bulk host duplication with bounded concurrency
  - Smart remark numbering
  - Group/sort preview
  - Local credential cache with restrictive permissions
  - Automatic dependency bootstrap
  - Clean Sherlook terminal UI

Run:
    python3 pasarguard_host_manager.py
"""

from __future__ import annotations

import asyncio
import getpass
import json
import os
import re
import shutil
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
BLUE = "\033[94m"
MAGENTA = "\033[95m"
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
        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "--no-cache-dir", "pasarguard"],
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
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600
    except OSError:
        pass


def load_credentials() -> dict[str, str] | None:
    if not CONFIG_FILE.exists():
        return None

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not all(data.get(k) for k in ("base_url", "username", "password")):
            return None

        _chmod_private(CONFIG_FILE)
        return {
            "base_url": str(data["base_url"]).strip().rstrip("/"),
            "username": str(data["username"]),
            "password": str(data["password"]),
        }
    except (OSError, ValueError, TypeError):
        return None


def save_credentials(base_url: str, username: str, password: str) -> None:
    data = {
        "base_url": base_url.strip().rstrip("/"),
        "username": username.strip(),
        "password": password,
    }
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
# Remark / selection helpers
# ---------------------------------------------------------------------------

def split_base_and_number(remark: str) -> tuple[str, int]:
    remark = (remark or "").strip()
    match = NUMBER_RE.search(remark)
    if not match:
        return remark.rstrip(), 1

    number = int(match.group(1))
    start, end = match.span(1)
    base = (remark[:start] + remark[end:]).rstrip()
    return base, number


def next_available_number(hosts: list[Any], base: str) -> int:
    used = []
    for host in hosts:
        other_base, other_number = split_base_and_number(
            str(getattr(host, "remark", ""))
        )
        if other_base == base:
            used.append(other_number)
    return max(used, default=0) + 1


def build_remark(base: str, number: int, template: str) -> str:
    match = NUMBER_RE.search(template or "")
    if not match:
        return f"{base} {number}".strip()

    start, end = match.span(1)
    return f"{template[:start]}{number}{template[end:]}"


def parse_selection(text: str, max_index: int) -> list[int] | None:
    text = text.strip()
    if not text:
        return None

    indices: set[int] = set()

    for part in text.split(","):
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            bounds = [x.strip() for x in part.split("-", 1)]
            if len(bounds) != 2 or not all(x.isdigit() for x in bounds):
                return None

            start, end = map(int, bounds)
            if start > end:
                start, end = end, start
            indices.update(range(start, end + 1))
        elif part.isdigit():
            indices.add(int(part))
        else:
            return None

    if not indices or any(i < 1 or i > max_index for i in indices):
        return None

    return sorted(indices)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

async def login(base_url: str, username: str, password: str) -> PasarguardAPI:
    api = PasarguardAPI(
        base_url=base_url.rstrip("/"),
        timeout=API_TIMEOUT,
        verify=True,
    )
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
            if isinstance(value, (list, tuple)):
                hosts.extend(value)
        return hosts

    if hasattr(raw, "hosts"):
        return list(raw.hosts)

    return list(raw)


def model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    if isinstance(model, dict):
        return dict(model)
    return dict(vars(model))


def host_to_create_payload(host: Any) -> dict[str, Any]:
    data = model_to_dict(host)

    if hasattr(CreateHost, "model_fields"):
        allowed = set(CreateHost.model_fields.keys())
    elif hasattr(CreateHost, "__fields__"):
        allowed = set(CreateHost.__fields__.keys())
    else:
        allowed = set(data)

    # Never blindly send read-only/API response fields.
    return {k: v for k, v in data.items() if k in allowed}


def print_hosts(hosts: list[Any]) -> None:
    print(f"\n{CYAN}Hosts ({len(hosts)}):{RESET}")
    print("-" * 78)

    for i, host in enumerate(hosts, start=1):
        remark = getattr(host, "remark", "unnamed")
        tag = getattr(host, "inbound_tag", "?")
        address = getattr(host, "address", "?")
        port = getattr(host, "port", "?")
        print(f"{i:>3}) {remark}  [{tag} | {address}:{port}]")

    print("-" * 78)


# ---------------------------------------------------------------------------
# Duplicate
# ---------------------------------------------------------------------------

async def create_one(
    api: PasarguardAPI,
    payload: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> tuple[bool, str, str]:
    remark = str(payload.get("remark", "unnamed"))

    async with semaphore:
        for attempt in range(1, CREATE_RETRIES + 2):
            try:
                host = await api.create_host(
                    CreateHost(**payload),
                    token=api._token,
                )
                created = getattr(host, "remark", remark)
                return True, str(created), ""
            except Exception as exc:
                if attempt > CREATE_RETRIES:
                    return False, remark, f"{type(exc).__name__}: {exc}"
                await asyncio.sleep(0.6 * attempt)

    return False, remark, "Unknown error"


async def duplicate_host(api: PasarguardAPI, hosts: list[Any]) -> None:
    print_hosts(hosts)

    selection = input(
        "\nHost(s) to duplicate "
        "(e.g. 5 / 5-9 / 5,7,9): "
    ).strip()

    indices = parse_selection(selection, len(hosts))
    if not indices:
        print(f"{RED}Invalid selection.{RESET}")
        return

    count_raw = input("Copies of EACH selected host: ").strip()
    if not count_raw.isdigit() or int(count_raw) <= 0:
        print(f"{RED}Invalid number of copies.{RESET}")
        return

    count = int(count_raw)
    working_hosts = list(hosts)
    jobs: list[dict[str, Any]] = []

    # Allocate all names before concurrent API calls to prevent collisions.
    reserved: dict[str, set[int]] = {}

    for idx in indices:
        source = hosts[idx - 1]
        source_remark = str(getattr(source, "remark", ""))
        base, _ = split_base_and_number(source_remark)

        used = reserved.setdefault(base, set())
        existing = {
            num
            for h in working_hosts
            for other_base, num in [split_base_and_number(str(getattr(h, "remark", "")))]
            if other_base == base
        }
        start = max(existing | used, default=0) + 1

        for offset in range(count):
            number = start + offset
            used.add(number)

            payload = host_to_create_payload(source)
            payload["remark"] = build_remark(base, number, source_remark)
            jobs.append(payload)

    print(f"\n{CYAN}Creating {len(jobs)} host(s) with {MAX_CREATE_WORKERS} workers...{RESET}")

    semaphore = asyncio.Semaphore(MAX_CREATE_WORKERS)
    results = await asyncio.gather(
        *(create_one(api, payload, semaphore) for payload in jobs)
    )

    created = 0
    failed = 0

    for ok, remark, error in results:
        if ok:
            created += 1
            print(f"{GREEN}  ✓ Created: {remark}{RESET}")
        else:
            failed += 1
            print(f"{RED}  ✗ Failed: {remark}{RESET}")
            print(f"    {error}")

    print(f"\n{GREEN}Done.{RESET} Created: {created} | Failed: {failed}")
    pause()


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

async def sort_hosts(api: PasarguardAPI, hosts: list[Any]) -> None:
    groups: dict[str, list[tuple[int, Any]]] = {}
    group_order: list[str] = []

    for host in hosts:
        remark = str(getattr(host, "remark", ""))
        base, number = split_base_and_number(remark)

        if base not in groups:
            groups[base] = []
            group_order.append(base)

        groups[base].append((number, host))

    ordered: list[Any] = []
    for base in group_order:
        ordered.extend(host for _, host in sorted(groups[base], key=lambda x: x[0]))

    print(f"\n{CYAN}Proposed order:{RESET}")
    for i, host in enumerate(ordered, 1):
        print(f"{i:>3}) {getattr(host, 'remark', '')}")

    if not ordered:
        print(f"{YELLOW}No hosts to sort.{RESET}")
        return

    if not hasattr(ordered[0], "priority"):
        print(
            f"\n{YELLOW}This PasarGuard API model does not expose a "
            f"'priority' field. Nothing was changed on the panel.{RESET}"
        )
        pause()
        return

    confirm = input("\nSave this order to the panel? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled; nothing changed.")
        return

    success = 0

    for priority, host in enumerate(ordered):
        try:
            payload = host_to_create_payload(host)
            payload["priority"] = priority

            await api.modify_host(
                host_id=getattr(host, "id"),
                host=CreateHost(**payload),
                token=api._token,
            )
            success += 1
        except Exception as exc:
            print(
                f"{RED}  ✗ Failed: {getattr(host, 'remark', '')} — "
                f"{type(exc).__name__}: {exc}{RESET}"
            )

    print(f"\n{GREEN}Order saved for {success}/{len(ordered)} host(s).{RESET}")
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
            api = await login(
                creds["base_url"],
                creds["username"],
                creds["password"],
            )
            print(f"{GREEN}[+] Connected successfully.{RESET}\n")
        except Exception as exc:
            print(f"{RED}[!] Auto-login failed: {exc}{RESET}\n")

    if api is None:
        print(f"{CYAN}=== Connect to PasarGuard ==={RESET}")

        base_url = input("Panel URL: ").strip().rstrip("/")
        username = input("Admin username: ").strip()
        password = getpass.getpass("Password (hidden): ")

        if not base_url or not username or not password:
            print(f"{RED}[!] URL, username and password are required.{RESET}")
            return

        try:
            api = await login(base_url, username, password)
            print(f"{GREEN}[+] Connected successfully.{RESET}")

            save_choice = input(
                "Save credentials locally for next time? (y/n): "
            ).strip().lower()

            if save_choice == "y":
                save_credentials(base_url, username, password)
                print(
                    f"{GREEN}[+] Saved to {CONFIG_FILE} "
                    f"(permissions restricted to your user).{RESET}"
                )
        except Exception as exc:
            print(f"\n{RED}[!] Login failed: {type(exc).__name__}: {exc}{RESET}")
            return

    try:
        while True:
            try:
                hosts = await fetch_hosts(api)
            except Exception as exc:
                print(f"{RED}[!] Failed to fetch hosts: {exc}{RESET}")
                pause()
                continue

            print("\n" + "=" * 62)
            print(f"{CYAN}Sherlook PasarGuard Host Manager{RESET}")
            print(f"Active hosts: {GREEN}{len(hosts)}{RESET}")
            print("=" * 62)
            print("  1) 📋 Duplicate host(s)")
            print("  2) 🔢 Sort / group hosts")
            print("  3) 👀 Show host list")
            print("  4) 🔐 Logout / clear saved credentials")
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
                delete_credentials()
                break
            elif choice == "0":
                break
            else:
                print(f"{RED}Invalid choice.{RESET}")

    finally:
        if api is not None:
            try:
                await api.__aexit__(None, None, None)
            except Exception:
                pass

        print(f"\n{CYAN}Sherlook{RESET} — Bye 👋")


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopped by user.{RESET}")


if __name__ == "__main__":
    main()
