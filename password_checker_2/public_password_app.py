# public_password_app.py
# pip install flask pyngrok

import socket
import os
import subprocess
import webbrowser
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__, static_folder="static", template_folder="templates")

def check_password_rules(pw: str):
    issues = []
    if len(pw) < 8:
        issues.append("❌ At least 8 characters required")
    if not any(c.isupper() for c in pw):
        issues.append("❌ Add uppercase letter")
    if not any(c.islower() for c in pw):
        issues.append("❌ Add lowercase letter")
    if not any(c.isdigit() for c in pw):
        issues.append("❌ Add number")
    if not any(c in "!@#$%^&*()-_=+[]{};:'\",.<>?/|\\`~" for c in pw):
        issues.append("❌ Add special symbol (!@#$)")
    return issues

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    data = request.get_json() or {}
    pw = data.get("password", "")
    issues = check_password_rules(pw)
    resp = jsonify({"valid": len(issues) == 0, "issues": issues})
    # Allow simple cross-origin use while testing (safe for dev)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

def find_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def kill_old_ngrok_processes():
    try:
        if os.name == "nt":  # Windows
            subprocess.call("taskkill /F /IM ngrok.exe", shell=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.call("pkill -f ngrok", shell=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def start_ngrok_tunnel(local_port: int):
    """Try to start an ngrok tunnel via pyngrok. Return public_url or None."""
    try:
        from pyngrok import ngrok
    except Exception:
        print("pyngrok not available — skipping ngrok tunnel.")
        return None

    # Kill any lingering ngrok to avoid ERR_NGROK_108
    kill_old_ngrok_processes()

    # Optionally set auth token from environment
    auth_token = os.getenv("NGROK_AUTHTOKEN")
    if auth_token:
        try:
            ngrok.set_auth_token(auth_token)
        except Exception as e:
            print("Warning: ngrok set_auth_token failed:", e)

    try:
        tunnel = ngrok.connect(local_port, "http")
        public_url = tunnel.public_url
        return public_url
    except Exception as e:
        print("ngrok tunnel failed:", e)
        return None

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    from flask import Flask, render_template, request, jsonify

    app.run(host="0.0.0.0", port=10000)  # Render will assign the port
