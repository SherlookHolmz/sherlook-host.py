#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sherlook PasarGuard Manager

Host management utility for PasarGuard Panel.

The Host duplication path is implemented against the public Pasarguard SDK:
    POST /api/host/

Designed for pasarguard==2.4.0 (Python >=3.10).
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
API_TIMEOUT = 30.0
CREATE_CONCURRENCY = 4
CREATE_ATTEMPTS = 2
PASARGUARD_VERSION = "2.4.0"
NUMBER_RE = re.compile(r"(\d+)(?!.*\d)")

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
{DIM}Fast • Async • Safe API Management • Host Duplication{RESET}
""")


def pause(message: str = "Press Enter to continue...") -> None:
    try:
        input(f"\n{DIM}{message}{RESET}")
    except (EOFError, KeyboardInterrupt):
        pass


# ---------------------------------------------------------------------------
# Optional direct-run dependency guard
# ---------------------------------------------------------------------------
def ensure_dependency() -> None:
    try:
        import pasarguard  # noqa: F401
        return
    except ImportError:
        pass

    print(f"{RED}[!] pasarguard is not installed in this Python environment.{RESET}")
    print(f"{YELLOW}[i] Use the supplied installer; it creates an isolated virtualenv and installs pasarguard=={PASARGUARD_VERSION}.{RESET}")
    raise SystemExit(1)


ensure_dependency()
from pasarguard import CreateHost, PasarguardAPI  # noqa: E402


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------
def _chmod_private(path: Path) -> None:
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
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
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "base_url": base_url.strip().rstrip("/"),
                    "username": username.strip(),
                    "password": password,
                },
                f,
                indent=2,
            )
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
# Generic helpers
# ---------------------------------------------------------------------------
def get_attr(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def model_dump(obj: Any) -> dict[str, Any]:
    """Convert Pydantic/dict/object to a dictionary without guessing field names."""
    if isinstance(obj, dict):
        return dict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="python")
    if hasattr(obj, "dict"):
        return obj.dict()
    data: dict[str, Any] = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if callable(value):
            continue
        data[name] = value
    return data


def split_base_and_number(remark: str) -> tuple[str, int]:
    remark = (remark or "").strip()
    match = NUMBER_RE.search(remark)
    if not match:
        return remark, 1
    number = int(match.group(1))
    start, end = match.span(1)
    base = (remark[:start] + remark[end:]).strip()
    return base, number


def next_remark(existing: set[str], source_remark: str) -> str:
    """Return the next free remark while preserving the source naming pattern."""
    source = (source_remark or "unnamed").strip() or "unnamed"
    base, source_num = split_base_and_number(source)
    if not base:
        base = "unnamed"

    candidate = f"{base} {source_num + 1}" if NUMBER_RE.search(source) else f"{base} 2"
    counter = 2 if not NUMBER_RE.search(source) else source_num + 1
    while candidate in existing:
        counter += 1
        candidate = f"{base} {counter}"
    existing.add(candidate)
    return candidate


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


def short_value(value: Any, max_len: int = 70) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        text = str(value)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def exception_text(exc: Exception) -> str:
    """Include HTTP response details when the SDK raises an HTTPStatusError."""
    response = getattr(exc, "response", None)
    if response is not None:
        status = getattr(response, "status_code", "?")
        try:
            body = response.text
        except Exception:
            body = ""
        body = (body or "").strip().replace("\n", " ")
        return f"HTTP {status}: {body[:500]}" if body else f"HTTP {status}: {exc}"
    return str(exc)


def should_retry_exception(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None) if response is not None else None
    if status == 429:
        return True
    if isinstance(status, int) and 500 <= status < 600:
        return True
    return exc.__class__.__name__ in {
        "ConnectError",
        "ReadTimeout",
        "WriteTimeout",
        "PoolTimeout",
        "ConnectTimeout",
        "RemoteProtocolError",
    }


# ---------------------------------------------------------------------------
# PasarGuard API
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
        api._token = token.access_token  # SDK's normal internal token path.
        return api
    except Exception:
        await api.__aexit__(*sys.exc_info())
        raise


async def fetch_hosts(api: PasarguardAPI) -> list[Any]:
    """Fetch all hosts using the current SDK contract."""
    raw = await api.get_hosts(token=api._token, offset=0, limit=0)
    if isinstance(raw, dict):
        values: list[Any] = []
        for val in raw.values():
            values.extend(val if isinstance(val, (list, tuple)) else [val])
        return values
    if hasattr(raw, "hosts"):
        return list(raw.hosts)
    return list(raw)


def print_hosts(hosts: list[Any]) -> None:
    print(f"\n{CYAN}Hosts ({len(hosts)}):{RESET}")
    print("-" * 102)
    for i, host in enumerate(hosts, start=1):
        remark = get_attr(host, "remark", "unnamed")
        tag = get_attr(host, "inbound_tag", "?")
        address = get_attr(host, "address", "?")
        port = get_attr(host, "port", "?")
        priority = get_attr(host, "priority", "?")
        disabled = get_attr(host, "is_disabled", False)
        state = f"{RED}DISABLED{RESET}" if disabled else f"{GREEN}ACTIVE{RESET}"
        print(
            f"{i:>3}) {remark}  [tag={tag} | address={short_value(address)} "
            f"| port={port} | priority={priority} | {state}]"
        )
    print("-" * 102)


# ---------------------------------------------------------------------------
# Real Host duplication
# ---------------------------------------------------------------------------
def host_to_create_model(source_host: Any, remark: str) -> CreateHost:
    """Clone every Host API field that PasarGuard accepts, but never clone the DB id."""
    data = model_dump(source_host)
    data.pop("id", None)
    data["remark"] = remark

    # BaseHost responses can contain fields that changed representation between
    # SDK revisions. Re-validate through CreateHost so the SDK performs the
    # same schema validation it uses for normal creation.
    return CreateHost.model_validate(data)


async def host_exists_by_remark(api: PasarguardAPI, remark: str) -> Any | None:
    """Used after an ambiguous POST failure to prevent duplicate retries."""
    try:
        hosts = await fetch_hosts(api)
    except Exception:
        return None
    for host in hosts:
        if str(get_attr(host, "remark", "")).strip() == remark:
            return host
    return None


async def create_one_host(
    api: PasarguardAPI,
    source_host: Any,
    remark: str,
    semaphore: asyncio.Semaphore,
) -> tuple[bool, str, Any | None]:
    async with semaphore:
        try:
            payload = host_to_create_model(source_host, remark)
        except Exception as exc:
            return False, f"schema validation failed: {exception_text(exc)}", None

        last_error = "unknown error"
        for attempt in range(1, CREATE_ATTEMPTS + 1):
            try:
                created = await api.create_host(host=payload, token=api._token)
                created_id = get_attr(created, "id", "?")
                return True, f"created id={created_id}", created
            except Exception as exc:
                last_error = exception_text(exc)

                # A POST can succeed server-side while the client loses the
                # response. Before retrying, look up the exact generated remark.
                existing = await host_exists_by_remark(api, remark)
                if existing is not None:
                    existing_id = get_attr(existing, "id", "?")
                    return True, f"created id={existing_id} (confirmed after ambiguous response)", existing

                if attempt >= CREATE_ATTEMPTS or not should_retry_exception(exc):
                    break
                await asyncio.sleep(0.8 * attempt)

        return False, last_error, None


async def duplicate_host(api: PasarguardAPI, hosts: list[Any]) -> None:
    if not hosts:
        print(f"{YELLOW}No hosts found.{RESET}")
        pause()
        return

    print_hosts(hosts)
    selection = input("\nHost(s) to duplicate (e.g. 5 / 5-9 / 5,7,9): ").strip()
    indices = parse_selection(selection, len(hosts))
    if not indices:
        print(f"{RED}Invalid selection.{RESET}")
        pause()
        return

    count_raw = input("Copies of EACH selected host: ").strip()
    if not count_raw.isdigit() or int(count_raw) <= 0:
        print(f"{RED}Invalid copies.{RESET}")
        pause()
        return
    copies = int(count_raw)

    selected = [hosts[i - 1] for i in indices]
    requested = len(selected) * copies
    print(f"\n{CYAN}Preparing {requested} Host clone(s)...{RESET}")

    # Reserve every generated remark before any POST starts, preventing races
    # between concurrent creation workers.
    existing_remarks = {
        str(get_attr(host, "remark", "")).strip()
        for host in hosts
        if str(get_attr(host, "remark", "")).strip()
    }

    jobs: list[tuple[Any, str, int, int]] = []
    for source_index, source_host in zip(indices, selected):
        source_remark = str(get_attr(source_host, "remark", "unnamed"))
        for copy_no in range(1, copies + 1):
            remark = next_remark(existing_remarks, source_remark)
            jobs.append((source_host, remark, source_index, copy_no))

    print(f"{DIM}Only the database id is removed; all other Host fields are cloned.{RESET}")
    print(f"{DIM}inbound_tag/address/port/SNI/host/path/security/transport/etc. are preserved.{RESET}\n")

    if input(f"{YELLOW}Create {requested} clone(s) in PasarGuard now? (y/n): {RESET}").strip().lower() != "y":
        print("Cancelled.")
        pause()
        return

    semaphore = asyncio.Semaphore(CREATE_CONCURRENCY)
    results: list[tuple[int, str, bool, str, Any | None]] = []

    async def run_job(position: int, job: tuple[Any, str, int, int]) -> tuple[int, str, bool, str, Any | None]:
        source_host, remark, source_index, copy_no = job
        ok, message, created = await create_one_host(api, source_host, remark, semaphore)
        return source_index, remark, ok, message, created

    tasks = [asyncio.create_task(run_job(pos, job)) for pos, job in enumerate(jobs, start=1)]
    completed = 0
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)
        completed += 1
        source_index, remark, ok, message, created = result
        icon = "✓" if ok else "✗"
        color = GREEN if ok else RED
        print(f"{color}  [{completed:>2}/{requested}] {icon} source#{source_index} -> {remark} | {message}{RESET}")

    successes = [r for r in results if r[2]]
    failures = [r for r in results if not r[2]]

    print(
        f"\n{GREEN}Duplicate completed.{RESET} "
        f"Created/confirmed: {len(successes)} | Failed: {len(failures)}"
    )

    # Strong verification against the panel state, not just local task results.
    if successes:
        try:
            final_hosts = await fetch_hosts(api)
            final_remarks = {
                str(get_attr(h, "remark", "")).strip() for h in final_hosts
            }
            verified = sum(1 for _, remark, *_ in successes if remark in final_remarks)
            print(f"{CYAN}Panel verification: {verified}/{len(successes)} clone(s) visible after refresh.{RESET}")
        except Exception as exc:
            print(f"{YELLOW}[!] Verification refresh failed: {exception_text(exc)}{RESET}")

    if failures:
        print(f"\n{RED}Failed clones:{RESET}")
        for source_index, remark, _, message, _ in sorted(failures):
            print(f"  - source#{source_index} -> {remark}: {message}")

    pause()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------
async def delete_hosts(api: PasarguardAPI) -> None:
    try:
        hosts = await fetch_hosts(api)
    except Exception as exc:
        print(f"{RED}[!] Failed to fetch hosts: {exception_text(exc)}{RESET}")
        pause()
        return

    if not hosts:
        print(f"{YELLOW}No hosts found.{RESET}")
        pause()
        return
    print_hosts(hosts)

    selection = input("\nSelect Host(s) to delete (e.g. 1 / 1-3 / 1,3): ").strip()
    indices = parse_selection(selection, len(hosts))
    if not indices:
        print(f"{RED}Invalid selection.{RESET}")
        pause()
        return

    if input(f"{YELLOW}Confirm deleting {len(indices)} Host(s)? (y/n): {RESET}").strip().lower() != "y":
        print("Cancelled.")
        pause()
        return

    success, failed = 0, 0
    for idx in indices:
        host = hosts[idx - 1]
        host_id = get_attr(host, "id")
        name = get_attr(host, "remark", "unnamed")
        if host_id is None:
            print(f"{RED}  ✗ Cannot delete {name}: missing host id{RESET}")
            failed += 1
            continue
        try:
            await api.remove_host(host_id=host_id, token=api._token)
            print(f"{GREEN}  ✓ Deleted: {name} (id={host_id}){RESET}")
            success += 1
        except Exception as exc:
            print(f"{RED}  ✗ Failed to delete {name}: {exception_text(exc)}{RESET}")
            failed += 1

    print(f"\n{GREEN}Done.{RESET} Deleted: {success} | Failed: {failed}")
    pause()


# ---------------------------------------------------------------------------
# Core Config Editor
# ---------------------------------------------------------------------------
async def get_active_core_id(api: PasarguardAPI) -> int:
    try:
        if hasattr(api, "get_all_cores"):
            cores = await api.get_all_cores(token=api._token)
            if isinstance(cores, list) and cores:
                for core in cores:
                    core_id = get_attr(core, "id", None)
                    if core_id is not None:
                        return int(core_id)
    except Exception:
        pass
    return 1


async def edit_core_config(api: PasarguardAPI) -> None:
    print(f"\n{CYAN}Discovering active core...{RESET}")
    core_id = await get_active_core_id(api)
    print(f"{CYAN}Fetching Config for Core ID [{core_id}]...{RESET}")

    try:
        raw_config = await api.get_core_config(core_id=core_id, token=api._token)
    except TypeError:
        try:
            raw_config = await api.get_core_config(core_id, token=api._token)
        except Exception as exc:
            print(f"{RED}[!] Failed to fetch core config: {exception_text(exc)}{RESET}")
            pause()
            return
    except Exception as exc:
        print(f"{RED}[!] Failed to fetch core config: {exception_text(exc)}{RESET}")
        pause()
        return

    config_dict = model_dump(raw_config)
    fd, temp_path = tempfile.mkstemp(suffix=".json", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False, default=str)

        print(f"\n{YELLOW}⚠️  WARNING: You are about to edit the raw Xray JSON configuration.{RESET}")
        print(f"{DIM}Invalid Xray JSON can break a core. The manager validates JSON syntax before upload.{RESET}")
        pause("Press Enter to open your editor...")

        editor = os.environ.get("EDITOR") or ("nano" if os.name != "nt" else "notepad")
        subprocess.run([editor, temp_path], check=False)

        with open(temp_path, "r", encoding="utf-8") as f:
            new_config_dict = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"{RED}[!] Invalid JSON format: {exc}{RESET}")
        pause()
        return
    except Exception as exc:
        print(f"{RED}[!] Could not edit/read config: {exception_text(exc)}{RESET}")
        pause()
        return
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    if new_config_dict == config_dict:
        print(f"{GREEN}No changes detected. Cancelled.{RESET}")
        pause()
        return

    if input(f"\n{YELLOW}Push new Core Config to the server? (y/n): {RESET}").strip().lower() != "y":
        print("Cancelled.")
        pause()
        return

    try:
        if not hasattr(api, "modify_core_config"):
            print(f"{RED}[!] Your installed SDK does not expose modify_core_config().{RESET}")
            pause()
            return
        try:
            await api.modify_core_config(
                core_id=core_id,
                core_config=new_config_dict,
                token=api._token,
            )
        except TypeError:
            await api.modify_core_config(core_id, new_config_dict, token=api._token)
        print(f"{GREEN}[+] Core Config successfully updated!{RESET}")
    except Exception as exc:
        print(f"{RED}[!] Failed to update core config: {exception_text(exc)}{RESET}")
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
            print(f"{RED}[!] Auto-login failed: {exception_text(exc)}{RESET}\n")

    if api is None:
        print(f"{CYAN}=== Connect to PasarGuard ==={RESET}")
        base_url = input("Panel URL: ").strip().rstrip("/")
        username = input("Admin username: ").strip()
        password = getpass.getpass("Password (hidden): ")
        if not base_url or not username or not password:
            print(f"{RED}[!] Fields required.{RESET}")
            return
        try:
            api = await login(base_url, username, password)
            print(f"{GREEN}[+] Connected successfully.{RESET}")
            if input("Save credentials? (y/n): ").strip().lower() == "y":
                save_credentials(base_url, username, password)
        except Exception as exc:
            print(f"\n{RED}[!] Login failed: {exception_text(exc)}{RESET}")
            return

    try:
        while True:
            try:
                hosts = await fetch_hosts(api)
                fetch_error = None
            except Exception as exc:
                hosts = []
                fetch_error = exc

            print("\n" + "=" * 62)
            print(f"{CYAN}Sherlook PasarGuard Manager{RESET}")
            print(f"Active hosts: {GREEN}{len(hosts)}{RESET}")
            if fetch_error:
                print(f"{YELLOW}Host refresh warning: {exception_text(fetch_error)}{RESET}")
            print("=" * 62)
            print("  1) 📋 Duplicate host(s)")
            print("  2) 👀 Show host list")
            print(f"  3) {RED}🗑️  Delete Host(s){RESET}")
            print(f"  4) {YELLOW}⚙️  Edit Core Config (Manage Inbounds, Outbounds, Routing){RESET}")
            print("  8) 🔐 Logout / clear credentials")
            print("  0) 🚪 Exit")

            choice = input("\n> ").strip()
            if choice == "1":
                await duplicate_host(api, hosts)
            elif choice == "2":
                print_hosts(hosts)
                pause()
            elif choice == "3":
                await delete_hosts(api)
            elif choice == "4":
                await edit_core_config(api)
            elif choice == "8":
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
