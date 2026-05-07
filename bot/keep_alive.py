import os
import logging
from threading import Thread

from flask import Flask
from waitress import serve

log = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    # Este mensaje aparecerá cuando visites la URL de Render
    return "PyA Bot Online 🚀"

def run():
    # Render usa el puerto 8080 por defecto, pero lo dejamos dinámico
    port = int(os.getenv("PORT", "8080"))
    # waitress en lugar del dev server de Flask
    serve(app, host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Esto asegura que el hilo muera si el bot principal muere
    t.start()
