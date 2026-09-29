#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pardus ETAP 23 Spoofing & MEB Integration Utility
Designed for Faz 1 / Faz 2 Smart Boards running alternative distributions (Fedora).
Maintained by @uhcal-oss (Urla Hakan Çeken Anadolu Lisesi Open Source)
"""

import sys
import os
import json
import subprocess
import shutil
import urllib.request
import urllib.error

ETAP_OS_RELEASE = """PRETTY_NAME="Pardus ETAP GNU/Linux 23 (yirmiuc)"
NAME="Pardus ETAP GNU/Linux"
VERSION_ID="23.4"
VERSION="23.4 (etap-yirmiuc)"
VERSION_CODENAME=etap-yirmiuc
ID=pardus
HOME_URL="https://www.pardus.org.tr/"
SUPPORT_URL="https://forum.pardus.org.tr/"
BUG_REPORT_URL="https://talep.pardus.org.tr/"
ID_LIKE=debian
PARDUS_CODENAME=yirmiuc
"""

ETAP_LSB_RELEASE = """DISTRIB_ID=Pardus
DISTRIB_RELEASE=23.4
DISTRIB_CODENAME=yirmiuc
DISTRIB_DESCRIPTION="Pardus ETAP 23.4"
"""

ETAP_ISSUE = "Pardus GNU/Linux 23 \\n \\l\n"
ETAP_ISSUE_NET = "Pardus GNU/Linux 23\n"
ETAP_DEBIAN_VERSION = "12.4\n"
ETAP_PARDUS_RELEASE = "Pardus 23.4 (yirmiuc)\n"

LSB_RELEASE_SCRIPT = """#!/usr/bin/env bash
# Universal LSB release provider for Pardus ETAP spoofing
if [ "$1" = "-a" ] || [ "$1" = "--all" ] || [ $# -eq 0 ]; then
    echo "Distributor ID:\tPardus"
    echo "Description:\tPardus ETAP 23.4 (yirmiuc)"
    echo "Release:\t23.4"
    echo "Codename:\tyirmiuc"
elif [ "$1" = "-s" ] || [ "$1" = "--short" ]; then
    case "$2" in
        -i|--id) echo "Pardus" ;;
        -d|--description) echo "Pardus ETAP 23.4 (yirmiuc)" ;;
        -r|--release) echo "23.4" ;;
        -c|--codename) echo "yirmiuc" ;;
        *) echo "Pardus" ;;
    esac
elif [ "$1" = "-i" ] || [ "$1" = "--id" ]; then echo "Distributor ID:\tPardus"
elif [ "$1" = "-d" ] || [ "$1" = "--description" ]; then echo "Description:\tPardus ETAP 23.4 (yirmiuc)"
elif [ "$1" = "-r" ] || [ "$1" = "--release" ]; then echo "Release:\t23.4"
elif [ "$1" = "-c" ] || [ "$1" = "--codename" ]; then echo "Codename:\tyirmiuc"
else
    echo "Distributor ID:\tPardus"
    echo "Description:\tPardus ETAP 23.4 (yirmiuc)"
    echo "Release:\t23.4"
    echo "Codename:\tyirmiuc"
fi
"""

BACKUP_DIR = "/var/lib/pardus-etap-spoof/backups"

def require_root():
    if os.geteuid() != 0:
        print("[!] This operation requires root privileges. Please run with sudo.", file=sys.stderr)
        sys.exit(1)

def get_primary_mac():
    """Finds MAC address of first non-loopback ethernet/wireless device."""
    sys_class_net = "/sys/class/net"
    if not os.path.exists(sys_class_net):
        return None
    
    # Prefer wired ethernet (en*, eth*) then wifi (wl*)
    interfaces = os.listdir(sys_class_net)
    sorted_ifaces = sorted(interfaces, key=lambda x: (not (x.startswith('en') or x.startswith('eth')), x))
    
    for iface in sorted_ifaces:
        if iface == 'lo':
            continue
        addr_file = os.path.join(sys_class_net, iface, "address")
        if os.path.exists(addr_file):
            try:
                with open(addr_file, "r") as f:
                    mac = f.read().strip().lower()
                    if mac and mac != "00:00:00:00:00:00":
                        return mac
            except Exception:
                continue
    return None

def check_meb_registration(mac=None):
    if not mac:
        mac = get_primary_mac()
    if not mac:
        return {"status": "error", "error": "No valid network MAC address found"}
    
    url = f"http://api-etap.eba.gov.tr:1000/api/board/check?mac={mac}"
    headers = {"etap-app-code": "eta_register!", "User-Agent": "eta-register/2.0.8"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {"status": "ok", "mac": mac, "data": data}
    except urllib.error.URLError as e:
        return {"status": "network_error", "mac": mac, "error": str(e)}
    except Exception as e:
        return {"status": "error", "mac": mac, "error": str(e)}

def is_spoof_active():
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read()
                return "Pardus ETAP" in content
        except Exception:
            return False
    return False

def enable_spoof():
    require_root()
    print("[*] Enabling Pardus ETAP 23 identity spoofing...")
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs("/etc/dnf/vars", exist_ok=True)
    
    # 1. Protect DNF variable releasever
    releasever_path = "/etc/dnf/vars/releasever"
    basearch_path = "/etc/dnf/vars/basearch"
    
    # Detect current Fedora releasever if not already pinned
    fedora_ver = "44"
    if os.path.exists("/usr/lib/os-release"):
        with open("/usr/lib/os-release") as f:
            for line in f:
                if line.startswith("VERSION_ID="):
                    fedora_ver = line.strip().split("=")[1].replace('"', '')
                    break
    
    with open(releasever_path, "w") as f:
        f.write(f"{fedora_ver}\n")
    with open(basearch_path, "w") as f:
        f.write("x86_64\n")
    print(f"  [+] Pinned DNF releasever to {fedora_ver} in {releasever_path} (prevents package manager breakage)")

    # 2. Back up original files/symlinks
    for filepath in ["/etc/os-release", "/etc/issue", "/etc/issue.net"]:
        backup_dest = os.path.join(BACKUP_DIR, os.path.basename(filepath))
        if os.path.exists(filepath) and not os.path.exists(backup_dest):
            if os.path.islink(filepath):
                target = os.readlink(filepath)
                with open(backup_dest + ".symlink", "w") as sf:
                    sf.write(target)
            else:
                shutil.copy2(filepath, backup_dest)
            print(f"  [+] Backed up original {filepath}")

    # 3. Write Pardus ETAP release files
    if os.path.islink("/etc/os-release") or os.path.exists("/etc/os-release"):
        os.remove("/etc/os-release")
    with open("/etc/os-release", "w") as f:
        f.write(ETAP_OS_RELEASE)
    print("  [+] Installed /etc/os-release (Pardus ETAP 23.4)")

    with open("/etc/lsb-release", "w") as f:
        f.write(ETAP_LSB_RELEASE)
    print("  [+] Installed /etc/lsb-release (Pardus ETAP 23.4)")

    if os.path.islink("/etc/issue") or os.path.exists("/etc/issue"):
        os.remove("/etc/issue")
    with open("/etc/issue", "w") as f:
        f.write(ETAP_ISSUE)
    print("  [+] Installed /etc/issue (Pardus GNU/Linux 23)")

    if os.path.islink("/etc/issue.net") or os.path.exists("/etc/issue.net"):
        os.remove("/etc/issue.net")
    with open("/etc/issue.net", "w") as f:
        f.write(ETAP_ISSUE_NET)
    print("  [+] Installed /etc/issue.net (Pardus GNU/Linux 23)")

    with open("/etc/debian_version", "w") as f:
        f.write(ETAP_DEBIAN_VERSION)
    print("  [+] Installed /etc/debian_version (12.4)")

    with open("/etc/pardus-release", "w") as f:
        f.write(ETAP_PARDUS_RELEASE)
    print("  [+] Installed /etc/pardus-release (Pardus 23.4)")

    # 4. Install universal lsb_release shim
    lsb_shim_path = "/usr/local/bin/lsb_release"
    with open(lsb_shim_path, "w") as f:
        f.write(LSB_RELEASE_SCRIPT)
    os.chmod(lsb_shim_path, 0o755)
    print(f"  [+] Installed universal lsb_release shim in {lsb_shim_path}")

    print("\n[✓] Pardus ETAP 23 spoofing successfully activated!")

def disable_spoof():
    require_root()
    print("[*] Reverting to native Fedora identification...")

    # 1. Restore os-release
    if os.path.exists("/etc/os-release"):
        os.remove("/etc/os-release")
    if os.path.exists(os.path.join(BACKUP_DIR, "os-release.symlink")):
        with open(os.path.join(BACKUP_DIR, "os-release.symlink")) as f:
            target = f.read().strip()
        os.symlink(target, "/etc/os-release")
    elif os.path.exists("/usr/lib/os-release"):
        os.symlink("../usr/lib/os-release", "/etc/os-release")
    print("  [+] Restored /etc/os-release -> ../usr/lib/os-release")

    # 2. Restore issue & issue.net
    for item in ["issue", "issue.net"]:
        path = f"/etc/{item}"
        if os.path.exists(path):
            os.remove(path)
        sym_backup = os.path.join(BACKUP_DIR, f"{item}.symlink")
        if os.path.exists(sym_backup):
            with open(sym_backup) as f:
                target = f.read().strip()
            os.symlink(target, path)
        elif os.path.exists(f"/usr/lib/{item}"):
            os.symlink(f"../usr/lib/{item}", path)
        print(f"  [+] Restored {path}")

    # 3. Remove Pardus-specific files
    for f in ["/etc/lsb-release", "/etc/debian_version", "/etc/pardus-release", "/usr/local/bin/lsb_release"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  [-] Removed {f}")

    print("\n[✓] Native Fedora identity restored!")

def print_status():
    active = is_spoof_active()
    status_str = "\033[92mACTIVE (Pardus ETAP 23)\033[0m" if active else "\033[93mINACTIVE (Fedora Native)\033[0m"
    print(f"=== Pardus ETAP Spoofing Status ===")
    print(f"Status: {status_str}")
    
    # Python distro check
    try:
        import distro
        print("\n--- Python Distro Telemetry ---")
        print(f"  distro.id():           {distro.id()}")
        print(f"  distro.name():         {distro.name()}")
        print(f"  distro.version():      {distro.version()}")
        print(f"  distro.codename():     {distro.codename()}")
        print(f"  distro.lsb_release:    {distro.lsb_release_info()}")
    except ImportError:
        print("  [!] python3-distro is not installed")

    # Hardware DMI
    print("\n--- Smart Board Hardware Info ---")
    sys_vendor = "Unknown"
    product_name = "Unknown"
    board_name = "Unknown"
    if os.path.exists("/sys/class/dmi/id/sys_vendor"):
        with open("/sys/class/dmi/id/sys_vendor") as f: sys_vendor = f.read().strip()
    if os.path.exists("/sys/class/dmi/id/product_name"):
        with open("/sys/class/dmi/id/product_name") as f: product_name = f.read().strip()
    if os.path.exists("/sys/class/dmi/id/board_name"):
        with open("/sys/class/dmi/id/board_name") as f: board_name = f.read().strip()
    print(f"  Vendor:                {sys_vendor}")
    print(f"  Product Name:          {product_name}")
    print(f"  Board Name:            {board_name}")

    # Primary MAC
    mac = get_primary_mac()
    print(f"  Primary MAC:           {mac or 'Not detected'}")

    # MEB Registration Check
    print("\n--- MEB EBA ETAP Central Verification ---")
    res = check_meb_registration(mac)
    if res.get("status") == "ok":
        d = res.get("data", {})
        if d.get("registered"):
            info = d.get("data", {})
            print(f"  Registration Status:   \033[92mREGISTERED WITH MEB\033[0m")
            print(f"  School Name:           {info.get('school_name')} (Code: {info.get('school_code')})")
            print(f"  Location:              {info.get('city_name')} / {info.get('town_name')}")
            print(f"  Unit / Room:           {info.get('unit_name')}")
            print(f"  Phase:                 {info.get('phase')}")
            print(f"  Board ID:              {info.get('board_id')}")
        else:
            print(f"  Registration Status:   \033[91mNOT REGISTERED\033[0m")
    else:
        print(f"  Registration Check:    Error connecting to MEB server: {res.get('error')}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "help"]:
        print("Usage: etap-spoof [enable|disable|status|meb-check]")
        print("Commands:")
        print("  enable     Spoof system as official Pardus ETAP 23 GNU/Linux")
        print("  disable    Revert system to native Fedora identity")
        print("  status     Display current spoofing status and MEB telemetry")
        print("  meb-check  Query MEB EBA central backend for board registration")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd in ["enable", "on", "start"]:
        enable_spoof()
    elif cmd in ["disable", "off", "revert", "stop"]:
        disable_spoof()
    elif cmd in ["status", "info"]:
        print_status()
    elif cmd in ["meb-check", "check"]:
        mac = get_primary_mac()
        res = check_meb_registration(mac)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"[!] Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
