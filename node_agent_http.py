# node_agent_http.py
"""
Node agent (HTTP mode): calls Authority REST API endpoints to register and verify.
Usage:
  python node_agent_http.py register --ip ... --hostname ... --mac ... --url http://127.0.0.1:5001
  python node_agent_http.py verify --ip ... --hostname ... --mac ... --url http://127.0.0.1:5001
"""
import argparse
import requests
import sys

def do_register(base_url, ip, hostname, mac, salt=None):
    payload = {"ip": ip, "hostname": hostname, "mac": mac}
    if salt is not None:
        payload['salt'] = salt
    r = requests.post(f"{base_url.rstrip('/')}/api/register", json=payload, timeout=5)
    try:
        data = r.json()
    except Exception:
        print("Non-JSON response", r.text)
        return False
    if r.status_code in (200, 201) and data.get('status') == 'ok':
        print(f"Registered. Token: {data.get('token')}")
        return True
    else:
        print("Register failed:", data.get('error', r.text))
        return False

def do_verify(base_url, ip, hostname, mac, salt=None):
    payload = {"ip": ip, "hostname": hostname, "mac": mac}
    if salt is not None:
        payload['salt'] = salt
    r = requests.post(f"{base_url.rstrip('/')}/api/verify", json=payload, timeout=5)
    data = r.json() if r.headers.get('content-type','').startswith('application/json') else {}
    if r.status_code == 200 and data.get('status') == 'ok':
        print("Verified" if data.get('verified') else "Not verified")
        return data.get('verified', False)
    else:
        print("Verify failed:", data.get('error', r.text))
        return False

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    p_reg = sub.add_parser('register')
    p_reg.add_argument('--ip', required=True)
    p_reg.add_argument('--hostname', required=True)
    p_reg.add_argument('--mac', required=True)
    p_reg.add_argument('--url', default='http://127.0.0.1:5001')

    p_ver = sub.add_parser('verify')
    p_ver.add_argument('--ip', required=True)
    p_ver.add_argument('--hostname', required=True)
    p_ver.add_argument('--mac', required=True)
    p_ver.add_argument('--url', default='http://127.0.0.1:5001')

    args = parser.parse_args()
    if args.cmd == 'register':
        success = do_register(args.url, args.ip, args.hostname, args.mac)
        sys.exit(0 if success else 2)
    elif args.cmd == 'verify':
        ok = do_verify(args.url, args.ip, args.hostname, args.mac)
        sys.exit(0 if ok else 2)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
