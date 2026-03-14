from .database import db
from datetime import datetime

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(150), nullable=True)

class Permission(db.Model):
    __tablename__ = "permisos"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    type = db.Column(db.String(50))
    component = db.Column(db.String(50))
    description = db.Column(db.String(150), nullable=True)

class User(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(100), nullable=False)

class WebTracking(db.Model):
    __tablename__ = 'webtracking'
    id = db.Column(db.Integer, primary_key=True)
    idusuario = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    ipaddress = db.Column(db.String(45), nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WebHistory(db.Model):
    __tablename__ = 'webhistory'
    id = db.Column(db.Integer, primary_key=True)
    idwebtracking = db.Column(db.Integer, db.ForeignKey('webtracking.id'))
    site = db.Column(db.String(100))
    domain = db.Column(db.String(100))
    ip = db.Column(db.String(45))
    timesvisited = db.Column(db.Integer, default=1)
    timevisited = db.Column(db.DateTime, default=datetime.utcnow)
    fecha = db.Column(db.Date, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)