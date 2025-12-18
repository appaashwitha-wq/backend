# SSCDNA — Secure Spark Cluster using DNA Cryptography (Prototype)

This prototype demonstrates generating a DNA-based token from node identity (IP, Hostname, MAC), registering nodes with an Authority, verifying them, and rotating tokens.

Files:
- `dna_utils.py` — DNA token generator
 - `file_tokenizer.py` — CLI to generate ACTG tokens for files (new)
- `authority.py` — Registry (CSV) and operations: register, verify, rotate
- `node_agent.py` — Node-side CLI to register and verify
- `demo.py` — Script showing registration, verification, fake attempt, rotation
- `registry.csv` — CSV storage (created at runtime)
- `architecture.svg` — Simple architecture diagram

Run demo:

```bash
python demo.py
```

Generate ACTG tokens for repository files (new):

```bash
python file_tokenizer.py --length 32
```

This will print a 32-base ACTG token for each file in the project using SHA-256 -> 2-bit mapping.

Notes:
- Token generation follows the exact 7-step algorithm specified in the project description.
- Rotation uses a salt derived from simulated epoch date to change tokens every N days.
