from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    # Este mensaje aparecerá cuando visites la URL de Render
    return "PyA Bot Online 🚀"

def run():
    # Render usa el puerto 8080 por defecto, pero lo dejamos dinámico
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # Esto asegura que el hilo muera si el bot principal muere
    t.start()