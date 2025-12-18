# dna_utils.py
"""
DNA token generation utilities (7-step algorithm) — improved.

Functions:
 - generate_full_hex(ip, hostname, mac, salt=None) -> full hex string
 - generate_dna_token(ip, hostname, mac, salt=None, random_window=True, window_len=8) -> 8-char token
 - helpers available for ACTG tokens (unchanged)
"""

from typing import Optional
import secrets

# --- helpers (same algorithm but normalized inputs) ---
def _normalize(ip: str, hostname: str, mac: str) -> tuple:
    """Normalize inputs for stable cross-platform results."""
    return ip.strip().lower(), hostname.strip().lower(), mac.strip().lower()

def _str_to_binary(s: str) -> str:
    return ''.join(f"{ord(c):08b}" for c in s)

def _binary_to_dna(bin_str: str) -> str:
    table = {'00':'A','01':'C','10':'G','11':'T'}
    if len(bin_str) % 2 != 0:
        bin_str = '0' + bin_str
    return ''.join(table[bin_str[i:i+2]] for i in range(0, len(bin_str), 2))

def _dna_to_base4_digits(dna: str) -> str:
    mapping = {'A':'0','C':'1','G':'2','T':'3'}
    return ''.join(mapping[b] for b in dna)

def _base4_to_int(base4: str) -> int:
    val = 0
    for ch in base4:
        val = val * 4 + int(ch)
    return val

def generate_full_hex(ip: str, hostname: str, mac: str, salt: Optional[str] = None) -> str:
    """
    Produce the full hexadecimal representation (not truncated).
    Always returns lowercase hex string of the big integer (no padding).
    """
    ip_n, host_n, mac_n = _normalize(ip, hostname, mac)
    combined = f"{ip_n}|{host_n}|{mac_n}"
    if salt:
        combined = combined + '|' + str(salt)
    binary = _str_to_binary(combined)
    dna = _binary_to_dna(binary)
    base4 = _dna_to_base4_digits(dna)
    n = _base4_to_int(base4)
    return format(n, 'x')  # lowercase hex

def generate_dna_token(ip: str, hostname: str, mac: str,
                       salt: Optional[str] = None,
                       random_window: bool = True,
                       window_len: int = 8,
                       full_hex: Optional[str] = None) -> dict:
    """
    Generate an 8-character (by default) DNA token.
    Returns dict with: { 'full_hex', 'token', 'offset', 'window_len' }.

    - random_window=True: chooses a cryptographically secure random offset inside the full_hex and returns window_len chars.
    - random_window=False: returns the last window_len characters (deterministic).
    - If you supply full_hex precomputed, it will use that (for tests).
    """
    if full_hex is None:
        full_hex = generate_full_hex(ip, hostname, mac, salt)
    # normalize hex to uppercase for token readability
    hex_upper = full_hex.upper()
    L = len(hex_upper)
    if window_len <= 0:
        raise ValueError("window_len must be positive")
    if L <= window_len:
        # if full hex shorter than window, pad left with zeros and return
        token = hex_upper.rjust(window_len, '0')[-window_len:]
        return {'full_hex': hex_upper, 'token': token, 'offset': 0, 'window_len': window_len}

    if random_window:
        max_offset = L - window_len
        offset = secrets.randbelow(max_offset + 1)  # inclusive
    else:
        offset = L - window_len

    token = hex_upper[offset:offset + window_len]
    return {'full_hex': hex_upper, 'token': token, 'offset': offset, 'window_len': window_len}

# --- ACTG helpers (unchanged; kept for file-tokenizer or optional use) ---
import hashlib
def _bytes_to_actg(b: bytes) -> str:
    table = {'00': 'A', '01': 'C', '10': 'G', '11': 'T'}
    bits = ''.join(f"{byte:08b}" for byte in b)
    if len(bits) % 2 != 0:
        bits = '0' + bits
    return ''.join(table[bits[i:i+2]] for i in range(0, len(bits), 2))

def generate_actg_token_from_string(s: str, length: Optional[int] = 32) -> str:
    digest = hashlib.sha256(s.encode('utf-8')).digest()
    actg = _bytes_to_actg(digest)
    return actg if length is None else actg[:length]

def generate_actg_token_for_file(path: str, length: Optional[int] = 32) -> str:
    with open(path, 'rb') as f:
        data = f.read()
    digest = hashlib.sha256(data).digest()
    actg = _bytes_to_actg(digest)
    return actg if length is None else actg[:length]

# quick demo when run directly
if __name__ == '__main__':
    demo = generate_dna_token('10.50.4.8','HD_DN01','10:78:D2:55:95:A8', salt='epoch-2025-10-16')
    print("Full hex:", demo['full_hex'])
    print("Token:", demo['token'], "offset:", demo['offset'])
