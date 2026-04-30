import os
import tkinter as tk
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow


load_dotenv()

class GoogleAuth:
    def __init__(self):
        
        self.client_config = {
            "installed": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")]
            }
        }
        self.scopes = ['https://www.googleapis.com/auth/tasks.readonly']

    def authenticate(self):
        
        if not self.client_config["installed"]["client_id"]:
            raise ValueError("Error: GOOGLE_CLIENT_ID no encontrado en el .env")

        flow = InstalledAppFlow.from_client_config(
            self.client_config, 
            scopes=self.scopes
        )
        
        
        creds = flow.run_local_server(port=0)
        return creds


def login_workflow():
    try:
        auth = GoogleAuth()
        creds = auth.authenticate()
        print(f"Token obtenido: {creds.token[:10]}...") 
        status_label.config(text="Estado: Conectado a Google", fg="#2ecc71")
    except Exception as e:
        print(f"Error de login: {e}")
        status_label.config(text="Estado: Error de Conexión", fg="#e74c3c")

root = tk.Tk()
root.geometry("1200x850")
root.title("Workflow Manager - Secure Login")

status_label = tk.Label(root, text="Estado: Desconectado", pady=20)
status_label.pack()

btn = tk.Button(root, text="Iniciar Sesión con Google", 
                command=login_workflow, bg="#4285F4", fg="white")
btn.pack(pady=10)

root.mainloop()