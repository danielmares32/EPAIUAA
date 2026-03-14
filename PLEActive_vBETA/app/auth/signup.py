from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import User
from ..database import db

bp = Blueprint('signup', __name__)

@bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    hashed_password = generate_password_hash(data['contrasena'], method='pbkdf2:sha256')
    new_user = User(
        nombre=data['nombre'],
        apellido=data['apellido'],
        usuario=data['usuario'],
        contrasena=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        "message": "Usuario creado exitosamente",
        "status": True,
        "code": 200
        }), 201