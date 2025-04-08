from flask import Flask, request, send_file
import os

app = Flask(__name__)
UPLOAD_FOLDER = "screens"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return '''
        <h1>👀 Zdalny Podgląd</h1>
        <p>Przejdź do <a href="/view">/view</a>, aby zobaczyć ostatni zrzut ekranu.</p>
    '''

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

    return f'''
        <html>
        <head>
            <meta http-equiv="refresh" content="3">
            <title>Podgląd ekranu</title>
        </head>
        <body style="text-align:center; background-color:#111;">
            <h2 style="color:white;">Zdalny ekran:</h2>
            <img src="/static/{filename}" style="max-width:95%; border:2px solid white;" />
        </body>
        </html>
    '''

# Kopiujemy plik do katalogu static, aby można go było łatwo serwować
@app.after_request
def move_screenshot_to_static(response):
    src = os.path.join(UPLOAD_FOLDER, "latest.png")
    dst = os.path.join(app.static_folder, "latest.png")
    if os.path.exists(src):
        os.makedirs(app.static_folder, exist_ok=True)
        try:
            if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                with open(src, "rb") as fsrc:
                    with open(dst, "wb") as fdst:
                        fdst.write(fsrc.read())
        except Exception as e:
            print("Błąd kopiowania do static:", e)
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
