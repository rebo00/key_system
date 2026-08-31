import sqlite3
import random
import string
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_NAME = "key_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_code TEXT UNIQUE NOT NULL,
            is_used INTEGER DEFAULT 0,
            device_id TEXT DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Key Admin Panel</title>
    <style>
        body { font-family: sans-serif; padding: 20px; background: #f4f4f9; text-align: right; direction: rtl; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        button { background: #28a745; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background: #333; color: white; }
    </style>
</head>
<body>
    <div class="card">
        <h2>پانێڵی دروستکردنی کۆدی VIP</h2>
        <form action="/admin/generate" method="post">
            <label>چەند کۆد دروست بکرێت؟</label>
            <input type="number" name="count" value="5" min="1" max="50">
            <button type="submit">دروستکردن</button>
        </form>
    </div>

    <div class="card">
        <h2>لیستی کۆدەکان</h2>
        <table>
            <tr>
                <th>ژمارە</th>
                <th>کۆد (Key)</th>
                <th>بارودۆخ</th>
                <th>ئایدی مۆبایل (Device ID)</th>
            </tr>
            {% for key in keys %}
            <tr>
                <td>{{ key[0] }}</td>
                <td><b>{{ key[1] }}</b></td>
                <td>{% if key[2] == 1 %} <span style="color:red;">بەکارهاتووە</span> {% else %} <span style="color:green;">بەکارنەهاتووە</span> {% endif %}</td>
                <td>{{ key[3] if key[3] else 'دیاری نەکراوە' }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/verify-key', methods=['POST'])
def verify_key():
    data = request.get_json() or request.form
    user_key = data.get('key')
    device_id = data.get('deviceId')

    if not user_key or not device_id:
        return jsonify({"success": False, "message": "کۆد یان ئایدی مۆبایل بنێرە!"})

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_used, device_id FROM keys WHERE key_code = ?", (user_key,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"success": False, "message": "کۆدەکە هەڵەیە!"})

    is_used, registered_device = row

    if is_used == 1 and registered_device != device_id:
        conn.close()
        return jsonify({"success": False, "message": "ئەم کۆدە پێشتر لە مۆبایلێکی تر بەکارهاتووە!"})

    if is_used == 0:
        cursor.execute("UPDATE keys SET is_used = 1, device_id = ? WHERE key_code = ?", (device_id, user_key))
        conn.commit()

    conn.close()
    return jsonify({"success": True, "message": "کۆدەکە سەرکەوتوو بوو! بەخێربێیت."})

@app.route('/admin', methods=['GET'])
def admin_panel():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM keys ORDER BY id DESC")
    keys = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, keys=keys)

@app.route('/admin/generate', methods=['POST'])
def generate_keys():
    count = int(request.form.get('count', 1))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    for _ in range(count):
        part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        new_key = f"VIP-{part1}-{part2}"
        try:
            cursor.execute("INSERT INTO keys (key_code) VALUES (?)", (new_key,))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    return '<script>alert("کۆدەکان دروستکران!"); window.location.href="/admin";</script>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
