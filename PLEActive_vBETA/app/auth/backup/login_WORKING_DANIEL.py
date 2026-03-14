# app/auth/login.py
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify

bp = Blueprint('login', __name__, url_prefix='/auth')  # <-- ¡Agrega url_prefix!

# Función real que realiza la autenticación externa
def login_externo(usuario, contrasena):
    url = "https://uninovadeplan.dev11.javali.pt/user/login"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
    }

    data = {
        "name": usuario,
        "pass": contrasena,
        "form_id": "user_login_form",
        "op": "Iniciar sesión"
    }

    print(data)

    try:
        response = requests.post(url, headers=headers, data=data)

        # Validación: buscamos el token en el HTML
        soup = BeautifulSoup(response.text, "html.parser")
        script_tags = soup.find_all("script", type="application/vnd.drupal-ajax")

        for tag in script_tags:
            token_raw = tag.get("data-big-pipe-replacement-for-placeholder-with-id", "")
            if "token=" in token_raw:
                return {
                    "status": True,
                    "message": "Inicio de sesión exitoso",
                    "token": token_raw
                }

        return {
            "status": False,
            "message": "Credenciales inválidas o token no encontrado."
        }

    except Exception as e:
        return {
            "status": False,
            "message": f"Error en la solicitud: {e}"
        }

# Ruta expuesta por Flask
@bp.route('/login', methods=['POST'])
def login_route():
    usuario = request.form.get("username")
    contrasena = request.form.get("password")

    if not usuario or not contrasena:
        return jsonify({"status": False, "error": "Faltan campos."}), 400

    resultado = login_externo(usuario, contrasena)

    if resultado.get("status"):
        return jsonify({"status": True, "message": resultado.get("message"), "token": resultado.get("token")}), 200
    else:
        return jsonify({"status": False, "error": resultado.get("message")}), 401