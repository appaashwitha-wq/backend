"""Enhanced Flask UI with Bootstrap styling and better organization."""
import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from authority import REGISTRY, register_node, verify_node, rotate_tokens, is_valid_ip, is_valid_mac
import csv
from collections import deque
from functools import wraps

# Configure logging to file and console with more detail
log_file = os.path.join(os.path.dirname(__file__), 'flask_app.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s\nFile: %(pathname)s:%(lineno)d\nFunction: %(funcName)s\n',
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # 'w' mode to start fresh
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info(f"Flask app starting. Template folder: {os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))}")
logger.info(f"Available templates: {os.listdir(os.path.join(os.path.dirname(__file__), 'templates'))}")

app = Flask(__name__, 
            template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')))
app.secret_key = os.urandom(24)  # Generate secure secret key

# Template names
TEMPLATE_NODES = 'nodes.html'
TEMPLATE_VERIFY = 'verify.html'
TEMPLATE_REGISTER = 'register.html'
TEMPLATE_ROTATE = 'rotate.html'
TEMPLATE_ERROR = 'error.html'

def get_current_time():
    """Get current time in UTC."""
    return datetime.utcnow()  # Use naive UTC time consistently

def parse_datetime(dt_str):
    """Parse datetime string to naive UTC datetime."""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)  # Make naive
    return dt

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {f.__name__}: {str(e)}")
            try:
                # Try to render error template
                return render_template(TEMPLATE_ERROR, error="An internal server error occurred."), 500
            except Exception:
                # If error template fails, return basic error
                logger.exception("Error template failed")
                return "Internal Server Error", 500
    return wrapper

# Register error handler for all 500 errors
@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled error")
    try:
        return render_template(TEMPLATE_ERROR, error="An internal server error occurred."), 500
    except Exception:
        return "Internal Server Error", 500

# Keep track of recent verifications (last 5)
recent_verifications = deque(maxlen=5)

def read_registry():
    """Read registry and compute node status and age."""
    nodes = []
    try:
        with REGISTRY.open('r', newline='') as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Parse created timestamp (ensure naive UTC)
                created = parse_datetime(r['created'])
                current_time = get_current_time()
                age = current_time - created
                
                # Compute status: active (< 3 days), warning (3-6 days), error (>6 days)
                if age < timedelta(days=3):
                    status = 'active'
                elif age < timedelta(days=6):
                    status = 'warning'
                else:
                    status = 'error'
                
                nodes.append({
                    'ip': r['ip'],
                    'hostname': r['hostname'],
                    'mac': r['mac'],
                    'token': r['token'],
                    'status': status,
                    'age': f"{age.days}d {age.seconds//3600}h ago"
                })
    except FileNotFoundError:
        pass
    return nodes

@app.route('/')
@handle_errors
def index():
    """Show registered nodes with status."""
    try:
        nodes = read_registry()
        logger.info(f"Rendering index with {len(nodes)} nodes")
        return render_template(TEMPLATE_NODES, nodes=nodes)
    except Exception as e:
        logger.exception("Error in index route")
        raise

@app.route('/verify', methods=['GET', 'POST'])
@handle_errors
def verify():
    """Show verification form and handle submissions."""
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        hostname = request.form.get('hostname', '')
        mac = request.form.get('mac', '')
        
        # Validate inputs
        if not is_valid_ip(ip):
            flash('Invalid IP address format', 'danger')
        elif not is_valid_mac(mac):
            flash('Invalid MAC address format', 'danger')
        else:
            success = verify_node(ip, hostname, mac)
            result = 'Node identity verified successfully!' if success else 'Verification failed'
            
            # Record verification
            recent_verifications.appendleft({
                'hostname': hostname,
                'ip': ip,
                'success': success,
                'time': get_current_time().strftime('%H:%M:%S')
            })
            
            return render_template(TEMPLATE_VERIFY,
                                result=result,
                                success=success,
                                recent_verifications=recent_verifications)
    
    return render_template(TEMPLATE_VERIFY, recent_verifications=recent_verifications)

@app.route('/register', methods=['GET', 'POST'])
@handle_errors
def register():
    """Show registration form and handle submissions."""
    message = None
    
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        hostname = request.form.get('hostname', '')
        mac = request.form.get('mac', '')
        
        try:
            if not is_valid_ip(ip):
                raise ValueError('Invalid IP address format')
            if not is_valid_mac(mac):
                raise ValueError('Invalid MAC address format')
            if not hostname.strip():
                raise ValueError('Hostname is required')
            
            token = register_node(ip, hostname, mac)
            logger.info(f"Successfully registered node {hostname} ({ip})")
            return render_template(TEMPLATE_REGISTER,
                                message={'type': 'success',
                                        'text': f'Node registered successfully! Token: {token}'})
        
        except ValueError as e:
            logger.warning(f"Node registration failed: {str(e)}")
            return render_template(TEMPLATE_REGISTER,
                                message={'type': 'danger',
                                        'text': str(e)})
        except Exception as e:
            logger.exception("Unexpected error during node registration")
            return render_template(TEMPLATE_REGISTER,
                                message={'type': 'danger',
                                        'text': "An internal error occurred during registration"})
    
    return render_template(TEMPLATE_REGISTER, message=message)

@app.route('/rotate', methods=['GET', 'POST'])
@handle_errors
def rotate():
    """Show rotation form and handle submissions."""
    rotation_history = []  # Will implement rotation history tracking if needed
    
    if request.method == 'POST':
        try:
            days = int(request.form.get('days', 7))
            if not 1 <= days <= 365:
                raise ValueError('Days must be between 1 and 365')
            
            salt = rotate_tokens(days)
            current_time = get_current_time()
            return render_template(TEMPLATE_ROTATE,
                                message={'type': 'success',
                                        'text': f'Tokens rotated successfully using salt: {salt}'},
                                current_epoch=current_time.date(),
                                rotation_history=rotation_history)
        
        except (ValueError, TypeError) as e:
            current_time = get_current_time()
            return render_template(TEMPLATE_ROTATE,
                                message={'type': 'danger',
                                        'text': str(e)},
                                current_epoch=current_time.date(),
                                rotation_history=rotation_history)
    
    return render_template(TEMPLATE_ROTATE,
                         current_epoch=get_current_time().date(),
                         rotation_history=rotation_history)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)