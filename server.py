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
    filename = "latest.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return "<h2>Brak screena! Czekam na pierwszy zrzut ekranu...</h2>", 200
    return send_file(filepath, mimetype='image/png')

@app.route('/')
def index():
    return '''
        <h1>👀 Zdalny Podgląd</h1>
        <p>Przejdź do <a href="/view">/view</a>, aby zobaczyć ostatni ekran.</p>
    '''

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
