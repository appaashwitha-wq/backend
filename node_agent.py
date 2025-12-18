"""
Node agent to collect IP, MAC, and Hostname and interact with authority functions.

For demo purposes, the agent accepts values via CLI flags instead of reading system interfaces.
"""
import argparse
from dna_utils import generate_dna_token
from authority import register_node, verify_node, is_valid_ip, is_valid_mac

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

    args = parser.parse_args()
    if args.cmd=='register':
        # local token for node
        if not is_valid_ip(args.ip):
            print('Invalid IP format')
            return
        if not is_valid_mac(args.mac):
            print('Invalid MAC format')
            return
        token = generate_dna_token(args.ip, args.hostname, args.mac)
        print(f'Node local token: {token}')
        # call authority register
        register_node(args.ip, args.hostname, args.mac)
    elif args.cmd=='verify':
        print('Node requesting verification...')
        if not is_valid_ip(args.ip) or not is_valid_mac(args.mac):
            print('Invalid IP or MAC format')
            return
        ok = verify_node(args.ip, args.hostname, args.mac)
        print('Verified' if ok else 'Not verified')
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
