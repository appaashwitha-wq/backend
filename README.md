# backend
SSCDNA enhances security in Apache Spark clusters using DNA cryptography for dynamic node authentication. Node attributes (IP, MAC, hostname) generate unique DNA-based tokens that are periodically rotated. A Flask server manages authentication, blocks malicious nodes, and ensures secure, low-overhead cluster access.
