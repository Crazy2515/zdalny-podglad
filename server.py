from flask import Flask, request, send_file, jsonify, render_template_string
import os
import datetime
import json

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
COMMAND_FILE = "command.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/view")
def view():
    return render_template_string('''
        <html>
        <head>
            <title>Zdalny Podgląd</title>
            <style>
                body { background: #111; color: white; text-align: center; font-family: sans-serif; }
                img { max-width: 90%; border: 2px solid white; margin: 10px auto; display: block; }
                .panel { margin-top: 20px; }
                button { margin: 5px; padding: 10px 20px; font-size: 16px; cursor: pointer; }
                .status-box { margin-top: 20px; padding: 10px; background: #222; border: 1px solid #555; display: inline-block; }
            </style>
            <script>
                async function sendCommand(action) {
                    await fetch("/command", {
                        method: "POST",
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: "action=" + action
                    });
                    updateStatus();
                }

                async function updateStatus() {
                    const res = await fetch("/command");
                    const data = await res.json();
                    document.getElementById("status").innerText = `Status: ${data.paused ? 'Zatrzymany' : 'Aktywny'} | Interwał: ${data.interval}s`;
                }

                setInterval(updateStatus, 3000);
                window.onload = updateStatus;
            </script>
        </head>
        <body>
            <h1>📸 Podgląd Ekranu</h1>
            <img src="/latest" />

            <div class="panel">
                <button onclick="sendCommand('one_shot')">Zrób screena teraz</button>
                <button onclick="sendCommand('pause')">Pauza</button>
                <button onclick="sendCommand('resume')">Start</button>
                <button onclick="sendCommand('faster')">Szybciej</button>
                <button onclick="sendCommand('slower')">Wolniej</button>
        <div class="status-box" id="status">
                Status: ładowanie...
            </div>
        </body>
        </html>
    ''')

@app.route("/latest")
def latest():
    files = sorted(os.listdir(UPLOAD_FOLDER))
    if not files:
        return "Brak screenów.", 404
    return send_file(os.path.join(UPLOAD_FOLDER, files[-1]), mimetype='image/png')

@app.route("/upload", methods=['POST'])
def upload():
    file = request.files['screenshot']
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{now}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return "OK"

@app.route("/history")
def history():
    files = sorted(os.listdir(UPLOAD_FOLDER))
    images = "".join([f'<li><a href="/screens/{f}" target="_blank">{f}</a></li>' for f in files])
    return f"<h1>Historia Screenów</h1><ul>{images}</ul>"

@app.route("/screens/<filename>")
def get_screen(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), mimetype='image/png')

@app.route("/command", methods=['GET', 'POST'])
def command():
    if request.method == 'POST':
        action = request.form.get("action")
        data = {}
        if os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "r") as f:
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

        with open(COMMAND_FILE, "w") as f:
            json.dump(data, f)

        return "OK"
    else:
        if not os.path.exists(COMMAND_FILE):
            return jsonify({"paused": False, "interval": 5})
        with open(COMMAND_FILE, "r") as f:
            return jsonify(json.load(f))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)       </div>

         
