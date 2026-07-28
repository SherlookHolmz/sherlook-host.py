cat << 'EOF' > /usr/local/bin/sherlook
#!/usr/bin/env python3
import os
import sys
import time
import shutil
import socket
import json
import subprocess

# ==========================================
# SHERLOOK CORE ENGINE v3.0 - CLEAN & STABLE
# ==========================================

VALID_COUNTRIES = {
    'de': 'Germany', 'tr': 'Turkey', 'us': 'USA', 'fr': 'France', 'at': 'Austria',
    'nl': 'Netherlands', 'gb': 'UK', 'ca': 'Canada', 'sg': 'Singapore', 'jp': 'Japan',
    'fi': 'Finland', 'es': 'Spain', 'pl': 'Poland', 'it': 'Italy', 'ch': 'Switzerland',
    'au': 'Australia', 'in': 'India', 'ua': 'Ukraine', 'kr': 'South Korea', 'ru': 'Russia'
}

BASE_PORT = 9080
BASE_CONTROL_PORT = 19080

INSTANCES_DIR = "/etc/tor/sherlook_instances"
DATA_DIR_BASE = "/var/lib/tor/sherlook_data"
INSTALL_FLAG_FILE = "/etc/tor/sherlook_installed"

COLOR_PRIMARY = "\033[1;36m"
COLOR_SUCCESS = "\033[1;32m"
COLOR_WARN = "\033[1;33m"
COLOR_ERROR = "\033[1;31m"
COLOR_RESET = "\033[0m"

def clear_screen():
    os.system("clear")

def print_banner():
    print(f"{COLOR_PRIMARY} ┌──────────────────────────────────────────────┐{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │               SHERLOOK v3.0                  │{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} │     Strict Route Engine & Eazy Panel         │{COLOR_RESET}")
    print(f"{COLOR_PRIMARY} └──────────────────────────────────────────────┘{COLOR_RESET}")

def check_root():
    if os.getuid() != 0:
        print(f"{COLOR_ERROR}[-] Error: Root privileges required.{COLOR_RESET}")
        sys.exit(1)

def run_cmd(cmd, check=True):
    try:
        subprocess.run(cmd, check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def show_progress_bar(duration, task_name):
    steps = 15
    for i in range(steps + 1):
        percent = int((i / steps) * 100)
        filled = int(steps * i // steps)
        bar = '█' * filled + '░' * (steps - filled)
        sys.stdout.write(f"\r{COLOR_PRIMARY}[*] {task_name:<25} [{bar}] {percent}%{COLOR_RESET}")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()

def is_system_installed():
    return os.path.exists(INSTALL_FLAG_FILE)

def detect_tor_user():
    try:
        with open('/etc/passwd', 'r') as f:
            if 'debian-tor:' in f.read(): return 'debian-tor'
    except: pass
    return 'tor'

def install_dependencies():
    show_progress_bar(1.0, "Updating Packages")
    subprocess.run(['apt-get', 'update', '-qq'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    show_progress_bar(1.5, "Installing Core")
    subprocess.run(['apt-get', 'install', '-y', '--no-install-recommends', 'tor', 'tor-geoipdb', 'curl'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    run_cmd(["systemctl", "stop", "tor"])
    run_cmd(["systemctl", "disable", "tor"])

def setup_base_instance():
    clear_screen()
    print_banner()
    if is_system_installed():
        print(f"{COLOR_WARN}[!] System is already installed.{COLOR_RESET}")
        input("\nPress Enter...")
        return
    install_dependencies()
    os.makedirs(os.path.dirname(INSTALL_FLAG_FILE), exist_ok=True)
    with open(INSTALL_FLAG_FILE, "w") as f: f.write("installed")
    print(f"\n{COLOR_SUCCESS}[+] Engine installed successfully!{COLOR_RESET}")
    input("\nPress Enter...")

def setup_eazy_panel():
    clear_screen()
    print_banner()
    print(f"{COLOR_PRIMARY}» Option 2 - Eazy Panel (Direct Connect){COLOR_RESET}\n")
    if not is_system_installed():
        print(f"{COLOR_ERROR}[-] Install engine first (Option 1).{COLOR_RESET}")
        input("\nPress Enter...")
        return

    print("This will create a secure, unblockable tunnel to your server.")
    target_port = input("Enter local port to expose (e.g., 22 for SSH, 8000 for Panel): ").strip()
    
    if not target_port.isdigit(): return

    hs_dir = "/var/lib/tor/sherlook_eazy"
    torrc_path = "/etc/tor/sherlook_eazy_torrc"
    tor_user = detect_tor_user()
    
    os.makedirs(hs_dir, exist_ok=True)
    
    config = f"""DataDirectory {hs_dir}
HiddenServiceDir {hs_dir}
HiddenServicePort {target_port} 127.0.0.1:{target_port}
Log notice syslog
"""
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
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    with open("/etc/systemd/system/sherlook-eazy.service", 'w') as f: f.write(service_content)
        
    run_cmd(["systemctl", "daemon-reload"])
    run_cmd(["systemctl", "enable", "sherlook-eazy"])
    run_cmd(["systemctl", "restart", "sherlook-eazy"])
    
    show_progress_bar(2.0, "Generating Direct Link")
    
    try:
        with open(f"{hs_dir}/hostname", 'r') as f:
            onion_addr = f.read().strip()
        print(f"\n{COLOR_SUCCESS}[+] Eazy Panel Active!{COLOR_RESET}")
        print(f"Direct Server Address: {COLOR_WARN}{onion_addr}{COLOR_RESET}")
        print(f"Use this address in your client/browser to connect directly.")
    except:
        print(f"\n{COLOR_ERROR}[-] Failed to generate address. Check port and Tor status.{COLOR_RESET}")
        
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
                        socks = [l.split()[1].split(':')[-1] for l in f if 'SocksPort' in l][0]
                        instances[code] = {'socks': socks}
                except: pass
    return instances

def detect_geoip():
    paths = [("/usr/share/tor/geoip", "/usr/share/tor/geoip6"), ("/var/lib/tor/geoip", "/var/lib/tor/geoip6")]
    for g4, g6 in paths:
        if os.path.exists(g4): return g4, g6
    return "/usr/share/tor/geoip", "/usr/share/tor/geoip6"

def setup_location():
    while True:
        clear_screen()
        print_banner()
        print(f"{COLOR_PRIMARY}» Option 4 - Add Node{COLOR_RESET}\n")
        installed = get_installed_instances()
        avail = {k: v for k, v in VALID_COUNTRIES.items() if k not in installed}
        
        for idx, (code, name) in enumerate(avail.items(), 1):
            print(f"  {idx:02d} - [{code.upper()}] {name}")
        print(f"  00 - Back")

        choice = input("\nSelect index: ").strip()
        if choice in ['0', '00', '']: break
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(avail): continue

        code = list(avail.keys())[int(choice) - 1]
        socks_port = BASE_PORT + list(VALID_COUNTRIES.keys()).index(code)
        control_port = BASE_CONTROL_PORT + list(VALID_COUNTRIES.keys()).index(code)
        
        create_node(code, socks_port, control_port)

def create_node(code, socks, control):
    name = f"sherlook_{code}"
    c_dir, d_dir = f"{INSTANCES_DIR}/{name}", f"{DATA_DIR_BASE}/{name}"
    g4, g6 = detect_geoip()
    tor_user = detect_tor_user()
    
    os.makedirs(c_dir, exist_ok=True); os.makedirs(d_dir, exist_ok=True)
    
    with open(f"{c_dir}/torrc", 'w') as f:
        f.write(f"DataDirectory {d_dir}\nSocksPort 0.0.0.0:{socks}\nControlPort 127.0.0.1:{control}\nCookieAuthentication 0\nGeoIPFile {g4}\nGeoIPv6File {g6}\nExitNodes {{{code}}}\nStrictNodes 1\nMaxMemInQueues 8 MB\nAvoidDiskWrites 1\nNumEntryGuards 2\n")
        
    run_cmd(["chown", "-R", f"{tor_user}:{tor_user}", c_dir])
    run_cmd(["chown", "-R", f"{tor_user}:{tor_user}", d_dir])
    run_cmd(["chmod", "700", d_dir])
    
    svc = f"[Unit]\nDescription=Sherlook Node {code.upper()}\n[Service]\nType=simple\nExecStart=/usr/sbin/tor -f {c_dir}/torrc\nUser={tor_user}\nMemoryMax=35M\nRestart=always\n[Install]\nWantedBy=multi-user.target"
    with open(f"/etc/systemd/system/sherlook-{code}.service", 'w') as f: f.write(svc)
        
    run_cmd(["systemctl", "daemon-reload"]); run_cmd(["systemctl", "enable", "--now", f"sherlook-{code}"])
    
    show_progress_bar(2.5, f"Routing {code.upper()}")
    live_ip = check_ip(socks)
    print(f"\n{COLOR_SUCCESS}[+] Node {code.upper()} Online -> IP: {live_ip}{COLOR_RESET}")
    input("\nPress Enter...")

def check_ip(socks):
    try:
        res = subprocess.run(['curl', '-s', '--socks5-hostname', f'127.0.0.1:{socks}', '--max-time', '5', 'http://ip-api.com/json'], capture_output=True, text=True)
        if res.returncode == 0: return json.loads(res.stdout).get('query', 'Disconnected')
    except: pass
    return "Disconnected"

def view_nodes():
    clear_screen()
    print_banner()
    installed = get_installed_instances()
    if not installed: return input("\nNo nodes. Press Enter...")
    
    print(f"{COLOR_PRIMARY}┌{'─'*47}┐{COLOR_RESET}")
    print(f"{COLOR_PRIMARY}│{COLOR_RESET} {'Code':<6} │ {'Port':<6} │ {'Live IP':<27} {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY}├{'─'*47}┤{COLOR_RESET}")
    for code, info in installed.items():
        print(f"{COLOR_PRIMARY}│{COLOR_RESET} {code.upper():<6} │ {info['socks']:<6} │ {check_ip(info['socks']):<27} {COLOR_PRIMARY}│{COLOR_RESET}")
    print(f"{COLOR_PRIMARY}└{'─'*47}┘{COLOR_RESET}")
    input("\nPress Enter...")

def delete_node():
    clear_screen()
    print_banner()
    installed = get_installed_instances()
    for idx, code in enumerate(installed.keys(), 1): print(f"  {idx} - [{code.upper()}]")
    c = input("\nSelect node index to delete (0 to cancel): ").strip()
    if c.isdigit() and 1 <= int(c) <= len(installed):
        code = list(installed.keys())[int(c)-1]
        run_cmd(["systemctl", "disable", "--now", f"sherlook-{code}"])
        os.remove(f"/etc/systemd/system/sherlook-{code}.service")
        shutil.rmtree(f"{INSTANCES_DIR}/sherlook_{code}", ignore_errors=True)
        print(f"{COLOR_SUCCESS}[+] Node removed.{COLOR_RESET}"); time.sleep(1)

def uninstall():
    clear_screen(); print_banner()
    if input("Uninstall everything? (y/N): ").lower() == 'y':
        for code in get_installed_instances().keys(): run_cmd(["systemctl", "disable", "--now", f"sherlook-{code}"])
        run_cmd(["systemctl", "disable", "--now", "sherlook-eazy"])
        shutil.rmtree(INSTANCES_DIR, ignore_errors=True); shutil.rmtree(DATA_DIR_BASE, ignore_errors=True)
        shutil.rmtree("/var/lib/tor/sherlook_eazy", ignore_errors=True)
        if os.path.exists(INSTALL_FLAG_FILE): os.remove(INSTALL_FLAG_FILE)
        print(f"{COLOR_SUCCESS}[+] Removed.{COLOR_RESET}"); time.sleep(1)

def main():
    check_root()
    while True:
        clear_screen()
        print_banner()
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}1{COLOR_RESET}{COLOR_PRIMARY}] » Install Engine                           │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}2{COLOR_RESET}{COLOR_PRIMARY}] » Eazy Panel (Direct Connect)              │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}3{COLOR_RESET}{COLOR_PRIMARY}] » Uninstall System                         │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}4{COLOR_RESET}{COLOR_PRIMARY}] » Add Location Node                        │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}6{COLOR_RESET}{COLOR_PRIMARY}] » View Active Nodes                        │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}7{COLOR_RESET}{COLOR_PRIMARY}] » Delete Node                              │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} │  [{COLOR_PRIMARY}0{COLOR_RESET}{COLOR_PRIMARY}] » Exit                                     │{COLOR_RESET}")
        print(f"{COLOR_PRIMARY} └──────────────────────────────────────────────┘{COLOR_RESET}")
        
        c = input(" Enter choice [0-7]: ").strip()
        if c == '1': setup_base_instance()
        elif c == '2': setup_eazy_panel()
        elif c == '3': uninstall()
        elif c == '4': setup_location()
        elif c == '6': view_nodes()
        elif c == '7': delete_node()
        elif c == '0': sys.exit(0)

if __name__ == "__main__": main()
EOF

chmod +x /usr/local/bin/sherlook
/usr/local/bin/sherlook
