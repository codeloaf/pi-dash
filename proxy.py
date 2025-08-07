from flask import Flask, jsonify, send_from_directory, request
import requests
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

APP_ROOT = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(APP_ROOT, 'config.json')) as f:
    config = json.load(f)

pihole_sessions = {}

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

@app.route('/')
def index():
    return send_from_directory(APP_ROOT, 'index.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(APP_ROOT, 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(APP_ROOT, 'sw.js', mimetype='application/javascript')

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory(os.path.join(APP_ROOT, 'css'), path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory(os.path.join(APP_ROOT, 'js'), path)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/config')
def get_config():
    return jsonify(config)

def get_pihole_data(address, sid):
    url = f"{address}/api/stats/summary"
    headers = {'X-FTL-SID': sid}
    return requests.get(url, headers=headers, timeout=10, verify=False)

@app.route('/proxy')
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
        if response.status_code == 401:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
