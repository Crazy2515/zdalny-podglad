from flask import Flask, request, send_file
import os

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['screenshot']
    filename = "latest.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"Odebrano screena: {filepath}")
    return "OK"


@app.route('/view')
def view_screenshot():
    filepath = os.path.join(UPLOAD_FOLDER, "latest.png")
    if not os.path.exists(filepath):
        return "<h2>Brak screena! Czekam na pierwszy zrzut ekranu...</h2>", 200
    return send_file(filepath, mimetype='image/png')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
