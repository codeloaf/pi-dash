from flask import Flask, jsonify, send_from_directory, request, Blueprint
from markupsafe import escape
import requests
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# -- App Setup & Configuration --
APP_ROOT = os.path.dirname(os.path.realpath(__file__))

# Load configurations
with open(os.path.join(APP_ROOT, 'config.json')) as f:
    config = json.load(f)

with open(os.path.join(APP_ROOT, 'manifest.json')) as f:
    manifest_data = json.load(f)

with open(os.path.join(APP_ROOT, 'index.html')) as f:
    index_template = f.read()

with open(os.path.join(APP_ROOT, 'sw.js')) as f:
    sw_template = f.read()

# Prepare path variables
base_path_config = config.get('base_path', '/')
url_prefix = base_path_config
if url_prefix != '/' and url_prefix.endswith('/'):
    url_prefix = url_prefix[:-1]

html_base = base_path_config
if not html_base.endswith('/'):
    html_base += '/'

bp = Blueprint('pi-dash', __name__)
pihole_sessions = {}

# -- Pi-hole Authentication --
def authenticate_and_get_sid(address, password):
    auth_url = f"{address}/api/auth"
    payload = {"password": password}
    try:
        response = requests.post(auth_url, json=payload, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            new_sid = data.get("session", {}).get("sid")            
            if new_sid:
                print(f"Successfully authenticated with {address} and got new SID.")
                return new_sid
            elif data.get("session", {}).get("message") == "no password set":
                print(f"Pi-hole at {address} has no password set.")
                return "NO_PASSWORD"
            else:
                print(f"Authentication with {address} returned 200 OK but no SID found. Response: {data}")
                return None
        elif response.status_code == 401:
            print(f"Authentication failed for {address}: Incorrect Password (401 Unauthorized). Please check your password in config.json.")
            return None
        else:
            print(f"Authentication failed for {address} with status code {response.status_code}. Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"A network error occurred during authentication with {address}: {e}")
        return None

# -- Frontend Routes --
@bp.route('/')
def index():
    # Use cached templates and inject dynamic data
    icon_url = ''
    if manifest_data.get('icons'):
        icon_url = manifest_data['icons'][0].get('src', '')
    
    # Securely inject base href and icon URL
    base_tag = f'<base href="{escape(html_base)}">' # Inject base tag with escaped HTML to prevent XSS
    temp_html = index_template.replace('<head>', f'<head>\n    {base_tag}')
    final_html = temp_html.replace('{{ICON_URL}}', escape(icon_url))
    
    return final_html

@bp.route('/manifest.json')
def serve_manifest():
    # Use cached manifest and update start_url
    manifest_copy = manifest_data.copy()
    manifest_copy['start_url'] = html_base
    return jsonify(manifest_copy)

@bp.route('/sw.js')
def serve_sw():
    # Use cached service worker and inject cache URL
    sw_content = sw_template.replace('{{CACHE_URL}}', html_base)
    return sw_content, 200, {'Content-Type': 'application/javascript'}

@bp.route('/css/<path:path>')
def send_css(path):
    return send_from_directory(os.path.join(APP_ROOT, 'css'), path)

@bp.route('/js/<path:path>')
def send_js(path):
    return send_from_directory(os.path.join(APP_ROOT, 'js'), path)

@bp.route('/favicon.ico')
def favicon():
    return '', 204

# -- API Routes --
@bp.route('/config')
def get_config():
    return jsonify(config)

def get_pihole_data(address, sid):
    url = f"{address}/api/stats/summary"
    if sid == "NO_PASSWORD":
        return requests.get(url, timeout=10, verify=False)
    else:
        headers = {'X-FTL-SID': sid}
        return requests.get(url, headers=headers, timeout=10, verify=False)

@bp.route('/proxy')
def proxy():
    pihole_name = request.args.get('name')
    if not pihole_name:
        return jsonify({"error": "Pi-hole name not specified"}), 400

    pihole_config = next((p for p in config['piholes'] if p['name'] == pihole_name and p['enabled']), None)
    if not pihole_config:
        return jsonify({"error": f"Pi-hole '{pihole_name}' not found or not enabled"}), 404

    address = pihole_config['address']
    password = pihole_config['password']
    sid = pihole_sessions.get(pihole_name)

    if not sid:
        sid = authenticate_and_get_sid(address, password)
        if not sid:
            return jsonify({"error": f"Authentication failed for Pi-hole '{pihole_name}'"}), 500
        pihole_sessions[pihole_name] = sid

    try:
        response = get_pihole_data(address, sid)
        if response.status_code == 401 and sid != "NO_PASSWORD":
            print(f"SID for Pi-hole '{pihole_name}' expired. Re-authenticating...")
            sid = authenticate_and_get_sid(address, password)
            if not sid:
                return jsonify({"error": f"Re-authentication failed for Pi-hole '{pihole_name}'"}), 500
            pihole_sessions[pihole_name] = sid
            response = get_pihole_data(address, sid)

        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# -- App Initialization --
app.register_blueprint(bp, url_prefix=url_prefix)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
