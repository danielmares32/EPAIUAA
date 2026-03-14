# Proyecto EPAI SISTEMA

EPAI (Entorno Personal de Aprendizaje Inteligente) es una plataforma integral diseñada para apoyar la creación, personalización y actualización de entornos de aprendizaje. Este sistema interactúa de manera personalizada con docentes y estudiantes, ofreciendo recomendaciones inteligentes y adaptativas que facilitan la mejora continua de competencias.

Módulo de Seguimiento y Retroalimentación: El sistema monitorea las interacciones de los usuarios y recolecta calificaciones para ajustar las recomendaciones futuras. Incluye la función de calificación y comentario sobre la calidad de los recursos y cursos ofrecidos.

## Descripción

El sistema EPAI permite a los usuarios (docentes y estudiantes) configurar y enriquecer su entorno de aprendizaje mediante recomendaciones de cursos, herramientas, recursos y contactos. Utiliza algoritmos de recomendación y filtros personalizados para mejorar la pertinencia de los recursos sugeridos, adaptándose a los perfiles de accesibilidad y necesidades específicas de cada usuario.

### Funcionalidades

- **Crear Usuario:** Permite registrar un nuevo usuario, verificando si el nombre de usuario ya existe.
- **Manejo de Errores:** Responde con códigos de estado y mensajes adecuados para errores comunes, como la duplicación de nombres de usuario.
- **Interfaz de usuario:** Brinda una interfaz gráfica para el login y vista de Dashboard de EPAI.
- **Chrome Integration:** Extrae historial de navegación de Chrome y genera keywords usando NLP avanzado.
- **PLE Management:** Gestión completa de entornos de aprendizaje personalizados.
- **API Synchronization:** Sincronización automática de datos con servidor remoto mediante POST requests.

## Requisitos

- Python 3.x
- Flask
- SQLAlchemy
- Flask-Migrate
- QT5
- bcrypt
- scapy
- requests

## Instalación

### 1. Clonar el repositorio

#### Repositorio principal
```
git clone https://github.com/manuelhuertasespinoza/EPAI-SISTEMA.git
cd EPAI-SISTEMA
```
#### Cambiar de rama (de ser necesario únicamente)

```
git checkout login
```

### 2. Crear el entorno virtual

```
python -m venv venv
source venv/bin/activate  # En Linux/macOS
venv\Scripts\activate     # En Windows
```

### 3. Instalar dependencias

```
pip install -r requirements.txt
```

### 4. Ejecución del servicio

```
python main.py
```

#### 4.1 Ejecución del servicio en ciertos sistemas operativos con niveles de usuarios

En Algunos sistemas operativos como Linux, existe manejo de niveles y de ejecución restringida para ciertas herramientas según lo que realicen, en este caso, es necesario en estos tipos de sistemas ejecutar el aplicativo como super usuario de la siguiente manera:

```
sudo python main.py
```

### 5. CURLS

#### Creación de usuario

```
curl --location 'http://127.0.0.1:5000/signup' \
--header 'Content-Type: application/json' \
--data-raw '{
    "nombre": "name",
    "apellido": "lastname",
    "usuario": "user",
    "contrasena": "password"
}'
```

#### Verificación de usuario

```
curl --location 'http://127.0.0.1:5000/login' \
--header 'Content-Type: application/json' \
--data-raw '{
    "usuario": "user",
    "contrasena": "password"
}'
```

#### Verificar perfiles de usuario de Google Chrome

```
curl --location 'http://127.0.0.1:5000/chrome/profiles'
```

#### Extraer keywords de Chrome por perfil

```
curl --location 'http://127.0.0.1:5000/chrome/keywords/Default'
```

## Características Avanzadas

### Integración con Chrome
- **Extracción de historial:** Acceso directo a la base de datos de Chrome
- **Análisis NLP:** Generación de keywords usando RAKE, KeyBERT, YAKE y spaCy
- **Soporte multiplataforma:** Windows, macOS y Linux
- **Procesamiento en background:** Interfaz no bloqueante con threads Qt

### Sincronización API
- **Endpoint:** `https://uninovadeplan-ws.javali.pt/tracked-data-batch`
- **Formato:** JSON con estructura completa de tracked data
- **Threading seguro:** Manejo apropiado de Qt signals/slots
- **Feedback visual:** Overlays de progreso y confirmación con batch IDs

### 6. Anexo

#### Login

![Login](/assets/preview_login.png)

#### Dashboard

![Dashboard](/assets/preview_dashboard.png)