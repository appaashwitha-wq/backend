"""
Authority service: register nodes, verify tokens, rotate tokens (CSV storage).

Usage (CLI):
  python authority.py register --ip IP --hostname NAME --mac MAC
  python authority.py verify --ip IP --hostname NAME --mac MAC
  python authority.py rotate --days N
"""
import csv
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dna_utils import generate_dna_token


def is_valid_ip(ip: str) -> bool:
    # Very simple IPv4 validation
    pattern = r'^((25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(25[0-5]|2[0-4]\d|1?\d?\d)$'
    return re.match(pattern, ip) is not None


def is_valid_mac(mac: str) -> bool:
    # Accepts formats like AA:BB:CC:DD:EE:FF or AABB.CCDD.EEFF or AABBCCDDEEFF
    mac = mac.strip()
    patterns = [r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', r'^[0-9A-Fa-f]{12}$', r'^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$']
    return any(re.match(p, mac) for p in patterns)

REGISTRY = Path(__file__).parent / 'registry.csv'

def _ensure_registry():
    if not REGISTRY.exists():
        with REGISTRY.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ip','hostname','mac','token','created'])

def register_node(ip: str, hostname: str, mac: str, salt: Optional[str]=None):
    _ensure_registry()
    if not is_valid_ip(ip):
        raise ValueError(f'Invalid IP address: {ip}')
    if not is_valid_mac(mac):
        raise ValueError(f'Invalid MAC address: {mac}')
    token = generate_dna_token(ip, hostname, mac, salt)
    now = datetime.utcnow().isoformat()
    # check duplicates
    rows = []
    with REGISTRY.open('r', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # prevent duplicate exact ip/mac/hostname
    for r in rows:
        if r['ip']==ip and r['mac']==mac and r['hostname']==hostname:
            print('Node already registered. Updating token and timestamp.')
            r['token']=token
            r['created']=now
            break
    else:
        rows.append({'ip':ip,'hostname':hostname,'mac':mac,'token':token,'created':now})

    with REGISTRY.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ip','hostname','mac','token','created'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Registered {hostname} -> {token}")
    return token

def verify_node(ip: str, hostname: str, mac: str, salt: Optional[str]=None) -> bool:
    _ensure_registry()
    if not is_valid_ip(ip):
        print(f'Invalid IP address: {ip}')
        return False
    if not is_valid_mac(mac):
        print(f'Invalid MAC address: {mac}')
        return False
    recomputed = generate_dna_token(ip, hostname, mac, salt)
    with REGISTRY.open('r', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['hostname']==hostname:
                stored = r['token']
                if stored == recomputed and r['ip']==ip and r['mac']==mac:
                    print('Verification success')
                    return True
                else:
                    print('Verification failed: token or identity mismatch')
                    print('Stored:', stored, 'Recomputed:', recomputed)
                    return False
    print('Hostname not registered')
    return False

def rotate_tokens(days: int =7, salt_prefix: str='epoch'):
    """Simulate rotation by re-registering nodes with a salt based on days.

    For demo, we create a salt string like 'epoch-<date>' using UTC today + days offset.
    """
    _ensure_registry()
    rows = []
    with REGISTRY.open('r', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # compute new salt (simulate advancing epoch by `days` days)
    epoch_date = (datetime.utcnow() + timedelta(days=days)).date().isoformat()
    salt = f"{salt_prefix}-{epoch_date}"

    for r in rows:
        new_token = generate_dna_token(r['ip'], r['hostname'], r['mac'], salt)
        r['token'] = new_token
        r['created'] = datetime.utcnow().isoformat()

    with REGISTRY.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ip','hostname','mac','token','created'])
        writer.writeheader()
        writer.writerows(rows)

    print(f'Rotated tokens using salt="{salt}"')
    return salt


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    p_reg = sub.add_parser('register')
    p_reg.add_argument('--ip', required=True)
    p_reg.add_argument('--hostname', required=True)
    p_reg.add_argument('--mac', required=True)

    p_ver = sub.add_parser('verify')
    p_ver.add_argument('--ip', required=True)
    p_ver.add_argument('--hostname', required=True)
    p_ver.add_argument('--mac', required=True)

    p_rot = sub.add_parser('rotate')
    p_rot.add_argument('--days', type=int, default=7)

    args = parser.parse_args()
    if args.cmd=='register':
        register_node(args.ip, args.hostname, args.mac)
    elif args.cmd=='verify':
        verify_node(args.ip, args.hostname, args.mac)
    elif args.cmd=='rotate':
        rotate_tokens(args.days)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
