from flask import Flask, render_template, send_from_directory, jsonify
import os
import json

app = Flask(__name__, static_folder='static', template_folder='templates')

# === Route: Dashboard page ===
@app.route('/')
def home():
    return render_template('dash.html')

# === Route: Serve triage JSON data ===
@app.route('/data/page_triage_log.json')
def triage_data():
    try:
        data_path = os.path.join('data', 'page_triage_log.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Route: Serve visuals ===
@app.route('/static/visuals/<path:filename>')
def serve_visuals(filename):
    return send_from_directory(os.path.join(app.static_folder, 'visuals'), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
