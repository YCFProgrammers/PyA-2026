from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests

load_dotenv("log.env")

app = Flask(__name__)
CORS(app)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

@app.route("/auth/google", methods=["POST"])
def google_auth():
    try:
        data = request.get_json()
        token = data.get("token")

        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        user_data = {
            "name": idinfo.get("name"),
            "email": idinfo.get("email"),
            "picture": idinfo.get("picture")
        }

        return jsonify({
            "status": "success",
            "user": user_data,
            "access_token": token
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401


if __name__ == "__main__":
    app.run(port=5000, debug=True)