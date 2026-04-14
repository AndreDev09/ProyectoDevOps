from flask import Flask, jsonify
import datetime

app = Flask(__name__)

VERSION = "1.0.1-stable"

@app.route("/")
def home():
    return jsonify({
        "mensaje": "App financiera operativa",
        "proyecto": "Restaurante-JJIA-Finanzas",
        "version": VERSION
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "up",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": VERSION
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)