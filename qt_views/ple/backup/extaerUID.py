import json
import os

def obtener_valor_json(archivo_json, clave):
  try:
    with open(archivo_json, 'r') as f:
      datos_json = json.load(f)
      return datos_json.get(clave) # Usa get() para evitar errores si la clave no existe
  except FileNotFoundError:
    print(f"Error: Archivo no encontrado: {archivo_json}")
    return None
  except json.JSONDecodeError:
    print(f"Error: Archivo JSON inválido: {archivo_json}")
    return None
  except Exception as e:
      print(f"Error inesperado: {e}")
      return None

# Ejemplo de uso
#C:\000_PLE_Active\DetallesPLE
#archivo = './auth/perfil_usuario.json'


directorio_actual = os.getcwd()
print(f"Directorio actual: {directorio_actual}")
cadenaDirPrincipal = directorio_actual
#print(cadenaDirPrincipal)
subcadena = "qt_views"
indice = cadenaDirPrincipal.index(subcadena)
realIndex = indice-1
#print(f"La subcadena '{subcadena}' se encuentra en la posición {indice}.")
#cadena = "Python es genial"
subcadenaReal = cadenaDirPrincipal[:realIndex]  #
#print(subcadenaReal)
# Ruta relativa a un archivo en un subdirectorio
ruta_relativa = "\\app\\auth\\perfil_usuario.json"
#print(f"Ruta relativa: {ruta_relativa}")
finalLocation = subcadenaReal + ruta_relativa
print(f"final Location: {finalLocation}")

clave_a_extraer = 'uid'
valor = obtener_valor_json(finalLocation, clave_a_extraer)

if valor:
  print(f"El valor de '{clave_a_extraer}' es: {valor}")
else:
  print(f"No se pudo encontrar la clave '{clave_a_extraer}' en el archivo.")
 
 

