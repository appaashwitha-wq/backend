"""
Node client that interacts with the SSCDNA Authority API (Flask).

Demonstrates:
1. Register nodes
2. Verify legitimate node
3. Attempt fake node registration
4. Rotate tokens
"""

import requests

BASE_URL = "http://127.0.0.1:5001"  # Flask API URL

# Node definitions
nodes = [
    {"ip": "192.168.1.5", "hostname": "worker1", "mac": "A4:5E:60:22:AA:01"},
    {"ip": "192.168.1.6", "hostname": "worker2", "mac": "A4:5E:60:22:BB:02"},
]

def register_node(node):
    resp = requests.post(f"{BASE_URL}/register", json=node)
    print("📨 Registration Response:")
    try:
      print(resp.json())
    except Exception as e:
      print("⚠️ Failed to parse JSON:", resp.text)

def verify_node(node):
    resp = requests.post(f"{BASE_URL}/verify", json=node)
    print("📨 Verification Response:")
    try:
      print(resp.json())
    except Exception as e:
      print("⚠️ Failed to parse JSON:", resp.text)

def rotate_tokens(days=7):
    resp = requests.post(f"{BASE_URL}/rotate", json={"days": days})
    print("📨 Rotation Response:")
    try:
      print(resp.json())
    except Exception as e:
      print("⚠️ Failed to parse JSON:", resp.text)  

def run_demo():
    print("🧩 Step 1: Register Nodes")
    for n in nodes:
        register_node(n)

    print("\n🔍 Step 2: Verify Legit Node")
    verify_node(nodes[0])

    print("\n🚫 Step 3: Fake Node Attempt")
    fake_node = {"ip":"10.0.0.9", "hostname":"worker1", "mac":"FF:FF:FF:FF:FF:FF"}
    verify_node(fake_node)

    print("\n♻️ Step 4: Rotate Tokens")
    rotate_tokens(7)

if __name__ == "__main__":
    run_demo()
