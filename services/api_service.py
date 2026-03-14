import requests

API_BASE_URL = "http://127.0.0.1:5000"

def login(usuario: str, contrasena: str) -> dict:
    """
    Realiza una solicitud al endpoint de login.
    Args:
        usuario (str): Nombre de usuario.
        contrasena (str): Contraseña.
    Returns:
        dict: Respuesta del servidor en formato JSON.
    """
    url = f"{API_BASE_URL}/login"
    payload = {"usuario": usuario, "contrasena": contrasena}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Levanta una excepción para códigos de error HTTP
        return response.json()  # Devuelve el JSON si todo salió bien
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}  # Retorna el error como un diccionario
