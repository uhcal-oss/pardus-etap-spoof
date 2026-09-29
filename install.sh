#!/usr/bin/env bash
set -e

# Pardus ETAP Spoof Installer
# Urla Hakan Çeken Anadolu Lisesi (@uhcal-oss)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="/usr/local/bin/etap-spoof"

echo "=== Pardus ETAP 23 Spoof Installer ==="

if [ "$EUID" -ne 0 ]; then
    echo "[!] Please run with sudo: sudo ./install.sh"
    exit 1
fi

# Ensure python3-distro is installed
if ! python3 -c "import distro" &>/dev/null; then
    echo "[*] Installing python3-distro..."
    dnf install -y python3-distro
fi

echo "[*] Installing etap-spoof to ${BIN_PATH}..."
install -m 0755 "${SCRIPT_DIR}/etap-spoof.py" "${BIN_PATH}"

echo "[✓] Installation complete!"
echo "Usage:"
echo "  sudo etap-spoof enable   - Activate Pardus ETAP 23 identity"
echo "  sudo etap-spoof disable  - Revert to native Fedora identity"
echo "  etap-spoof status        - View spoofing & MEB registration status"
