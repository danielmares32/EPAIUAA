import requests
import json
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify, session
import os

# --- Configuración ---
bp = Blueprint('auth', __name__, url_prefix='/auth')
#siSePuede=10
#idUsuarioSesion = None
global idUsuarioSesion


def authenticate_and_get_profile(usuario, contrasena):
    """
    Realiza el login externo, extrae el ID de usuario de la respuesta HTML
    y, si tiene éxito, obtiene los datos del perfil.
    """
    login_url = "https://uninovadeplan.dev11.javali.pt/user/login"
    profile_url_template = "https://uninovadeplan-ws.javali.pt/get-platform-profile/{}"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
    }

    login_data = {
        "name": usuario,
        "pass": contrasena,
        "form_id": "user_login_form",
        "op": "Iniciar sesión"
    }

    # Usamos una sesión para que las cookies se manejen automáticamente
    with requests.Session() as s:
        try:
            # 1. Intento de Login
            login_response = s.post(login_url, headers=headers, data=login_data, timeout=10)
            login_response.raise_for_status()

            # 2. Extracción del ID de Usuario desde el HTML de respuesta
            soup = BeautifulSoup(login_response.text, "html.parser")
            
            # Buscamos la etiqueta <script> que contiene la configuración de Drupal en JSON
            settings_script = soup.find('script', {'data-drupal-selector': 'drupal-settings-json'})

            if not settings_script:
                return {"status": False, "message": "Login fallido. No se encontró la información de sesión en la respuesta."}

            user_id = None
            
            try:
                # Parseamos el contenido de la etiqueta <script> como JSON
                drupal_settings = json.loads(settings_script.string)
                
                # Extraemos la ruta actual, ej: "user/1"
                current_path = drupal_settings.get('path', {}).get('currentPath', '')
                
                # Verificamos que la ruta comience con "user/"
                if current_path.startswith('user/'):
                    extracted_part = current_path.split('/')[-1]
                    if extracted_part.isdigit():
                        user_id = extracted_part
                        idUsuarioSesion = extracted_part

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                return {"status": False, "message": f"No se pudo encontrar un ID de usuario existente en la respuesta: {e}"}

            if not user_id:
                 return {"status": False, "message": "Credenciales inválidas o usuario inexistente."}

            print(f"Login exitoso. ID de usuario extraído: {user_id}")  #Aquí se imprime el userID
            #idUsuarioSesion = user_id

            # 3. Obtención del Perfil del Usuario
            profile_url = profile_url_template.format(user_id)
            from config.config import get_auth_headers
            profile_headers = {'accept': 'application/json'}
            profile_headers.update(get_auth_headers())
            
            profile_response = s.get(profile_url, headers=profile_headers, timeout=10)
            profile_response.raise_for_status()
            
            profile_data = profile_response.json()
            
            #mi_variable = {"nombre": "Juan", "edad": 30, "ciudad": "Madrid"}
            #guardar_en_json(profile_data, "perfil_usuario.json")
            
            #nombre_archivo = "C:\\000_PLE_Active\\EPAI-SISTEMA-UAM-USERID\\app\\auth\\perfil_usuario.json" 
            #C:\000_PLE_Active\ultimaVersionDanielPost\app\auth
            #nombre_archivo = "C:\\000_PLE_Active\\ultimaVersionDanielPostv1\\app\\auth\\perfil_usuario.json"  #Funcionando
            #nombre_archivo = "./auth/perfil_usuario.json"
            directorio_actual = os.getcwd()
            cadenaDirPrincipal = directorio_actual
            print(f"Directorio actual: {directorio_actual}")
            print(cadenaDirPrincipal)
            # Ruta relativa a un archivo en un subdirectorio
            ruta_relativa = "\\app\\auth\\perfil_usuario.json"
            print(f"Ruta relativa: {ruta_relativa}")
            finalLocation = cadenaDirPrincipal + ruta_relativa
            print(f"final Location: {finalLocation}")
            # Crear la ruta absoluta a partir de la relativa
            ruta_absoluta = os.path.join(directorio_actual, ruta_relativa)
            print(f"Ruta absoluta: {ruta_absoluta}")
            nombre_archivo = finalLocation
            try:
                with open(nombre_archivo, 'w') as f:
                  json.dump(profile_data, f, indent=4)  # indent para formato legible
                print(f"Datos guardados exitosamente en {nombre_archivo}")
                print("Esto está funcionando")
            except Exception as e:
              print(f"Error al guardar en {nombre_archivo}: {e}")
            
            

            # 4. Éxito: Devolvemos el perfil completo
            return {
                "status": True,
                "message": "Inicio de sesión y obtención de perfil exitosos.",
                "profile": profile_data
            }

        except requests.exceptions.RequestException as e:
            return {"status": False, "message": f"Error en la comunicación con el servicio externo: {e}"}
        except Exception as e:
            return {"status": False, "message": f"Error inesperado en el proceso: {e}"}

# --- Rutas de la API

@bp.route('/login', methods=['POST'])
def login_route():
    """
    Endpoint para que el cliente (la app de QT) inicie sesión.
    """
    usuario = request.form.get("username")
    contrasena = request.form.get("password")

    if not usuario or not contrasena:
        return jsonify({"status": False, "error": "Faltan los campos 'username' y 'password'."}), 400

    resultado = authenticate_and_get_profile(usuario, contrasena)

    if resultado.get("status"):
        # Si el login es exitoso, guardamos el perfil en la sesión.
        session['user_profile'] = resultado.get("profile")
        
        # Devolvemos el perfil al cliente.
        return jsonify({
            "status": True,
            "message": resultado.get("message"),
            "profile": resultado.get("profile")
        }), 200
    else:
        # Si falla, devolvemos el error.
        return jsonify({"status": False, "error": resultado.get("message")}), 401

@bp.route('/profile', methods=['GET'])
def get_profile_route():
    """
    Endpoint para obtener el perfil del usuario logueado en cualquier momento.
    Recupera la información guardada en la sesión.
    """
    if 'user_profile' in session:
        return jsonify({
            "status": True,
            "profile": session['user_profile']
        }), 200
    else:
        return jsonify({
            "status": False,
            "error": "No hay sesión activa. Por favor, inicie sesión primero."
        }), 401