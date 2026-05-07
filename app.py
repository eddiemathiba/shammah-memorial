from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import uuid
import qrcode
import os

app = Flask(__name__)

DB_FILE = 'obituaries.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS obituaries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        birth_date TEXT,
        death_date TEXT,
        funeral_date TEXT,
        biography TEXT,
        service_programme TEXT,
        photo_url TEXT
    )''')
    conn.commit()
    conn.close()

# ====================== HOME ======================
@app.route('/')
def index():
    return render_template('index.html')

# ====================== ADMIN ======================
@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    obits = [dict(row) for row in conn.execute('SELECT * FROM obituaries ORDER BY name').fetchall()]
    conn.close()
    return render_template('admin.html', obits=obits)

# ====================== CREATE ======================
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        obit_id = str(uuid.uuid4())
        name = request.form['name']
        birth_date = request.form['birth_date']
        death_date = request.form['death_date']
        funeral_date = request.form.get('funeral_date', '')
        biography = request.form['biography']
        service_programme = request.form.get('service_programme', '')
        photo_url = request.form.get('photo_url', '')

        conn = sqlite3.connect(DB_FILE)
        conn.execute('''INSERT INTO obituaries 
                     (id, name, birth_date, death_date, funeral_date, biography, service_programme, photo_url) 
                     VALUES (?,?,?,?,?,?,?,?)''',
                     (obit_id, name, birth_date, death_date, funeral_date, biography, service_programme, photo_url))
        conn.commit()
        conn.close()

        # Dynamic QR Code for Render / Local
        base_url = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '127.0.0.1:5000')
        protocol = "https" if "render" in base_url else "http"
        qr_data = f"{protocol}://{base_url}/obituary/{obit_id}"

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        os.makedirs('static/qr', exist_ok=True)
        img.save(f'static/qr/{obit_id}.png')

        return render_template('success.html', obit_id=obit_id, name=name)

    return render_template('create.html')

# ====================== EDIT ======================
@app.route('/edit/<obit_id>', methods=['GET', 'POST'])
def edit(obit_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birth_date']
        death_date = request.form['death_date']
        funeral_date = request.form.get('funeral_date', '')
        biography = request.form['biography']
        service_programme = request.form.get('service_programme', '')
        photo_url = request.form.get('photo_url', '')

        conn.execute('''UPDATE obituaries SET 
                     name=?, birth_date=?, death_date=?, funeral_date=?, 
                     biography=?, service_programme=?, photo_url=? 
                     WHERE id=?''',
                     (name, birth_date, death_date, funeral_date, biography, service_programme, photo_url, obit_id))
        conn.commit()
        conn.close()

        return redirect('/admin')

    row = conn.execute('SELECT * FROM obituaries WHERE id = ?', (obit_id,)).fetchone()
    conn.close()
    if not row:
        return "Obituary not found", 404

    return render_template('edit.html', obit=dict(row))

# ====================== OBITUARY PAGE ======================
@app.route('/obituary/<obit_id>')
def obituary(obit_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT * FROM obituaries WHERE id = ?', (obit_id,)).fetchone()
    conn.close()
    if not row:
        return "Obituary not found", 404
    return render_template('obituary.html', obit=dict(row))

# ====================== SCAN ======================
@app.route('/scan')
def scan():
    return render_template('scan.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)