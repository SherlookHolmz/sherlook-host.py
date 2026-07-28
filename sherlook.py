#!/usr/bin/env python3
import os
import sys
import time
import shutil
import socket
import datetime
import subprocess

# Version: 1.4 T.Sin
# Tel: @T_sinn
LICENSE_USER = "Sin.Kabir"
LICENSE_REMAINING = "∞"
LICENSE_PLAN = "g"

VALID_COUNTRIES = {
    'de': 'Germany', 'tr': 'Turkey', 'us': 'United States', 'fr': 'France',
    'at': 'Austria', 'be': 'Belgium', 'ro': 'Romania', 'ca': 'Canada',
    'sg': 'Singapore', 'jp': 'Japan', 'ie': 'Ireland', 'fi': 'Finland',
    'es': 'Spain', 'pl': 'Poland', 'nl': 'Netherlands', 'it': 'Italy',
    'ch': 'Switzerland', 'se': 'Sweden', 'no': 'Norway', 'dk': 'Denmark',
    'is': 'Iceland', 'au': 'Australia', 'in': 'India', 'hk': 'Hong Kong',
    'ua': 'Ukraine', 'cz': 'Czech Republic', 'kr': 'South Korea', 'za': 'South Africa',
    'mx': 'Mexico', 'my': 'Malaysia', 'az': 'Azerbaijan', 'cy': 'Cyprus',
    'gr': 'Greece', 'pt': 'Portugal', 'hu': 'Hungary', 'lu': 'Luxembourg',
    'gb': 'United Kingdom', 'ar': 'Argentina', 'tw': 'Taiwan', 'bg': 'Bulgaria',
    'il': 'Israel', 'md': 'Moldova', 'ru': 'Russia', 'ir': 'Chile',
    'cr': 'Costa Rica', 'vn': 'Vietnam', 'id': 'Indonesia', 'sc': 'Seychelles',
    'hr': 'Croatia', 'tn': 'Tunisia'
}

PLAN_COUNTRIES = {
    'b': ['de', 'us', 'tr', 'at', 'fr'],
    's': ['de', 'tr', 'us', 'fr', 'at', 'be', 'ro', 'ca', 'sg', 'jp', 'ie', 'fi', 'es', 'pl', 'nl'],
    'g': list(VALID_COUNTRIES.keys())
}

BASE_PORT = 9080
BASE_CONTROL_PORT = 19080

INSTANCES_DIR = "/etc/tor/tsin_instances"
DATA_DIR_BASE = "/var/lib/tor/tsin_data"
INSTALL_FLAG_FILE = "/etc/tor/tsin_installed"
CONFIG_MODE_FILE = "/etc/tor/tsin_config_mode"

OLD_INSTANCES_DIR = "/etc/tor/instances"
OLD_DATA_DIR_BASE = "/var/lib/tor-instances"

COLOR_PRIMARY = "\033[1;36m"
COLOR_SECONDARY = "\033[1;34m"
COLOR_SUCCESS = "\033[1;32m"
COLOR_WARN = "\033[1;33m"
COLOR_ERROR = "\033[1;31m"
COLOR_MUTED = "\033[1;30m"
COLOR_WHITE = "\033[1;37m"
COLOR_RESET = "\033[0m"

def get_plan_color():
    if LICENSE_PLAN == 'b':
        return "\033[0;33m"
    elif LICENSE_PLAN == 's':
        return "\033[1;37m"
    else:
        return "\033[1;33m" 

def get_allowed_countries():
    return set(PLAN_COUNTRIES.get(LICENSE_PLAN, list(VALID_COUNTRIES.keys())))

def get_required_plan_label(country_code):
    if country_code in get_allowed_countries():
        return None
    if country_code in PLAN_COUNTRIES['s']:
        return "Silver/Gold"
    return "Gold"

def format_plan_label(req):
    b = COLOR_SECONDARY
    s = COLOR_WHITE
    g = COLOR_WARN
    r = COLOR_RESET
    if req == "Silver/Gold":
        return f"{b}[{r}{s}Silver{r}{b}/{r}{g}Gold{r}{b}]{r}"
    elif req == "Gold":
        return f"{b}[{r}{g}Gold{r}{b}]{r}       "

def enforce_plan_restrictions():
    if LICENSE_PLAN == 'g':
        return
    installed = get_installed_instances()
    allowed = get_allowed_countries()
    to_remove = [code for code in installed if code not in allowed]
    if not to_remove:
        return
    print(f"\n{COLOR_WARN}[!] Plan enforcement: Removing {len(to_remove)} node(s) outside your current subscription...{COLOR_RESET}")
    for code in to_remove:
        country_name = VALID_COUNTRIES.get(code, code.upper())
        print(f"    {COLOR_ERROR}[-] Removing {country_name} [{code.upper()}]{COLOR_RESET}")
        delete_node(code)
    print(f"{COLOR_SUCCESS}[+] Cleanup complete. {len(to_remove)} restricted node(s) removed.{COLOR_RESET}\n")
    time.sleep(2)

def get_port_mode():
    if os.path.exists(CONFIG_MODE_FILE):
        try:
            with open(CONFIG_MODE_FILE, 'r') as f:
                mode = f.read().strip()
                if mode in ['static', 'organic']:
                    return mode
        except Exception:
            pass
    return 'static'

def set_port_mode(mode):
    try:
        os.makedirs(os.path.dirname(CONFIG_MODE_FILE), exist_ok=True)
        with open(CONFIG_MODE_FILE, 'w') as f:
            f.write(mode)
        return True
    except Exception:
        return False

def get_static_port_for_country(country_code):
    keys = list(VALID_COUNTRIES.keys())
    if country_code in keys:
        idx = keys.index(country_code)
        socks = BASE_PORT + idx
        control = BASE_CONTROL_PORT + idx
        return socks, control
    return BASE_PORT, BASE_CONTROL_PORT

def detect_geoip_paths():
    possible_paths = [
        ("/usr/share/tor/geoip", "/usr/share/tor/geoip6"),
        ("/var/lib/tor/geoip", "/var/lib/tor/geoip6"),
        ("/etc/tor/geoip", "/etc/tor/geoip6")
    ]
    for geoip, geoip6 in possible_paths:
        if os.path.exists(geoip):
            return geoip, geoip6
    return "/usr/share/tor/geoip", "/usr/share/tor/geoip6"

def fetch_global_license():
    global LICENSE_USER, LICENSE_REMAINING, LICENSE_PLAN
    LICENSE_USER = "Sin.Kabir"
    LICENSE_REMAINING = "∞"
    LICENSE_PLAN = "g"

def clear_screen():
    os.system("clear")

def print_banner():
    print(f"{COLOR_PRIMARY} ┌────────────────────────────────────────────────────────┐{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ████████╗     ██████╗  ██╗ ███╗   ██╗                 {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}  ╚══██╔══╝    ██╔════╝  ██║ ████╗  ██║                 {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}     ██║       ╚█████╗   ██║ ██╔██╗ ██║                 {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}     ██║        ╚═══██╗  ██║ ██║╚██╗██║                 {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}     ██║  ██╗  ███████║  ██║ ██║ ╚████║                 {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │{COLOR_SECONDARY}     ╚═╝  ╚═╝  ╚══════╝  ╚═╝ ╚═╝  ╚═══╝                 {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{COLOR_RESET}")
    
    col1_raw = f" User: {LICENSE_USER}"
    col2_raw = f" Remaining: {LICENSE_REMAINING}"
    
    if len(col1_raw) > 24:
        col1_raw = col1_raw[:21] + "..."
    if len(col2_raw) > 27:
        col2_raw = col2_raw[:24] + "..."
        
    col1 = f"{col1_raw:<25}"
    col2 = f"{col2_raw:<28}"
    
    plan_color = get_plan_color()
    col1_colored = col1.replace(LICENSE_USER, f"{plan_color}{LICENSE_USER}{COLOR_RESET}{COLOR_PRIMARY}")
    
    rem_color = COLOR_SUCCESS
    if "hour" in LICENSE_REMAINING or "minute" in LICENSE_REMAINING:
        rem_color = COLOR_WARN
    elif "Expired" in LICENSE_REMAINING:
        rem_color = COLOR_ERROR
        
    col2_colored = col2.replace(LICENSE_REMAINING, f"{rem_color}{LICENSE_REMAINING}{COLOR_RESET}{COLOR_PRIMARY}")
    print(f"{COLOR_PRIMARY} │ {col1_colored}│{col2_colored} │{COLOR_RESET}")
    
    dev_user = "t.me/T_Sinn"
    engine_ver = "V1.4"
    col1_row2 = f" Dev : {dev_user}"
    col2_row2 = f" Engine   : {engine_ver}"
    
    col1_r2 = f"{col1_row2:<25}"
    col2_r2 = f"{col2_row2:<28}"
    
    col1_r2_colored = col1_r2.replace(dev_user, f"{COLOR_SECONDARY}{dev_user}{COLOR_RESET}{COLOR_PRIMARY}")
    col2_r2_colored = col2_r2.replace(engine_ver, f"{COLOR_SECONDARY}{engine_ver}{COLOR_RESET}{COLOR_PRIMARY}")
    print(f"{COLOR_PRIMARY} │ {col1_r2_colored}│{col2_r2_colored} │{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} └────────────────────────────────────────────────────────┘{COLOR_RESET}")

def check_root():
    if os.getuid() != 0:
        print(f"{COLOR_ERROR}[-] Error: This script requires Root privileges to manage services.{COLOR_RESET}")
        print("[*] Please run it using 'sudo python3'.")
        sys.exit(1)

def run_cmd(cmd, check=True):
    try:
        subprocess.run(cmd, check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def show_progress_bar(duration, task_name):
    steps = 30
    for i in range(steps + 1):
        percent = int((i / steps) * 100)
        filled_length = int(steps * i // steps)
        bar = f'{COLOR_PRIMARY}█{COLOR_RESET}' * filled_length + f'{COLOR_MUTED}░{COLOR_RESET}' * (steps - filled_length)
        sys.stdout.write(f"\r{COLOR_SECONDARY}[*] {task_name:<38} {COLOR_WHITE}[{bar}] {COLOR_SUCCESS}{percent}%{COLOR_RESET}")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', int(port))) != 0

def is_system_installed():
    return os.path.exists(INSTALL_FLAG_FILE)

def get_installed_instances():
    instances = {}
    all_codes = set()
    if os.path.exists(INSTANCES_DIR):
        for item in os.listdir(INSTANCES_DIR):
            if item.startswith("tsin_"):
                all_codes.add(item.replace("tsin_", ""))
                
    if os.path.exists(OLD_INSTANCES_DIR):
        for item in os.listdir(OLD_INSTANCES_DIR):
            if item.startswith("tsin_"):
                all_codes.add(item.replace("tsin_", ""))
                
    for country_code in all_codes:
        service_file = f"/etc/systemd/system/tsin-{country_code}.service"
        active_path = None
        if os.path.exists(service_file):
            try:
                with open(service_file, 'r') as sf:
                    content = sf.read()
                    if "tsin_instances" in content:
                        active_path = f"{INSTANCES_DIR}/tsin_{country_code}"
                    elif "/etc/tor/instances" in content:
                        active_path = f"{OLD_INSTANCES_DIR}/tsin_{country_code}"
            except Exception:
                pass
                
        is_old = False
        config_dir = None
        if active_path and os.path.exists(f"{active_path}/torrc"):
            config_dir = active_path
            is_old = (OLD_INSTANCES_DIR in active_path)
        else:
            new_path = f"{INSTANCES_DIR}/tsin_{country_code}"
            old_path = f"{OLD_INSTANCES_DIR}/tsin_{country_code}"
            if os.path.exists(f"{new_path}/torrc"):
                config_dir = new_path
                is_old = False
            elif os.path.exists(f"{old_path}/torrc"):
                config_dir = old_path
                is_old = True
                
        if config_dir:
            config_path = f"{config_dir}/torrc"
            socks_port = None
            control_port = None
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        line_lower = line.lower()
                        if line_lower.startswith("socksport"):
                            parts = line.split()
                            if len(parts) > 1:
                                val = parts[1]
                                socks_port = val.split(':')[-1] if ":" in val else val
                        elif line_lower.startswith("controlport"):
                            parts = line.split()
                            if len(parts) > 1:
                                val = parts[1]
                                control_port = val.split(':')[-1] if ":" in val else val
            except Exception:
                pass
                
            instances[country_code] = {
                'socks': socks_port,
                'control': control_port,
                'path': config_dir,
                'is_old_path': is_old
            }
            
    return instances

def install_dependencies():
    try:
        show_progress_bar(1.5, "Syncing system repositories")
        subprocess.run(['sudo', 'apt', 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        
        show_progress_bar(2.0, "Downloading secure network libraries")
        subprocess.run(['sudo', 'apt', 'install', '-y', 'tor', 'tor-geoipdb', 'python3-pip', 'curl'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        
        show_progress_bar(1.8, "Deploying core system drivers")
        subprocess.run(['pip3', 'install', '--break-system-packages', 'requests', 'requests[socks]'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        subprocess.run(['pip', 'install', '--break-system-packages', 'requests', 'requests[socks]'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        
        show_progress_bar(1.0, "Optimizing background engines")
        subprocess.run(['sudo', 'systemctl', 'stop', 'tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        subprocess.run(['sudo', 'systemctl', 'disable', 'tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        pass

def delete_node(country_code):
    run_cmd(["sudo", "systemctl", "stop", f"tsin-{country_code}"])
    run_cmd(["sudo", "systemctl", "disable", f"tsin-{country_code}"])
    
    service_file = f"/etc/systemd/system/tsin-{country_code}.service"
    if os.path.exists(service_file):
        try:
            os.remove(service_file)
        except Exception:
            pass

    config_dir = f"{INSTANCES_DIR}/tsin_{country_code}"
    data_dir = f"{DATA_DIR_BASE}/tsin_{country_code}"
    
    if os.path.exists(config_dir):
        shutil.rmtree(config_dir, ignore_errors=True)
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)

    old_config_dir = f"{OLD_INSTANCES_DIR}/tsin_{country_code}"
    old_data_dir = f"{OLD_DATA_DIR_BASE}/tsin_{country_code}"

    if os.path.exists(old_config_dir):
        shutil.rmtree(old_config_dir, ignore_errors=True)
    if os.path.exists(old_data_dir):
        shutil.rmtree(old_data_dir, ignore_errors=True)
        
    run_cmd(["sudo", "systemctl", "daemon-reload"])

def create_tsin_instance(country_code, socks_port, control_port):
    instance_name = f"tsin_{country_code}"
    inst_conf_dir = f"{INSTANCES_DIR}/{instance_name}"
    inst_data_dir = f"{DATA_DIR_BASE}/{instance_name}"
    
    os.makedirs(inst_conf_dir, exist_ok=True)
    os.makedirs(inst_data_dir, exist_ok=True)
    
    geoip_path, geoip6_path = detect_geoip_paths()
    
    config_content = f"""# Tsin configuration for {country_code.upper()}
DataDirectory {inst_data_dir}
SocksPort 0.0.0.0:{socks_port} NoIsolateClientAddr NoIsolateSOCKSAuth NoIsolateClientProtocol NoIsolateDestPort NoIsolateDestAddr
ControlPort 127.0.0.1:{control_port}
CookieAuthentication 0
GeoIPFile {geoip_path}
GeoIPv6File {geoip6_path}
ExitNodes {{{country_code}}}
StrictNodes 1
MaxCircuitDirtiness 1800
NumEntryGuards 8
KeepalivePeriod 60
OptimisticData 1
"""
    with open(f"{inst_conf_dir}/torrc", 'w') as f:
        f.write(config_content)
        
    run_cmd(["sudo", "chown", "-R", "debian-tor:debian-tor", inst_conf_dir])
    run_cmd(["sudo", "chown", "-R", "debian-tor:debian-tor", inst_data_dir])
    run_cmd(["sudo", "chmod", "700", inst_data_dir])
    
    service_file = f"/etc/systemd/system/tsin-{country_code}.service"
    service_content = f"""[Unit]
Description=Tsin Connection Node for {country_code.upper()}
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/tor -f {inst_conf_dir}/torrc
User=debian-tor
LimitNOFILE=32768
Restart=on-failure
WorkingDirectory={inst_data_dir}

[Install]
WantedBy=multi-user.target
"""
    with open(service_file, 'w') as f:
        f.write(service_content)
        
    run_cmd(["sudo", "systemctl", "daemon-reload"])
    run_cmd(["sudo", "systemctl", "enable", f"tsin-{country_code}"])
    run_cmd(["sudo", "systemctl", "restart", f"tsin-{country_code}"])
    
    return True

def get_node_ip(socks_port):
    try:
        import requests
        # بررسی آی‌پی با 5 بار تلاش (همون‌طور که خواسته بودی)
        for _ in range(5):
            try:
                url = 'http://checkip.amazonaws.com'
                get_ip = requests.get(url, proxies={
                    'http': f'socks5://127.0.0.1:{socks_port}',
                    'https': f'socks5://127.0.0.1:{socks_port}'
                }, timeout=6)
                ip = get_ip.text.strip()
                if ip:
                    return ip
            except Exception:
                time.sleep(1.5)
    except ImportError:
        pass
    return "Disconnected"

def render_row(c0, c1, c2, c3, c4, color_code=""):
    s0 = f"{c0:<4}"
    s1 = f"{c1:<22}"
    s2 = f"{c2:<6}"
    s3 = f"{c3:<12}"
    s4 = f"{c4:<20}"
    
    if color_code:
        s0 = f"{color_code}{s0}\033[0m"
        s1 = f"{color_code}{s1}\033[0m"
        s2 = f"{color_code}{s2}\033[0m"
        s3 = f"{color_code}{s3}\033[0m"
        s4 = f"{color_code}{s4}\033[0m"
    
    return f"{COLOR_PRIMARY}│{COLOR_RESET} {s0} {COLOR_PRIMARY}│{COLOR_RESET} {s1} {COLOR_PRIMARY}│{COLOR_RESET} {s2} {COLOR_PRIMARY}│{COLOR_RESET} {s3} {COLOR_PRIMARY}│{COLOR_RESET} {s4} {COLOR_PRIMARY}│{COLOR_RESET}"

def setup_base_instance():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 1 - Install Engine{COLOR_RESET}\n")
    
    if is_system_installed():
        print(f"{COLOR_WARN}[!] Main engine is already installed on the system.{COLOR_RESET}")
        input("\nPress Enter to return to main menu...")
        return
        
    install_dependencies()
    
    try:
        os.makedirs(os.path.dirname(INSTALL_FLAG_FILE), exist_ok=True)
        with open(INSTALL_FLAG_FILE, "w") as f:
            f.write("installed")
        print(f"\n{COLOR_SUCCESS}[+] Engine successfully installed!{COLOR_RESET}")
    except Exception as e:
        print(f"\n{COLOR_ERROR}[-] Configuration failed: {e}{COLOR_RESET}")
        
    input("\nPress Enter to return to main menu...")

def perform_smart_bootstrap(country_code, socks_port):
    service_name = f"tsin-{country_code}"
    print(f"\n[*] Initializing routing verification. Please wait...")
    show_progress_bar(4.0, "Bootstrapping tunnel connection")

    for attempt in range(1, 6):
        live_ip = get_node_ip(socks_port)
        if live_ip and live_ip != "Disconnected":
            return True, live_ip

        if attempt < 5:
            show_progress_bar(3.0, f"Re-routing node (Attempt {attempt}/5)")
            run_cmd(["sudo", "systemctl", "reload", service_name], check=False)
            run_cmd(["sudo", "systemctl", "restart", service_name], check=False)
            time.sleep(1.5)

    return False, None

def setup_additional_location():
    while True:
        clear_screen()
        print_banner()
        print(f"{COLOR_PRIMARY}» Option 4 - Add Location Node{COLOR_RESET}\n")
        
        if not is_system_installed():
            print(f"{COLOR_ERROR}[-] No active engine setup detected! Please run Option 1 first to install the core system.{COLOR_RESET}")
            input("\nPress Enter to return to main menu...")
            return
            
        installed = get_installed_instances()
        available = {k: v for k, v in VALID_COUNTRIES.items() if k not in installed}
        if not available:
            print("[+] All supported locations are already configured.")
            input("\nPress Enter to return to main menu...")
            return

        print("Available Locations:")
        available_list = sorted(available.items(), key=lambda x: (get_required_plan_label(x[0]) is not None))
        for idx, (code, country_name) in enumerate(available_list, 1):
            static_socks, _ = get_static_port_for_country(code)
            req = get_required_plan_label(code)
            if req:
                print(f"  {idx:02d} - [{code.upper()}] [{static_socks}] - {country_name:<16}  {format_plan_label(req)}")
            else:
                print(f"  {COLOR_PRIMARY}{idx:02d} -{COLOR_RESET} [{code.upper()}] [{static_socks}] - {country_name}")
        print(f"  {COLOR_ERROR}00 -{COLOR_RESET} Back to main menu")

        choice = input("\nSelect location index: ").strip()
        if choice == '0' or choice == '00' or not choice:
            break

        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(available_list):
            print(f"{COLOR_ERROR}[-] Invalid selection.{COLOR_RESET}")
            time.sleep(1.5)
            continue

        selected_code, selected_name = available_list[int(choice) - 1]
        req_plan = get_required_plan_label(selected_code)
        if req_plan:
            print(f"{COLOR_ERROR}[-] Installing {selected_name} requires a {req_plan} subscription.{COLOR_RESET}")
            time.sleep(2)
            continue

        mode = get_port_mode()
        if mode == 'static':
            next_socks_port, next_control_port = get_static_port_for_country(selected_code)
            while not is_port_free(next_socks_port):
                next_socks_port += 1
                next_control_port = next_socks_port + 10000
        else:
            used_ports = {int(inst['socks']) for inst in installed.values() if inst['socks'] and inst['socks'].isdigit()}
            candidate = BASE_PORT
            while True:
                if candidate not in used_ports and is_port_free(candidate):
                    break
                candidate += 1
            next_socks_port = candidate
            next_control_port = next_socks_port + 10000
            
        print(f"\n[*] Deploying Node: {selected_name} [{selected_code.upper()}] on SOCKS Port {next_socks_port}...")
        print(f"{COLOR_WARN}[!] Please wait. Engine requires active route generation on first launch.{COLOR_RESET}")
        
        if create_tsin_instance(selected_code, next_socks_port, next_control_port):
            verified, live_ip = perform_smart_bootstrap(selected_code, next_socks_port)
            
            if verified:
                print(f"\n{COLOR_SUCCESS}[+] Node {selected_name} is successfully online!{COLOR_RESET}")
                print(f"[*] Secured IP: {COLOR_WARN}{live_ip}{COLOR_RESET}")
            else:
                print(f"\n{COLOR_ERROR}⚠️ Node {selected_name} failed to resolve an active routing pathway.{COLOR_RESET}")
                print(f"{COLOR_WARN}[*] Removing offline/unstable configuration automatically to preserve resource integrity...{COLOR_RESET}")
                delete_node(selected_code)
                print(f"{COLOR_SUCCESS}[+] Cleanup completed. Please try again or select an alternate gateway country.{COLOR_RESET}")
            
            input("\nPress Enter to continue...")
        else:
            print(f"{COLOR_ERROR}[-] Deployment failed.{COLOR_RESET}")
            time.sleep(2)

def view_installed_locations():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 6 - View Active Nodes{COLOR_RESET}\n")
    
    if not is_system_installed():
        print(f"{COLOR_ERROR}[- ] Core system not installed. Please initialize using Option 1.{COLOR_RESET}")
        input("\nPress Enter to return...")
        return
        
    installed = get_installed_instances()
    if not installed:
        print(f"{COLOR_WARN}[!] No locations deployed yet. Use Option 4 to deploy your first location.{COLOR_RESET}")
        input("\nPress Enter to return...")
        return
        
    print("[*] Probing active systems and fetching live connection status...")
    
    try:
        sorted_instances = sorted(
            installed.items(), 
            key=lambda item: int(item[1]['socks']) if item[1]['socks'] and item[1]['socks'].isdigit() else 0
        )
    except Exception:
        sorted_instances = list(installed.items())
        
    border = "─" * 78
    print(f"{COLOR_PRIMARY}┌{border}┐{COLOR_RESET}")
    print(render_row("ID", "Location", "Code", "Node Port", "Live IP Address", color_code=COLOR_WHITE))
    print(f"{COLOR_PRIMARY}├{border}┤{COLOR_RESET}")
    
    for idx, (code, info) in enumerate(sorted_instances, 1):
        country_name = VALID_COUNTRIES.get(code, "Custom Exit")
        socks = info['socks'] or "N/A"
        
        status_check = subprocess.run(['systemctl', 'is-active', f'tsin-{code}'], stdout=subprocess.PIPE, text=True)
        is_active = status_check.stdout.strip() == 'active'
        
        live_ip = "Offline"
        if is_active:
            live_ip = get_node_ip(socks)
            
        print(render_row(f"{idx:02d}", country_name, code.upper(), socks, live_ip))
        
    print(f"{COLOR_PRIMARY}└{border}┘{COLOR_RESET}")
    input("\nPress Enter to return to main menu...")

def edit_or_delete_location():
    while True:
        clear_screen()
        print_banner()
        print(f"{COLOR_PRIMARY}» Option 7 - Edit or Delete Nodes{COLOR_RESET}\n")
        
        if not is_system_installed():
            print(f"{COLOR_ERROR}[-] Core system not installed. Please initialize using Option 1.{COLOR_RESET}")
            input("\nPress Enter to return...")
            return
            
        installed = get_installed_instances()
        if not installed:
            print(f"{COLOR_ERROR}[- ] No active nodes to manage.{COLOR_RESET}")
            input("\nPress Enter to return...")
            return
            
        try:
            sorted_instances = sorted(
                installed.items(), 
                key=lambda item: int(item[1]['socks']) if item[1]['socks'] and item[1]['socks'].isdigit() else 0
            )
        except Exception:
            sorted_instances = list(installed.items())
            
        print("Installed Nodes (Sorted by Port):")
        for idx, (code, info) in enumerate(sorted_instances, 1):
            country_name = VALID_COUNTRIES.get(code, code.upper())
            print(f"  {COLOR_PRIMARY}{idx:02d} -{COLOR_RESET} {country_name} [Port: {info['socks']}]")
        print(f"  {COLOR_ERROR}00 -{COLOR_RESET} Back to main menu")
        
        choice = input("\nSelect node index to manage: ").strip()
        if choice == '0' or choice == '00' or not choice:
            return
            
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(sorted_instances):
            print(f"{COLOR_ERROR}[- ] Invalid input.{COLOR_RESET}")
            time.sleep(1.5)
            continue
            
        target_code, target_info = sorted_instances[int(choice) - 1]
        target_name = VALID_COUNTRIES.get(target_code, target_code.upper())
        
        while True:
            clear_screen()
            print_banner()
            print(f"{COLOR_PRIMARY}» Managing Node: {COLOR_WARN}{target_name}{COLOR_RESET}\n")
            print(f"  {COLOR_PRIMARY}1 -{COLOR_RESET} Modify Node Port")
            print(f"  {COLOR_ERROR}2 -{COLOR_RESET} Delete Node Config & Service")
            print(f"  {COLOR_WHITE}0 -{COLOR_RESET} Back to Node List")
            
            act_choice = input("\nSelect action: ").strip()
            
            if act_choice == '0' or not act_choice:
                break
                
            elif act_choice == '1':
                new_port = input(f"Enter new Node port (Current: {target_info['socks']}): ").strip()
                if not new_port.isdigit():
                    print(f"{COLOR_ERROR}[- ] Error: Ports must be numeric.{COLOR_RESET}")
                    time.sleep(1.5)
                    continue
                    
                if not is_port_free(new_port) and new_port != target_info['socks']:
                    print(f"{COLOR_ERROR}[- ] Port {new_port} is already bound by another service on the server!{COLOR_RESET}")
                    time.sleep(2)
                    continue
                    
                new_control = int(new_port) + 10000
                print(f"[*] Reconfiguring node {target_name} on port {new_port}...")
                create_tsin_instance(target_code, new_port, new_control)
                target_info['socks'] = new_port
                target_info['control'] = str(new_control)
                print(f"{COLOR_SUCCESS}[+] Node configuration updated and service restarted successfully.{COLOR_RESET}")
                input("\nPress Enter to continue...")
                
            elif act_choice == '2':
                confirm = input(f"⚠️ Are you sure you want to completely purge '{target_name}'? [y/N]: ").strip().lower()
                if confirm == 'y':
                    print(f"[*] Disabling and cleaning services for {target_name}...")
                    delete_node(target_code)
                    print(f"{COLOR_SUCCESS}[+] Node {target_name} cleanly deleted from system.{COLOR_RESET}")
                    time.sleep(1.5)
                    break
                else:
                    print("[-] Cancelled.")
                    time.sleep(1)

def uninstall_system():
    clear_screen()
    print_banner()
    print(f"{COLOR_ERROR}» Option 3 - Uninstall System{COLOR_RESET}\n")
    
    if not is_system_installed():
        print(f"{COLOR_WARN}[!] Tsin system is already uninstalled or not detected on this server.{COLOR_RESET}")
        input("\nPress Enter to return to main menu...")
        return
        
    confirm = input("⚠️ Are you sure you want to completely uninstall Tsin and wipe all configurations? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("[-] Uninstall process cancelled.")
        time.sleep(1)
        return
        
    print("\n[*] Initiating full system purge...")
    
    installed = get_installed_instances()
    for code in installed.keys():
        show_progress_bar(0.4, f"Purging Node {code.upper()}")
        delete_node(code)
            
    show_progress_bar(0.8, "Wiping node config structures")
    if os.path.exists(INSTANCES_DIR):
        for item in os.listdir(INSTANCES_DIR):
            if item.startswith("tsin_"):
                shutil.rmtree(os.path.join(INSTANCES_DIR, item), ignore_errors=True)
                
    if os.path.exists(OLD_INSTANCES_DIR):
        for item in os.listdir(OLD_INSTANCES_DIR):
            if item.startswith("tsin_"):
                shutil.rmtree(os.path.join(OLD_INSTANCES_DIR, item), ignore_errors=True)
                
    show_progress_bar(0.8, "Wiping database environments")
    if os.path.exists(DATA_DIR_BASE):
        for item in os.listdir(DATA_DIR_BASE):
            if item.startswith("tsin_"):
                shutil.rmtree(os.path.join(DATA_DIR_BASE, item), ignore_errors=True)
                
    if os.path.exists(OLD_DATA_DIR_BASE):
        for item in os.listdir(OLD_DATA_DIR_BASE):
            if item.startswith("tsin_"):
                shutil.rmtree(os.path.join(OLD_DATA_DIR_BASE, item), ignore_errors=True)
                
    if os.path.exists(INSTALL_FLAG_FILE):
        os.remove(INSTALL_FLAG_FILE)
    if os.path.exists(CONFIG_MODE_FILE):
        os.remove(CONFIG_MODE_FILE)
                
    show_progress_bar(1.5, "Reclaiming system resources")
    subprocess.run(["sudo", "apt", "purge", "-y", "tor", "tor-geoipdb"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    subprocess.run(["sudo", "apt", "autoremove", "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    
    run_cmd(["sudo", "systemctl", "daemon-reload"])
    
    print(f"\n{COLOR_SUCCESS}[+] Tsin system successfully completely uninstalled and resources reclaimed!{COLOR_RESET}")
    input("\nPress Enter to return to main menu...")

def update_system():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 2 - Update System{COLOR_RESET}\n")
    
    confirm = input("⚠️ Are you sure you want to update the system? [y/N]: ").strip().lower()
    if confirm in ['y', 'yes']:
        clear_screen()
        print(f"\n{COLOR_SUCCESS}[*] Closing program and executing automatic update script...{COLOR_RESET}")
        time.sleep(1.5)
        cmd = 'curl -sL "https://raw.githubusercontent.com/1NoJoom/T.Sin/main/install.sh?v=$(date +%s)" | tr -d "\\r" | sudo bash'
        os.system(cmd)
        sys.exit(0)
    else:
        print("[-] Update operation cancelled.")
        time.sleep(1.5)

def setup_advanced_settings():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 8 - Advanced Port Settings{COLOR_RESET}\n")
    
    current_mode = get_port_mode()
    mode_text = "Static Dedicated Port (Fixed Country Ports)" if current_mode == 'static' else "Organic Sequential Ports (9080, 9081...)"
    
    print(f"Current Port Mode: {COLOR_WARN}{mode_text}{COLOR_RESET}")
    print("\nSelect Installation Rule:")
    print(f"  {COLOR_PRIMARY}1 -{COLOR_RESET} Static Dedicated Ports (Default - Every country gets its fixed unique port)")
    print(f"  {COLOR_PRIMARY}2 -{COLOR_RESET} Organic Sequential Ports (Classic behavior - 9080 increments sequentially)")
    print(f"  {COLOR_WHITE}0 -{COLOR_RESET} Back to main menu")
    
    choice = input("\nEnter choice [0-2]: ").strip()
    if choice == '1':
        if set_port_mode('static'):
            print(f"{COLOR_SUCCESS}[+] Configuration set to Static Dedicated Ports successfully!{COLOR_RESET}")
        else:
            print(f"{COLOR_ERROR}[-] Failed to write configuration mode.{COLOR_RESET}")
    elif choice == '2':
        if set_port_mode('organic'):
            print(f"{COLOR_SUCCESS}[+] Configuration set to Organic Sequential Ports successfully!{COLOR_RESET}")
        else:
            print(f"{COLOR_ERROR}[-] Failed to write configuration mode.{COLOR_RESET}")
    else:
        return
    time.sleep(1.5)

def deploy_node_silently(code, name, mode, installed):
    if mode == 'static':
        socks, control = get_static_port_for_country(code)
        while not is_port_free(socks):
            socks += 1
            control = socks + 10000
    else:
        used_ports = {int(inst['socks']) for inst in installed.values() if inst['socks'] and inst['socks'].isdigit()}
        candidate = BASE_PORT
        while True:
            if candidate not in used_ports and is_port_free(candidate):
                break
            candidate += 1
        socks = candidate
        control = socks + 10000
        
    if create_tsin_instance(code, socks, control):
        verified, live_ip = perform_smart_bootstrap(code, socks)
        if verified:
            installed[code] = {'socks': str(socks), 'control': str(control), 'path': f"{INSTANCES_DIR}/tsin_{code}"}
            return True, live_ip
        else:
            delete_node(code)
            return False, None
    return False, None

def setup_bulk_deployment():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 5 - Bulk Add Nodes{COLOR_RESET}\n")
    
    if not is_system_installed():
        print(f"{COLOR_ERROR}[-] No active base setup detected! Please run Option 1 first to install the core system.{COLOR_RESET}")
        input("\nPress Enter to return to main menu...")
        return
        
    print("Select Bulk Installation Profile:")
    print(f"  {COLOR_PRIMARY}1 -{COLOR_RESET} Deploy All Remaining Locations Automatically (Recommended)")
    print(f"  {COLOR_PRIMARY}2 -{COLOR_RESET} Select Multiple Custom Locations manually")
    print(f"  {COLOR_ERROR}0 -{COLOR_RESET} Back to main menu")
    
    choice = input("\nEnter choice [0-2]: ").strip()
    if choice == '0' or not choice:
        return
        
    installed = get_installed_instances()
    allowed = get_allowed_countries()
    available = {k: v for k, v in VALID_COUNTRIES.items() if k not in installed}

    if not available:
        print(f"{COLOR_WARN}[!] All supported locations are already configured and active!{COLOR_RESET}")
        input("\nPress Enter to return...")
        return
        
    mode = get_port_mode()
    
    if choice == '1':
        deployable = {k: v for k, v in available.items() if k in allowed}
        restricted_count = len(available) - len(deployable)
        print(f"\n[*] Deploying {len(deployable)} locations silently under '{mode.upper()}' routing specifications...")
        if restricted_count:
            print(f"{COLOR_WARN}[!] {restricted_count} location(s) skipped — not included in your current subscription.{COLOR_RESET}")
        success_count = 0
        failed_count = 0

        for idx, (code, name) in enumerate(deployable.items(), 1):
            print(f"\n{COLOR_SECONDARY}[*] [{idx}/{len(deployable)}] Installing {name:<18}{COLOR_RESET}")
            ok, ip = deploy_node_silently(code, name, mode, installed)
            if ok:
                success_count += 1
                print(f"    {COLOR_SUCCESS}[+] Online -> {name} ({ip}){COLOR_RESET}")
            else:
                failed_count += 1
                print(f"    {COLOR_ERROR}[- ] Timeout -> {name} (Bypassing...){COLOR_RESET}")
                time.sleep(2)

        print(f"\n{COLOR_SUCCESS}[+] Bulk setup finished: {success_count} deployed, {failed_count} skipped.{COLOR_RESET}")
        input("\nPress Enter to return...")
        
    elif choice == '2':
        clear_screen()
        print_banner()
        print(f"{COLOR_PRIMARY}» Select Locations to Deploy (e.g., 1, 3, 5-7, de, tr){COLOR_RESET}\n")
        
        available_list = sorted(available.items(), key=lambda x: (get_required_plan_label(x[0]) is not None))
        for idx, (code, country_name) in enumerate(available_list, 1):
            static_socks, _ = get_static_port_for_country(code)
            req = get_required_plan_label(code)
            if req:
                print(f"  {idx:02d} - [{code.upper()}] [{static_socks}] - {country_name:<16}  {format_plan_label(req)}")
            else:
                print(f"  {COLOR_PRIMARY}{idx:02d} -{COLOR_RESET} [{code.upper()}] [{static_socks}] - {country_name}")

        inputs = input("\nSelect indices, ranges or country codes: ").strip()
        if not inputs:
            return
            
        selected_nodes = []
        parts = [p.strip().lower() for p in inputs.split(',') if p.strip()]
        for part in parts:
            if part in available:
                node_data = (part, available[part])
                if node_data not in selected_nodes:
                    selected_nodes.append(node_data)
            elif '-' in part:
                try:
                    start_str, end_str = part.split('-')
                    start = int(start_str.strip())
                    end = int(end_str.strip())
                    for idx in range(start, end + 1):
                        if 1 <= idx <= len(available_list):
                            node_data = available_list[idx - 1]
                            if node_data not in selected_nodes:
                                selected_nodes.append(node_data)
                except ValueError:
                    pass
            elif part.isdigit():
                idx = int(part)
                if 1 <= idx <= len(available_list):
                    node_data = available_list[idx - 1]
                    if node_data not in selected_nodes:
                        selected_nodes.append(node_data)
                        
        if not selected_nodes:
            print(f"{COLOR_ERROR}[- ] Selection array returned empty.{COLOR_RESET}")
            time.sleep(1.5)
            return

        deployable_nodes = [(c, n) for c, n in selected_nodes if not get_required_plan_label(c)]
        restricted_nodes = [(c, n) for c, n in selected_nodes if get_required_plan_label(c)]

        print(f"\n{COLOR_SUCCESS}[+] Selected {len(selected_nodes)} locations for deployment:{COLOR_RESET}")
        for code, name in selected_nodes:
            req = get_required_plan_label(code)
            if req:
                print(f"  - {name:<16} [{code.upper()}]  {format_plan_label(req)}")
            else:
                print(f"  - {name} [{code.upper()}]")

        if restricted_nodes:
            print(f"\n{COLOR_WARN}[!] {len(restricted_nodes)} location(s) will be skipped — not in your current subscription.{COLOR_RESET}")

        if not deployable_nodes:
            print(f"{COLOR_ERROR}[-] No eligible locations to deploy under your current plan.{COLOR_RESET}")
            input("\nPress Enter to return...")
            return

        confirm = input(f"\nProceed with deploying {len(deployable_nodes)} eligible location(s)? [Y/n]: ").strip().lower()
        if confirm == 'n':
            return

        print(f"\n[*] Starting batch execution for {len(deployable_nodes)} targets...")
        success_count = 0
        failed_count = 0

        for idx, (code, name) in enumerate(deployable_nodes, 1):
            print(f"\n{COLOR_SECONDARY}[*] [{idx}/{len(deployable_nodes)}] Processing {name:<18}{COLOR_RESET}")
            ok, ip = deploy_node_silently(code, name, mode, installed)
            if ok:
                success_count += 1
                print(f"    {COLOR_SUCCESS}[+] Online -> {name} ({ip}){COLOR_RESET}")
            else:
                failed_count += 1
                print(f"    {COLOR_ERROR}[- ] Timeout -> {name} (Skipping node){COLOR_RESET}")
                time.sleep(2)

        print(f"\n{COLOR_SUCCESS}[+] Batch setup finished: {success_count} deployed, {failed_count} skipped.{COLOR_RESET}")
        input("\nPress Enter to return...")

def launch_ez_panel():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» EZ-Panel Setup / Launch{COLOR_RESET}\n")

    # درخواست اطلاعات پنل از کاربر
    print(f"{COLOR_WARN}[!] Please provide EZ-Panel configuration details:{COLOR_RESET}")
    server_ip = input(f" {COLOR_SECONDARY}↳ Server Address (IP): {COLOR_RESET}").strip()
    admin_user = input(f" {COLOR_SECONDARY}↳ Admin Username: {COLOR_RESET}").strip()
    admin_pass = input(f" {COLOR_SECONDARY}↳ Admin Password: {COLOR_RESET}").strip()

    ez_paths = [
        "/usr/local/bin/EZ-Panel",
        "/usr/bin/EZ-Panel",
        "/usr/local/bin/ez-panel",
        "/usr/bin/ez-panel",
        "/opt/ez-panel/ez-panel",
        "/opt/ez-panel/start.sh",
        "/usr/local/bin/ezpanel",
    ]
    
    installed_path = None
    for p in ez_paths:
        if os.path.exists(p) and os.access(p, os.X_OK):
            installed_path = p
            break

    if not installed_path:
        which_path = shutil.which("EZ-Panel") or shutil.which("ez-panel")
        if which_path and os.path.exists(which_path):
            installed_path = which_path

    time.sleep(0.5)
    clear_screen()

    if installed_path:
        print(f"{COLOR_SUCCESS}[+] EZ-Panel detected. Launching...{COLOR_RESET}")
        time.sleep(1)
        # پاس دادن متغیرها برای استفاده احتمالی پنل و اجرای آن با sudo -E برای حفظ متغیرها
        os.environ['EZ_IP'] = server_ip
        os.environ['EZ_USER'] = admin_user
        os.environ['EZ_PASS'] = admin_pass
        os.system(f"sudo -E {installed_path}")
    else:
        print(f"{COLOR_SECONDARY}[*] EZ-Panel not found. Downloading and installing...{COLOR_RESET}")
        time.sleep(1)
        # ست کردن اطلاعات ورودی کاربر به عنوان متغیرهای نصبی برای دریافت داخل اسکریپت بش
        cmd = f'export EZ_IP="{server_ip}" EZ_USER="{admin_user}" EZ_PASS="{admin_pass}" && sudo -E bash -c "$(curl -sL "https://raw.githubusercontent.com/1NoJoom/EZ-Panel/main/install.sh?v=$(date +%s)" | tr -d \'\\r\')"'
        os.system(cmd)

    sys.exit(0)

def main():
    check_root()
    fetch_global_license()
    enforce_plan_restrictions()

    while True:
        clear_screen()
        print_banner()
        
        installed = get_installed_instances()
        active_count = len(installed)
        system_installed = is_system_installed()
        
        print(f"{COLOR_PRIMARY} ┌────────────────────────────────────────────────────────┐{COLOR_RESET}")
        
        if system_installed:
            status_val = f"Active ({active_count} Node{'s' if active_count != 1 else ''})"
            status_color = COLOR_SUCCESS
        else:
            status_val = "Not Installed"
            status_color = COLOR_ERROR
            
        status_text = f"  System Status: {status_val}"
        padded_status = f"{status_text:<54}"
        colored_status = padded_status.replace(status_val, f"{status_color}{status_val}{COLOR_RESET}{COLOR_PRIMARY}")
        print(f"{COLOR_PRIMARY} │ {colored_status} │{COLOR_RESET}")
        
        print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{COLOR_RESET}")
        
        def print_menu_row(opt, desc):
            raw_text = f"  [{opt}] » {desc}"
            padded = f"{raw_text:<54}"
            cyan = COLOR_SECONDARY
            colored = padded.replace(f"[{opt}] »", f"[{COLOR_PRIMARY}{opt}{COLOR_RESET}{COLOR_PRIMARY}] {cyan}»{COLOR_RESET}{COLOR_PRIMARY}")
            print(f"{COLOR_PRIMARY} │ {colored} │{COLOR_RESET}")
            
        print_menu_row("1", "Install Engine")
        print_menu_row("2", "Update System")
        print_menu_row("3", "Uninstall System")
        
        print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{COLOR_RESET}")
        
        print_menu_row("4", "Add Location Node")
        print_menu_row("5", "Bulk Add Nodes")
        print_menu_row("6", "View Active Nodes")
        print_menu_row("7", "Edit or Delete Nodes")
        print_menu_row("8", "Advanced Port Settings")
        
        print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{COLOR_RESET}")
        print_menu_row("9", "EZ-Panel")

        reset_val = COLOR_RESET
        print(f"{COLOR_PRIMARY} ├────────────────────────────────────────────────────────┤{reset_val}")
        print_menu_row("0", "Exit Program")
        print(f"{COLOR_PRIMARY} └────────────────────────────────────────────────────────┘{COLOR_RESET}")
        
        choice = input(" \033[1;37mEnter choice [0-9]: \033[0m").strip()
        
        if choice == '1':
            setup_base_instance()
        elif choice == '2':
            update_system()
        elif choice == '3':
            uninstall_system()
        elif choice == '4':
            setup_additional_location()
        elif choice == '5':
            setup_bulk_deployment()
        elif choice == '6':
            view_installed_locations()
        elif choice == '7':
            edit_or_delete_location()
        elif choice == '8':
            setup_advanced_settings()
        elif choice == '9':
            launch_ez_panel()
        elif choice == '0':
            clear_screen()
            print(f"{COLOR_SUCCESS}Thank you for using T.Sin Multi-Node Master. Exiting...{COLOR_RESET}")
            break
        else:
            print(f"{COLOR_ERROR}[-] Invalid selection.{COLOR_RESET}")
            time.sleep(1.5)

if __name__ == "__main__":
    main()
