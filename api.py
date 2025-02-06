from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Conexão com o banco de dados SQLite
def connect_db():
    return sqlite3.connect('licenses.db')

@app.route('/validate', methods=['POST'])
def validate_license():
    data = request.json
    license_key = data.get('license_key')
    if not license_key:
        return jsonify({'error': 'Chave de licença não fornecida'}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM licenses WHERE license_key = ? AND is_active = 1",
        (license_key,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({'error': 'Chave inválida ou inativa'}), 400

    expiration_date = result[2]
    if datetime.now() > datetime.fromisoformat(expiration_date):
        return jsonify({'error': 'Chave expirada'}), 400

    return jsonify({'message': 'Chave válida', 'expiration_date': expiration_date}), 200

@app.route('/generate', methods=['POST'])
def generate_license():
    data = request.json
    admin_key = data.get('admin_key')
    days_valid = data.get('days_valid', 30)

    # Valida a chave de administração
    if admin_key != '40028922':
        return jsonify({'error': 'Acesso negado'}), 403

    # Gera uma nova chave
    license_key = f"LICENSE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    expiration_date = (datetime.now() + timedelta(days=days_valid)).isoformat()

    # Salva no banco de dados
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO licenses (license_key, expiration_date, is_active) VALUES (?, ?, ?)",
        (license_key, expiration_date, 1)
    )
    conn.commit()
    conn.close()

    return jsonify({'license_key': license_key, 'expiration_date': expiration_date}), 201

if __name__ == '__main__':
    app.run(debug=True)