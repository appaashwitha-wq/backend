"""Demo script to showcase registration, verification, fake attempt, and rotation."""
from authority import register_node, verify_node, rotate_tokens

def run_demo():
    print('--- Demo: Register two nodes ---')
    token1 = register_node('192.168.1.5','worker1','A4:5E:60:22:AA:01')
    token2 = register_node('192.168.1.6','worker2','A4:5E:60:22:BB:02')

    print('\n--- Verify legitimate node ---')
    verify_node('192.168.1.5','worker1','A4:5E:60:22:AA')

    print('\n--- Fake node attempt (same hostname, different MAC) ---')
    verify_node('10.0.0.9','worker1','FF:FF:FF:FF:FF:FF')

    print('\n--- Rotate tokens (simulate 7 days) ---')
    rotate_tokens(7)

    print('\n--- Verify after rotation (old identity should fail if salt used) ---')
    # For this simple demo, rotation replaced tokens in registry. A verify with same ip/mac will pass
    verify_node('192.168.1.5','worker1','A4:5E:60:22:AA:01')

if __name__ == '__main__':
    run_demo()
