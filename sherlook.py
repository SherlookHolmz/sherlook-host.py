#!/usr/bin/env python3
# ====================================================================
#  SHERLOOK ADVANCED TOR ROUTING ENGINE - STRICT CORE (FULL RECOVERED)
# ====================================================================

import os
import sys
import time
import shutil
import socket
import json
import subprocess
import glob

VALID_COUNTRIES = {
    'de': 'Germany', 'tr': 'Turkey', 'us': 'United States', 'fr': 'France', 'at': 'Austria',
    'be': 'Belgium', 'ro': 'Romania', 'ca': 'Canada', 'sg': 'Singapore', 'jp': 'Japan',
    'ie': 'Ireland', 'fi': 'Finland', 'es': 'Spain', 'pl': 'Poland', 'nl': 'Netherlands',
    'it': 'Italy', 'ch': 'Switzerland', 'se': 'Sweden', 'no': 'Norway', 'dk': 'Denmark',
    'is': 'Iceland', 'au': 'Australia', 'in': 'India', 'hk': 'Hong Kong', 'ua': 'Ukraine',
    'cz': 'Czech Republic', 'kr': 'South Korea', 'za': 'South Africa', 'mx': 'Mexico', 'my': 'Malaysia',
    'az': 'Azerbaijan', 'cy': 'Cyprus', 'gr': 'Greece', 'pt': 'Portugal', 'hu': 'Hungary',
    'lu': 'Luxembourg', 'gb': 'United Kingdom', 'ar': 'Argentina', 'tw': 'Taiwan', 'bg': 'Bulgaria',
    'il': 'Israel', 'md': 'Moldova', 'ru': 'Russia', 'cl': 'Chile', 'cr': 'Costa Rica',
    'vn': 'Vietnam', 'id': 'Indonesia', 'sc': 'Seychelles', 'hr': 'Croatia', 'tn': 'Tunisia'
}

BASE_SOCKS_PORT = 9080
BASE_CONTROL_PORT = 19080

INSTANCES_DIR = "/etc/tor/sherlook_instances"
DATA_DIR_BASE = "/var/lib/tor/sherlook_data"
INSTALL_FLAG_FILE = "/etc/tor/sherlook_installed"

COLOR_PRIMARY = "\033[1;36m"
COLOR_SECONDARY = "\033[1;34m"
COLOR_SUCCESS = "\033[1;32m"
COLOR_WARN = "\033[1;33m"
COLOR_ERROR = "\033[1;31m"
COLOR_MUTED = "\033[1;30m"
COLOR_WHITE = "\033[1;37m"
COLOR_RESET = "\033[0m"

def clear_screen():
    os.system("clear")

def print_banner():
    print(f"{COLOR_PRIMARY} ┌────────────────────────────────────────────────────────┐{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ███████╗██╗  ██╗███████╗██████╗ ██╗      ██████╗  ██████╗ ██╗  ██╗  {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ██╔════╝██║  ██║██╔════╝██╔══██╗██║     ██╔═══██╗██╔═══██╗██║ ██╔╝  {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ███████╗███████║█████╗  ██████╔╝██║     ██║   ██║██║   ██║█████═╝   {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ╚════██║██╔══██║██╔══╝  ██╔══██╗██║     ██║   ██║██║   ██║██╔═██╗   {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ███████║██║  ██║███████╗██║  ██║███████╗╚██████╔╝╚██████╔╝██║  ██╗  {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝  {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │  Engine : Sherlook Core Engine v3.6                    │{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │  Status : Strict GeoIP Routing / Full Clean Protocol   │{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} └────────────────────────────────────────────────────────┘{COLOR_RESET}")

def check_root():
    if os.getuid() != 0:
        print(f"{COLOR_ERROR}[-] Error: Root privileges are required to run Sherlook.{COLOR_RESET}")
        sys.exit(1)

def run_cmd(cmd, check=True):
    try:
        subprocess.run(cmd, check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def show_progress_bar(duration, task_name):
    steps = 25
    for i in range(steps + 1):
        percent = int((i / steps) * 100)
        filled = int(steps * i // steps)
        bar = f'{COLOR_PRIMARY}█{COLOR_RESET}' * filled + f'{COLOR_MUTED}░{COLOR_RESET}' * (steps - filled)
        sys.stdout.write(f"\r{COLOR_SECONDARY}[*] {task_name:<38} [{bar}] {COLOR_SUCCESS}{percent}%{COLOR_RESET}")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', int(port))) != 0

def get_free_port(start_port):
    port = int(start_port)
    while port < 65535:
        if is_port_free(port): return port
        port += 1
    return start_port

def detect_tor_user():
    try:
        with open('/etc/passwd', 'r') as f:
            content = f.read()
            if 'debian-tor:' in content: return 'debian-tor'
            elif 'tor:' in content: return 'tor'
    except Exception: pass
    return 'debian-tor'

def detect_geoip_paths():
    possible_paths = [
        ("/usr/share/tor/geoip", "/usr/share/tor/geoip6"),
        ("/var/lib/tor/geoip", "/var/lib/tor/geoip6")
    ]
    for geoip, geoip6 in possible_paths:
        if os.path.exists(geoip) and os.path.exists(geoip6):
            return geoip, geoip6
    return None, None

def is_system_installed():
    return os.path.exists(INSTALL_FLAG_FILE)

def check_ip_once(socks_port, timeout=6):
    proxy = f"socks5h://127.0.0.1:{socks_port}"
    try:
        cmd = ['curl', '--proxy', proxy, '--max-time', str(timeout), '-s', 'http://ip-api.com/json']
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if data.get('status') == 'success':
                return f"{data.get('query', 'N/A')} [{data.get('countryCode', '??')}]"
    except Exception:
        pass
    return None

def verify_tor_circuit(socks_port, max_attempts=4, delay=4):
    print(f"\n{COLOR_WARN}[*] Building Tor circuit & validating exit node (4 attempts max)...{COLOR_RESET}")
    for attempt in range(1, max_attempts + 1):
        sys.stdout.write(f"\r[*] Attempt {attempt}/{max_attempts}: Requesting IP from Tor circuit...")
        sys.stdout.flush()
        ip_res = check_ip_once(socks_port, timeout=6)
        if ip_res:
            print(f"\n{COLOR_SUCCESS}[+] Circuit established successfully on Attempt {attempt}!{COLOR_RESET}")
            return ip_res
        time.sleep(delay)
    print()
    return f"{COLOR_ERROR}Disconnected{COLOR_RESET}"

def install_dependencies():
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"

    show_progress_bar(1.0, "Updating APT Repositories")
    subprocess.run(['apt-get', 'update', '-qq'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    show_progress_bar(1.5, "Installing Package 1/4: Tor Service")
    subprocess.run(['apt-get', 'install', '-y', 'tor'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    show_progress_bar(1.5, "Installing Package 2/4: Tor GeoIP Database")
    subprocess.run(['apt-get', 'install', '-y', 'tor-geoipdb'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    show_progress_bar(1.0, "Installing Package 3/4: TorSocks Interface")
    subprocess.run(['apt-get', 'install', '-y', 'torsocks'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    show_progress_bar(1.0, "Installing Package 4/4: Curl & Net-Tools")
    subprocess.run(['apt-get', 'install', '-y', 'curl', 'procps', 'net-tools'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    run_cmd(["systemctl", "stop", "tor"])
    run_cmd(["systemctl", "disable", "tor"])

def setup_base_instance():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 1 - Install Core Engine{COLOR_RESET}\n")
    if is_system_installed():
        print(f"{COLOR_WARN}[!] Sherlook engine is already initialized.{COLOR_RESET}")
        input("\nPress Enter to return...")
        return
    install_dependencies()
    os.makedirs(os.path.dirname(INSTALL_FLAG_FILE), exist_ok=True)
    with open(INSTALL_FLAG_FILE, "w") as f: f.write("installed")
    print(f"\n{COLOR_SUCCESS}[+] Sherlook engine successfully installed!{COLOR_RESET}")
    input("\nPress Enter to return...")

def setup_eazy_panel():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 2 - Eazy Panel (Direct Server Connect){COLOR_RESET}\n")
    if not is_system_installed():
        print(f"{COLOR_ERROR}[-] Engine not installed! Please run Option 1 first.{COLOR_RESET}")
        input("\nPress Enter to return...")
        return

    target_port = input("Enter local server port (e.g., 22 for SSH, 8080 or 8000 for Panel): ").strip()
    if not target_port.isdigit():
        print(f"{COLOR_ERROR}[-] Invalid port number.{COLOR_RESET}")
        input("\nPress Enter...")
        return

    hs_dir = "/var/lib/tor/sherlook_eazy"
    torrc_path = "/etc/tor/sherlook_eazy_torrc"
    tor_user = detect_tor_user()
    
    os.makedirs(hs_dir, exist_ok=True)
    config = f"DataDirectory {hs_dir}\nHiddenServiceDir {hs_dir}\nHiddenServicePort {target_port} 127.0.0.1:{target_port}\nLog notice syslog\n"
    with open(torrc_path, 'w') as f: f.write(config)
        
    run_cmd(["chown", "-R", f"{tor_user}:{tor_user}", hs_dir])
    run_cmd(["chmod", "700", hs_dir])
    
    service_content = f"""[Unit]
Description=Sherlook Eazy Panel Tunnel
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/tor -f {torrc_path}
User={tor_user}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/sherlook-eazy.service", 'w') as f: f.write(service_content)
    run_cmd(["systemctl", "daemon-reload"])
    run_cmd(["systemctl", "enable", "--now", "sherlook-eazy"])
    
    show_progress_bar(3.0, "Generating Secure Direct Address")
    
    try:
        with open(f"{hs_dir}/hostname", 'r') as f: onion_addr = f.read().strip()
        print(f"\n{COLOR_SUCCESS}[+] Eazy Panel Active Successfully!{COLOR_RESET}")
        print(f"Direct Onion Address: {COLOR_WARN}{onion_addr}{COLOR_RESET}")
        print(f"Port Forwarded: {COLOR_PRIMARY}{target_port}{COLOR_RESET}")
    except Exception:
        print(f"\n{COLOR_ERROR}[-] Tunnel active, address generating in background. Check again in a few seconds.{COLOR_RESET}")
        
    input("\nPress Enter to return...")

def get_installed_instances():
    instances = {}
    if os.path.exists(INSTANCES_DIR):
        for item in os.listdir(INSTANCES_DIR):
            if item.startswith("sherlook_"):
                code = item.replace("sherlook_", "")
                conf = f"{INSTANCES_DIR}/{item}/torrc"
                try:
                    with open(conf, 'r') as f:
                        socks, control = None, None
                        for line in f:
                            if 'SocksPort' in line: socks = line.split()[1].split(':')[-1]
                            elif 'ControlPort' in line: control = line.split()[1].split(':')[-1]
                        instances[code] = {'socks': socks, 'control': control}
                except Exception: pass
    return instances

def create_sherlook_instance(country_code, socks_port, control_port):
    instance_name = f"sherlook_{country_code}"
    inst_conf_dir = f"{INSTANCES_DIR}/{instance_name}"
    inst_data_dir = f"{DATA_DIR_BASE}/{instance_name}"
    tor_user = detect_tor_user()
    
    os.makedirs(inst_conf_dir, exist_ok=True)
    os.makedirs(inst_data_dir, exist_ok=True)
    
    geoip_path, geoip6_path = detect_geoip_paths()
    geoip_config = ""
    if geoip_path and geoip6_path:
        geoip_config = f"GeoIPFile {geoip_path}\nGeoIPv6File {geoip6_path}\n"
    
    config = f"""DataDirectory {inst_data_dir}
SocksPort 0.0.0.0:{socks_port}
ControlPort 127.0.0.1:{control_port}
CookieAuthentication 0
{geoip_config}ExitNodes {{{country_code}}}
StrictNodes 1
"""
    with open(f"{inst_conf_dir}/torrc", 'w') as f: f.write(config)
    
    run_cmd(["chmod", "755", INSTANCES_DIR])
    run_cmd(["chmod", "755", inst_conf_dir])
    run_cmd(["chown", "-R", f"{tor_user}:{tor_user}", inst_conf_dir])
    run_cmd(["chown", "-R", f"{tor_user}:{tor_user}", inst_data_dir])
    run_cmd(["chmod", "700", inst_data_dir])
    
    service = f"""[Unit]
Description=Sherlook Dedicated Node [{country_code.upper()}]
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/tor -f {inst_conf_dir}/torrc
User={tor_user}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    with open(f"/etc/systemd/system/sherlook-{country_code}.service", 'w') as f: f.write(service)
    run_cmd(["systemctl", "daemon-reload"])
    run_cmd(["systemctl", "enable", "--now", f"sherlook-{country_code}"])

def setup_single_location():
    while True:
        clear_screen()
        print_banner()
        print(f"{COLOR_PRIMARY}» Option 3 - Add Single Location Node{COLOR_RESET}\n")
        installed = get_installed_instances()
        
        country_keys = list(VALID_COUNTRIES.keys())
        for idx, code in enumerate(country_keys, 1):
            name = VALID_COUNTRIES[code]
            socks = BASE_SOCKS_PORT + (idx - 1)
            if code in installed:
                status_str = f"{COLOR_SUCCESS}[Installed]{COLOR_RESET}"
            else:
                status_str = f"[Port: {socks}]"
            print(f"  {COLOR_PRIMARY}{idx:02d} -{COLOR_RESET} [{code.upper()}] {status_str:<20} - {name}")
        print(f"  {COLOR_ERROR}00 -{COLOR_RESET} Back to main menu")

        choice = input("\nSelect location index: ").strip()
        if choice in ['0', '00', '']: break
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(country_keys): continue

        selected_code = country_keys[int(choice) - 1]
        if selected_code in installed:
            print(f"\n{COLOR_WARN}[!] Location [{selected_code.upper()}] is already installed.{COLOR_RESET}")
            input("\nPress Enter...")
            continue

        offset = int(choice) - 1
        socks_port = get_free_port(BASE_SOCKS_PORT + offset)
        control_port = get_free_port(BASE_CONTROL_PORT + offset)
        
        create_sherlook_instance(selected_code, socks_port, control_port)
        live_ip = verify_tor_circuit(socks_port, max_attempts=4, delay=4)
        print(f"\n{COLOR_SUCCESS}[+] Node Active! Live Exit IP: {live_ip}{COLOR_RESET}")
        input("\nPress Enter to continue...")

def setup_bulk_locations():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 4 - Bulk Deploy Location Nodes{COLOR_RESET}\n")
    installed = get_installed_instances()
    avail = [k for k in VALID_COUNTRIES.keys() if k not in installed]
    print("Enter country codes separated by comma (e.g. de,us,fr,tr) or 'all':")
    raw = input("\nSelection: ").strip().lower()
    if not raw: return
    
    targets = avail if raw == 'all' else [c.strip() for c in raw.split(',') if c.strip() in avail]
    for code in targets:
        offset = list(VALID_COUNTRIES.keys()).index(code)
        socks = get_free_port(BASE_SOCKS_PORT + offset)
        ctrl = get_free_port(BASE_CONTROL_PORT + offset)
        print(f" -> Deploying [{code.upper()}] on SOCKS :{socks}...")
        create_sherlook_instance(code, socks, ctrl)
    print(f"\n{COLOR_SUCCESS}[+] Bulk deployment finished!{COLOR_RESET}")
    input("\nPress Enter...")

def view_installed_locations():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 5 - Active Nodes & Live IP Diagnostics{COLOR_RESET}\n")
    installed = get_installed_instances()
    if not installed:
        print(f"{COLOR_WARN}[!] No active nodes deployed.{COLOR_RESET}")
        input("\nPress Enter...")
        return

    border = "─" * 65
    print(f"{COLOR_PRIMARY}┌{border}┐{COLOR_RESET}")
    print(f"{COLOR_PRIMARY}│{COLOR_RESET} {'ID':<4} {COLOR_PRIMARY}│{COLOR_RESET} {'Target Country':<18} {COLOR_PRIMARY}│{COLOR_RESET} {'Code':<6} {COLOR_PRIMARY}│{COLOR_RESET} {'SOCKS':<8} {COLOR_PRIMARY}│{COLOR_RESET} {'Live Exit IP':<20} {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY}├{border}┤{COLOR_RESET}")
    
    for idx, (code, info) in enumerate(installed.items(), 1):
        name = VALID_COUNTRIES.get(code, "Custom Exit")
        live_ip = check_ip_once(info['socks'], timeout=4) or f"{COLOR_ERROR}Disconnected{COLOR_RESET}"
        print(f"{COLOR_PRIMARY}│{COLOR_RESET} {idx:02d:<4} {COLOR_PRIMARY}│{COLOR_RESET} {name:<18} {COLOR_PRIMARY}│{COLOR_RESET} {code.upper():<6} {COLOR_PRIMARY}│{COLOR_RESET} {info['socks']:<8} {COLOR_PRIMARY}│{COLOR_RESET} {live_ip:<20} {COLOR_PRIMARY}│{COLOR_RESET}")
    
    print(f"{COLOR_PRIMARY}└{border}┘{COLOR_RESET}")
    input("\nPress Enter to return...")

def renew_node_circuits():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 6 - Request New IP Circuit (Signal NEWNYM){COLOR_RESET}\n")
    installed = get_installed_instances()
    if not installed:
        print(f"{COLOR_WARN}[!] No active nodes found.{COLOR_RESET}")
        input("\nPress Enter...")
        return

    for idx, (code, info) in enumerate(installed.items(), 1):
        print(f"  {idx} - [{code.upper()}] {VALID_COUNTRIES.get(code, code)} (Control: {info['control']})")
    
    choice = input("\nSelect node index to renew (or 'all'): ").strip().lower()
    if not choice: return

    def send_signal(ctrl):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect(('127.0.0.1', int(ctrl)))
                s.sendall(b'AUTHENTICATE ""\r\n')
                if "250" in s.recv(1024).decode():
                    s.sendall(b'SIGNAL NEWNYM\r\n')
                    return "250" in s.recv(1024).decode()
        except Exception: pass
        return False

    if choice == 'all':
        for code, info in installed.items():
            res = send_signal(info['control'])
            print(f"[*] Node [{code.upper()}]: " + (f"{COLOR_SUCCESS}IP Renewed{COLOR_RESET}" if res else f"{COLOR_ERROR}Failed{COLOR_RESET}"))
    elif choice.isdigit() and 1 <= int(choice) <= len(installed):
        code = list(installed.keys())[int(choice) - 1]
        if send_signal(installed[code]['control']):
            print(f"\n{COLOR_SUCCESS}[+] New IP circuit requested for [{code.upper()}].{COLOR_RESET}")
        else:
            print(f"\n{COLOR_ERROR}[-] Signal failed.{COLOR_RESET}")

    input("\nPress Enter...")

def delete_location():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 7 - Delete Node{COLOR_RESET}\n")
    installed = get_installed_instances()
    if not installed: return input("\nNo active nodes. Press Enter...")
    for idx, (code, info) in enumerate(installed.items(), 1):
        print(f"  {idx} - [{code.upper()}] {VALID_COUNTRIES.get(code, code)} (Port: {info['socks']})")
    
    choice = input("\nSelect node index to delete (0 to cancel): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(installed):
        code = list(installed.keys())[int(choice) - 1]
        run_cmd(["systemctl", "disable", "--now", f"sherlook-{code}"])
        if os.path.exists(f"/etc/systemd/system/sherlook-{code}.service"):
            os.remove(f"/etc/systemd/system/sherlook-{code}.service")
        shutil.rmtree(f"{INSTANCES_DIR}/sherlook_{code}", ignore_errors=True)
        shutil.rmtree(f"{DATA_DIR_BASE}/sherlook_{code}", ignore_errors=True)
        print(f"\n{COLOR_SUCCESS}[+] Node [{code.upper()}] deleted.{COLOR_RESET}")
        time.sleep(1)

def uninstall_system():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 8 - Full System Deep Purge & Uninstall{COLOR_RESET}\n")
    confirm = input("Are you sure you want to completely remove Sherlook and all data? (y/N): ").strip().lower()
    if confirm != 'y':
        return

    print(f"\n{COLOR_WARN}[*] Stopping all Sherlook services & purging system files...{COLOR_RESET}")
    
    # 1. Stop and remove all systemd services
    service_files = glob.glob("/etc/systemd/system/sherlook*.service")
    for s_file in service_files:
        s_name = os.path.basename(s_file)
        print(f" -> Stopping & removing service: {s_name}")
        run_cmd(["systemctl", "disable", "--now", s_name])
        try:
            os.remove(s_file)
        except Exception:
            pass
    
    run_cmd(["systemctl", "daemon-reload"])
    run_cmd(["systemctl", "reset-failed"])

    # 2. Delete all directories and leftover configs
    paths_to_remove = [
        INSTANCES_DIR,
        DATA_DIR_BASE,
        "/var/lib/tor/sherlook_eazy",
        "/etc/tor/sherlook_eazy_torrc",
        INSTALL_FLAG_FILE,
        "/usr/local/bin/sherlook"
    ]
    
    for path in paths_to_remove:
        if os.path.isdir(path):
            print(f" -> Purging directory: {path}")
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            print(f" -> Purging file: {path}")
            try:
                os.remove(path)
            except Exception:
                pass

    print(f"\n{COLOR_SUCCESS}[+] Sherlook completely uninstalled and wiped from system!{COLOR_RESET}")
    time.sleep(2)

def main():
    check_root()
    while True:
        clear_screen()
        print_banner()
        installed = get_installed_instances()
        status = f"{COLOR_SUCCESS}Active ({len(installed)} Nodes Deployed){COLOR_RESET}" if is_system_installed() else f"{COLOR_ERROR}Not Installed{COLOR_RESET}"
        
        print(f"{COLOR_PRIMARY} ┌────────────────────────────────────────────────────────┐{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  Engine Status: {status:<47} │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}1{COLOR_RESET}{COLOR_PRIMARY}] » Install Core Engine                                 │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}2{COLOR_RESET}{COLOR_PRIMARY}] » Eazy Panel (Direct Connect Tunnel)                  │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}3{COLOR_RESET}{COLOR_PRIMARY}] » Add Single Location Node                            │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}4{COLOR_RESET}{COLOR_PRIMARY}] » Bulk Deploy Location Nodes                          │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}5{COLOR_RESET}{COLOR_PRIMARY}] » View Active Nodes & Live IP Diagnostics             │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}6{COLOR_RESET}{COLOR_PRIMARY}] » Renew IP Circuit (New Identity)                     │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}7{COLOR_RESET}{COLOR_PRIMARY}] » Delete Location Node                                │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}8{COLOR_RESET}{COLOR_PRIMARY}] » Uninstall Whole System                              │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}0{COLOR_RESET}{COLOR_PRIMARY}] » Exit                                                │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} └────────────────────────────────────────────────────────┘{COLOR_RESET}")
        
        choice = input(" Enter choice [0-8]: ").strip()
        if choice == '1': setup_base_instance()
        elif choice == '2': setup_eazy_panel()
        elif choice == '3': setup_single_location()
        elif choice == '4': setup_bulk_locations()
        elif choice == '5': view_installed_locations()
        elif choice == '6': renew_node_circuits()
        elif choice == '7': delete_location()
        elif choice == '8': uninstall_system()
        elif choice == '0': sys.exit(0)

if __name__ == "__main__":
    main()
