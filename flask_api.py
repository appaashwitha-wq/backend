from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import hashlib
import json
import os
from datetime import datetime
from dna_utils import generate_dna_token  # assuming the function is named same

app = Flask(__name__)
CORS(app)

REGISTRY_FILE = "node_registry.json"
WINDOW_LEN = 8  # length of token window


# -----------------------------
# Utility Functions
# -----------------------------
def _read_registry():
    """Read existing registered nodes from JSON file."""
    if not os.path.exists(REGISTRY_FILE):
        return []
    with open(REGISTRY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write_registry(data):
    """Write nodes to JSON file."""
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)



# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def home():
    rows = _read_registry()
    return render_template("home.html", nodes=rows)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new node via form (HTML) or JSON (API)."""
    if request.method == 'POST':
        # Support both form and JSON requests
        if request.is_json:
            data = request.get_json()
            ip = data.get('ip')
            hostname = data.get('hostname')
            mac = data.get('mac')
        else:
            ip = request.form.get('ip')
            hostname = request.form.get('hostname')
            mac = request.form.get('mac')

        # Validate input
        if not ip or not hostname or not mac:
            msg = "All fields are required!"
            if request.is_json:
                return jsonify({"error": msg}), 400
            return render_template("register.html", message={"type": "danger", "text": msg})

        # Generate DNA token
        dna_dict = generate_dna_token(ip, hostname, mac, window_len=WINDOW_LEN)
        full_hex = dna_dict['full_hex']
        token = dna_dict['token']
        offset = dna_dict['offset']

        created = datetime.utcnow().isoformat()
        rows = _read_registry()

        # Check if node already exists
        for r in rows:
            if r['ip'] == ip and r['hostname'] == hostname and r['mac'] == mac:
                r.update({
                    'full_hex': full_hex,
                    'token': token,
                    'offset': offset,
                    'window_len': WINDOW_LEN,
                    'created': created
                })
                _write_registry(rows)
                msg = f"Node re-registered successfully! Token: {token}"
                if request.is_json:
                    return jsonify({"message": msg, "token": token})
                return render_template("register.html", message={"type": "success", "text": msg})

        # Add new node
        rows.append({
            'ip': ip, 'hostname': hostname, 'mac': mac,
            'full_hex': full_hex,
            'token': token,
            'offset': offset,
            'window_len': WINDOW_LEN,
            'created': created
        })
        _write_registry(rows)

        msg = f"Node registered successfully! Token: {token}"
        if request.is_json:
            return jsonify({"message": msg, "token": token})
        return render_template("register.html", message={"type": "success", "text": msg})

    # GET request → show registration page
    return render_template("register.html")



@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify if a node exists using hostname and token."""
    if request.method == 'POST':
        hostname = request.form.get('hostname')
        token = request.form.get('token')

        if not hostname or not token:
            return render_template(
                "verify.html",
                message={"type": "danger", "text": "Hostname and token are required!"}
            )

        rows = _read_registry()
        for r in rows:
            # Check if hostname exists and token matches
            stored_token = r.get('full_hex', '')[r.get('offset', 0): r.get('offset', 0) + r.get('window_len', 8)]
            if r['hostname'] == hostname and stored_token == token:
                return render_template(
                    "verify.html",
                    message={"type": "success", "text": f"✅ Node verified successfully!"}
                )

        return render_template(
            "verify.html",
            message={"type": "danger", "text": f"❌ Node verification failed!"}
        )

    # GET → display verification page
    return render_template("verify.html")
@app.route('/rotate', methods=['GET'])
def rotate():
    """Simulate token rotation for all nodes."""
    rows = _read_registry()

    for r in rows:
        # Deterministic rotation (or you can randomize by random_window=True)
        dna_dict = generate_dna_token(r['ip'], r['hostname'], r['mac'],
                                       random_window=False, window_len=WINDOW_LEN)
        r['token'] = dna_dict['token']
        r['full_hex'] = dna_dict['full_hex']
        r['offset'] = dna_dict['offset']
        r['window_len'] = dna_dict['window_len']
        r['created'] = datetime.utcnow().isoformat()

    _write_registry(rows)
    return render_template("rotate.html",
                           message={"type": "info", "text": "🔁 Tokens rotated successfully for all nodes!"})

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
